from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    type: str
    id: Optional[str] = None
    ts: Optional[float] = None
    originator: Optional[str] = None


class SessionConfiguredEvent(BaseEvent):
    type: Literal["SessionConfiguredEvent"] = "SessionConfiguredEvent"
    session_id: str
    cwd: str


class TaskStartedEvent(BaseEvent):
    type: Literal["TaskStartedEvent"] = "TaskStartedEvent"
    session_id: str
    prompt: str


class AgentMessageDeltaEvent(BaseEvent):
    type: Literal["AgentMessageDeltaEvent"] = "AgentMessageDeltaEvent"
    content: str


class AgentMessageEvent(BaseEvent):
    type: Literal["AgentMessageEvent"] = "AgentMessageEvent"
    content: str


class AgentReasoningDeltaEvent(BaseEvent):
    type: Literal["AgentReasoningDeltaEvent"] = "AgentReasoningDeltaEvent"
    content: str


class AgentReasoningRawContentDeltaEvent(BaseEvent):
    type: Literal["AgentReasoningRawContentDeltaEvent"] = "AgentReasoningRawContentDeltaEvent"
    content: str


class ToolCallBeginEvent(BaseEvent):
    type: Literal["ToolCallBeginEvent"] = "ToolCallBeginEvent"
    name: str
    call_id: Optional[str] = None


class ToolCallEndEvent(BaseEvent):
    type: Literal["ToolCallEndEvent"] = "ToolCallEndEvent"
    name: str
    success: Optional[bool] = None


class ExecCommandBeginEvent(BaseEvent):
    type: Literal["ExecCommandBeginEvent"] = "ExecCommandBeginEvent"
    call_id: Optional[str] = None
    command: List[str]
    cwd: Optional[str] = None
    session_id: Optional[str] = None


class ExecCommandEndEvent(BaseEvent):
    type: Literal["ExecCommandEndEvent"] = "ExecCommandEndEvent"
    exit_code: Optional[int] = None
    success: Optional[bool] = None
    session_id: Optional[str] = None


class PatchApplyBeginEvent(BaseEvent):
    type: Literal["PatchApplyBeginEvent"] = "PatchApplyBeginEvent"
    call_id: Optional[str] = None


class PatchApplyEndEvent(BaseEvent):
    type: Literal["PatchApplyEndEvent"] = "PatchApplyEndEvent"
    call_id: Optional[str] = None
    success: Optional[bool] = None


class FileChange(BaseModel):
    path: str
    status: Literal["added", "modified", "deleted", "renamed"]
    # Optional metadata can be extended later


class TurnDiffEvent(BaseEvent):
    type: Literal["TurnDiffEvent"] = "TurnDiffEvent"
    files: List[FileChange]


class ApplyPatchApprovalRequestEvent(BaseEvent):
    type: Literal["ApplyPatchApprovalRequestEvent"] = "ApplyPatchApprovalRequestEvent"
    request_id: str
    description: Optional[str] = None
    session_id: Optional[str] = None
    timeout_s: Optional[float] = None


class ExecApprovalRequestEvent(BaseEvent):
    type: Literal["ExecApprovalRequestEvent"] = "ExecApprovalRequestEvent"
    request_id: str
    description: Optional[str] = None
    session_id: Optional[str] = None
    timeout_s: Optional[float] = None


class StreamErrorEvent(BaseEvent):
    type: Literal["StreamErrorEvent"] = "StreamErrorEvent"
    code: Optional[str] = None
    message: str


class ErrorEvent(BaseEvent):
    type: Literal["ErrorEvent"] = "ErrorEvent"
    message: str


class TaskCompleteEvent(BaseEvent):
    type: Literal["TaskCompleteEvent"] = "TaskCompleteEvent"
    final_text: str

