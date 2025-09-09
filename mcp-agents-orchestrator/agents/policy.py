"""
Simple per-task policy enforced by the MCP client helpers.

The orchestrator sets environment variables inside the task runner thread:
- AGENT_ALLOW_MCP_STDIO: semicolon-separated list of allowed commands (e.g. "npx;python"). "*" allows all.
- AGENT_ALLOW_HTTP_PREFIXES: semicolon-separated URL prefixes allowed for HTTP MCP.
- AGENT_SANDBOX_MODE: "read-only" | "workspace-write" | "danger-full-access" (advisory for tools).
"""
from __future__ import annotations

import os
from typing import Optional


def _split(v: Optional[str]) -> list[str]:
    if not v:
        return []
    return [s.strip() for s in v.split(";") if s.strip()]


def is_stdio_command_allowed(command: str) -> bool:
    allow = os.getenv("AGENT_ALLOW_MCP_STDIO", "*")
    if allow == "*":
        return True
    allowed = set(_split(allow))
    base = command.split("/")[-1].split("\\")[-1]
    return command in allowed or base in allowed


def is_http_url_allowed(url: str) -> bool:
    prefixes = _split(os.getenv("AGENT_ALLOW_HTTP_PREFIXES", ""))
    if not prefixes:
        # default: block unless explicitly allowed
        return False
    return any(url.startswith(p) for p in prefixes)

