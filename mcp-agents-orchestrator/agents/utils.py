"""
Utility functions for Pocket Flow agents
Shared utilities to avoid circular imports
Includes: LLM helper, sandbox-aware filesystem helpers
"""
from __future__ import annotations

from openai import OpenAI
import os
from pathlib import Path
from typing import Union


def call_llm(prompt: str, model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """Call OpenAI LLM; degrade gracefully if not configured.

    If OPENAI_API_KEY is missing or a request fails, returns a simple
    fallback string so upstream nodes can use their own fallback logic.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "LLM unavailable: missing OPENAI_API_KEY"
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception:
        return "LLM call failed"


# Sandbox-aware filesystem utilities

def get_sandbox_mode() -> str:
    """Return current sandbox mode: read-only | workspace-write | danger-full-access"""
    return os.getenv("AGENT_SANDBOX_MODE", "read-only")


def _writes_allowed() -> bool:
    mode = get_sandbox_mode().lower()
    return mode in ("workspace-write", "danger-full-access")


def _to_path(p: Union[str, Path]) -> Path:
    return p if isinstance(p, Path) else Path(p)


def _ensure_subpath(base: Path, target: Path) -> Path:
    base_r = base.resolve()
    target_r = target.resolve()
    # Ensure target is within base (prevents path escape)
    import os as _os
    if _os.path.commonpath([str(base_r), str(target_r)]) != str(base_r):
        raise PermissionError(f"Path escapes sandbox: {target_r} not under {base_r}")
    return target_r


def safe_mkdir(base: Union[str, Path], *segments: Union[str, Path], exist_ok: bool = True) -> Path:
    """Create a directory under base if writes are allowed and path is within base.

    Returns the absolute resolved Path to the created directory.
    """
    if not _writes_allowed():
        raise PermissionError("Sandbox is read-only; directory creation is blocked")
    base_p = _to_path(base)
    rel = Path()
    for s in segments:
        rel = rel / _to_path(s)
    dest = _ensure_subpath(base_p, base_p / rel)
    dest.mkdir(parents=True, exist_ok=exist_ok)
    return dest


def safe_write_text(base: Union[str, Path], rel_path: Union[str, Path], content: str) -> Path:
    """Write text to a file under base with sandbox checks.

    Ensures parent directories exist. Returns absolute resolved Path.
    """
    if not _writes_allowed():
        raise PermissionError("Sandbox is read-only; file write is blocked")
    base_p = _to_path(base)
    rel_p = _to_path(rel_path)
    dest = _ensure_subpath(base_p, base_p / rel_p)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


# Lightweight progress/plan emitters for in-process agents
def emit_progress(shared_or_token: Union[str, dict], message: str, level: str = "info", data: dict | None = None) -> None:
    """Emit a progress entry via orchestrator TaskStore and MCP notify.

    Accepts a shared dict from PocketFlow nodes or a task token (request_id).
    Safe if orchestrator helpers are unavailable.
    """
    try:
        if isinstance(shared_or_token, dict):
            req = shared_or_token.get("request") if "request" in shared_or_token else None
            token = getattr(req, "request_id", None) if req is not None else None
        else:
            token = str(shared_or_token)
        if not token:
            return
        # Import lazily to avoid circular dependencies on module import
        from mcp_agents_orchestrator.__main__ import TASKS, notify
        TASKS.append_progress(token, message, level=level, data=data)
        try:
            notify("notifications/progress", {"progress": 0.0, "progressToken": token, "message": message})
        except Exception:
            pass
    except Exception:
        # Best-effort; ignore if orchestrator not present
        pass


def emit_plan(shared_or_token: Union[str, dict], steps: list[dict], explanation: str | None = None) -> None:
    """Emit a plan_update notification with steps [{step, status}]."""
    try:
        if isinstance(shared_or_token, dict):
            req = shared_or_token.get("request") if "request" in shared_or_token else None
            token = getattr(req, "request_id", None) if req is not None else None
        else:
            token = str(shared_or_token)
        if not token:
            return
        from mcp_agents_orchestrator.__main__ import notify
        payload = {"plan": steps}
        if explanation:
            payload["explanation"] = explanation
        notify("plan_update", payload)
    except Exception:
        pass
