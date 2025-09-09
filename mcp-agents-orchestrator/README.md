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

Design Notes
- Tools return a single text content block to keep integration simple.
- Task state is held in-memory; replace `TaskStore` with a filesystem/db backend as needed.
- Extend `DEFAULT_AGENTS` or implement `agents.create/update/delete` in a future phase.
