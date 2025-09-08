"""
Minimal event schema and adapter for agent-exec streaming.

This keeps a stable surface that we can evolve toward codex-rs parity.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


class EventsAdapter:
    def __init__(
        self,
        json_mode: bool = False,
        event_id: Optional[str] = None,
        originator: str = "cadenza_cli_py",
        session_id: Optional[str] = None,
        session_cwd: Optional[str] = None,
    ) -> None:
        self.json_mode = json_mode
        self.event_id = event_id or _gen_id()
        self.originator = originator
        self.session_id = session_id
        self.session_cwd = session_cwd

    # High-level lifecycle
    def session_configured(self, session_id: str, cwd: str) -> Dict[str, Any]:
        ev = {
            "type": "SessionConfigured",
            "id": self.event_id,
            "ts": _ts(),
            "session_id": session_id,
            "cwd": cwd,
            "originator": self.originator,
        }
        return ev

    def task_started(self, session_id: str, prompt: str) -> Dict[str, Any]:
        return {
            "type": "TaskStarted",
            "id": self.event_id,
            "ts": _ts(),
            "session_id": session_id,
            "prompt": prompt,
            "originator": self.originator,
        }

    def task_complete(self, final_text: str) -> Dict[str, Any]:
        return {
            "type": "TaskComplete",
            "id": self.event_id,
            "ts": _ts(),
            "final_text": final_text,
            "originator": self.originator,
        }

    # Assistant content
    def agent_message_delta(self, content: str) -> Dict[str, Any]:
        return {
            "type": "AgentMessageDelta",
            "id": self.event_id,
            "ts": _ts(),
            "content": content,
            "originator": self.originator,
        }

    def agent_message(self, content: str) -> Dict[str, Any]:
        return {
            "type": "AgentMessage",
            "id": self.event_id,
            "ts": _ts(),
            "content": content,
            "originator": self.originator,
        }

    def reasoning_delta(self, content: str) -> Dict[str, Any]:
        return {
            "type": "AgentReasoningDelta",
            "id": self.event_id,
            "ts": _ts(),
            "content": content,
            "originator": self.originator,
        }

    def reasoning_raw_delta(self, content: str) -> Dict[str, Any]:
        return {
            "type": "AgentReasoningRawContentDelta",
            "id": self.event_id,
            "ts": _ts(),
            "content": content,
            "originator": self.originator,
        }

    def tool_result(self, name: Optional[str], content: str) -> Dict[str, Any]:
        ev = {
            "type": "ToolResult",
            "id": self.event_id,
            "ts": _ts(),
            "content": content,
            "originator": self.originator,
        }
        if name:
            ev["name"] = name
        return ev

    # Tool calls
    def tool_call_begin(self, name: str) -> Dict[str, Any]:
        return {
            "type": "ToolCallBegin",
            "id": self.event_id,
            "ts": _ts(),
            "name": name,
            "call_id": _gen_id(),
            "originator": self.originator,
        }

    def tool_call_end(self, name: str, success: Optional[bool] = None) -> Dict[str, Any]:
        ev: Dict[str, Any] = {
            "type": "ToolCallEnd",
            "id": self.event_id,
            "ts": _ts(),
            "name": name,
            "originator": self.originator,
        }
        if success is not None:
            ev["success"] = success
        return ev

    # Reasoning helpers (structure only; no chain-of-thought content)
    def reasoning_section_break(self, label: str) -> Dict[str, Any]:
        return {
            "type": "AgentReasoningSectionBreak",
            "id": self.event_id,
            "ts": _ts(),
            "label": label,
            "originator": self.originator,
        }

    # Event-bus mapping (orchestrator internal events -> public events)
    def from_bus_event(self, ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        et = ev.get("type")
        if et == "tool_start":
            return self.tool_call_begin(ev.get("name", "unknown"))
        if et == "tool_end":
            return self.tool_call_end(ev.get("name", "unknown"), success=True)
        if et == "exec_begin":
            return {
                "type": "ExecCommandBegin",
                "id": self.event_id,
                "ts": _ts(),
                "command": ev.get("command"),
                "cwd": ev.get("cwd"),
                "call_id": ev.get("call_id"),
                "originator": self.originator,
                "session_id": self.session_id,
            }
        if et == "exec_end":
            return {
                "type": "ExecCommandEnd",
                "id": self.event_id,
                "ts": _ts(),
                "exit_code": ev.get("exit_code"),
                "success": ev.get("success"),
                "originator": self.originator,
                "session_id": self.session_id,
            }
        if et == "patch_begin":
            return {
                "type": "PatchApplyBegin",
                "id": self.event_id,
                "ts": _ts(),
                "call_id": ev.get("call_id"),
                "originator": self.originator,
            }
        if et == "patch_end":
            return {
                "type": "PatchApplyEnd",
                "id": self.event_id,
                "ts": _ts(),
                "call_id": ev.get("call_id"),
                "success": ev.get("success"),
                "originator": self.originator,
            }
        if et == "approval_request":
            t = "ApplyPatchApprovalRequest" if ev.get("operation") == "patch_application" else "ApprovalRequest"
            return {
                "type": t,
                "id": self.event_id,
                "ts": _ts(),
                "request_id": ev.get("id"),
                "operation": ev.get("operation"),
                "description": ev.get("description"),
                "session_id": ev.get("session_id"),
                "timeout_s": ev.get("timeout_s"),
                "details": ev.get("details"),
                "originator": self.originator,
            }
        if et == "turn_diff":
            return {
                "type": "TurnDiff",
                "id": self.event_id,
                "ts": _ts(),
                "files": ev.get("files", []),
                "originator": self.originator,
            }
        if et == "exec_session_output":
            return {
                "type": "ExecSessionOutput",
                "id": self.event_id,
                "ts": _ts(),
                "session_id": ev.get("session_id"),
                "stream": ev.get("stream"),
                "data_b64": ev.get("data_b64"),
                "encoding": "base64",
                "originator": self.originator,
            }
        return None


def _ts() -> float:
    return time.time()


def _gen_id() -> str:
    import uuid
    return str(uuid.uuid4())
