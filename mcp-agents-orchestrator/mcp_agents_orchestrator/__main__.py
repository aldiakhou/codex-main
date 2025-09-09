import json
import sys
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

JSONRPC = "2.0"
MCP_VERSION = "2025-06-18"


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


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: Dict[str, Dict[str, Any]] = {}

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
        return task

    def update(self, task_id: str, **patch: Any) -> None:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            t.update(patch)

    def append_progress(self, task_id: str, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
        entry = {"ts": int(time.time() * 1000), "level": level, "message": message}
        if data:
            entry["data"] = data
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            t.setdefault("progress", []).append(entry)

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            t = self._tasks.get(task_id)
            return json.loads(json.dumps(t)) if t else None

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return False
            t["status"] = "canceled"
            return True


TASKS = TaskStore()


# Simple in-memory agent registry (replace with file-backed persistence as needed)
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
        return {
            "jsonrpc": JSONRPC,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps({"agents": DEFAULT_AGENTS})}
                ],
                "structuredContent": {"agents": DEFAULT_AGENTS},
            },
        }

    if name == "agents.start_task":
        agent_id = str(args.get("agent_id", ""))
        goal = str(args.get("goal", ""))
        params = args.get("params") or {}
        task = TASKS.create(agent_id, goal, params)

        def worker(task_id: str, goal_text: str):
            TASKS.update(task_id, status="running", started_at=int(time.time() * 1000))
            TASKS.append_progress(task_id, "Agent received goal", data={"goal": goal_text})
            # Simulate work
            for step in ["collecting_sources", "extracting_insights", "drafting_report"]:
                TASKS.append_progress(task_id, step.replace("_", " ").title())
                time.sleep(0.8)
            TASKS.update(task_id, status="completed", completed_at=int(time.time() * 1000), result={"summary": f"Task complete: {goal_text}"})

        threading.Thread(target=worker, args=(task["task_id"], goal), daemon=True).start()
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

