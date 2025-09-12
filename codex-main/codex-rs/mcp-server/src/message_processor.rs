use std::collections::HashMap;
use std::path::PathBuf;

use crate::codex_message_processor::CodexMessageProcessor;
use crate::codex_tool_config::CodexToolCallParam;
use crate::codex_tool_config::CodexToolCallReplyParam;
use crate::codex_tool_config::create_tool_for_codex_tool_call_param;
use crate::codex_tool_config::create_tool_for_codex_tool_call_reply_param;
// Agents tools are now built-in in core; MCP server no longer exposes them
// (agents_* types no longer used here)
// (no agent-spec mapping in MCP server anymore)
use crate::error_code::INVALID_REQUEST_ERROR_CODE;
use crate::outgoing_message::OutgoingMessageSender;
use codex_protocol::mcp_protocol::ClientRequest;

use codex_core::ConversationManager;
use codex_core::config::Config;
use codex_core::protocol::Submission;
use codex_login::AuthManager;
use mcp_types::CallToolRequestParams;
use mcp_types::CallToolResult;
use mcp_types::ClientRequest as McpClientRequest;
use mcp_types::ContentBlock;
use mcp_types::JSONRPCError;
use mcp_types::JSONRPCErrorError;
use mcp_types::JSONRPCNotification;
use mcp_types::JSONRPCRequest;
use mcp_types::JSONRPCResponse;
use mcp_types::ListToolsResult;
use mcp_types::ModelContextProtocolRequest;
use mcp_types::RequestId;
use mcp_types::ServerCapabilitiesTools;
use mcp_types::ServerNotification;
use mcp_types::TextContent;
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::task;
use uuid::Uuid;

pub(crate) struct MessageProcessor {
    codex_message_processor: CodexMessageProcessor,
    outgoing: Arc<OutgoingMessageSender>,
    initialized: bool,
    codex_linux_sandbox_exe: Option<PathBuf>,
    conversation_manager: Arc<ConversationManager>,
    running_requests_id_to_codex_uuid: Arc<Mutex<HashMap<RequestId, Uuid>>>,
}

