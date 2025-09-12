use crate::config::Config;
use crate::protocol::AskForApproval;
use crate::protocol::SandboxPolicy;
use codex_agents::AgentSpec;

/// Apply an `AgentSpec` to a base `Config`, returning the updated config
/// for running that agent.
pub fn apply_spec_to_config(mut cfg: Config, spec: &AgentSpec) -> Config {
    if let Some(m) = &spec.model {
        cfg.model = m.clone();
    }
    if let Some(cwd) = &spec.cwd {
        cfg.cwd = std::path::PathBuf::from(cwd);
    }

    if let Some(ap) = &spec.approval_policy {
        if let Ok(v) = serde_json::from_str::<AskForApproval>(&format!("\"{}\"", ap)) {
            cfg.approval_policy = v;
        }
    }
    if let Some(sb) = &spec.sandbox {
        if let Ok(v) = serde_json::from_str::<SandboxPolicy>(&format!("{{\"mode\":\"{}\"}}", sb)) {
            cfg.sandbox_policy = v;
        }
    }

    let allow = |k: &str| spec.allowed_builtin_tools.iter().any(|t| t == k);
    if !spec.allowed_builtin_tools.is_empty() {
        cfg.include_plan_tool = allow("plan");
        cfg.include_apply_patch_tool = allow("apply_patch");
        cfg.tools_web_search_request = allow("web_search");
        cfg.include_view_image_tool = allow("view_image");
    }

    if !spec.instructions.is_empty() {
        cfg.base_instructions = Some(spec.instructions.clone());
    }
    cfg.allowed_mcp_tools = spec.allowed_mcp_tools.clone();
    cfg
}

