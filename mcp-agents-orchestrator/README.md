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
- Codex-auth aware: reads ~/.codex/auth.json (ChatGPT plan tokens or API key) so your agents do not need raw keys.

Permissions (MVP)
- Pass a `permission_profile` object to `agents.start_task` to control tool use:
  - `tool_allowlist`: supports entries like `"mcp"` (defaults to `npx;python` stdio), `"mcp:stdio:npx"`, `"mcp:stdio:python"`, or HTTP prefixes like `"https://example.com/"`.
  - `sandbox`: one of `read-only | workspace-write | danger-full-access` (exported via `AGENT_SANDBOX_MODE`).
  - Example: `{ "tool_allowlist": ["mcp", "mcp:stdio:python", "https://api.example.com/"], "sandbox": "workspace-write" }`.

Progress & Plan
- The real agent path emits a 5-step plan: Initialize → Prepare tools → Run flow → Format result → Finalize, with progress entries for each stage.

Usage
1) Ensure Python 3.9+ is available on PATH.
2) Install deps: `pip install -r mcp-agents-orchestrator/requirements.txt`
3) Launch Codex with an MCP server entry in `~/.codex/config.toml` (choose one):

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

4) Start the app. Codex will spawn the orchestrator lazily when a model decides to call an `agents.*` tool.

Auth
- The orchestrator inspects `~/.codex/auth.json` (or `CODEX_HOME/auth.json`) like the Rust CLI:
  - ChatGPT plan: uses `tokens.access_token` with `Authorization: Bearer <token>` and `chatgpt-account-id` when present.
  - API key: uses `OPENAI_API_KEY` from auth.json or environment.
- Per-task env exports for agent code:
  - `AGENT_OPENAI_AUTHORIZATION` (always set when available)
  - `AGENT_OPENAI_BASE_URL` (ChatGPT backend or OpenAI API base)
  - `AGENT_CHATGPT_ACCOUNT_ID` (when available)
  - `OPENAI_API_KEY` (only in API-key mode for SDKs)

Built-in Example Agent
- ID: `simple` (registered via `agents/mcp_enhanced_agents.py`)
- Behavior: calls the OpenAI Responses API (non-streaming) using Codex auth and returns a summary + raw response.
- Try it via tools:

```
agents.list
agents.start_task {"agent_id":"simple", "goal":"Say hello and summarize: hello world"}
agents.task_status {"task_id":"<value from start_task>"}
```

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
