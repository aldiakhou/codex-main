"""
Protocol stream runner: emits codex-protocol-style events to stdout as JSONL.

This provides a minimal parity layer with codex-rs `proto` mode by mapping
orchestrator events and chat deltas to codex-protocol event names.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional
from pathlib import Path

from ..core.config import Config
from ..core.orchestrator import CodexOrchestrator
from ..proto.events_adapter import EventsAdapter
from .models import (
    SessionConfiguredEvent,
    TaskStartedEvent,
    AgentMessageDeltaEvent,
    AgentMessageEvent,
    AgentReasoningDeltaEvent,
    AgentReasoningRawContentDeltaEvent,
    ToolCallBeginEvent,
    ToolCallEndEvent,
    ExecCommandBeginEvent,
    ExecCommandEndEvent,
    PatchApplyBeginEvent,
    PatchApplyEndEvent,
    TurnDiffEvent,
    FileChange,
    ApplyPatchApprovalRequestEvent,
    ExecApprovalRequestEvent,
    StreamErrorEvent,
    ErrorEvent,
    TaskCompleteEvent,
)


async def run_protocol_stream(prompt: str, config: Config, cwd: Optional[str] = None) -> None:
    """Run a single protocol stream turn, writing JSONL events to stdout.

    This is a minimal implementation that:
    - Emits SessionConfigured and TaskStarted events
    - Streams AgentMessageDelta and related reasoning deltas
    - Emits ToolCallBegin/End, Exec/Patch begin/end via the event bus mapping
    - Emits TaskComplete at the end
    """
    orch = CodexOrchestrator(config)
    await orch.initialize()

    try:
        import uuid as _uuid
        sid = str(_uuid.uuid4())
        workdir = cwd or str(Path.cwd())
        orch.create_session(sid, workdir)

        adapter = EventsAdapter(json_mode=True, event_id=str(_uuid.uuid4()), originator="cadenza_proto_py", session_id=sid, session_cwd=workdir)

        # helper: emit jsonl
        def emit(ev: BaseException | dict | object) -> None:
            if isinstance(ev, (SessionConfiguredEvent, TaskStartedEvent, AgentMessageDeltaEvent,
                               AgentMessageEvent, AgentReasoningDeltaEvent, AgentReasoningRawContentDeltaEvent,
                               ToolCallBeginEvent, ToolCallEndEvent, ExecCommandBeginEvent, ExecCommandEndEvent,
                               PatchApplyBeginEvent, PatchApplyEndEvent, TurnDiffEvent,
                               ApplyPatchApprovalRequestEvent, ExecApprovalRequestEvent,
                               StreamErrorEvent, ErrorEvent, TaskCompleteEvent)):
                print(ev.model_dump_json())
            elif isinstance(ev, dict):
                print(json.dumps(ev, ensure_ascii=False))
            else:
                try:
                    print(json.dumps(ev, ensure_ascii=False))
                except Exception:
                    print(json.dumps({"type": "ErrorEvent", "message": str(ev)}))

        async def consume_bus():
            async for ev in orch.events.subscribe(types=[
                "tool_start",
                "tool_end",
                "exec_begin",
                "exec_end",
                "patch_begin",
                "patch_end",
                "approval_request",
                "turn_diff",
                "exec_session_output",
            ]):
                et = ev.get("type")
                try:
                    if et == "tool_start":
                        emit(ToolCallBeginEvent(name=ev.get("name") or "tool", call_id=ev.get("call_id")))
                    elif et == "tool_end":
                        emit(ToolCallEndEvent(name=ev.get("name") or "tool", success=True))
                    elif et == "exec_begin":
                        emit(ExecCommandBeginEvent(call_id=ev.get("call_id"), command=ev.get("command") or [], cwd=ev.get("cwd"), session_id=ev.get("session_id")))
                    elif et == "exec_end":
                        emit(ExecCommandEndEvent(exit_code=ev.get("exit_code"), success=ev.get("success"), session_id=ev.get("session_id")))
                    elif et == "patch_begin":
                        emit(PatchApplyBeginEvent(call_id=ev.get("call_id")))
                    elif et == "patch_end":
                        emit(PatchApplyEndEvent(call_id=ev.get("call_id"), success=ev.get("success")))
                    elif et == "approval_request":
                        op = ev.get("operation")
                        rid = ev.get("id") or ev.get("request_id") or ""
                        if op == "patch_application":
                            emit(ApplyPatchApprovalRequestEvent(request_id=rid, description=ev.get("description"), session_id=ev.get("session_id"), timeout_s=ev.get("timeout_s")))
                        else:
                            emit(ExecApprovalRequestEvent(request_id=rid, description=ev.get("description"), session_id=ev.get("session_id"), timeout_s=ev.get("timeout_s")))
                    elif et == "turn_diff":
                        files = []
                        for f in ev.get("files", []) or []:
                            p = f.get("path") or ""
                            st = f.get("status") or "modified"
                            files.append(FileChange(path=p, status=st))
                        emit(TurnDiffEvent(files=files))
                except Exception as e:
                    emit(StreamErrorEvent(message=str(e)))

        # SessionConfigured + TaskStarted
        emit(SessionConfiguredEvent(session_id=sid, cwd=workdir))
        emit(TaskStartedEvent(session_id=sid, prompt=prompt))

        bus_task = asyncio.create_task(consume_bus())

        last_len = 0
        final_text: Optional[str] = None
        try:
            async for item in orch.chat([{"role": "user", "content": prompt}], session_id=sid, stream=True):
                if isinstance(item, dict) and item.get("type") == "delta":
                    content = item.get("content") or ""
                    new = content[last_len:]
                    last_len = len(content)
                    if new:
                        emit(AgentMessageDeltaEvent(content=new))
                    continue
                if isinstance(item, dict) and item.get("type") == "reasoning_raw_delta":
                    emit(AgentReasoningRawContentDeltaEvent(content=item.get("content") or ""))
                    continue
                if isinstance(item, dict) and item.get("type") == "reasoning_delta":
                    emit(AgentReasoningDeltaEvent(content=item.get("content") or ""))
                    continue
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    emit(ToolCallEndEvent(name=item.get("name") or "tool", success=True))
                    # also emit content as agent message
                    content = item.get("content") or ""
                    if content:
                        emit(AgentMessageDeltaEvent(content=content))
                    continue
                if isinstance(item, dict) and "content" in item and item.get("tool_calls") == []:
                    final_text = item.get("content")
                    if final_text:
                        emit(AgentMessageEvent(content=final_text))
                    break
        finally:
            bus_task.cancel()
            try:
                await bus_task
            except Exception:
                pass

        if final_text is None:
            final_text = ""
        emit(TaskCompleteEvent(final_text=final_text))
    finally:
        await orch.cleanup()


async def run_protocol_stdin(config: Config, cwd: Optional[str] = None) -> None:
    """Process protocol submissions from stdin (JSONL).

    Supported submissions (minimal):
    - {"type":"SubmitPrompt","prompt":"..."}
    - {"type":"Cancel"} (cancels the running turn if any)
    - {"type":"Exit"}
    """
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        import uuid as _uuid
        sid = str(_uuid.uuid4())
        workdir = cwd or str(Path.cwd())
        orch.create_session(sid, workdir)

        adapter = EventsAdapter(json_mode=True, event_id=str(_uuid.uuid4()), originator="cadenza_proto_py", session_id=sid, session_cwd=workdir)

        def emit(ev: object) -> None:
            if isinstance(ev, (SessionConfiguredEvent, TaskStartedEvent, AgentMessageDeltaEvent,
                               AgentMessageEvent, AgentReasoningDeltaEvent, AgentReasoningRawContentDeltaEvent,
                               ToolCallBeginEvent, ToolCallEndEvent, ExecCommandBeginEvent, ExecCommandEndEvent,
                               PatchApplyBeginEvent, PatchApplyEndEvent, TurnDiffEvent,
                               ApplyPatchApprovalRequestEvent, ExecApprovalRequestEvent,
                               StreamErrorEvent, ErrorEvent, TaskCompleteEvent)):
                print(ev.model_dump_json())
            else:
                try:
                    print(json.dumps(ev, ensure_ascii=False))
                except Exception:
                    print(json.dumps({"type": "ErrorEvent", "message": str(ev)}))

        emit(SessionConfiguredEvent(session_id=sid, cwd=workdir))

        running_task: Optional[asyncio.Task] = None

        async def consume_bus():
            async for ev in orch.events.subscribe(types=[
                "tool_start","tool_end","exec_begin","exec_end","patch_begin","patch_end","approval_request","turn_diff","exec_session_output"
            ]):
                et = ev.get("type")
                try:
                    if et == "tool_start":
                        emit(ToolCallBeginEvent(name=ev.get("name") or "tool", call_id=ev.get("call_id")))
                    elif et == "tool_end":
                        emit(ToolCallEndEvent(name=ev.get("name") or "tool", success=True))
                    elif et == "exec_begin":
                        emit(ExecCommandBeginEvent(call_id=ev.get("call_id"), command=ev.get("command") or [], cwd=ev.get("cwd"), session_id=ev.get("session_id")))
                    elif et == "exec_end":
                        emit(ExecCommandEndEvent(exit_code=ev.get("exit_code"), success=ev.get("success"), session_id=ev.get("session_id")))
                    elif et == "patch_begin":
                        emit(PatchApplyBeginEvent(call_id=ev.get("call_id")))
                    elif et == "patch_end":
                        emit(PatchApplyEndEvent(call_id=ev.get("call_id"), success=ev.get("success")))
                    elif et == "approval_request":
                        rid = ev.get("id") or ev.get("request_id") or ""
                        op = ev.get("operation")
                        if op == "patch_application":
                            emit(ApplyPatchApprovalRequestEvent(request_id=rid, description=ev.get("description"), session_id=ev.get("session_id"), timeout_s=ev.get("timeout_s")))
                        else:
                            emit(ExecApprovalRequestEvent(request_id=rid, description=ev.get("description"), session_id=ev.get("session_id"), timeout_s=ev.get("timeout_s")))
                    elif et == "turn_diff":
                        files = []
                        for f in ev.get("files", []) or []:
                            files.append(FileChange(path=f.get("path") or "", status=f.get("status") or "modified"))
                        emit(TurnDiffEvent(files=files))
                except Exception as e:
                    emit(StreamErrorEvent(message=str(e)))

        bus_task = asyncio.create_task(consume_bus())

        async def run_turn(prompt: str):
            nonlocal running_task
            # Cancel any existing task
            if running_task and not running_task.done():
                running_task.cancel()
            emit(TaskStartedEvent(session_id=sid, prompt=prompt))
            last_len = 0

            async def _stream():
                final: Optional[str] = None
                try:
                    async for item in orch.chat([{"role": "user", "content": prompt}], session_id=sid, stream=True):
                        if isinstance(item, dict) and item.get("type") == "delta":
                            content = item.get("content") or ""
                            new = content[last_len:]
                            nonlocal last_len
                            last_len = len(content)
                            if new:
                                emit(AgentMessageDeltaEvent(content=new))
                        elif isinstance(item, dict) and item.get("type") == "reasoning_raw_delta":
                            emit(AgentReasoningRawContentDeltaEvent(content=item.get("content") or ""))
                        elif isinstance(item, dict) and item.get("type") == "reasoning_delta":
                            emit(AgentReasoningDeltaEvent(content=item.get("content") or ""))
                        elif isinstance(item, dict) and item.get("type") == "tool_result":
                            emit(ToolCallEndEvent(name=item.get("name") or "tool", success=True))
                            content = item.get("content") or ""
                            if content:
                                emit(AgentMessageDeltaEvent(content=content))
                        elif isinstance(item, dict) and "content" in item and item.get("tool_calls") == []:
                            final = item.get("content")
                            if final:
                                emit(AgentMessageEvent(content=final))
                            break
                except Exception as e:
                    emit(StreamErrorEvent(message=str(e)))
                finally:
                    emit(TaskCompleteEvent(final_text=final or ""))

            running_task = asyncio.create_task(_stream())

        import sys
        for line in sys.stdin:
            line = (line or "").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                emit(ErrorEvent(message="Invalid JSON line"))
                continue
            t = (obj.get("type") or obj.get("op") or "").lower()
            if t in ("subm","submit","submitprompt") or obj.get("prompt"):
                prompt = obj.get("prompt") or ""
                if prompt:
                    await run_turn(prompt)
            elif t in ("cancel","stop"):
                if running_task and not running_task.done():
                    running_task.cancel()
                    running_task = None
            elif t in ("exit","quit"):
                break
            # else ignore unknown submissions

        if running_task:
            with contextlib.suppress(Exception):
                await running_task
        bus_task.cancel()
        with contextlib.suppress(Exception):
            await bus_task
    finally:
        await orch.cleanup()