impl MessageProcessor {
    /// Create a new `MessageProcessor`, retaining a handle to the outgoing
    /// `Sender` so handlers can enqueue messages to be written to stdout.
    pub(crate) fn new(
        outgoing: OutgoingMessageSender,
        codex_linux_sandbox_exe: Option<PathBuf>,
        config: Arc<Config>,
    ) -> Self {
        let outgoing = Arc::new(outgoing);
        let auth_manager =
            AuthManager::shared(config.codex_home.clone(), config.preferred_auth_method);
        let conversation_manager = Arc::new(ConversationManager::new(auth_manager.clone()));
        let codex_message_processor = CodexMessageProcessor::new(
            auth_manager,
            conversation_manager.clone(),
            outgoing.clone(),
            codex_linux_sandbox_exe.clone(),
            config.clone(),
        );
        Self {
            codex_message_processor,
            outgoing,
            initialized: false,
            codex_linux_sandbox_exe,
            conversation_manager,
            running_requests_id_to_codex_uuid: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub(crate) async fn process_request(&mut self, request: JSONRPCRequest) {
        if let Ok(request_json) = serde_json::to_value(request.clone())
            && let Ok(codex_request) = serde_json::from_value::<ClientRequest>(request_json)
        {
            // If the request is a Codex request, handle it with the Codex
            // message processor.
            self.codex_message_processor
                .process_request(codex_request)
                .await;
            return;
        }

        // Hold on to the ID so we can respond.
        let request_id = request.id.clone();

        let client_request = match McpClientRequest::try_from(request) {
            Ok(client_request) => client_request,
            Err(e) => {
                tracing::warn!("Failed to convert request: {e}");
                return;
            }
        };

        // Dispatch to a dedicated handler for each request type.
        match client_request {
            McpClientRequest::InitializeRequest(params) => {
                self.handle_initialize(request_id, params).await;
            }
            McpClientRequest::PingRequest(params) => {
                self.handle_ping(request_id, params).await;
            }
            McpClientRequest::ListResourcesRequest(params) => {
                self.handle_list_resources(params);
            }
            McpClientRequest::ListResourceTemplatesRequest(params) => {
                self.handle_list_resource_templates(params);
            }
            McpClientRequest::ReadResourceRequest(params) => {
                self.handle_read_resource(params);
            }
            McpClientRequest::SubscribeRequest(params) => {
                self.handle_subscribe(params);
            }
            McpClientRequest::UnsubscribeRequest(params) => {
                self.handle_unsubscribe(params);
            }
            McpClientRequest::ListPromptsRequest(params) => {
                self.handle_list_prompts(params);
            }
            McpClientRequest::GetPromptRequest(params) => {
                self.handle_get_prompt(params);
            }
            McpClientRequest::ListToolsRequest(params) => {
                self.handle_list_tools(request_id, params).await;
            }
            McpClientRequest::CallToolRequest(params) => { self.handle_call_tool(request_id, params).await; }
            McpClientRequest::SetLevelRequest(params) => {
                self.handle_set_level(params);
            }
            McpClientRequest::CompleteRequest(params) => {
                self.handle_complete(params);
            }
        }
    }

    /// Handle a standalone JSON-RPC response originating from the peer.
    pub(crate) async fn process_response(&mut self, response: JSONRPCResponse) {
        tracing::info!("<- response: {:?}", response);
        let JSONRPCResponse { id, result, .. } = response;
        self.outgoing.notify_client_response(id, result).await
    }

    /// Handle a fire-and-forget JSON-RPC notification.
    pub(crate) async fn process_notification(&mut self, notification: JSONRPCNotification) {
        let server_notification = match ServerNotification::try_from(notification) {
            Ok(n) => n,
            Err(e) => {
                tracing::warn!("Failed to convert notification: {e}");
                return;
            }
        };

        // Similar to requests, route each notification type to its own stub
        // handler so additional logic can be implemented incrementally.
        match server_notification {
            ServerNotification::CancelledNotification(params) => {
                self.handle_cancelled_notification(params).await;
            }
            ServerNotification::ProgressNotification(params) => {
                self.handle_progress_notification(params);
            }
            ServerNotification::ResourceListChangedNotification(params) => {
                self.handle_resource_list_changed(params);
            }
            ServerNotification::ResourceUpdatedNotification(params) => {
                self.handle_resource_updated(params);
            }
            ServerNotification::PromptListChangedNotification(params) => {
                self.handle_prompt_list_changed(params);
            }
            ServerNotification::ToolListChangedNotification(params) => {
                self.handle_tool_list_changed(params);
            }
            ServerNotification::LoggingMessageNotification(params) => {
                self.handle_logging_message(params);
            }
        }
    }

    /// Handle an error object received from the peer.
    pub(crate) fn process_error(&mut self, err: JSONRPCError) {
        tracing::error!("<- error: {:?}", err);
    }

    async fn handle_initialize(
        &mut self,
        id: RequestId,
        params: <mcp_types::InitializeRequest as ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("initialize -> params: {:?}", params);

        if self.initialized {
            // Already initialised: send JSON-RPC error response.
            let error = JSONRPCErrorError {
                code: INVALID_REQUEST_ERROR_CODE,
                message: "initialize called more than once".to_string(),
                data: None,
            };
            self.outgoing.send_error(id, error).await;
            return;
        }

        self.initialized = true;

        // Build a minimal InitializeResult. Fill with placeholders.
        let result = mcp_types::InitializeResult {
            capabilities: mcp_types::ServerCapabilities {
                completions: None,
                experimental: None,
                logging: None,
                prompts: None,
                resources: None,
                tools: Some(ServerCapabilitiesTools {
                    list_changed: Some(true),
                }),
            },
            instructions: None,
            protocol_version: params.protocol_version.clone(),
            server_info: mcp_types::Implementation {
                name: "codex-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
                title: Some("Codex".to_string()),
            },
        };

        self.send_response::<mcp_types::InitializeRequest>(id, result)
            .await;
    }

    async fn send_response<T>(&self, id: RequestId, result: T::Result)
    where
        T: ModelContextProtocolRequest,
    {
        self.outgoing.send_response(id, result).await;
    }

    async fn handle_ping(
        &self,
        id: RequestId,
        params: <mcp_types::PingRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("ping -> params: {:?}", params);
        let result = json!({});
        self.send_response::<mcp_types::PingRequest>(id, result)
            .await;
    }

    fn handle_list_resources(
        &self,
        params: <mcp_types::ListResourcesRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("resources/list -> params: {:?}", params);
    }

    fn handle_list_resource_templates(
        &self,
        params:
            <mcp_types::ListResourceTemplatesRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("resources/templates/list -> params: {:?}", params);
    }

    fn handle_read_resource(
        &self,
        params: <mcp_types::ReadResourceRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("resources/read -> params: {:?}", params);
    }

    fn handle_subscribe(
        &self,
        params: <mcp_types::SubscribeRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("resources/subscribe -> params: {:?}", params);
    }

    fn handle_unsubscribe(
        &self,
        params: <mcp_types::UnsubscribeRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("resources/unsubscribe -> params: {:?}", params);
    }

    fn handle_list_prompts(
        &self,
        params: <mcp_types::ListPromptsRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("prompts/list -> params: {:?}", params);
    }

    fn handle_get_prompt(
        &self,
        params: <mcp_types::GetPromptRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("prompts/get -> params: {:?}", params);
    }

    async fn handle_list_tools(
        &self,
        id: RequestId,
        params: <mcp_types::ListToolsRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::trace!("tools/list -> {params:?}");
        let result = ListToolsResult {
            tools: vec![
                create_tool_for_codex_tool_call_param(),
                create_tool_for_codex_tool_call_reply_param(),
                
            ],
            next_cursor: None,
        };

        self.send_response::<mcp_types::ListToolsRequest>(id, result)
            .await;
    }

    async fn handle_call_tool(
        &mut self,
        id: RequestId,
        params: <mcp_types::CallToolRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("tools/call -> params: {:?}", params);
        let CallToolRequestParams { name, arguments } = params;

        match name.as_str() {
            "codex" => self.handle_tool_call_codex(id, arguments).await,
            "codex-reply" => {
                self.handle_tool_call_codex_session_reply(id, arguments)
                    .await
            }
            // agents-* tools are now built-in; no longer exposed via MCP
            "agents-list" | "agents-start" | "agents-status" | "agents-reload" | "agents-cancel" => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_string(),
                        text: "agents-* tools are not exposed via MCP; use built-in tools".to_string(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
            }
            _ => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_string(),
                        text: format!("Unknown tool '{name}'"),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result)
                    .await;
            }
        }
    }

