"""
Codex CLI/TOML settings models for the Workbench Settings UI.

These models mirror the keys documented in codex-main/docs/config.md.
They are intentionally permissive (string enums) to avoid tight coupling
with the Rust side while providing structure for the UI and validation.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, RootModel, field_validator


# --- Enums as str-literals for UI friendliness ---

ApprovalPolicy = Literal["untrusted", "on-failure", "on-request", "never"]
SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
FileOpener = Literal["vscode", "vscode-insiders", "windsurf", "cursor", "none"]
AuthMethod = Literal["chatgpt", "apikey"]
HistoryPersistence = Literal["save-all", "none"]
ReasoningEffort = Literal["minimal", "low", "medium", "high"]
ReasoningSummary = Literal["auto", "concise", "detailed", "none"]
Verbosity = Literal["low", "medium", "high"]
WireApi = Literal["chat", "responses"]


class SandboxWorkspaceWrite(BaseModel):
    writable_roots: List[str] = Field(default_factory=list)
    network_access: bool = False
    exclude_tmpdir_env_var: bool = False
    exclude_slash_tmp: bool = False


class ShellEnvironmentPolicy(BaseModel):
    inherit: Literal["all", "core", "none"] = "all"
    ignore_default_excludes: bool = False
    exclude: List[str] = Field(default_factory=list)
    set: Dict[str, str] = Field(default_factory=dict)
    include_only: List[str] = Field(default_factory=list)


class History(BaseModel):
    persistence: HistoryPersistence = "save-all"
    # max_bytes is currently ignored by CLI but we keep it for parity
    max_bytes: Optional[int] = None


class ModelProvider(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    env_key: Optional[str] = None
    wire_api: Optional[WireApi] = None
    query_params: Dict[str, str] = Field(default_factory=dict)
    http_headers: Dict[str, str] = Field(default_factory=dict)
    env_http_headers: Dict[str, str] = Field(default_factory=dict)
    request_max_retries: Optional[int] = None
    stream_max_retries: Optional[int] = None
    stream_idle_timeout_ms: Optional[int] = None


class McpServer(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class Profiles(RootModel[Dict[str, Dict[str, Any]]]):
    # Profiles are arbitrary named tables that mirror top-level keys.
    # RootModel is required for pydantic v2 root models.
    root: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def get(self, name: str) -> Dict[str, Any]:
        return self.root.get(name, {})

    def set(self, name: str, value: Dict[str, Any]) -> None:
        self.root[name] = value

    def delete(self, name: str) -> None:
        if name in self.root:
            del self.root[name]

    def names(self) -> List[str]:
        return sorted(self.root.keys())


class CodexConfig(BaseModel):
    # General
    model: Optional[str] = None
    model_provider: Optional[str] = None
    model_context_window: Optional[int] = None
    model_max_output_tokens: Optional[int] = None
    model_verbosity: Optional[Verbosity] = None

    # Safety
    approval_policy: Optional[ApprovalPolicy] = None
    sandbox_mode: Optional[SandboxMode] = None
    sandbox_workspace_write: Optional[SandboxWorkspaceWrite] = None

    # Features
    tools: Dict[str, Any] = Field(default_factory=dict)  # e.g. {"web_search": true}
    disable_response_storage: Optional[bool] = None
    hide_agent_reasoning: Optional[bool] = None
    show_raw_agent_reasoning: Optional[bool] = None
    model_reasoning_effort: Optional[ReasoningEffort] = None
    model_reasoning_summary: Optional[ReasoningSummary] = None

    # File opener and docs
    file_opener: Optional[FileOpener] = None
    project_doc_max_bytes: Optional[int] = None

    # Auth + provider tuning
    preferred_auth_method: Optional[AuthMethod] = None
    chatgpt_base_url: Optional[str] = None

    # Notifications & history
    notify: Optional[List[str]] = None
    history: Optional[History] = None

    # Providers and MCP
    model_providers: Dict[str, ModelProvider] = Field(default_factory=dict)
    mcp_servers: Dict[str, McpServer] = Field(default_factory=dict)

    # Shell env
    shell_environment_policy: Optional[ShellEnvironmentPolicy] = None

    # Profiles & profile selection
    profile: Optional[str] = None
    profiles: Optional[Profiles] = None

    # Advanced / experimental
    experimental_resume: Optional[str] = None
    experimental_instructions_file: Optional[str] = None
    experimental_use_exec_command_tool: Optional[bool] = None
    responses_originator_header_internal_override: Optional[str] = None

    # Projects trust map (stringly-typed)
    projects: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    @field_validator("model_context_window", "model_max_output_tokens", "project_doc_max_bytes")
    def _non_negative(cls, v):  # type: ignore[override]
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v


def default_codex_config() -> CodexConfig:
    return CodexConfig(
        model=None,
        model_provider=None,
        approval_policy="on-request",
        sandbox_mode="read-only",
        tools={},
        history=History(),
        model_providers={},
        mcp_servers={},
    )
