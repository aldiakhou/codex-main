use std::collections::HashMap;
use std::sync::Arc;

use anyhow::Result;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInfo {
    pub id: String,
    pub name: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartTaskParams {
    pub goal: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub context: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartTaskResult {
    pub task_id: Uuid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "status", rename_all = "kebab-case")]
pub enum TaskState {
    Pending,
    Running,
    Complete { result: serde_json::Value },
    Error { message: String },
    Cancelled,
}

#[async_trait]
pub trait Agent: Send + Sync {
    fn id(&self) -> &'static str;
    fn name(&self) -> &'static str;
    fn description(&self) -> &'static str;

    async fn start(&self, params: StartTaskParams, store: TaskStore, task_id: Uuid) -> Result<()>;
}

/// Very simple built-in agent that immediately completes with a structured
/// response. Intended as a smoke-test without external APIs.
pub struct StructuredEchoAgent;

#[async_trait]
impl Agent for StructuredEchoAgent {
    fn id(&self) -> &'static str { "structured" }
    fn name(&self) -> &'static str { "Structured Echo" }
    fn description(&self) -> &'static str {
        "Returns a minimal structured summary of the provided goal/context"
    }

    async fn start(&self, params: StartTaskParams, store: TaskStore, task_id: Uuid) -> Result<()> {
        store.set(task_id, TaskState::Running).await;

        // Simulate brief work and produce a minimal structured result.
        sleep(Duration::from_millis(10)).await;
        let result = serde_json::json!({
            "agent": self.id(),
            "summary": {
                "goal": params.goal,
                "context": params.context,
            }
        });
        store.set(task_id, TaskState::Complete { result }).await;
        Ok(())
    }
}

#[derive(Clone, Default)]
pub struct AgentRegistry {
    agents: Arc<Vec<Arc<dyn Agent>>>,
}

impl AgentRegistry {
    pub fn default_with_builtins() -> Self {
        let mut list: Vec<Arc<dyn Agent>> = Vec::new();
        list.push(Arc::new(StructuredEchoAgent));
        // Placeholder entry so `agents-list` surfaces a discoverable id.
        struct WebSearchInfoAgent;
        #[async_trait]
        impl Agent for WebSearchInfoAgent {
            fn id(&self) -> &'static str { "web_search" }
            fn name(&self) -> &'static str { "Web Search" }
            fn description(&self) -> &'static str { "Uses web_search tool when available with fallback" }
            async fn start(&self, _p: StartTaskParams, _s: TaskStore, _t: Uuid) -> Result<()> { Ok(()) }
        }
        list.push(Arc::new(WebSearchInfoAgent));
        Self { agents: Arc::new(list) }
    }

    pub fn list(&self) -> Vec<AgentInfo> {
        self.agents
            .iter()
            .map(|a| AgentInfo {
                id: a.id().to_string(),
                name: a.name().to_string(),
                description: a.description().to_string(),
            })
            .collect()
    }

    pub fn get(&self, id: &str) -> Option<Arc<dyn Agent>> {
        self.agents.iter().find(|a| a.id() == id).cloned()
    }
}

#[derive(Clone, Default)]
pub struct TaskStore {
    inner: Arc<RwLock<HashMap<Uuid, TaskState>>>,
}

impl TaskStore {
    pub fn new() -> Self { Self::default() }

    pub async fn create(&self) -> Uuid {
        let id = Uuid::new_v4();
        self.inner.write().await.insert(id, TaskState::Pending);
        id
    }

    pub async fn set(&self, id: Uuid, state: TaskState) {
        self.inner.write().await.insert(id, state);
    }

    pub async fn get(&self, id: Uuid) -> Option<TaskState> {
        self.inner.read().await.get(&id).cloned()
    }
}

// ---------------- Agents.toml loader -----------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSpec {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub instructions: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub approval_policy: Option<String>,
    #[serde(default)]
    pub sandbox: Option<String>,
    #[serde(default)]
    pub cwd: Option<String>,
    #[serde(default)]
    pub allowed_builtin_tools: Vec<String>,
    #[serde(default)]
    pub allowed_mcp_tools: Vec<String>,
    /// JSON schema as string; when present, the final output must validate.
    #[serde(default)]
    pub output_schema: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct AgentsTomlFile {
    #[serde(flatten)]
    pub agents: std::collections::BTreeMap<String, AgentTomlEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct AgentTomlEntry {
    pub name: Option<String>,
    pub description: Option<String>,
    pub instructions: Option<String>,
    pub model: Option<String>,
    pub approval_policy: Option<String>,
    pub sandbox: Option<String>,
    pub cwd: Option<String>,
    #[serde(default)]
    pub allowed_builtin_tools: Vec<String>,
    #[serde(default)]
    pub allowed_mcp_tools: Vec<String>,
    pub output_schema: Option<String>,
}

pub fn load_agents_from_home(codex_home: &std::path::Path) -> std::io::Result<Vec<AgentSpec>> {
    let path = codex_home.join("agents.toml");
    let Ok(contents) = std::fs::read_to_string(&path) else {
        return Ok(Vec::new());
    };
    let parsed: AgentsTomlFile = toml::from_str(&contents)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, format!("agents.toml: {e}")))?;
    let mut out = Vec::new();
    for (id, entry) in parsed.agents.into_iter() {
        out.push(AgentSpec {
            id: id.clone(),
            name: entry.name.unwrap_or_else(|| id.clone()),
            description: entry.description.unwrap_or_default(),
            instructions: entry.instructions.unwrap_or_default(),
            model: entry.model,
            approval_policy: entry.approval_policy,
            sandbox: entry.sandbox,
            cwd: entry.cwd,
            allowed_builtin_tools: entry.allowed_builtin_tools,
            allowed_mcp_tools: entry.allowed_mcp_tools,
            output_schema: entry.output_schema,
        });
    }
    Ok(out)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSummary {
    pub id: String,
    pub name: String,
    pub description: String,
}

pub fn summarize_agents(specs: &[AgentSpec], builtins: &[AgentInfo]) -> Vec<AgentSummary> {
    let mut v: Vec<AgentSummary> = builtins
        .iter()
        .map(|b| AgentSummary { id: b.id.clone(), name: b.name.clone(), description: b.description.clone() })
        .collect();
    v.extend(specs.iter().map(|s| AgentSummary { id: s.id.clone(), name: s.name.clone(), description: s.description.clone() }));
    v
}
