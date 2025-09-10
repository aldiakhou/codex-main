import json
import sys
import threading
import time
import uuid
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

JSONRPC = "2.0"
MCP_VERSION = "2025-06-18"

# Ensure sibling packages (agents/, core/) are importable regardless of CWD
try:
    import pathlib
    _ROOT = pathlib.Path(__file__).resolve().parents[1]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass


def log(msg: str) -> None:
    try:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()
    except Exception:
        pass


def write_message(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


@dataclass
class Implementation:
    name: str
    version: str


@dataclass
class ToolInputSchema:
    type: str = "object"
    properties: Optional[Dict[str, Any]] = None
    required: Optional[List[str]] = None


@dataclass
class Tool:
    name: str
    inputSchema: ToolInputSchema
    description: Optional[str] = None
    title: Optional[str] = None


def _state_dir() -> str:
    home = os.path.expanduser("~")
    p = os.path.join(home, ".codex", "agents")
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass
    return p


def notify(method: str, params: Dict[str, Any]) -> None:
    # JSON-RPC notification (no id)
    try:
        msg = {"jsonrpc": JSONRPC, "method": method, "params": params}
        write_message(msg)
    except Exception:
        pass


# ---- User-defined agents (aliases) persistence ----
class UserAgentsStore:
    """File-backed store for simple user-defined agents.

    File format (~/.codex/agents/agents.json):
    {
      "agents": [
        {"id": "my-research", "alias_of": "deep_research", "name": "My Research", "description": "..."}
      ]
    }
    """

    def __init__(self) -> None:
        self._dir = _state_dir()
        self._path = os.path.join(self._dir, "agents.json")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("agents") or []
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict) and isinstance(it.get("id"), str):
                            self._cache[it["id"]] = it
        except Exception:
            # Best-effort; ignore corrupt files in MVP
            self._cache = {}
        finally:
            self._loaded = True

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        self._load()
        return self._cache.get(agent_id)

    def list(self) -> List[Dict[str, Any]]:
        self._load()
        return list(self._cache.values())


USER_AGENTS = UserAgentsStore()


# ---- Approval state (submission_id mapping) ----
_APPROVAL_DECISIONS: Dict[str, str] = {}
_CALL_TO_SUBMISSION: Dict[str, str] = {}
_APPROVAL_LOCK = threading.Lock()

def _ensure_submission_id_for_call(call_id: str) -> str:
    with _APPROVAL_LOCK:
        sid = _CALL_TO_SUBMISSION.get(call_id)
        if sid:
            return sid
        sid = f"sub_{uuid.uuid4().hex[:10]}"
        _CALL_TO_SUBMISSION[call_id] = sid
        return sid

def record_approval_decision(submission_id: str, decision: str, call_id: Optional[str] = None) -> None:
    with _APPROVAL_LOCK:
        _APPROVAL_DECISIONS[submission_id] = decision
        if call_id:
            _CALL_TO_SUBMISSION.setdefault(call_id, submission_id)

def get_submission_id_for_call(call_id: str) -> Optional[str]:
    with _APPROVAL_LOCK:
        return _CALL_TO_SUBMISSION.get(call_id)

def wait_for_decision(submission_id: str, timeout_secs: float = 120.0) -> Optional[str]:
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        with _APPROVAL_LOCK:
            d = _APPROVAL_DECISIONS.get(submission_id)
            if d:
                return d
        time.sleep(0.2)
    return None


# ---- Helper notifiers agents can import/use ----
def exec_approval_request(call_id: str, command: list[str], cwd: str, reason: Optional[str] = None) -> None:
    submission_id = _ensure_submission_id_for_call(call_id)
    payload = {"call_id": call_id, "submission_id": submission_id, "command": command, "cwd": cwd}
    if reason:
        payload["reason"] = reason
    notify("exec_approval_request", payload)


def exec_command_begin(call_id: str, command: list[str], cwd: str) -> None:
    notify("exec_command_begin", {"call_id": call_id, "command": command, "cwd": cwd})


def exec_command_output_delta(call_id: str, stream: str, chunk_bytes: bytes) -> None:
    import base64
    notify("exec_command_output_delta", {"call_id": call_id, "stream": stream, "chunk": base64.b64encode(chunk_bytes).decode("ascii")})