    #[cfg(test)]
    async fn handle_tool_call_agents_list(&self, id: RequestId) {
        let builtins = self.agents_registry.list();
        let agents = codex_agents::summarize_agents(&self.configured_agents, &builtins);
        let result = CallToolResult {
            content: vec![ContentBlock::TextContent(TextContent {
                r#type: "text".to_string(),
                text: format!("{} agents", agents.len()),
                annotations: None,
            })],
            is_error: Some(false),
            structured_content: Some(serde_json::to_value(&agents).unwrap_or(serde_json::Value::Null)),
        };
        self.send_response::<mcp_types::CallToolRequest>(id, result).await;
    }

    #[cfg(test)]
    async fn handle_tool_call_agents_start(
        &self,
        id: RequestId,
        arguments: Option<serde_json::Value>,
    ) {
        let params: AgentsStartParams = match arguments
            .and_then(|v| serde_json::from_value::<AgentsStartParams>(v).ok())
        {
            Some(p) => p,
            None => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Missing arguments for agents-start; require `goal`".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
                return;
            }
        };

        let agent_id = params.agent_id.clone().unwrap_or_else(|| "structured".to_string());

        let store = self.agents_tasks.clone();
        let task_id = store.create().await;

        // Build a two-phase prompt for a multi-turn agent: (1) outline+gather, (2) draft+summarize.
        let goal = params.goal.clone();
        let context = params.context.clone();
        let json_guidance = r#"Return ONLY valid JSON with this shape:
{
  "topic": string,
  "summary": string,
  "key_points": [string, ...],
  "risks": [string, ...],
  "open_questions": [string, ...],
  "citations": [ {"title": string, "url": string, "snippet": string }, ... ]
}
Do not include markdown fences or extra text."#;
        // Phase 1 prompt: outline + gather sources (use web_search if available), no final brief yet.
        let prompt_phase1: String = {
            let gather_line = if agent_id == "web_search" {
                "Use web_search if available to gather 3-6 relevant sources (title,url,snippet)."
            } else {
                "If web_search is unavailable, gather key facts from your knowledge as placeholders for sources."
            };
            match context.clone() {
                Some(ctx) => format!(
                    "Phase 1 — Outline and Gather\n- Create a compact outline for the goal.\n- {gather_line}\n- Do NOT write the final brief yet.\nReturn ONLY JSON: {{\"outline\":[string,...],\"sources\":[{{\"title\":string,\"url\":string,\"snippet\":string}},...]}}\nGoal: {goal}\nContext: {ctx}"
                ),
                None => format!(
                    "Phase 1 — Outline and Gather\n- Create a compact outline for the goal.\n- {gather_line}\n- Do NOT write the final brief yet.\nReturn ONLY JSON: {{\"outline\":[string,...],\"sources\":[{{\"title\":string,\"url\":string,\"snippet\":string}},...]}}\nGoal: {goal}"
                ),
            }
        };
        // Phase 2 prompt (base): draft + summarize into strict JSON output using prior outline/sources.
        let prompt_phase2_base: String = format!(
            "Phase 2 — Draft and Summarize\n- Using the outline and sources from Phase 1, produce the final concise research brief.\n{json_guidance}\nGoal: {goal}"
        );

