import json
import os
from pathlib import Path
from typing import Optional


CODEX_HOME_ENV = "CODEX_HOME"
AUTH_FILE_NAME = "auth.json"


def codex_home_dir() -> Path:
    home = os.getenv(CODEX_HOME_ENV)
    if home:
        return Path(home).expanduser()
    return Path.home() / ".codex"


def auth_file_path() -> Path:
    return codex_home_dir() / AUTH_FILE_NAME


def save_api_key(api_key: str) -> None:
    codex_home = codex_home_dir()
    codex_home.mkdir(parents=True, exist_ok=True)
    data = {"mode": "api_key", "api_key": api_key}
    (codex_home / AUTH_FILE_NAME).write_text(json.dumps(data), encoding="utf-8")


def load_api_key() -> Optional[str]:
    # prefer environment if present (OPENAI_API_KEY)
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    p = auth_file_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("mode") == "api_key":
            return data.get("api_key")
    except Exception:
        return None
    return None


def clear_auth() -> bool:
    p = auth_file_path()
    if p.exists():
        p.unlink()
        return True
    return False


def is_logged_in() -> bool:
    return load_api_key() is not None


def safe_format_key(key: str) -> str:
    if len(key) <= 13:
        return "***"
    return f"{key[:8]}***{key[-5:]}"

