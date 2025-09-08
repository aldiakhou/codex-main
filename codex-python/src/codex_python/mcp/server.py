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
    def __init__(self) -> None:
        self._conversations: dict[str, ConversationState] = {}
        self._lock = asyncio.Lock()

    async def create(self, cwd: str, orchestrator: CodexOrchestrator) -> ConversationState:
        session_id = str(uuid.uuid4())
        await orchestrator.initialize()
        orchestrator.create_session(session_id, cwd)
        state = ConversationState(session_id=session_id, cwd=cwd, orchestrator=orchestrator)
        async with self._lock:
            self._conversations[session_id] = state
        return state

    async def get(self, session_id: str) -> Optional[ConversationState]:
        async with self._lock:
            return self._conversations.get(session_id)


# --- MCP server wiring ---


class CodexMCPServer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._conversations = ConversationManager()
        self._server = None
        self._running: dict[str, asyncio.Task] = {}
        self._req_to_session: dict[str, str] = {}

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
            ]

        @server.call_tool()
        async def _call_tool(name: str, arguments: dict) -> Any:  # type: ignore
            if name == "codex":
                return await self._handle_codex(arguments or {})
            if name == "codex-reply":
                return await self._handle_codex_reply(arguments or {})
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
        # Bridge orchestrator bus to MCP notifications while this turn runs
        async def forward_bus():
            async for ev in state.orchestrator.events.subscribe(types=[
                "tool_start","tool_end","exec_begin","exec_end","patch_begin","patch_end","turn_diff"
            ]):
                if not emit:
                    continue
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
            # Append final assistant message
            if final_text:
                state.messages.append(LLMMessage(role="assistant", content=final_text))
            state.turn_count += 1
        finally:
            try:
                bus_task.cancel()
                with contextlib.suppress(Exception):
                    await bus_task
            except Exception:
                pass

        if emit and final_text:
            await self._send_progress_notification("codex.completed", {
                "request_id": request_id,
                "session_id": state.session_id,
                "final_text": final_text,
            })

        return final_text

    async def _send_progress_notification(self, method_suffix: str, params: Dict[str, Any]) -> None:
        if not self._server:
            return
        method = f"notifications/{method_suffix}"
        await self._server.send_notification(method, params)


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