def _to_jsonable(obj: Any) -> Any:
    """Best-effort conversion of objects to JSON-serializable structures."""
    try:
        # Pydantic v2 BaseModel
        if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
            return obj.model_dump()
    except Exception:
        pass
    # Built-ins
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, tuple):
        return [_to_jsonable(v) for v in obj]
    # Fallback: primitive or string
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

def exec_command_end(call_id: str, exit_code: int, stdout: str = "", stderr: str = "", formatted_output: str = "", duration_ms: int = 0) -> None:
    notify("exec_command_end", {"call_id": call_id, "exit_code": exit_code, "stdout": stdout, "stderr": stderr, "formatted_output": formatted_output, "duration_ms": duration_ms})


def apply_patch_approval_request(call_id: str, changes: Dict[str, Any], reason: Optional[str] = None, grant_root: Optional[str] = None) -> None:
    submission_id = _ensure_submission_id_for_call(call_id)
    payload: Dict[str, Any] = {"call_id": call_id, "submission_id": submission_id, "changes": changes}
    if reason:
        payload["reason"] = reason
    if grant_root:
        payload["grant_root"] = grant_root
    notify("apply_patch_approval_request", payload)


def patch_apply_begin(call_id: str, changes: Dict[str, Any], auto_approved: bool = False) -> None:
    notify("patch_apply_begin", {"call_id": call_id, "auto_approved": bool(auto_approved), "changes": changes})