        let conversation_manager = self.conversation_manager.clone();
        let config = self.config.clone();
        let running_map = self.agents_running.clone();
        let outgoing = self.outgoing.clone();
        let id_for_meta = id.clone();
        let configured_agents_for_spawn = self.configured_agents.clone();
        
        let agent_id_for_spawn = agent_id.clone();
        let allowed_for_response: Vec<String> = if let Some(spec) = self.configured_agents.iter().find(|a| a.id == agent_id) { spec.allowed_mcp_tools.clone() } else { Vec::new() };

        tokio::spawn(async move {
            store.set(task_id, codex_agents::TaskState::Running).await;
            // Helper to emit plan updates across 4 steps.
            let send_plan = |outline, gather, draft, summarize, explanation: String| {
                let outgoing = outgoing.clone();
                let id_meta = id_for_meta.clone();
                async move {
                    let plan = codex_protocol::plan_tool::UpdatePlanArgs {
                        explanation: Some(explanation.to_string()),
                        plan: vec![
                            codex_protocol::plan_tool::PlanItemArg { step: "Outline".to_string(), status: outline },
                            codex_protocol::plan_tool::PlanItemArg { step: "Gather".to_string(), status: gather },
                            codex_protocol::plan_tool::PlanItemArg { step: "Draft".to_string(), status: draft },
                            codex_protocol::plan_tool::PlanItemArg { step: "Summarize".to_string(), status: summarize },
                        ],
                    };
                    let event = codex_core::protocol::Event { id: String::new(), msg: codex_core::protocol::EventMsg::PlanUpdate(plan) };
                    outgoing
                        .send_event_as_notification(
                            &event,
                            Some(crate::outgoing_message::OutgoingNotificationMeta::new(Some(id_meta))),
                        )
                        .await;
                }
            };
            use codex_protocol::plan_tool::StepStatus::{Completed, InProgress, Pending};
            // Start with Outline in progress
            send_plan(InProgress, Pending, Pending, Pending, "Plan: outline".to_string()).await;
            // Spawn conversation (consider configured agent)
            let mut cfg = (*config).clone();
            if let Some(spec) = configured_agents_for_spawn.iter().find(|a| a.id == agent_id_for_spawn) {
                cfg = codex_agents::apply_spec_to_config(cfg, spec);
            } else {
                if agent_id_for_spawn == "web_search" { cfg.tools_web_search_request = true; }
                cfg.include_plan_tool = true;
            }
            let nc = match conversation_manager.new_conversation(cfg) .await {
                Ok(nc) => nc,
                Err(e) => {
                    store.set(task_id, codex_agents::TaskState::Error { message: format!("failed to start conversation: {e}") }).await;
                    return;
                }
            };
            let conversation = nc.conversation.clone();

            // Track running conversation for cancellation
            {
                let mut guard = running_map.lock().await;
                guard.insert(task_id, conversation.clone());
            }

            // Submit Phase 1 prompt
            use codex_core::protocol::{Op, InputItem, EventMsg};
            let items1 = vec![InputItem::Text { text: prompt_phase1 }];
            let sub_id_res = conversation.submit(Op::UserInput { items: items1 }).await;
            if let Err(e) = sub_id_res {
                store.set(task_id, codex_agents::TaskState::Error { message: format!("submit failed: {e}") }).await;
                let mut guard = running_map.lock().await;
                guard.remove(&task_id);
                return;
            }

            let mut phase: u8 = 1;
            let mut final_text = String::new();
            let mut turn1_output = String::new();
            // Draft progress reporting
            let mut draft_chars: usize = 0;
            let mut last_bucket: usize = 0; // 0, 600, 1500
            let mut outline_done = false;
            let mut gather_started = false;
            let mut gather_done = false;
            let mut draft_started = false;
            let mut summarize_started = false;
            loop {
                match conversation.next_event().await {
                    Ok(ev) => match ev.msg {
                        EventMsg::WebSearchBegin(_wb) if phase == 1 => {
                            gather_started = true;
                            send_plan(Completed, InProgress, Pending, Pending, "Plan: gather".to_string()).await;
                            outline_done = true;
                        }
                        EventMsg::WebSearchEnd(_we) if phase == 1 => {
                            gather_done = true;
                            send_plan(Completed, Completed, Pending, Pending, "Plan: gathered".to_string()).await;
                        }
                        EventMsg::AgentMessageDelta(d) => {
                            if phase == 1 {
                                turn1_output.push_str(&d.delta);
                            } else {
                                final_text.push_str(&d.delta);
                                draft_chars += d.delta.len();
                                // More responsive plan updates at thresholds
                                let bucket = if draft_chars >= 1500 { 1500 } else if draft_chars >= 600 { 600 } else { 0 };
                                if bucket > last_bucket {
                                    last_bucket = bucket;
                                    let expl = format!("Plan: draft (~{} chars)", draft_chars);
                                    send_plan(Completed, if gather_done { Completed } else if gather_started { InProgress } else { Pending }, InProgress, Pending, expl).await;
                                }
                            }
                        }
                        EventMsg::AgentMessage(m) => {
                            if phase == 1 {
                                turn1_output = m.message;
                            } else {
                                final_text = m.message;
                                if draft_started && !summarize_started {
                                    use codex_protocol::plan_tool::StepStatus::{Completed, InProgress, Pending};
                                    let gather_status = if gather_done { Completed } else if gather_started { InProgress } else { Pending };
                                    // Small delay to make the phase transition visible
                                    tokio::time::sleep(std::time::Duration::from_millis(120)).await;
                                    send_plan(Completed, gather_status, Completed, InProgress, "Plan: summarize".to_string()).await;
                                    summarize_started = true;
                                }
                            }
                        }
                        EventMsg::TaskComplete(_done) => {
                            if phase == 1 {
                                // End of Phase 1: move to Phase 2
                                use codex_protocol::plan_tool::StepStatus::{Completed, Pending};
                                send_plan(Completed, if gather_done { Completed } else { Pending }, Pending, Pending, "Plan: phase 1 complete".to_string()).await;
                                tokio::time::sleep(std::time::Duration::from_millis(150)).await;

                                // Submit Phase 2 prompt (include Phase 1 output, truncated)
                                let mut p2 = prompt_phase2_base.clone();
                                let t1 = if turn1_output.len() > 8000 { &turn1_output[..8000] } else { &turn1_output };
                                p2.push_str("\n\nPhase 1 output (outline+sources):\n");
                                p2.push_str(t1);
                                let items2 = vec![InputItem::Text { text: p2 }];
                                let _ = conversation.submit(Op::UserInput { items: items2 }).await;
                                phase = 2;
                                draft_started = true;
                                // Mark Draft InProgress now
                                send_plan(Completed, if gather_done { Completed } else { Pending }, codex_protocol::plan_tool::StepStatus::InProgress, Pending, "Plan: draft".to_string()).await;
                                continue;
                            } else {
                                // End of Phase 2
                                // Parse model output as JSON and validate against agent schema when present.
                                let mut parsed = None;
                                if let Ok(v) = serde_json::from_str::<serde_json::Value>(&final_text) {
                                    parsed = Some(v);
                                }
                                let mut schema_err: Option<String> = None;
                                if let Some(spec) = configured_agents_for_spawn.iter().find(|a| a.id == agent_id_for_spawn) {
                                    if let Some(schema_str) = &spec.output_schema {
                                        if let Ok(schema_json) = serde_json::from_str::<serde_json::Value>(schema_str) {
                                            if let Ok(compiled) = JSONSchema::compile(&schema_json) {
                                                match &parsed {
                                                    Some(val) => {
                                                        if let Err(errors) = compiled.validate(val) {
                                                            let msg = errors.map(|e| e.to_string()).collect::<Vec<_>>().join("; ");
                                                            schema_err = Some(format!("output schema validation failed: {msg}"));
                                                        }
                                                    }
                                                    None => schema_err = Some("final output is not valid JSON".to_string()),
                                                }
                                            } else {
                                                tracing::warn!("invalid output_schema for agent {}", agent_id_for_spawn);
                                            }
                                        } else {
                                            tracing::warn!("output_schema is not valid JSON for agent {}", agent_id_for_spawn);
                                        }
                                    }
                                }
                                if let Some(err) = schema_err {
                                    store.set(task_id, codex_agents::TaskState::Error { message: err }).await;
                                } else {
                                    let value = parsed.unwrap_or_else(|| serde_json::json!({ "message": final_text }));
                                    store.set(task_id, codex_agents::TaskState::Complete { result: value }).await;
                                }
                                // Emit final plan update as Completed for all steps.
                                let gather_status = if gather_done || gather_started { codex_protocol::plan_tool::StepStatus::Completed } else { codex_protocol::plan_tool::StepStatus::Pending };
                                send_plan(codex_protocol::plan_tool::StepStatus::Completed, gather_status, codex_protocol::plan_tool::StepStatus::Completed, codex_protocol::plan_tool::StepStatus::Completed, "Plan: complete".to_string()).await;
                                break;
                            }
                        }
                        EventMsg::TurnAborted(_) => {
                            store.set(task_id, codex_agents::TaskState::Cancelled).await;
                            break;
                        }
                        EventMsg::Error(e) => {
                            store.set(task_id, codex_agents::TaskState::Error { message: e.message }).await;
                            break;
                        }
                        _ => {}
                    },
                    Err(e) => {
                        store.set(task_id, codex_agents::TaskState::Error { message: format!("event error: {e}") }).await;
                        break;
                    }
                }
            }

            // Cleanup running map
            let mut guard = running_map.lock().await;
            guard.remove(&task_id);
        });

