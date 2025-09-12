#![allow(dead_code)]
use mcp_types::Tool;
use mcp_types::ToolInputSchema;
use schemars::JsonSchema;
use schemars::r#gen::SchemaSettings;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, Default)]
#[serde(rename_all = "camelCase")]
pub struct AgentsListParams {}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AgentsStartParams {
    /// Optional id of the agent to run (defaults to a sensible built-in)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,

    /// The goal/task description for the agent
    pub goal: String,

    /// Optional free-form context object the agent may use
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub context: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AgentsToolsetParams {
    /// The id of the agent to query
    pub agent_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AgentsStatusParams {
    pub task_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct AgentsCancelParams {
    pub task_id: String,
}

fn schema_for<T: JsonSchema>() -> ToolInputSchema {
    let schema = SchemaSettings::draft2019_09()
        .with(|s| {
            s.inline_subschemas = true;
            s.option_add_null_type = false;
        })
        .into_generator()
        .into_root_schema_for::<T>();

    #[expect(clippy::expect_used)]
    let schema_value = serde_json::to_value(&schema).expect("schema serializes");
    serde_json::from_value::<ToolInputSchema>(schema_value)
        .expect("tool input schema should parse from generated JSON")
}

pub(crate) fn create_tool_agents_list() -> Tool {
    Tool {
        name: "agents-list".to_string(),
        title: Some("Agents: List".to_string()),
        description: Some("List available built-in agents".to_string()),
        input_schema: schema_for::<AgentsListParams>(),
        output_schema: None,
        annotations: None,
    }
}

pub(crate) fn create_tool_agents_start() -> Tool {
    Tool {
        name: "agents-start".to_string(),
        title: Some("Agents: Start Task".to_string()),
        description: Some("Start an agent task and get a task id".to_string()),
        input_schema: schema_for::<AgentsStartParams>(),
        output_schema: None,
        annotations: None,
    }
}

pub(crate) fn create_tool_agents_reload() -> Tool {
    Tool {
        name: "agents-reload".to_string(),
        title: Some("Agents: Reload".to_string()),
        description: Some("Reload agents from ~/.codex/agents.toml and return the list".to_string()),
        input_schema: schema_for::<AgentsListParams>(),
        output_schema: None,
        annotations: None,
    }
}

pub(crate) fn create_tool_agents_status() -> Tool {
    Tool {
        name: "agents-status".to_string(),
        title: Some("Agents: Task Status".to_string()),
        description: Some("Get the current status/result of an agent task".to_string()),
        input_schema: schema_for::<AgentsStatusParams>(),
        output_schema: None,
        annotations: None,
    }
}

pub(crate) fn create_tool_agents_cancel() -> Tool {
    Tool {
        name: "agents-cancel".to_string(),
        title: Some("Agents: Cancel Task".to_string()),
        description: Some("Request cancellation of an agent task".to_string()),
        input_schema: schema_for::<AgentsCancelParams>(),
        output_schema: None,
        annotations: None,
    }
}

pub(crate) fn create_tool_agents_toolset() -> Tool {
    Tool {
        name: "agents-toolset".to_string(),
        title: Some("Agents: Toolset".to_string()),
        description: Some("Get the effective built-in and MCP tools for an agent id".to_string()),
        input_schema: schema_for::<AgentsToolsetParams>(),
        output_schema: None,
        annotations: None,
    }
}
