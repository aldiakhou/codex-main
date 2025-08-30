"""
Data models for AI Development Workbench
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
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


class BackendConfig(BaseModel):
    """Backend/Codex configuration"""
    codex_path: Optional[str] = None
    profile: Optional[str] = None
    timeout: int = 300  # seconds
    max_retries: int = 3
    log_level: str = "info"


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
    def create_login_request(cls, operation_id: Optional[str] = None) -> 'Operation':
        """Create a login request operation"""
        if operation_id is None:
            operation_id = f"login_{int(datetime.now().timestamp())}"

        return cls(
            id=operation_id,
            op={"type": "login_chat_gpt"}
        )

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
    """Event received from backend"""
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
    def is_login_response(self) -> bool:
        return self.type in ["login_chat_gpt_response", "login_chat_gpt_complete"]

    @property
    def is_error(self) -> bool:
        return self.type == "error"