        let result = CallToolResult {
            content: vec![ContentBlock::TextContent(TextContent {
                r#type: "text".to_string(),
                text: format!("started agent '{agent_id}' as task {task_id}"),
                annotations: None,
            })],
            is_error: Some(false),
            structured_content: Some(serde_json::json!({"task_id": task_id, "allowed_mcp_tools": allowed_for_response})),
        };
        self.send_response::<mcp_types::CallToolRequest>(id, result).await;
    }

    #[cfg(test)]
    async fn handle_tool_call_agents_status(
        &self,
        id: RequestId,
        arguments: Option<serde_json::Value>,
    ) {
        let params: AgentsStatusParams = match arguments
            .and_then(|v| serde_json::from_value::<AgentsStatusParams>(v).ok())
        {
            Some(p) => p,
            None => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Missing arguments for agents-status; require `task_id`".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
                return;
            }
        };
        let tid = match uuid::Uuid::parse_str(&params.task_id) {
            Ok(v) => v,
            Err(_) => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Invalid task_id".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
                return;
            }
        };
        let state = self.agents_tasks.get(tid).await;
        let result = CallToolResult {
            content: vec![ContentBlock::TextContent(TextContent {
                r#type: "text".to_string(),
                text: match &state { Some(s) => format!("{s:?}"), None => "not found".to_string() },
                annotations: None,
            })],
            is_error: Some(state.is_none()),
            structured_content: state
                .and_then(|s| serde_json::to_value(s).ok())
                .or(Some(serde_json::json!({"status":"not-found"}))),
        };
        self.send_response::<mcp_types::CallToolRequest>(id, result).await;
    }

    #[cfg(test)]
    async fn handle_tool_call_agents_cancel(
        &self,
        id: RequestId,
        arguments: Option<serde_json::Value>,
    ) {
        let params: AgentsCancelParams = match arguments
            .and_then(|v| serde_json::from_value::<AgentsCancelParams>(v).ok())
        {
            Some(p) => p,
            None => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Missing arguments for agents-cancel; require `task_id`".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
                return;
            }
        };
        let tid = match uuid::Uuid::parse_str(&params.task_id) {
            Ok(v) => v,
            Err(_) => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Invalid task_id".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result).await;
                return;
            }
        };

        let maybe_conv = { self.agents_running.lock().await.remove(&tid) };
        if let Some(conversation) = maybe_conv {
            let _ = conversation.submit(codex_core::protocol::Op::Interrupt).await;
            self.agents_tasks.set(tid, codex_agents::TaskState::Cancelled).await;
            let result = CallToolResult {
                content: vec![ContentBlock::TextContent(TextContent {
                    r#type: "text".to_string(),
                    text: "cancel requested".to_string(),
                    annotations: None,
                })],
                is_error: Some(false),
                structured_content: Some(serde_json::json!({"cancelled": true})),
            };
            self.send_response::<mcp_types::CallToolRequest>(id, result).await;
        } else {
            let result = CallToolResult {
                content: vec![ContentBlock::TextContent(TextContent {
                    r#type: "text".to_string(),
                    text: "task not running".to_string(),
                    annotations: None,
                })],
                is_error: Some(true),
                structured_content: Some(serde_json::json!({"cancelled": false, "reason": "not running"})),
            };
            self.send_response::<mcp_types::CallToolRequest>(id, result).await;
        }
    }
    async fn handle_tool_call_codex(&self, id: RequestId, arguments: Option<serde_json::Value>) {
        let (initial_prompt, config): (String, Config) = match arguments {
            Some(json_val) => match serde_json::from_value::<CodexToolCallParam>(json_val) {
                Ok(tool_cfg) => match tool_cfg.into_config(self.codex_linux_sandbox_exe.clone()) {
                    Ok(cfg) => cfg,
                    Err(e) => {
                        let result = CallToolResult {
                            content: vec![ContentBlock::TextContent(TextContent {
                                r#type: "text".to_owned(),
                                text: format!(
                                    "Failed to load Codex configuration from overrides: {e}"
                                ),
                                annotations: None,
                            })],
                            is_error: Some(true),
                            structured_content: None,
                        };
                        self.send_response::<mcp_types::CallToolRequest>(id, result)
                            .await;
                        return;
                    }
                },
                Err(e) => {
                    let result = CallToolResult {
                        content: vec![ContentBlock::TextContent(TextContent {
                            r#type: "text".to_owned(),
                            text: format!("Failed to parse configuration for Codex tool: {e}"),
                            annotations: None,
                        })],
                        is_error: Some(true),
                        structured_content: None,
                    };
                    self.send_response::<mcp_types::CallToolRequest>(id, result)
                        .await;
                    return;
                }
            },
            None => {
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_string(),
                        text:
                            "Missing arguments for codex tool-call; the `prompt` field is required."
                                .to_string(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(id, result)
                    .await;
                return;
            }
        };

        // Clone outgoing and server to move into async task.
        let outgoing = self.outgoing.clone();
        let conversation_manager = self.conversation_manager.clone();
        let running_requests_id_to_codex_uuid = self.running_requests_id_to_codex_uuid.clone();

        // Spawn an async task to handle the Codex session so that we do not
        // block the synchronous message-processing loop.
        task::spawn(async move {
            // Run the Codex session and stream events back to the client.
            crate::codex_tool_runner::run_codex_tool_session(
                id,
                initial_prompt,
                config,
                outgoing,
                conversation_manager,
                running_requests_id_to_codex_uuid,
            )
            .await;
        });
    }

    async fn handle_tool_call_codex_session_reply(
        &self,
        request_id: RequestId,
        arguments: Option<serde_json::Value>,
    ) {
        tracing::info!("tools/call -> params: {:?}", arguments);

        // parse arguments
        let CodexToolCallReplyParam { session_id, prompt } = match arguments {
            Some(json_val) => match serde_json::from_value::<CodexToolCallReplyParam>(json_val) {
                Ok(params) => params,
                Err(e) => {
                    tracing::error!("Failed to parse Codex tool call reply parameters: {e}");
                    let result = CallToolResult {
                        content: vec![ContentBlock::TextContent(TextContent {
                            r#type: "text".to_owned(),
                            text: format!("Failed to parse configuration for Codex tool: {e}"),
                            annotations: None,
                        })],
                        is_error: Some(true),
                        structured_content: None,
                    };
                    self.send_response::<mcp_types::CallToolRequest>(request_id, result)
                        .await;
                    return;
                }
            },
            None => {
                tracing::error!(
                    "Missing arguments for codex-reply tool-call; the `session_id` and `prompt` fields are required."
                );
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: "Missing arguments for codex-reply tool-call; the `session_id` and `prompt` fields are required.".to_owned(),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(request_id, result)
                    .await;
                return;
            }
        };
        let session_id = match Uuid::parse_str(&session_id) {
            Ok(id) => id,
            Err(e) => {
                tracing::error!("Failed to parse session_id: {e}");
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: format!("Failed to parse session_id: {e}"),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                self.send_response::<mcp_types::CallToolRequest>(request_id, result)
                    .await;
                return;
            }
        };

        // Clone outgoing to move into async task.
        let outgoing = self.outgoing.clone();
        let running_requests_id_to_codex_uuid = self.running_requests_id_to_codex_uuid.clone();

        let codex = match self.conversation_manager.get_conversation(session_id).await {
            Ok(c) => c,
            Err(_) => {
                tracing::warn!("Session not found for session_id: {session_id}");
                let result = CallToolResult {
                    content: vec![ContentBlock::TextContent(TextContent {
                        r#type: "text".to_owned(),
                        text: format!("Session not found for session_id: {session_id}"),
                        annotations: None,
                    })],
                    is_error: Some(true),
                    structured_content: None,
                };
                outgoing.send_response(request_id, result).await;
                return;
            }
        };

        // Spawn the long-running reply handler.
        tokio::spawn({
            let codex = codex.clone();
            let outgoing = outgoing.clone();
            let prompt = prompt.clone();
            let running_requests_id_to_codex_uuid = running_requests_id_to_codex_uuid.clone();

            async move {
                crate::codex_tool_runner::run_codex_tool_session_reply(
                    codex,
                    outgoing,
                    request_id,
                    prompt,
                    running_requests_id_to_codex_uuid,
                    session_id,
                )
                .await;
            }
        });
    }

    fn handle_set_level(
        &self,
        params: <mcp_types::SetLevelRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("logging/setLevel -> params: {:?}", params);
    }

    fn handle_complete(
        &self,
        params: <mcp_types::CompleteRequest as mcp_types::ModelContextProtocolRequest>::Params,
    ) {
        tracing::info!("completion/complete -> params: {:?}", params);
    }

    // ---------------------------------------------------------------------
    // Notification handlers
    // ---------------------------------------------------------------------

    async fn handle_cancelled_notification(
        &self,
        params: <mcp_types::CancelledNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        let request_id = params.request_id;
        // Create a stable string form early for logging and submission id.
        let request_id_string = match &request_id {
            RequestId::String(s) => s.clone(),
            RequestId::Integer(i) => i.to_string(),
        };

        // Obtain the session_id while holding the first lock, then release.
        let session_id = {
            let map_guard = self.running_requests_id_to_codex_uuid.lock().await;
            match map_guard.get(&request_id) {
                Some(id) => *id, // Uuid is Copy
                None => {
                    tracing::warn!("Session not found for request_id: {}", request_id_string);
                    return;
                }
            }
        };
        tracing::info!("session_id: {session_id}");

        // Obtain the Codex conversation from the server.
        let codex_arc = match self.conversation_manager.get_conversation(session_id).await {
            Ok(c) => c,
            Err(_) => {
                tracing::warn!("Session not found for session_id: {session_id}");
                return;
            }
        };

        // Submit interrupt to Codex.
        let err = codex_arc
            .submit_with_id(Submission {
                id: request_id_string,
                op: codex_core::protocol::Op::Interrupt,
            })
            .await;
        if let Err(e) = err {
            tracing::error!("Failed to submit interrupt to Codex: {e}");
            return;
        }
        // unregister the id so we don't keep it in the map
        self.running_requests_id_to_codex_uuid
            .lock()
            .await
            .remove(&request_id);
    }

    fn handle_progress_notification(
        &self,
        params: <mcp_types::ProgressNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!("notifications/progress -> params: {:?}", params);
    }

    fn handle_resource_list_changed(
        &self,
        params: <mcp_types::ResourceListChangedNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!(
            "notifications/resources/list_changed -> params: {:?}",
            params
        );
    }

    fn handle_resource_updated(
        &self,
        params: <mcp_types::ResourceUpdatedNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!("notifications/resources/updated -> params: {:?}", params);
    }

    fn handle_prompt_list_changed(
        &self,
        params: <mcp_types::PromptListChangedNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!("notifications/prompts/list_changed -> params: {:?}", params);
    }

    fn handle_tool_list_changed(
        &self,
        params: <mcp_types::ToolListChangedNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!("notifications/tools/list_changed -> params: {:?}", params);
    }

    fn handle_logging_message(
        &self,
        params: <mcp_types::LoggingMessageNotification as mcp_types::ModelContextProtocolNotification>::Params,
    ) {
        tracing::info!("notifications/message -> params: {:?}", params);
    }
}




