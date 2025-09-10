import json
import os
import time
from typing import Any, Dict, Optional, Tuple


CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CODEX_HOME = os.path.join(os.path.expanduser("~"), ".codex")


class AuthError(Exception):
    pass


def _codex_home() -> str:
    return os.environ.get("CODEX_HOME", DEFAULT_CODEX_HOME)


def _auth_file() -> str:
    return os.path.join(_codex_home(), "auth.json")


def _read_auth_json(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    p = path or _auth_file()
    try:
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _extract_tokens(auth: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    # Returns (api_key, id_token, access_token, account_id)
    api_key = None
    id_token = None
    access_token = None
    account_id = None

    try:
        api_key = auth.get("OPENAI_API_KEY") or auth.get("openai_api_key")
    except Exception:
        api_key = None
    try:
        tokens = auth.get("tokens") or {}
        # Rust serializes id_token as a raw string; allow object with raw_jwt fallback too
        it = tokens.get("id_token")
        if isinstance(it, dict):
            id_token = it.get("raw_jwt")
        elif isinstance(it, str):
            id_token = it
        access_token = tokens.get("access_token")
        account_id = tokens.get("account_id")
    except Exception:
        pass
    return api_key, id_token, access_token, account_id


def _should_use_api_key(auth: Dict[str, Any]) -> bool:
    # Basic policy: prefer ChatGPT (access_token) when tokens exist.
    # Fall back to API key if no tokens, or AGENT_FORCE_API_KEY=1 is set.
    force_api = os.environ.get("AGENT_FORCE_API_KEY", "").strip() == "1"
    if force_api:
        return True
    _, id_token, access_token, _ = _extract_tokens(auth)
    if id_token and access_token:
        return False
    return True


def _maybe_refresh(auth: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal refresh: if we have refresh_token and AGENT_REFRESH_TOKENS=1, try refreshing
    try:
        if os.environ.get("AGENT_REFRESH_TOKENS", "").strip() != "1":
            return auth
        tokens = auth.get("tokens") or {}
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return auth
        import requests
        resp = requests.post(
            "https://auth.openai.com/oauth/token",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "openid profile email",
            },
            timeout=30,
        )
        if resp.ok:
            data = resp.json()
            tokens["id_token"] = data.get("id_token", tokens.get("id_token"))
            tokens["access_token"] = data.get("access_token", tokens.get("access_token"))
            tokens["refresh_token"] = data.get("refresh_token", tokens.get("refresh_token"))
            auth["tokens"] = tokens
            auth["last_refresh"] = _now_iso()
            # Best-effort writeback
            try:
                path = _auth_file()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(auth, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return auth
    except Exception:
        return auth


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get_provider_context() -> Dict[str, Any]:
    """
    Decide between API key and ChatGPT token based on ~/.codex/auth.json and env.
    Returns dict: { mode, base_url, authorization, account_id }
    """
    # Env override: prefer explicit OPENAI_API_KEY if set and not empty
    env_api_key = os.environ.get("OPENAI_API_KEY")
    auth = _read_auth_json() or {}
    auth = _maybe_refresh(auth)
    api_key, _id_token, access_token, account_id = _extract_tokens(auth)

    # If env key set, use api-key mode regardless
    if env_api_key and env_api_key.strip():
        return {
            "mode": "api_key",
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "authorization": f"Bearer {env_api_key.strip()}",
            "account_id": account_id,
        }

    # Policy: prefer ChatGPT when tokens exist and not forced to API key
    if not _should_use_api_key(auth) and access_token:
        return {
            "mode": "chatgpt",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "authorization": f"Bearer {access_token}",
            "account_id": account_id,
        }

    # Fall back to API key if present in auth.json
    if api_key and str(api_key).strip():
        return {
            "mode": "api_key",
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "authorization": f"Bearer {str(api_key).strip()}",
            "account_id": account_id,
        }

    raise AuthError("No usable Codex auth found. Log in via Codex CLI or set OPENAI_API_KEY.")

