"""
CodexConfigManager: load/save ~/.codex/config.toml and bridge to UI models.

Reading uses stdlib tomllib. Writing uses a minimal TOML serializer that
covers the value types used by Codex config (scalars, arrays, tables, and
tables-of-tables like model_providers and mcp_servers).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import os
import sys

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore

from .codex_settings import (
    CodexConfig,
    ModelProvider,
    McpServer,
    ShellEnvironmentPolicy,
    SandboxWorkspaceWrite,
    History,
    Profiles,
    default_codex_config,
)


class CodexConfigManager:
    def __init__(self, codex_home: Optional[Path] = None) -> None:
        self.codex_home = codex_home or self._resolve_codex_home()
        self.config_path = self.codex_home / "config.toml"

    def _resolve_codex_home(self) -> Path:
        raw = os.environ.get("CODEX_HOME")
        if raw:
            return Path(raw).expanduser()
        return Path.home() / ".codex"

    def load(self) -> CodexConfig:
        if tomllib is None:
            # Fallback to empty default if tomllib unavailable
            return default_codex_config()
        if not self.config_path.exists():
            return default_codex_config()
        try:
            data = self._read_toml(self.config_path)
        except Exception:
            # On parse error, prefer a safe default rather than raising in UI
            return default_codex_config()

        return self._from_dict(data)

    def save(self, cfg: CodexConfig) -> None:
        # Ensure directory exists
        self.codex_home.mkdir(parents=True, exist_ok=True)
        text = self._to_toml_text(cfg)
        self.config_path.write_text(text, encoding="utf-8")

    # --- Helpers: parse/serialize ---

    def _read_toml(self, path: Path) -> Dict[str, Any]:
        with path.open("rb") as f:
            return tomllib.load(f)  # type: ignore[arg-type]

    def _from_dict(self, raw: Dict[str, Any]) -> CodexConfig:
        # Map nested tables into pydantic models
        mp: Dict[str, ModelProvider] = {}
        for k, v in raw.get("model_providers", {}).items():
            mp[k] = ModelProvider(**v)

        mcp: Dict[str, McpServer] = {}
        for k, v in raw.get("mcp_servers", {}).items():
            # tolerate missing keys
            if "command" in v and isinstance(v["command"], str):
                mcp[k] = McpServer(
                    command=v["command"],
                    args=list(v.get("args", []) or []),
                    env=dict(v.get("env", {}) or {}),
                )

        swe = None
        if "sandbox_workspace_write" in raw:
            swe = SandboxWorkspaceWrite(**(raw.get("sandbox_workspace_write") or {}))

        sep = None
        if "shell_environment_policy" in raw:
            sep = ShellEnvironmentPolicy(**(raw.get("shell_environment_policy") or {}))

        hist = None
        if "history" in raw:
            hist = History(**(raw.get("history") or {}))

        profiles = None
        if "profiles" in raw and isinstance(raw["profiles"], dict):
            profiles = Profiles(root=raw["profiles"])  # type: ignore[arg-type]

        # Build codex config
        cfg = CodexConfig(
            model=raw.get("model"),
            model_provider=raw.get("model_provider"),
            model_context_window=raw.get("model_context_window"),
            model_max_output_tokens=raw.get("model_max_output_tokens"),
            model_verbosity=raw.get("model_verbosity"),
            approval_policy=raw.get("approval_policy"),
            sandbox_mode=raw.get("sandbox_mode"),
            sandbox_workspace_write=swe,
            tools=dict(raw.get("tools", {})),
            disable_response_storage=raw.get("disable_response_storage"),
            hide_agent_reasoning=raw.get("hide_agent_reasoning"),
            show_raw_agent_reasoning=raw.get("show_raw_agent_reasoning"),
            model_reasoning_effort=raw.get("model_reasoning_effort"),
            model_reasoning_summary=raw.get("model_reasoning_summary"),
            file_opener=raw.get("file_opener"),
            project_doc_max_bytes=raw.get("project_doc_max_bytes"),
            preferred_auth_method=raw.get("preferred_auth_method"),
            chatgpt_base_url=raw.get("chatgpt_base_url"),
            notify=list(raw.get("notify", []) or []) if raw.get("notify") is not None else None,
            history=hist,
            model_providers=mp,
            mcp_servers=mcp,
            shell_environment_policy=sep,
            profile=raw.get("profile"),
            profiles=profiles,
            experimental_resume=raw.get("experimental_resume"),
            experimental_instructions_file=raw.get("experimental_instructions_file"),
            experimental_use_exec_command_tool=raw.get("experimental_use_exec_command_tool"),
            responses_originator_header_internal_override=raw.get(
                "responses_originator_header_internal_override"
            ),
            projects=dict(raw.get("projects", {})),
        )
        return cfg

    # --- TOML writing ---

    def _to_toml_text(self, cfg: CodexConfig) -> str:
        lines: List[str] = []

        def w(line: str = "") -> None:
            lines.append(line)

        def q(s: str) -> str:
            s = s.replace("\\", "\\\\").replace("\"", "\\\"")
            return f'"{s}"'

        def render_value(v: Any) -> str:
            if isinstance(v, bool):
                return "true" if v else "false"
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, str):
                return q(v)
            if isinstance(v, list):
                return "[" + ", ".join(render_value(x) for x in v) + "]"
            if isinstance(v, dict):
                # Inline table
                items = ", ".join(f"{q(k)} = {render_value(val)}" for k, val in v.items())
                return "{ " + items + " }"
            return q(str(v))

        def write_kv(key: str, value: Any) -> None:
            if value is None:
                return
            w(f"{key} = {render_value(value)}")

        # Top-level scalars
        write_kv("model", cfg.model)
        write_kv("model_provider", cfg.model_provider)
        write_kv("model_context_window", cfg.model_context_window)
        write_kv("model_max_output_tokens", cfg.model_max_output_tokens)
        write_kv("model_verbosity", cfg.model_verbosity)
        write_kv("approval_policy", cfg.approval_policy)
        write_kv("sandbox_mode", cfg.sandbox_mode)
        write_kv("disable_response_storage", cfg.disable_response_storage)
        write_kv("hide_agent_reasoning", cfg.hide_agent_reasoning)
        write_kv("show_raw_agent_reasoning", cfg.show_raw_agent_reasoning)
        write_kv("model_reasoning_effort", cfg.model_reasoning_effort)
        write_kv("model_reasoning_summary", cfg.model_reasoning_summary)
        write_kv("file_opener", cfg.file_opener)
        write_kv("project_doc_max_bytes", cfg.project_doc_max_bytes)
        write_kv("preferred_auth_method", cfg.preferred_auth_method)
        write_kv("chatgpt_base_url", cfg.chatgpt_base_url)
        write_kv("profile", cfg.profile)

        # Tools table (only if non-empty or explicitly provided)
        if cfg.tools:
            w("\n[tools]")
            for k, v in cfg.tools.items():
                write_kv(k, v)

        # sandbox_workspace_write
        if cfg.sandbox_workspace_write is not None:
            swe = cfg.sandbox_workspace_write
            w("\n[sandbox_workspace_write]")
            write_kv("writable_roots", swe.writable_roots)
            write_kv("network_access", swe.network_access)
            write_kv("exclude_tmpdir_env_var", swe.exclude_tmpdir_env_var)
            write_kv("exclude_slash_tmp", swe.exclude_slash_tmp)

        # shell_environment_policy
        if cfg.shell_environment_policy is not None:
            sep = cfg.shell_environment_policy
            w("\n[shell_environment_policy]")
            write_kv("inherit", sep.inherit)
            write_kv("ignore_default_excludes", sep.ignore_default_excludes)
            write_kv("exclude", sep.exclude)
            if sep.set:
                write_kv("set", sep.set)
            if sep.include_only:
                write_kv("include_only", sep.include_only)

        # history
        if cfg.history is not None:
            w("\n[history]")
            write_kv("persistence", cfg.history.persistence)
            if cfg.history.max_bytes is not None:
                write_kv("max_bytes", cfg.history.max_bytes)

        # notify (argv array)
        if cfg.notify is not None:
            write_kv("notify", cfg.notify)

        # model_providers
        if cfg.model_providers:
            for pid, prov in cfg.model_providers.items():
                w(f"\n[model_providers.{pid}]")
                if prov.name is not None:
                    write_kv("name", prov.name)
                if prov.base_url is not None:
                    write_kv("base_url", prov.base_url)
                if prov.env_key is not None:
                    write_kv("env_key", prov.env_key)
                if prov.wire_api is not None:
                    write_kv("wire_api", prov.wire_api)
                if prov.query_params:
                    write_kv("query_params", prov.query_params)
                if prov.http_headers:
                    write_kv("http_headers", prov.http_headers)
                if prov.env_http_headers:
                    write_kv("env_http_headers", prov.env_http_headers)
                if prov.request_max_retries is not None:
                    write_kv("request_max_retries", prov.request_max_retries)
                if prov.stream_max_retries is not None:
                    write_kv("stream_max_retries", prov.stream_max_retries)
                if prov.stream_idle_timeout_ms is not None:
                    write_kv("stream_idle_timeout_ms", prov.stream_idle_timeout_ms)

        # mcp_servers
        if cfg.mcp_servers:
            for sid, server in cfg.mcp_servers.items():
                w(f"\n[mcp_servers.{sid}]")
                write_kv("command", server.command)
                if server.args:
                    write_kv("args", server.args)
                if server.env:
                    write_kv("env", server.env)

        # profiles
        if cfg.profiles is not None and getattr(cfg.profiles, "root", {}):
            for name, table in cfg.profiles.root.items():
                w(f"\n[profiles.{name}]")
                for k, v in table.items():
                    write_kv(k, v)

        # projects trust map
        if cfg.projects:
            for proj_path, table in cfg.projects.items():
                key = proj_path.replace("\"", '\\"')
                w(f"\n[projects.{q(key)}]")
                for k, v in table.items():
                    write_kv(k, v)

        # advanced
        if cfg.experimental_resume is not None:
            write_kv("experimental_resume", cfg.experimental_resume)
        if cfg.experimental_instructions_file is not None:
            write_kv("experimental_instructions_file", cfg.experimental_instructions_file)
        if cfg.experimental_use_exec_command_tool is not None:
            write_kv("experimental_use_exec_command_tool", cfg.experimental_use_exec_command_tool)
        if cfg.responses_originator_header_internal_override is not None:
            write_kv(
                "responses_originator_header_internal_override",
                cfg.responses_originator_header_internal_override,
            )

        return "\n".join(lines) + ("\n" if lines else "")


# Convenience singleton (mirrors existing app config manager style)
_codex_cfg_manager: Optional[CodexConfigManager] = None


def get_codex_config_manager() -> CodexConfigManager:
    global _codex_cfg_manager
    if _codex_cfg_manager is None:
        _codex_cfg_manager = CodexConfigManager()
    return _codex_cfg_manager
