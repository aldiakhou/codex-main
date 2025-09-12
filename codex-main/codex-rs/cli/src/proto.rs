use std::io::IsTerminal;

use clap::Parser;
use codex_common::CliConfigOverrides;
use codex_core::ConversationManager;
use codex_core::NewConversation;
use codex_core::config::Config;
use codex_core::config::ConfigOverrides;
use codex_core::protocol::Event;
use codex_core::protocol::EventMsg;
use codex_core::protocol::Submission;
use codex_core::protocol::Op;
use codex_core::protocol::{
    AgentsListedEvent, AgentListItem, AgentRunStartedEvent, AgentStatusEvent, AgentCancelledEvent,
};
use codex_agents::{load_agents_from_home, AgentRegistry, summarize_agents};
use jsonschema::JSONSchema;
use uuid::Uuid;
use codex_login::AuthManager;
use tokio::io::AsyncBufReadExt;
use tokio::io::BufReader;
use tracing::error;
use tracing::info;
use serde::Serialize;

#[derive(Debug, Parser)]
pub struct ProtoCli {
    #[clap(skip)]
    pub config_overrides: CliConfigOverrides,
}

pub async fn run_main(opts: ProtoCli) -> anyhow::Result<()> {
    if std::io::stdin().is_terminal() {
        anyhow::bail!("Protocol mode expects stdin to be a pipe, not a terminal");
    }

    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .init();

    let ProtoCli { config_overrides } = opts;
    let overrides_vec = config_overrides
        .parse_overrides()
        .map_err(anyhow::Error::msg)?;

    let overrides_vec_arc = std::sync::Arc::new(overrides_vec);
    let mut base_config = Config::load_with_cli_overrides((*overrides_vec_arc).clone(), ConfigOverrides::default())?;
    // Use conversation_manager API to start a conversation
    let conversation_manager = ConversationManager::new(AuthManager::shared(
        base_config.codex_home.clone(),
        base_config.preferred_auth_method,
    ));
    let NewConversation {
        conversation_id: _,
        conversation,
        session_configured,
    } = conversation_manager.new_conversation(base_config.clone()).await?;

    // Simulate streaming the session_configured event.
    let synthetic_event = Event {
        // Fake id value.
        id: "".to_string(),
        msg: EventMsg::SessionConfigured(session_configured),
    };
    let session_configured_event = match serde_json::to_string(&synthetic_event) {
        Ok(s) => s,
        Err(e) => {
            error!("Failed to serialize session_configured: {e}");
            return Err(anyhow::Error::from(e));
        }
    };
    println!("{session_configured_event}");

    // Helper to wrap events with per-run metadata when known.
    #[derive(Serialize)]
    struct EventMetaTop {
        task_id: Uuid,
        agent_id: String,
    }
    #[derive(Serialize)]
    struct EventWithMetaTop<'a> {
        #[serde(rename = "_meta")] meta: EventMetaTop,
        #[serde(flatten)] event: &'a Event,
    }
    fn emit_event_with_meta(event: &Event, task_id: Uuid, agent_id: &str) {
        let wrapped = EventWithMetaTop { meta: EventMetaTop { task_id, agent_id: agent_id.to_string() }, event };
        match serde_json::to_string(&wrapped) {
            Ok(s) => println!("{}", s),
            Err(e) => eprintln!("failed to serialize event with meta: {e}"),
        }
    }

    // Task that reads JSON lines from stdin and forwards to Submission Queue
    #[derive(Clone)]
    struct AgentTaskInfo {
        conv: std::sync::Arc<codex_core::CodexConversation>,
        status: String,
        error: Option<String>,
        agent_id: String,
    }
    let tasks = std::sync::Arc::new(tokio::sync::Mutex::new(
        std::collections::HashMap::<Uuid, AgentTaskInfo>::new(),
    ));
    let conversation_manager_arc = std::sync::Arc::new(conversation_manager);
    let codex_home = base_config.codex_home.clone();
    let overrides_vec2 = overrides_vec_arc.clone();
    let sq_fut = {
        let conversation = conversation.clone();
        let conversation_manager = conversation_manager_arc.clone();
        let tasks_map = tasks.clone();
        async move {
            let stdin = BufReader::new(tokio::io::stdin());
            let mut lines = stdin.lines();
            loop {
                let result = tokio::select! {
                    _ = tokio::signal::ctrl_c() => {
                        break
                    },
                    res = lines.next_line() => res,
                };

                match result {
                    Ok(Some(line)) => {
                        let line = line.trim();
                        if line.is_empty() {
                            continue;
                        }
                        match serde_json::from_str::<Submission>(line) {
                            Ok(sub) => {
                                // Intercept agent ops.
                                match sub.op.clone() {
                                    Op::ListAgents => {
                                        let builtins = AgentRegistry::default_with_builtins().list();
                                        let specs = load_agents_from_home(&codex_home).unwrap_or_default();
                                        let agents = summarize_agents(&specs, &builtins)
                                            .into_iter()
                                            .map(|s| AgentListItem { id: s.id, name: s.name, description: s.description })
                                            .collect::<Vec<_>>();
                                        let ev = Event { id: sub.id.clone(), msg: EventMsg::AgentsListed(AgentsListedEvent { agents }) };
                                        if let Ok(s) = serde_json::to_string(&ev) { println!("{}", s); }
                                        continue;
                                    }
                                    Op::StartAgent { id, input, context } => {
                                        let agent_id_owned = id.clone();
                                        let task_id = Uuid::new_v4();
                                        // Build specific config for the agent
                                        let mut cfg = Config::load_with_cli_overrides((*overrides_vec2).clone(), ConfigOverrides::default())
                                            .unwrap_or_else(|_| base_config.clone());
                                        // Load agent spec (prefer configured one)
                                        let specs = load_agents_from_home(&codex_home).unwrap_or_default();
                                        if let Some(spec) = specs.iter().find(|a| a.id == agent_id_owned) {
                                            cfg = codex_core::agents_helpers::apply_spec_to_config(cfg, spec);
                                        } else {
                                            // Simple builtin defaults
                                            if agent_id_owned == "web_search" { cfg.tools_web_search_request = true; }
                                            cfg.include_plan_tool = true;
                                        }

                                        let NewConversation { conversation: agent_conv, .. } = match conversation_manager.new_conversation(cfg).await {
                                            Ok(v) => v,
                                            Err(e) => {
                                                let ev = Event { id: sub.id.clone(), msg: EventMsg::Error(codex_core::protocol::ErrorEvent { message: format!("failed to start agent: {e:#}") }) };
                                                if let Ok(s) = serde_json::to_string(&ev) { println!("{}", s); }
                                                continue;
                                            }
                                        };

                                        // Emit started event with meta
                                        let started = Event { id: sub.id.clone(), msg: EventMsg::AgentRunStarted(AgentRunStartedEvent { agent_id: agent_id_owned.clone(), task_id }) };
                                        emit_event_with_meta(&started, task_id, &agent_id_owned);

                                        // Submit the user input (input or goal)
                                        let prompt = input.clone().unwrap_or_else(|| "".to_string());
                                        if !prompt.is_empty() || context.is_some() {
                                            let mut text = prompt;
                                            if let Some(ctx) = context.clone() {
                                                text.push_str("\n\nContext:\n");
                                                text.push_str(&serde_json::to_string_pretty(&ctx).unwrap_or_default());
                                            }
                                            let items = vec![codex_core::protocol::InputItem::Text { text }];
                                            let _ = agent_conv.submit(Op::UserInput { items }).await;
                                        }

                                        // Stream events to stdout and enforce optional output schema at end
                                        let specs_clone = specs.clone();
                                        let tasks_map2 = tasks_map.clone();
                                        let tid = task_id.clone();
                                        let agent_id_for_spawn = agent_id_owned.clone();
                                        let agent_conv_for_spawn = agent_conv.clone();
                                        #[derive(Serialize)]
                                        struct EventMeta {
                                            task_id: uuid::Uuid,
                                            agent_id: String,
                                        }
                                        #[derive(Serialize)]
                                        struct EventWithMeta<'a> {
                                            #[serde(rename = "_meta")] meta: EventMeta,
                                            #[serde(flatten)] event: &'a Event,
                                        }

                                        fn print_event_with_meta(event: &Event, task_id: uuid::Uuid, agent_id: &str) {
                                            let wrapped = EventWithMeta { meta: EventMeta { task_id, agent_id: agent_id.to_string() }, event };
                                            match serde_json::to_string(&wrapped) {
                                                Ok(s) => println!("{}", s),
                                                Err(e) => eprintln!("failed to serialize event with meta: {e}"),
                                            }
                                        }

                                        tokio::spawn(async move {
                                            let agent_conv = agent_conv_for_spawn;
                                            let mut final_text = String::new();
                                            loop {
                                                match agent_conv.next_event().await {
                                                    Ok(ev) => {
                                                        match &ev.msg {
                                                            EventMsg::AgentMessageDelta(d) => final_text.push_str(&d.delta),
                                                            EventMsg::AgentMessage(m) => final_text = m.message.clone(),
                                                            EventMsg::TaskComplete(_) => {
                                                                // Validate against schema if present for this agent id
                                                                if let Some(spec) = specs_clone.iter().find(|a| a.id == agent_id_for_spawn) {
                                                                    if let Some(schema_str) = &spec.output_schema {
                                                                        if let Ok(schema_json) = serde_json::from_str::<serde_json::Value>(schema_str) {
                                                                            if let Ok(compiled) = JSONSchema::compile(&schema_json) {
                                                                                match serde_json::from_str::<serde_json::Value>(&final_text) {
                                                                                    Ok(val) => {
                                                                                        if let Err(errors) = compiled.validate(&val) {
                                                                                            let msg = errors.map(|e| e.to_string()).collect::<Vec<_>>().join("; ");
                                                                                            let err_ev = Event { id: "".to_string(), msg: EventMsg::Error(codex_core::protocol::ErrorEvent { message: format!("output schema validation failed: {msg}") }) };
                                                                                             print_event_with_meta(&err_ev, tid, &agent_id_for_spawn);
                                                                                            let mut guard = tasks_map2.lock().await;
                                                                                            if let Some(info) = guard.get_mut(&tid) {
                                                                                                info.status = "error".to_string();
                                                                                                info.error = Some(format!("output schema validation failed: {msg}"));
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                    Err(_) => {
                                                                                        let err_ev = Event { id: "".to_string(), msg: EventMsg::Error(codex_core::protocol::ErrorEvent { message: "final output is not valid JSON".to_string() }) };
                                                                                        print_event_with_meta(&err_ev, tid, &agent_id_for_spawn);
                                                                                        let mut guard = tasks_map2.lock().await;
                                                                                        if let Some(info) = guard.get_mut(&tid) {
                                                                                            info.status = "error".to_string();
                                                                                            info.error = Some("final output is not valid JSON".to_string());
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                                let mut guard = tasks_map2.lock().await;
                                                                if let Some(info) = guard.get_mut(&tid) {
                                                                    if info.status != "error" { info.status = "complete".to_string(); }
                                                                }
                                                            }
                                                            _ => {}
                                                        }
                                                        print_event_with_meta(&ev, tid, &agent_id_for_spawn);
                                                        if matches!(ev.msg, EventMsg::TaskComplete(_) | EventMsg::ShutdownComplete) { break; }
                                                    }
                                                    Err(e) => {
                                                        let err_ev = Event { id: "".to_string(), msg: EventMsg::Error(codex_core::protocol::ErrorEvent { message: format!("agent stream error: {e:#}") }) };
                                                        print_event_with_meta(&err_ev, tid, &agent_id_for_spawn);
                                                        let mut guard = tasks_map2.lock().await;
                                                        if let Some(info) = guard.get_mut(&tid) {
                                                            info.status = "error".to_string();
                                                            info.error = Some(format!("agent stream error: {e:#}"));
                                                        }
                                                        break;
                                                    }
                                                }
                                            }
                                        });

                                        tasks_map.lock().await.insert(
                                            task_id,
                                            AgentTaskInfo { conv: agent_conv, status: "running".to_string(), error: None, agent_id: id.clone() },
                                        );
                                        continue;
                                    }
                                    Op::AgentStatus { task_id } => {
                                        let tid = Uuid::parse_str(&task_id).unwrap_or_else(|_| Uuid::nil());
                                        let (status, error, agent_id) = {
                                            let guard = tasks_map.lock().await;
                                            match guard.get(&tid) {
                                                Some(info) => (info.status.clone(), info.error.clone(), info.agent_id.clone()),
                                                None => ("not-found".to_string(), None, String::new()),
                                            }
                                        };
                                        let ev = Event { id: sub.id.clone(), msg: EventMsg::AgentStatus(AgentStatusEvent { task_id: tid, status, error }) };
                                        emit_event_with_meta(&ev, tid, &agent_id);
                                        continue;
                                    }
                                    Op::AgentCancel { task_id } => {
                                        let tid = Uuid::parse_str(&task_id).unwrap_or_else(|_| Uuid::nil());
                                        let agent_id_for_meta = {
                                            let guard = tasks_map.lock().await;
                                            guard.get(&tid).map(|i| i.agent_id.clone()).unwrap_or_default()
                                        };
                                        if let Some(info) = tasks_map.lock().await.get(&tid).cloned() {
                                            let _ = info.conv.submit(Op::Interrupt).await;
                                        }
                                        let ev = Event { id: sub.id.clone(), msg: EventMsg::AgentCancelled(AgentCancelledEvent { task_id: tid }) };
                                        emit_event_with_meta(&ev, tid, &agent_id_for_meta);
                                        continue;
                                    }
                                    Op::AgentsReload => {
                                        let builtins = AgentRegistry::default_with_builtins().list();
                                        let specs = load_agents_from_home(&codex_home).unwrap_or_default();
                                        let agents = summarize_agents(&specs, &builtins)
                                            .into_iter()
                                            .map(|s| AgentListItem { id: s.id, name: s.name, description: s.description })
                                            .collect::<Vec<_>>();
                                        let ev = Event { id: sub.id.clone(), msg: EventMsg::AgentsListed(AgentsListedEvent { agents }) };
                                        if let Ok(s) = serde_json::to_string(&ev) { println!("{}", s); }
                                        continue;
                                    }
                                    _ => {}
                                }
                                if let Err(e) = conversation.submit_with_id(sub).await {
                                    error!("{e:#}");
                                    break;
                                }
                            }
                            Err(e) => {
                                error!("invalid submission: {e}");
                            }
                        }
                    }
                    _ => {
                        info!("Submission queue closed");
                        break;
                    }
                }
            }
        }
    };

    // Task that reads events from the agent and prints them as JSON lines to stdout
    let eq_fut = async move {
        loop {
            let event = tokio::select! {
                _ = tokio::signal::ctrl_c() => break,
                event = conversation.next_event() => event,
            };
            match event {
                Ok(event) => {
                    let event_str = match serde_json::to_string(&event) {
                        Ok(s) => s,
                        Err(e) => {
                            error!("Failed to serialize event: {e}");
                            continue;
                        }
                    };
                    println!("{event_str}");
                }
                Err(e) => {
                    error!("{e:#}");
                    break;
                }
            }
        }
        info!("Event queue closed");
    };

    tokio::join!(sq_fut, eq_fut);
    Ok(())
}