def patch_apply_end(call_id: str, success: bool, stdout: str = "", stderr: str = "") -> None:
    notify("patch_apply_end", {"call_id": call_id, "success": bool(success), "stdout": stdout, "stderr": stderr})


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._snapshot_path = os.path.join(_state_dir(), "tasks.json")
        self._events_path = os.path.join(_state_dir(), "tasks.jsonl")

    def create(self, agent_id: str, goal: str, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        task = {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": "queued",
            "created_at": int(time.time() * 1000),
            "progress": [],
            "result": None,
            "error": None,
        }
        with self._lock:
            self._tasks[task_id] = task
            self._persist_event({"type": "create", "task": task})
            self._persist_snapshot()
        return task

    def update(self, task_id: str, **patch: Any) -> None:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            # Ensure results are JSON-serializable
            if "result" in patch:
                patch = dict(patch)
                patch["result"] = _to_jsonable(patch.get("result"))
            t.update(patch)
            self._persist_event({"type": "update", "task_id": task_id, "patch": patch})
            self._persist_snapshot()

    def append_progress(self, task_id: str, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
        entry = {"ts": int(time.time() * 1000), "level": level, "message": message}
        if data:
            entry["data"] = data
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            t.setdefault("progress", []).append(entry)
            # fire a progress notification (token = task_id)
            try:
                notify("notifications/progress", {"progress": float(len(t["progress"])), "progressToken": task_id, "message": message})
            except Exception:
                pass
            self._persist_event({"type": "progress", "task_id": task_id, "entry": entry})
            self._persist_snapshot()

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            t = self._tasks.get(task_id)
            # Return a deep copy without requiring strict JSON encoding here
            import copy
            return copy.deepcopy(t) if t else None

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return False
            t["status"] = "canceled"
            self._persist_event({"type": "canceled", "task_id": task_id})
            self._persist_snapshot()
            return True

    def _persist_event(self, obj: Dict[str, Any]) -> None:
        try:
            with open(self._events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _persist_snapshot(self) -> None:
        try:
            with open(self._snapshot_path, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


TASKS = TaskStore()


# Simple in-memory fallback agent registry (used if real agents fail to load)
DEFAULT_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "agent-researcher-1",
        "name": "Deep Researcher",
        "description": "Multi-hop research and synthesis",
        "provider": {"id": "openai", "model": "gpt-4o"},
        "sandbox": "read-only",
        "approval_policy": "on-request",
        "tool_allowlist": ["exec", "apply_patch", "mcp:web-search"],
    }
]


# ===== Agent bridge (loads your real agents if available) =====
class AgentBridge:
    def __init__(self) -> None:
        self.loaded = False
        self.error: Optional[str] = None
        self.registry = None  # agents.base.AgentRegistry

    def load(self) -> bool:
        if self.loaded:
            return True
        try:
            # Local shimmed core is available under `mcp-agents-orchestrator/core`
            # Your agents package is under `mcp-agents-orchestrator/agents`.
            from agents.base import get_agent_registry  # type: ignore
            from agents.mcp_enhanced_agents import register_mcp_agents  # type: ignore

            reg = get_agent_registry()
            # Register MCP + tool agents into the base registry (instantiates agents)
            register_mcp_agents(reg)
            self.registry = reg
            self.loaded = True
            return True
        except Exception as e:  # pragma: no cover - defensive
            self.error = str(e)
            return False

    def _expected_context(self, agent_id: str) -> List[str]:
        aid = agent_id.lower()
        if aid == "web_search":
            return ["query", "search_type", "max_results"]
        if aid == "deep_research":
            return ["topic", "depth", "focus_areas"]
        if aid == "live_monitoring":
            return ["monitoring_target", "metrics_to_track", "thresholds", "check_interval", "historical_data", "additional_context"]
        if aid == "rag":
            return ["query", "search_type", "max_results", "additional_context"]
        if aid == "analysis":
            return ["data", "analysis_type", "focus_areas", "additional_context"]
        if aid == "demo_exec_patch":
            return ["demo", "demo_exec_patch"]
        return []

    def _expected_context_schema(self, agent_id: str) -> List[Dict[str, Any]]:
        keys = self._expected_context(agent_id)
        # Simple descriptors for UI hints
        descriptions = {
            "query": "Primary query or question",
            "search_type": "general|news|academic",
            "max_results": "Maximum number of results",
            "topic": "Research topic",
            "depth": "brief|standard|comprehensive",
            "focus_areas": "List of focus areas",
            "monitoring_target": "Target system or source to monitor",
            "metrics_to_track": "List of metric names to track",
            "thresholds": "Mapping of metric→threshold",
            "check_interval": "Check cadence (e.g., 5 minutes)",
            "historical_data": "Recent data points for baseline",
            "additional_context": "Free-form additional context",
            "data": "Content or structured data to analyze",
            "analysis_type": "general|statistical|qualitative",
            "focus_areas": "List of areas to focus on",
            "demo": "Enable exec/patch demo",
            "demo_exec_patch": "Enable exec/patch demo",
        }
        types = {
            "query": "string",
            "search_type": "string",
            "max_results": "number",
            "topic": "string",
            "depth": "string",
            "focus_areas": "array",
            "monitoring_target": "string",
            "metrics_to_track": "array",
            "thresholds": "object",
            "check_interval": "string",
            "historical_data": "array",
            "additional_context": "string",
            "data": "string",
            "analysis_type": "string",
            "demo": "boolean",
            "demo_exec_patch": "boolean",
        }
        schema: List[Dict[str, Any]] = []
        for k in keys:
            schema.append({
                "key": k,
                "type": types.get(k, "string"),
                "required": False,
                "description": descriptions.get(k, k.replace("_", " ")),
            })
        return schema

    def list_agents(self) -> List[Dict[str, Any]]:
        if not self.load():
            return DEFAULT_AGENTS
        ids = self.registry.list_agents()
        agents: List[Dict[str, Any]] = []
        for aid in ids:
            try:
                info = self.registry.get_agent_info(aid) or {}
                # Try to fetch instance to expose server configs if available
                inst = None
                try:
                    inst = self.registry.get_agent(aid)  # type: ignore[attr-defined]
                except Exception:
                    inst = None
                server_detail = None
                if isinstance(info.get("server_configs_detail"), list):
                    server_detail = info.get("server_configs_detail")
                elif inst is not None and hasattr(inst, "server_configs"):
                    try:
                        sc = getattr(inst, "server_configs")
                        if isinstance(sc, list):
                            server_detail = sc
                    except Exception:
                        server_detail = None
                agents.append({
                    "id": aid,
                    "name": info.get("name", aid),
                    "description": info.get("description", ""),
                    "capabilities": info.get("capabilities", []),
                    "expected_context": self._expected_context(aid),
                    "expected_context_schema": self._expected_context_schema(aid),
                    "server_configs": server_detail,
                })
            except Exception:
                agents.append({"id": aid, "name": aid})
        # Merge user-defined agent aliases (do not override built-ins)
        try:
            builtin_ids = {a["id"] for a in agents}
            for u in USER_AGENTS.list():
                uid = str(u.get("id"))
                if not uid or uid in builtin_ids:
                    continue
                alias_of = u.get("alias_of")
                base_info: Optional[Dict[str, Any]] = None
                if isinstance(alias_of, str) and alias_of in [a["id"] for a in agents]:
                    base_info = next((a for a in agents if a["id"] == alias_of), None)
                agents.append({
                    "id": uid,
                    "name": u.get("name") or uid,
                    "description": u.get("description") or (base_info or {}).get("description", ""),
                    "capabilities": (base_info or {}).get("capabilities", []),
                    "expected_context": u.get("expected_context") or (base_info or {}).get("expected_context", []),
                    "expected_context_schema": u.get("expected_context_schema") or (base_info or {}).get("expected_context_schema", []),
                    "server_configs": (base_info or {}).get("server_configs"),
                    "alias_of": alias_of,
                })
        except Exception:
            pass
        return agents

    def start_task(self, task_id: str, agent_id: str, goal: str, params: Dict[str, Any], cwd: Optional[str], permission_profile: Optional[Dict[str, Any]] = None) -> None:
        ok = self.load()
        if not ok:
            # Fallback simulated work with plan updates
            def worker():
                TASKS.update(task_id, status="running", started_at=int(time.time() * 1000))
                TASKS.append_progress(task_id, "Agent received goal", data={"goal": goal})
                # Initial plan
                try:
                    notify("plan_update", {
                        "explanation": "Simulated task plan",
                        "plan": [
                            {"step": "Collect sources", "status": "in_progress"},
                            {"step": "Extract insights", "status": "pending"},
                            {"step": "Draft report", "status": "pending"}
                        ]
                    })
                except Exception:
                    pass
                steps = [
                    ("Collect sources", "collecting_sources"),
                    ("Extract insights", "extracting_insights"),
                    ("Draft report", "drafting_report"),
                ]
                for idx, (title, key) in enumerate(steps):
                    TASKS.append_progress(task_id, title)
                    time.sleep(0.8)
                    # Update plan statuses
                    try:
                        plan = []
                        for j, (t2, _k2) in enumerate(steps):
                            status = "completed" if j < idx else ("in_progress" if j == idx else "pending")
                            plan.append({"step": t2, "status": status})
                        notify("plan_update", {"plan": plan})
                    except Exception:
                        pass
                TASKS.update(task_id, status="completed", completed_at=int(time.time() * 1000), result={"summary": f"Task complete: {goal}"})
                try:
                    notify("background_event", {"message": f"Agent task {task_id} completed"})
                except Exception:
                    pass
            threading.Thread(target=worker, daemon=True).start()
            return

        # Real agent execution path
        from core.models import AIAgentRequest  # our shim type

        # Build per-task policy environment from permission_profile
        tool_allow = (permission_profile or {}).get("tool_allowlist", []) if isinstance(permission_profile, dict) else []
        stdio_cmds: List[str] = []
        http_prefixes: List[str] = []
        for entry in tool_allow:
            s = str(entry)
            ls = s.lower()
            # Allow generic MCP stdio defaults if wildcard present
            if ls in ("mcp", "mcp:*", "mcp-stdio", "mcp:stdio"):
                for cmd in ("npx", "python"):
                    if cmd not in stdio_cmds:
                        stdio_cmds.append(cmd)
            # Specific stdio command forms
            if ls.startswith("mcp:stdio:"):
                cmd = s.split(":", 2)[-1]
                if cmd and cmd not in stdio_cmds:
                    stdio_cmds.append(cmd)
            if ls.startswith("stdio:"):
                cmd = s.split(":", 1)[-1]
                if cmd and cmd not in stdio_cmds:
                    stdio_cmds.append(cmd)
            # HTTP prefixes
            if ls.startswith("mcp:http:") or ls.startswith("http:") or ls.startswith("https:"):
                # Keep original string for actual prefix (may be https://...)
                if s not in http_prefixes:
                    http_prefixes.append(s)
        # If no explicit stdio commands but any mcp tool was allowed, default to npx;python
        if not stdio_cmds and any(str(x).lower().startswith("mcp") for x in tool_allow):
            stdio_cmds = ["npx", "python"]
        stdio_allow = ";".join(stdio_cmds) if stdio_cmds else None
        http_allow = ";".join(http_prefixes) if http_prefixes else None
        sandbox_mode = (permission_profile or {}).get("sandbox") if isinstance(permission_profile, dict) else None

        # Resolve alias to base agent if needed
        base_agent_id = agent_id
        try:
            u = USER_AGENTS.get(agent_id)
            if u and isinstance(u.get("alias_of"), str):
                base_agent_id = str(u["alias_of"]) or agent_id
        except Exception:
            base_agent_id = agent_id

        async def run_agent_async():
            req = AIAgentRequest(request_id=task_id, text=goal, context=params or {}, cwd=cwd)
            try:
                TASKS.update(task_id, status="running", started_at=int(time.time() * 1000))
                TASKS.append_progress(task_id, "Agent started")
                result = await self.registry.process_request(base_agent_id, req)
                TASKS.update(task_id, status="completed", completed_at=int(time.time() * 1000), result=result)
                TASKS.append_progress(task_id, "Agent completed")
            except Exception as e:  # pragma: no cover
                TASKS.update(task_id, status="failed", error=str(e))

        def runner():
            try:
                import asyncio
                # Set policy env for this task
                old_stdio = os.environ.get("AGENT_ALLOW_MCP_STDIO")
                old_http = os.environ.get("AGENT_ALLOW_HTTP_PREFIXES")
                old_sandbox = os.environ.get("AGENT_SANDBOX_MODE")
                if stdio_allow is not None:
                    os.environ["AGENT_ALLOW_MCP_STDIO"] = stdio_allow
                if http_allow is not None:
                    os.environ["AGENT_ALLOW_HTTP_PREFIXES"] = http_allow
                if sandbox_mode is not None:
                    os.environ["AGENT_SANDBOX_MODE"] = str(sandbox_mode)
                asyncio.run(run_agent_async())
                # Restore
                if old_stdio is None:
                    os.environ.pop("AGENT_ALLOW_MCP_STDIO", None)
                else:
                    os.environ["AGENT_ALLOW_MCP_STDIO"] = old_stdio
                if old_http is None:
                    os.environ.pop("AGENT_ALLOW_HTTP_PREFIXES", None)
                else:
                    os.environ["AGENT_ALLOW_HTTP_PREFIXES"] = old_http
                if old_sandbox is None:
                    os.environ.pop("AGENT_SANDBOX_MODE", None)
                else:
                    os.environ["AGENT_SANDBOX_MODE"] = old_sandbox
            except Exception as e:  # pragma: no cover
                TASKS.update(task_id, status="failed", error=str(e))

        threading.Thread(target=runner, daemon=True).start()


BRIDGE = AgentBridge()


def list_tools() -> Dict[str, Any]:
    tools = [
        Tool(
            name="agents.list",
            title="List Agents",
            description="Return the list of configured agents",
            inputSchema=ToolInputSchema(properties={}, required=[]),
        ),
        Tool(
            name="agents.start_task",
            title="Start Agent Task",
            description="Start a background task on a configured agent",
            inputSchema=ToolInputSchema(
                properties={
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "goal": {"type": "string", "description": "High-level goal/instructions"},
                    "params": {"type": "object", "description": "Additional parameters"},
                    "cwd": {"type": "string", "description": "Working directory (optional)"},
                    "permission_profile": {"type": "object", "description": "Sandbox + approvals + tool allowlist"},
                },
                required=["agent_id", "goal"]
            ),
        ),
        Tool(
            name="agents.task_status",
            title="Get Task Status",
            description="Fetch the latest status for a task",
            inputSchema=ToolInputSchema(
                properties={"task_id": {"type": "string"}},
                required=["task_id"],
            ),
        ),
        Tool(
            name="agents.cancel_task",
            title="Cancel Task",
            description="Cancel a running task",
            inputSchema=ToolInputSchema(
                properties={"task_id": {"type": "string"}},
                required=["task_id"],
            ),
        ),
        Tool(
            name="agents.approval_decision",
            title="Record Approval Decision",
            description="Record user approval decision for exec/patch keyed by submission_id or call_id",
            inputSchema=ToolInputSchema(
                properties={
                    "kind": {"type": "string", "enum": ["exec", "patch"], "description": "Decision applies to exec or patch"},
                    "decision": {"type": "string", "enum": ["approved", "approved_for_session", "denied", "abort"], "description": "User decision"},
                    "submission_id": {"type": "string"},
                    "call_id": {"type": "string"},
                },
                required=["decision"],
            ),
        ),
    ]
    return {
        "jsonrpc": JSONRPC,
        "result": {"tools": [asdict(t) for t in tools]},
    }


def result_text(text: str) -> Dict[str, Any]:
    return {
        "jsonrpc": JSONRPC,
        "result": {
            "content": [
                {"type": "text", "text": text}
            ]
        },
    }


def handle_call(name: str, args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    args = args or {}
    if name == "agents.list":
        agents = BRIDGE.list_agents()
        return {
            "jsonrpc": JSONRPC,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps({"agents": agents})}
                ],
                "structuredContent": {"agents": agents},
            },
        }

    if name == "agents.start_task":
        agent_id = str(args.get("agent_id", ""))
        goal = str(args.get("goal", ""))
        params = args.get("params") or {}
        cwd = args.get("cwd")
        permission_profile = args.get("permission_profile") or {}
        task = TASKS.create(agent_id, goal, params)
        BRIDGE.start_task(task["task_id"], agent_id, goal, params, cwd, permission_profile)
        return result_text(f"Started task {task['task_id']} on agent {agent_id}")

    if name == "agents.task_status":
        task_id = str(args.get("task_id", ""))
        task = TASKS.get(task_id)
        if not task:
            return result_text(json.dumps({"error": "not_found", "task_id": task_id}))
        return {
            "jsonrpc": JSONRPC,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(task)}
                ],
                "structuredContent": task,
            },
        }

    if name == "agents.cancel_task":
        task_id = str(args.get("task_id", ""))
        ok = TASKS.cancel(task_id)
        return result_text(json.dumps({"task_id": task_id, "canceled": bool(ok)}))

    if name == "agents.approval_decision":
        kind = str(args.get("kind", ""))
        decision = str(args.get("decision", ""))
        submission_id = args.get("submission_id") or None
        call_id = args.get("call_id") or None
        if call_id and not submission_id:
            submission_id = get_submission_id_for_call(str(call_id))
        if isinstance(submission_id, str) and submission_id:
            record_approval_decision(submission_id, decision, str(call_id) if isinstance(call_id, str) else None)
            return result_text(json.dumps({"recorded": True, "submission_id": submission_id, "decision": decision, "kind": kind}))
        return result_text(json.dumps({"recorded": False, "reason": "missing submission_id"}))

    return {
        "jsonrpc": JSONRPC,
        "result": {
            "content": [{"type": "text", "text": f"unknown tool: {name}"}],
            "isError": True,
        },
    }


