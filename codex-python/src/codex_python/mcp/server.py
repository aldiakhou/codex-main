"""
MCP Server implementation for Cadenza (Codex Python).

Exposes a minimal MCP server over stdio with two tools mirroring codex-rs:
- "codex": start a new Codex session (returns the first assistant reply)
- "codex-reply": continue an existing session by session_id

Notes
- This implementation focuses on correctness and parity of tool shapes.
- Streaming and cancellation are left for a follow-up.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import structlog
from pydantic import BaseModel, Field
import time
import contextlib
from pathlib import Path

from ..core.config import Config
from ..core.orchestrator import CodexOrchestrator
from ..llm.client import LLMMessage

# MCP low-level server SDK imports
import mcp.types as mtypes  # type: ignore
from mcp.server.lowlevel import Server as LowLevelServer  # type: ignore
from mcp.server.lowlevel import NotificationOptions  # type: ignore
from mcp.server.models import InitializationOptions  # type: ignore
import mcp.server.stdio  # type: ignore


logger = structlog.get_logger(__name__)


# --- Tool input schemas (align with codex-rs mcp-server) ---


class CodexToolCallApprovalPolicy(str):
    # Mirror codex-rs enum values (kebab-case)
    Untrusted = "untrusted"
    OnFailure = "on-failure"
    OnRequest = "on-request"
    Never = "never"


class CodexToolCallSandboxMode(str):
    ReadOnly = "read-only"
    WorkspaceWrite = "workspace-write"
    DangerFullAccess = "danger-full-access"


class CodexToolCallParam(BaseModel):
    prompt: str = Field(..., description="Initial user prompt to start the Codex conversation")
    model: Optional[str] = Field(None, description="Override model name (e.g. 'o3', 'gpt-4o')")
    profile: Optional[str] = Field(None, description="Config profile to use")
    cwd: Optional[str] = Field(None, description="Working directory for this session")
    approval_policy: Optional[str] = Field(
        None, description="Approval policy: untrusted | on-failure | on-request | never"
    )
    sandbox: Optional[str] = Field(
        None, description="Sandbox mode: read-only | workspace-write | danger-full-access"
    )
    stream: Optional[bool] = Field(False, description="If true, stream deltas via MCP notifications")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Arbitrary config overrides (key -> JSON value)"
    )
    base_instructions: Optional[str] = Field(
        None, description="Override the base instructions for the agent"
    )
    include_plan_tool: Optional[bool] = Field(
        None, description="Whether to include the plan tool in the conversation"
    )


class CodexToolCallReplyParam(BaseModel):
    session_id: str = Field(..., description="Codex session id returned by the 'codex' tool")
    prompt: str = Field(..., description="Next user prompt to continue the conversation")


# --- Conversation state ---


@dataclass
class ConversationState:
    session_id: str
    cwd: str
    orchestrator: CodexOrchestrator
    messages: list[LLMMessage] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: time.time())
    turn_count: int = 0
    max_turns: int = 50
    ttl_seconds: float = 3600.0
    running_task: Optional[asyncio.Task] = None


class ConversationManager:
    def __init__(self, base_config: Config) -> None:
        self._conversations: dict[str, ConversationState] = {}
        self._lock = asyncio.Lock()
        self._config = base_config

    async def create(self, cwd: str, orchestrator: CodexOrchestrator) -> ConversationState:
        session_id = str(uuid.uuid4())
        # Non-interactive approvals for MCP: rely on external responses
        try:
            orchestrator.approval_manager.set_interactive(False)  # type: ignore[attr-defined]
        except Exception:
            pass
        await orchestrator.initialize()
        orchestrator.create_session(session_id, cwd)
        state = ConversationState(session_id=session_id, cwd=cwd, orchestrator=orchestrator)
        async with self._lock:
            self._conversations[session_id] = state
        return state

    async def get(self, session_id: str) -> Optional[ConversationState]:
        async with self._lock:
            state = self._conversations.get(session_id)
        if state:
            return state
        # Attempt to load from disk
        data = _load_session_from_disk(session_id)
        if not data:
            return None
        cwd = data.get("cwd") or await _cwd()
        orch = CodexOrchestrator(self._config)
        try:
            orch.approval_manager.set_interactive(False)  # type: ignore[attr-defined]
        except Exception:
            pass
        await orch.initialize()
        orch.create_session(session_id, cwd)
        state = ConversationState(session_id=session_id, cwd=cwd, orchestrator=orch)
        for msg in data.get("messages", []) or []:
            role = msg.get("role")
            content = msg.get("content")
            if isinstance(role, str) and isinstance(content, str):
                state.messages.append(LLMMessage(role=role, content=content))
        async with self._lock:
            self._conversations[session_id] = state
        return state


# --- MCP server wiring ---


class CodexMCPServer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._conversations = ConversationManager(config)
        self._server = None
        self._running: dict[str, asyncio.Task] = {}
        self._req_to_session: dict[str, str] = {}
        # Buffered exec streaming for pull-based clients
        self._exec_buffers: Dict[str, list[Dict[str, Any]]] = {}
        self._exec_status: Dict[str, Dict[str, Any]] = {}
        self._exec_buffers: Dict[str, list[Dict[str, Any]]] = {}
        self._exec_status: Dict[str, Dict[str, Any]] = {}

    def _build_tool_schema(self, model: type[BaseModel]) -> Dict[str, Any]:
        # Pydantic JSON Schema -> MCP ToolInputSchema-compatible dict
        s = model.model_json_schema(ref_template="#/$defs/{model}")
        # MCP expects JSON Schema Draft 2020-12 compatible — pydantic outputs 2020-12
        return s

    async def _handle_codex(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            params = CodexToolCallParam(**(args or {}))
        except Exception as e:
            return _error_result(f"Invalid parameters for codex: {e}")

        # Build a per-session orchestrator with overrides
        cfg = self._apply_overrides(self.config, params)
        orch = CodexOrchestrator(cfg)

        cwd = params.cwd or getattr(cfg, "working_directory", None) or await _cwd()  # type: ignore
        state = await self._conversations.create(cwd, orch)

        # Add the user message to conversation
        state.messages.append(LLMMessage(role="user", content=params.prompt))
        _save_session_to_disk(state)
        req_id = _gen_id()
        self._req_to_session[req_id] = state.session_id

        if params.stream:
            # Launch streaming background task and return immediately
            task = asyncio.create_task(self._run_streaming_turn(req_id, state))
            self._running[req_id] = task
            state.running_task = task
            return {
                "content": [
                    _text_block("Streaming started"),
                    _text_block(f"session_id: {state.session_id}"),
                    _text_block(f"request_id: {req_id}"),
                ],
                "structured_content": {
                    "session_id": state.session_id,
                    "request_id": req_id,
                    "streaming": True,
                },
            }
        else:
            final_text = await self._run_streaming_turn(req_id, state, emit=False)
            return {
                "content": [
                    _text_block(final_text or ""),
                    _text_block(f"session_id: {state.session_id}"),
                ],
                "structured_content": {
                    "session_id": state.session_id,
                    "request_id": req_id,
                    "streaming": False,
                    "final_text": final_text,
                },
            }

    async def _handle_codex_reply(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            params = CodexToolCallReplyParam(**(args or {}))
        except Exception as e:
            return _error_result(f"Invalid parameters for codex-reply: {e}")

        state = await self._conversations.get(params.session_id)
        if not state:
            return _error_result(f"Session not found for session_id: {params.session_id}")

        # Append user message and run turn
        state.messages.append(LLMMessage(role="user", content=params.prompt))
        req_id = _gen_id()
        self._req_to_session[req_id] = state.session_id
        # For reply, default to streaming for parity with inspector UX
        final_text = await self._run_streaming_turn(req_id, state, emit=False)
        _save_session_to_disk(state)
        return {
            "content": [_text_block(final_text or "")],
            "structured_content": {
                "session_id": state.session_id,
                "request_id": req_id,
                "streaming": False,
                "final_text": final_text,
            },
        }

    def _apply_overrides(self, base: Config, params: CodexToolCallParam) -> Config:
        # Create a shallow copy via dict roundtrip
        data = base.to_dict()
        # Apply known overrides
        if params.model:
            data["openai_model"] = params.model
        if params.approval_policy:
            data["approval_policy"] = params.approval_policy
        if params.sandbox:
            # Map to our sandbox fields
            data["enable_sandbox"] = params.sandbox != CodexToolCallSandboxMode.DangerFullAccess
            # normalize to our Config expected values
            data["sandbox_mode"] = (
                "workspace" if params.sandbox == CodexToolCallSandboxMode.WorkspaceWrite else params.sandbox
            )
        if params.base_instructions is not None:
            data["base_instructions"] = params.base_instructions
        # Arbitrary config overrides
        if params.config:
            _deep_set_multi(data, params.config)
        return Config.from_dict(data)

    async def run_stdio(self) -> None:
        """Run an MCP server over stdio using the low-level SDK."""
        server = LowLevelServer("codex-python")
        self._server = server

        codex_schema = self._build_tool_schema(CodexToolCallParam)
        codex_reply_schema = self._build_tool_schema(CodexToolCallReplyParam)
        exec_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command and arguments",
                },
                "cwd": {"type": "string"},
                "env": {"type": "object"},
                "stream": {"type": "boolean", "default": True},
                "requireApproval": {"type": "boolean", "default": True},
            },
            "required": ["command"],
        }
        patch_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "patch": {"type": "string", "description": "Unified diff text"},
                "root": {"type": "string"},
                "requireApproval": {"type": "boolean", "default": True},
            },
            "required": ["patch"],
        }
        backtrack_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "steps": {"type": "integer", "default": 1, "minimum": 1},
            },
            "required": ["session_id"],
        }
        fork_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "upto": {"type": "integer", "minimum": 0},
            },
            "required": ["session_id"],
        }
        respond_approval_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "decision": {"type": "string", "enum": ["approved", "denied", "cancelled"]},
                "responder": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["request_id", "decision"],
        }
        list_approvals_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "default": 100},
            },
        }
        watch_approvals_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "interval_s": {"type": "number", "default": 2.0, "minimum": 0.2},
                "max_ticks": {"type": "integer", "default": 0, "minimum": 0},
            },
        }

        @server.list_tools()
        async def _list_tools() -> list[mtypes.Tool]:  # type: ignore
            return [
                mtypes.Tool(
                    name="codex",
                    description=(
                        "Run a Codex session. Accepts configuration parameters matching the Codex Config struct."
                    ),
                    inputSchema=codex_schema,
                ),
                mtypes.Tool(
                    name="codex-reply",
                    description="Continue a Codex session by providing the session id and prompt.",
                    inputSchema=codex_reply_schema,
                ),
                mtypes.Tool(
                    name="exec",
                    description="Execute a command (non-interactive); optional streaming of stdout/stderr.",
                    inputSchema=exec_schema,
                ),
                mtypes.Tool(
                    name="apply_patch",
                    description="Apply a unified diff to the workspace root.",
                    inputSchema=patch_schema,
                ),
                mtypes.Tool(
                    name="codex-backtrack",
                    description="Backtrack a conversation by N steps (removes last user/assistant turns).",
                    inputSchema=backtrack_schema,
                ),
                mtypes.Tool(
                    name="codex-fork",
                    description="Fork a conversation to a new session; optionally include messages up to index.",
                    inputSchema=fork_schema,
                ),
                mtypes.Tool(
                    name="codex-respond-approval",
                    description="Respond to a pending approval request (approved|denied|cancelled)",
                    inputSchema=respond_approval_schema,
                ),
                mtypes.Tool(
                    name="codex-list-approvals",
                    description="List pending approval requests (optionally filtered by session)",
                    inputSchema=list_approvals_schema,
                ),
                mtypes.Tool(
                    name="codex-watch-approvals",
                    description="Emit periodic approvals snapshots as notifications/progress",
                    inputSchema=watch_approvals_schema,
                ),
                mtypes.Tool(
                    name="codex-exec-poll",
                    description="Poll buffered exec output by request_id (pull alternative to notifications)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "request_id": {"type": "string"},
                            "max_chunks": {"type": "integer", "minimum": 1, "default": 100},
                        },
                        "required": ["request_id"],
                    },
                ),
            ]

        @server.call_tool()
        async def _call_tool(name: str, arguments: dict) -> Any:  # type: ignore
            if name == "codex":
                return await self._handle_codex(arguments or {})
            if name == "codex-reply":
                return await self._handle_codex_reply(arguments or {})
            if name == "exec":
                return await self._handle_exec(arguments or {})
            if name == "apply_patch":
                return await self._handle_apply_patch(arguments or {})
            if name == "codex-backtrack":
                return await self._handle_backtrack(arguments or {})
            if name == "codex-fork":
                return await self._handle_fork(arguments or {})
            if name == "codex-respond-approval":
                return await self._handle_respond_approval(arguments or {})
            if name == "codex-list-approvals":
                return await self._handle_list_approvals(arguments or {})
            if name == "codex-watch-approvals":
                return await self._handle_watch_approvals(arguments or {})
            if name == "codex-exec-poll":
                return await self._handle_exec_poll(arguments or {})
            raise ValueError(f"Unknown tool: {name}")

        @server.notification("notifications/cancelled")
        async def _on_cancelled(params: dict[str, Any]) -> None:
            rid = params.get("requestId") or params.get("request_id")
            if isinstance(rid, int):
                rid = str(rid)
            if isinstance(rid, str):
                task = self._running.pop(rid, None)
                if task and not task.done():
                    task.cancel()

        logger.info("Starting Codex MCP server (stdio)")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="codex-python",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def _run_streaming_turn(self, request_id: str, state: ConversationState, *, emit: bool = True) -> str:
        """Run a single turn streaming via MCP notifications, persist tool messages, and return final text.

        If emit=False, does not send MCP notifications; still persists tool outputs and returns final text.
        """
        # Check session policy
        now = time.time()
        if now - state.created_at > state.ttl_seconds:
            return "[session expired]"
        if state.turn_count >= state.max_turns:
            return "[turn limit reached]"

        final_text = ""
        usage: Optional[Dict[str, Any]] = None
        # Bridge orchestrator bus to MCP notifications while this turn runs
        async def forward_bus():
            async for ev in state.orchestrator.events.subscribe(types=[
                "tool_start","tool_end","exec_begin","exec_end","patch_begin","patch_end","turn_diff","approval_request"
            ]):
                if not emit:
                    continue
                if ev.get("type") == "approval_request":
                    await self._send_progress_notification("codex.approval_request", {
                        "request_id": request_id,
                        "session_id": state.session_id,
                        "approval": ev,
                    })
                else:
                    await self._send_progress_notification("codex.event", {
                        "request_id": request_id,
                        "session_id": state.session_id,
                        "event": ev,
                    })

        bus_task = asyncio.create_task(forward_bus())
        try:
            async for item in state.orchestrator.chat(state.messages, stream=True):
                if isinstance(item, dict):
                    t = item.get("type")
                    if t == "delta":
                        content = item.get("content") or ""
                        final_text = content or final_text
                        if emit and content:
                            await self._send_progress_notification("codex.delta", {
                                "request_id": request_id,
                                "session_id": state.session_id,
                                "content": content,
                            })
                    elif t in ("reasoning_raw_delta","reasoning_delta"):
                        if emit:
                            await self._send_progress_notification("codex.reasoning", {
                                "request_id": request_id,
                                "session_id": state.session_id,
                                "kind": t,
                                "content": item.get("content") or "",
                            })
                    elif t == "tool_result":
                        # Persist tool result into conversation as a tool message
                        tool_text = item.get("content") or ""
                        state.messages.append(LLMMessage(role="tool", content=tool_text))
                        if emit and tool_text:
                            await self._send_progress_notification("codex.tool_result", {
                                "request_id": request_id,
                                "session_id": state.session_id,
                                "content": tool_text,
                            })
                    elif "content" in item and item.get("tool_calls") == []:
                        final_text = item.get("content") or final_text
                        if isinstance(item.get("usage"), dict):
                            usage = item.get("usage")
            # Append final assistant message
            if final_text:
                state.messages.append(LLMMessage(role="assistant", content=final_text))
            state.turn_count += 1
            _save_session_to_disk(state)
        finally:
            try:
                bus_task.cancel()
                with contextlib.suppress(Exception):
                    await bus_task
            except Exception:
                pass

        if emit and final_text:
            payload = {
                "request_id": request_id,
                "session_id": state.session_id,
                "final_text": final_text,
            }
            if usage:
                payload["usage"] = usage
            await self._send_progress_notification("codex.completed", payload)

        return final_text

    async def _send_progress_notification(self, method_suffix: str, params: Dict[str, Any]) -> None:
        if not self._server:
            return
        # Unified progress channel for clients expecting generic notifications
        await self._server.send_notification("notifications/progress", {"kind": method_suffix, **params})

    # --- Extra MCP tools implementations ---

    async def _ensure_session(self, cwd: Optional[str]) -> ConversationState:
        # Reuse or create a generic session for non-conversation tools
        orch = CodexOrchestrator(self.config)
        return await self._conversations.create(cwd or await _cwd(), orch)

    async def _handle_exec(self, args: Dict[str, Any]) -> Dict[str, Any]:
        cmd = args.get("command")
        if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
            return _error_result("'command' must be an array of strings")
        cwd = args.get("cwd")
        env = args.get("env") if isinstance(args.get("env"), dict) else None
        stream = bool(args.get("stream", True))
        require_approval = bool(args.get("requireApproval", True))

        state = await self._ensure_session(cwd)
        req_id = _gen_id()

        if stream:
            async def _run():
                async for item in state.orchestrator.execute_command_stream(
                    cmd,
                    session_id=state.session_id,
                    cwd=cwd,
                    env=env,
                    require_approval=require_approval,
                ):
                    t = item.get("type")
                    if t == "delta":
                        import base64
                        data = item.get("data") or b""
                        if isinstance(data, bytes):
                            b64 = base64.b64encode(data).decode("ascii")
                        else:
                            b64 = ""
                        chunk = {
                            "request_id": req_id,
                            "session_id": state.session_id,
                            "stream": item.get("stream"),
                            "data_b64": b64,
                        }
                        self._exec_buffers.setdefault(req_id, []).append(chunk)
                        await self._send_progress_notification("codex.exec.delta", chunk)
                    elif t == "result":
                        self._exec_status[req_id] = {"completed": True, "returncode": item.get("returncode")}
                        await self._send_progress_notification("codex.exec.completed", {
                            "request_id": req_id,
                            "session_id": state.session_id,
                            "returncode": item.get("returncode"),
                        })
                    elif t == "error":
                        self._exec_status[req_id] = {"completed": True, "error": item.get("message")}
                        await self._send_progress_notification("codex.exec.error", {
                            "request_id": req_id,
                            "session_id": state.session_id,
                            "message": item.get("message"),
                        })
                        break
            task = asyncio.create_task(_run())
            self._running[req_id] = task
            return {
                "content": [ _text_block("Exec streaming started") ],
                "structured_content": {
                    "request_id": req_id,
                    "session_id": state.session_id,
                    "streaming": True,
                }
            }
        else:
            res = await state.orchestrator.execute_command(
                cmd,
                session_id=state.session_id,
                cwd=cwd,
                env=env,
                require_approval=require_approval,
            )
            out = {
                "success": res.success,
                "session_id": state.session_id,
                "returncode": (res.result or {}).get("returncode") if isinstance(res.result, dict) else None,
                "stdout": (res.result or {}).get("stdout") if isinstance(res.result, dict) else None,
                "stderr": (res.result or {}).get("stderr") if isinstance(res.result, dict) else None,
            }
            return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_apply_patch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        patch_text = args.get("patch")
        if not isinstance(patch_text, str) or not patch_text:
            return _error_result("'patch' must be a non-empty string")
        root = args.get("root")
        require_approval = bool(args.get("requireApproval", True))
        state = await self._ensure_session(root)
        call_id = _gen_id()

        res = await state.orchestrator.apply_patch(
            patch_text,
            session_id=state.session_id,
            root_path=root,
            require_approval=require_approval,
        )
        out = {
            "success": res.success,
            "session_id": state.session_id,
            "details": res.metadata,
        }
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_exec_poll(self, args: Dict[str, Any]) -> Dict[str, Any]:
        req_id = args.get("request_id")
        if not isinstance(req_id, str) or not req_id:
            return _error_result("'request_id' is required")
        max_chunks = int(args.get("max_chunks", 100))
        buf = self._exec_buffers.get(req_id, [])
        out_chunks = buf[:max_chunks]
        self._exec_buffers[req_id] = buf[max_chunks:]
        status = self._exec_status.get(req_id, {"completed": False})
        out = {"request_id": req_id, "chunks": out_chunks, **status}
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_backtrack(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id = args.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return _error_result("'session_id' is required")
        steps = args.get("steps", 1)
        if not isinstance(steps, int) or steps < 1:
            return _error_result("'steps' must be a positive integer")
        state = await self._conversations.get(session_id)
        if not state:
            return _error_result(f"Session not found: {session_id}")
        # Remove last 2*steps messages (user+assistant pairs) if available
        remove = min(len(state.messages), steps * 2)
        if remove > 0:
            del state.messages[-remove:]
        _save_session_to_disk(state)
        out = {"session_id": session_id, "remaining_messages": len(state.messages)}
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_fork(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id = args.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return _error_result("'session_id' is required")
        upto = args.get("upto")
        state = await self._conversations.get(session_id)
        if not state:
            return _error_result(f"Session not found: {session_id}")
        new_orch = CodexOrchestrator(self.config)
        try:
            new_orch.approval_manager.set_interactive(False)  # type: ignore[attr-defined]
        except Exception:
            pass
        new_state = await self._conversations.create(state.cwd, new_orch)
        # Copy messages up to index
        msgs = state.messages[:]
        if isinstance(upto, int) and upto >= 0:
            msgs = msgs[: upto]
        new_state.messages.extend([LLMMessage(role=m.role, content=m.content) for m in msgs])
        _save_session_to_disk(new_state)
        out = {"session_id": new_state.session_id, "copied_messages": len(new_state.messages)}
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_respond_approval(self, args: Dict[str, Any]) -> Dict[str, Any]:
        req_id = args.get("request_id")
        decision = (args.get("decision") or "").lower()
        responder = args.get("responder")
        reason = args.get("reason")
        if not isinstance(req_id, str) or not req_id:
            return _error_result("'request_id' is required")
        from ..approval.system import ApprovalStatus  # lazy import to avoid cycles
        if decision == "approved":
            status = ApprovalStatus.APPROVED
        elif decision == "denied":
            status = ApprovalStatus.DENIED
        elif decision == "cancelled":
            status = ApprovalStatus.CANCELLED
        else:
            return _error_result("'decision' must be one of: approved|denied|cancelled")

        # Find the orchestrator that owns the pending request
        found = False
        # Snapshot current conversations dict
        convs = list(self._conversations._conversations.values())  # type: ignore[attr-defined]
        for state in convs:
            mgr = getattr(state.orchestrator, "approval_manager", None)
            if not mgr:
                continue
            try:
                if req_id in mgr.pending_requests:
                    ok = await mgr.respond_to_request(req_id, status, responder=responder, reason=reason)
                    found = found or ok
                    break
            except Exception:
                continue
        out = {"request_id": req_id, "updated": found}
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_list_approvals(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_filter = args.get("session_id")
        limit = args.get("limit", 100)
        items: list[Dict[str, Any]] = []
        convs = list(self._conversations._conversations.values())  # type: ignore[attr-defined]
        for state in convs:
            mgr = getattr(state.orchestrator, "approval_manager", None)
            if not mgr:
                continue
            try:
                reqs = mgr.get_pending_requests(session_id=session_filter)
            except Exception:
                continue
            for r in reqs:
                items.append({
                    "id": r.id,
                    "operation": r.operation,
                    "description": r.description,
                    "session_id": r.session_id,
                    "timeout_s": r.timeout,
                    "level": getattr(r.level, "value", str(r.level)),
                    "details": r.details,
                })
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break
        out = {"count": len(items), "items": items}
        return {"content": [ _text_block(json.dumps(out)) ], "structured_content": out}

    async def _handle_watch_approvals(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_filter = args.get("session_id")
        interval_s = float(args.get("interval_s", 2.0))
        max_ticks = int(args.get("max_ticks", 0))
        req_id = _gen_id()
        async def _run():
            ticks = 0
            while max_ticks <= 0 or ticks < max_ticks:
                ticks += 1
                # reuse list handler
                res = await self._handle_list_approvals({"session_id": session_filter})
                sc = res.get("structured_content") or {}
                await self._send_progress_notification("codex.approvals", {
                    "request_id": req_id,
                    "items": sc.get("items", []),
                    "count": sc.get("count", 0),
                    "session_id": session_filter,
                })
                await asyncio.sleep(interval_s)
        task = asyncio.create_task(_run())
        self._running[req_id] = task
        return {"content": [ _text_block("watching approvals") ], "structured_content": {"request_id": req_id}}


# --- helpers ---


def _text_block(text: str) -> Dict[str, Any]:
    return {"type": "text", "text": text}


def _error_result(message: str) -> Dict[str, Any]:
    return {"content": [ _text_block(message) ], "is_error": True}


async def _cwd() -> str:
    import os
    return os.getcwd()


def _deep_set_multi(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    for k, v in overrides.items():
        _deep_set(base, k, v)


def _deep_set(d: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".") if isinstance(path, str) else [path]
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


async def _run_turn_non_streaming(state: ConversationState) -> str:
    """Run a single turn using the orchestrator with accumulated messages (non-streaming)."""
    # Provide prior messages + the last user message to orchestrator
    # The orchestrator will inject the system context on its own, execute tools, etc.
    final_text = ""
    async for item in state.orchestrator.chat(state.messages, stream=False):
        if isinstance(item, dict) and item.get("content"):
            final_text = item["content"]
    if final_text:
        state.messages.append(LLMMessage(role="assistant", content=final_text))
    return final_text


def _gen_id() -> str:
    return str(uuid.uuid4())


# --- session persistence helpers ---

def _sessions_dir() -> Path:
    try:
        from ..auth.store import codex_home_dir  # type: ignore
        base = Path(codex_home_dir())
    except Exception:
        base = Path.home() / ".codex"
    d = base / "mcp_sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_file(session_id: str) -> Path:
    return _sessions_dir() / f"{session_id}.json"


def _save_session_to_disk(state: ConversationState) -> None:
    try:
        data = {
            "session_id": state.session_id,
            "cwd": state.cwd,
            "created_at": state.created_at,
            "turn_count": state.turn_count,
            "messages": [{"role": m.role, "content": m.content} for m in state.messages],
        }
        _session_file(state.session_id).write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def _load_session_from_disk(session_id: str) -> Optional[Dict[str, Any]]:
    p = _session_file(session_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
