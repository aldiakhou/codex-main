import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _history_path(default: Optional[str] = None) -> Path:
    if default:
        return Path(default)
    base = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "history.jsonl"


def append_event(event: Dict[str, Any], path: Optional[str] = None) -> None:
    p = _history_path(path)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def tail(n: int = 100, path: Optional[str] = None) -> Iterable[Dict[str, Any]]:
    p = _history_path(path)
    if not p.exists():
        return []
    lines: list[str] = []
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            lines.append(line.rstrip("\n"))
            if len(lines) > n:
                lines.pop(0)
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

