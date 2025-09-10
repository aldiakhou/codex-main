MCP Agents Orchestrator (MVP)

Overview
- A minimal Model Context Protocol (MCP) server over stdio that exposes your external agents as tools to Codex.
- Implements tools:
  - agents.list
  - agents.start_task
  - agents.task_status
  - agents.cancel_task

Status
- MVP, no external dependencies; pure Python stdio JSON-RPC.
- Notifications are logged by Codex at present; progress polling is supported via agents.task_status.

Permissions (MVP)
- Pass a `permission_profile` object to `agents.start_task` to control tool use:
  - `tool_allowlist`: supports entries like `"mcp"` (defaults to `npx;python` stdio), `"mcp:stdio:npx"`, `"mcp:stdio:python"`, or HTTP prefixes like `"https://example.com/"`.
  - `sandbox`: one of `read-only | workspace-write | danger-full-access` (exported via `AGENT_SANDBOX_MODE`).
  - Example: `{ "tool_allowlist": ["mcp", "mcp:stdio:python", "https://api.example.com/"], "sandbox": "workspace-write" }`.

Progress & Plan
- The real agent path emits a 5-step plan: Initialize → Prepare tools → Run flow → Format result → Finalize, with progress entries for each stage.

Usage
1) Ensure Python 3.9+ is available on PATH.
2) Launch Codex with an MCP server entry in `~/.codex/config.toml` (choose one):

```
[mcp_servers.agents_orchestrator]
command = "python"
args = ["-m", "mcp_agents_orchestrator"]
env = { PYTHONUNBUFFERED = "1" }
```

Or point to the script path directly (replace with your absolute path):

```
[mcp_servers.agents_orchestrator]
command = "python"
args = ["C:/Users/you/path/to/codex-main/mcp-agents-orchestrator/agents_orchestrator.py"]
env = { PYTHONUNBUFFERED = "1" }
```

3) Start the app. Codex will spawn the orchestrator lazily when a model decides to call an `agents.*` tool.

User-Defined Agents (Aliases)
- Optional file: `~/.codex/agents/agents.json`
- Minimal format to create aliases that point to built-in agents:

```
{
  "agents": [
    {
      "id": "my-research",
      "alias_of": "deep_research",
      "name": "My Deep Research",
      "description": "Customized deep research profile",
      "expected_context": ["topic", "depth", "focus_areas"]
    }
  ]
}
```

- Aliases show up in `agents.list` and are routed to the base agent during `agents.start_task`.

Design Notes
- Tools return a single text content block to keep integration simple.
- Task state is held in-memory; replace `TaskStore` with a filesystem/db backend as needed.
- Extend `DEFAULT_AGENTS` or implement `agents.create/update/delete` in a future phase.

Agent Metadata
- `agents.list` now returns `expected_context` (suggested context keys) and, for MCP agents, `server_configs` (full command/args when available) to help UIs build forms and setup requirements.
