"""
Data models for AI Development Workbench
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pathlib import Path


class Repository(BaseModel):
    """Represents a Git repository"""
    path: str
    name: str
    current_branch: str = "main"
    last_opened: Optional[datetime] = None

    @property
    def display_name(self) -> str:
        return f"{self.name} ({Path(self.path).name})"


class FileItem(BaseModel):
    """Represents a file in the repository"""
    path: str
    name: str
    is_directory: bool = False
    size: Optional[int] = None
    modified_time: Optional[datetime] = None
    git_status: Optional[str] = None  # "modified", "staged", "untracked", etc.


class BackendConfig(BaseModel):
    """Backend/Codex configuration"""
    codex_path: Optional[str] = None
    profile: Optional[str] = None
    timeout: int = 300  # seconds
    max_retries: int = 3
    log_level: str = "info"
    environment_variables: Dict[str, str] = Field(default_factory=dict)  # Custom env vars for codex process


class Operation(BaseModel):
    """JSON operation sent to backend"""
    id: str
    op: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

    @classmethod
    def create_user_input(cls, text: str, operation_id: Optional[str] = None) -> 'Operation':
        """Create a user input operation"""
        if operation_id is None:
            operation_id = f"user_input_{int(datetime.now().timestamp())}"

        return cls(
            id=operation_id,
            op={
                "type": "user_input",
                "items": [{"type": "text", "text": text}]
            }
        )

    @classmethod
    def create_user_turn(cls, text: str, cwd: str, operation_id: Optional[str] = None) -> 'Operation':
        """Create a user turn operation with working directory"""
        if operation_id is None:
            operation_id = f"user_turn_{int(datetime.now().timestamp())}"

        # Ensure path uses forward slashes for JSON compatibility
        normalized_cwd = cwd.replace("\\", "/")

        return cls(
            id=operation_id,
            op={
                "type": "user_turn",
                "items": [{"type": "text", "text": text}],
                "cwd": normalized_cwd,
                "approval_policy": "on-request",  # kebab-case for AskForApproval enum
                "sandbox_policy": {"mode": "read-only"},  # correct structure for SandboxPolicy
                "model": "gpt-5",  # use gpt-5 as shown in session
                "effort": "medium",  # lowercase for ReasoningEffort enum
                "summary": "auto"  # valid value for ReasoningSummary enum
            }
        )

    @classmethod
    def create_user_turn_ex(
        cls,
        text: str,
        cwd: str,
        approval_policy: str = "on-request",
        sandbox_mode: str = "read-only",
        model: str = "gpt-5",
        effort: str = "medium",
        summary: str = "auto",
        operation_id: Optional[str] = None,
    ) -> 'Operation':
        """Create a user turn operation with explicit policy/model knobs."""
        if operation_id is None:
            operation_id = f"user_turn_{int(datetime.now().timestamp())}"

        normalized_cwd = cwd.replace("\\", "/")

        return cls(
            id=operation_id,
            op={
                "type": "user_turn",
                "items": [{"type": "text", "text": text}],
                "cwd": normalized_cwd,
                "approval_policy": approval_policy,
                "sandbox_policy": {"mode": sandbox_mode},
                "model": model,
                "effort": effort,
                "summary": summary,
            },
        )

    @classmethod
    def create_override_turn_context(cls, cwd: str, operation_id: Optional[str] = None) -> 'Operation':
        """Create an operation to override the working directory for future turns"""
        if operation_id is None:
            operation_id = f"override_context_{int(datetime.now().timestamp())}"

        # Ensure path uses forward slashes for JSON compatibility
        normalized_cwd = cwd.replace("\\", "/")

        return cls(
            id=operation_id,
            op={
                "type": "override_turn_context",
                "cwd": normalized_cwd
            }
        )

    @classmethod
    # NOTE: Login is handled out-of-band via `codex login` and is not a proto operation.
    # See aiw.core.backend_service.BackendService.login_with_chatgpt()
    # and aiw.core.auth for helpers.

    @classmethod
    def create_interrupt(cls, operation_id: Optional[str] = None) -> 'Operation':
        """Create an interrupt operation to abort the current turn"""
        if operation_id is None:
            operation_id = f"interrupt_{int(datetime.now().timestamp())}"
        return cls(id=operation_id, op={"type": "interrupt"})

    @classmethod
    def create_exec_approval(cls, target_submission_id: str, decision: str, operation_id: Optional[str] = None) -> 'Operation':
        """Approve/deny an exec request. decision in {approved, approved_for_session, denied, abort}."""
        if operation_id is None:
            operation_id = f"exec_approval_{int(datetime.now().timestamp())}"
        return cls(
            id=operation_id,
            op={
                "type": "exec_approval",
                "id": target_submission_id,
                "decision": decision,
            },
        )

    @classmethod
    def create_patch_approval(cls, target_submission_id: str, decision: str, operation_id: Optional[str] = None) -> 'Operation':
        """Approve/deny a patch request. decision in {approved, approved_for_session, denied, abort}."""
        if operation_id is None:
            operation_id = f"patch_approval_{int(datetime.now().timestamp())}"
        return cls(
            id=operation_id,
            op={
                "type": "patch_approval",
                "id": target_submission_id,
                "decision": decision,
            },
        )

    @classmethod
    def create_get_history(cls, operation_id: Optional[str] = None) -> 'Operation':
        if operation_id is None:
            operation_id = f"get_history_{int(datetime.now().timestamp())}"
        return cls(id=operation_id, op={"type": "get_history"})

    @classmethod
    def create_list_mcp_tools(cls, operation_id: Optional[str] = None) -> 'Operation':
        if operation_id is None:
            operation_id = f"list_mcp_tools_{int(datetime.now().timestamp())}"
        return cls(id=operation_id, op={"type": "list_mcp_tools"})

    @classmethod
    def create_file_operation(cls, operation_type: str, file_path: str,
                            content: Optional[str] = None,
                            operation_id: Optional[str] = None) -> 'Operation':
        """Create a file-related operation"""
        if operation_id is None:
            operation_id = f"file_op_{int(datetime.now().timestamp())}"

        op_data = {
            "type": operation_type,
            "file_path": file_path
        }

        if content is not None:
            op_data["content"] = content

        return cls(id=operation_id, op=op_data)

    @classmethod
    def create_edit_file_operation(cls, file_path: str, instruction: str,
                                 operation_id: Optional[str] = None) -> 'Operation':
        """Create an edit file operation"""
        if operation_id is None:
            operation_id = f"edit_file_{int(datetime.now().timestamp())}"

        return cls(
            id=operation_id,
            op={
                "type": "edit_file",
                "file_path": file_path,
                "instruction": instruction
            }
        )


class Event(BaseModel):
    """Event received from backend (shape mirrors codex protocol Event.msg)."""
    type: str
    msg: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def is_agent_message(self) -> bool:
        return self.type == "agent_message"

    @property
    def is_agent_reasoning(self) -> bool:
        return self.type == "agent_reasoning"

    @property
    def is_error(self) -> bool:
        return self.type == "error"


## Removed duplicate Repository and FileItem definitions below


class Task(BaseModel):
    """Represents a task/workflow step"""
    id: str
    name: str
    type: str  # "edit_file", "run_tests", "apply_patch", etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # "pending", "running", "completed", "failed"
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class Workflow(BaseModel):
    """Represents a multi-step workflow"""
    id: str
    name: str
    description: Optional[str] = None
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None


class Run(BaseModel):
    """Represents a workflow execution"""
    id: str
    workflow_id: str
    repository_path: str
    status: str = "pending"  # "pending", "running", "completed", "failed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks: List[Task] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class Artifact(BaseModel):
    """Represents generated artifacts (diffs, logs, reports)"""
    id: str
    run_id: str
    type: str  # "diff", "log", "report", "file"
    name: str
    path: Optional[str] = None  # File path if stored on disk
    content: Optional[str] = None  # Content if stored in memory
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class Config(BaseModel):
    """Application configuration"""
    version: str = "1.0.0"
    ui: UIConfig = Field(default_factory=lambda: UIConfig())
    backend: BackendConfig = Field(default_factory=lambda: BackendConfig())
    repositories: List[Repository] = Field(default_factory=list)
    recent_workflows: List[str] = Field(default_factory=list)
    window_geometry: Optional[Dict[str, Any]] = None


class UIConfig(BaseModel):
    """UI-specific configuration"""
    theme: str = "system"  # "light", "dark", "system"
    font_size: int = 10
    show_line_numbers: bool = True
    word_wrap: bool = True
    auto_save: bool = True
    dock_positions: Dict[str, Any] = Field(default_factory=dict)
    layout_state: Optional[Dict[str, Any]] = None  # custom pane/dock layout persistence
    recent_files: List[str] = Field(default_factory=list)  # Recent file paths
    animations_enabled: bool = True  # Optional motion layer
    prefers_reduced_motion: bool = False  # Global reduce motion toggle
    custom_qss_path: Optional[str] = None  # External QSS override (dev)


## Removed duplicate BackendConfig definition below