def handle_request(req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        # minimal handshake
        result = {
            "jsonrpc": JSONRPC,
            "result": {
                "capabilities": {"tools": {"listChanged": False}},
                "protocolVersion": MCP_VERSION,
                "serverInfo": asdict(Implementation(name="agents-orchestrator", version="0.1.0")),
            },
        }
        result["id"] = req_id
        return result

    if method == "tools/list":
        result = list_tools()
        result["id"] = req_id
        return result

    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments")
        result = handle_call(str(name), arguments if isinstance(arguments, dict) else None)
        result["id"] = req_id
        return result

    if method == "ping":
        return {"jsonrpc": JSONRPC, "id": req_id, "result": {"ok": True}}

    # ignore unknowns
    return {"jsonrpc": JSONRPC, "id": req_id, "result": {"ok": False}}


def main() -> None:
    # Read newline-delimited JSON from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception as e:
            log(f"failed to parse json: {e}: {line}")
            continue

        if isinstance(msg, dict) and msg.get("jsonrpc") == JSONRPC:
            if "method" in msg and "id" in msg:
                # request
                try:
                    resp = handle_request(msg)
                    if resp is not None:
                        write_message(resp)
                except Exception as e:
                    err = {
                        "jsonrpc": JSONRPC,
                        "id": msg.get("id"),
                        "error": {"code": -32603, "message": f"Internal error: {e}"},
                    }
                    write_message(err)
            elif "method" in msg and "id" not in msg:
                # notification: ignore for MVP
                log(f"<- notification ignored: {msg.get('method')}")
            else:
                # response to our request: ignore (we never send requests)
                pass


if __name__ == "__main__":
    main()
