"""Conversation store for persisting chat sessions.
Phase 1: simple JSON rewrite per message (small scale)."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from threading import Lock

logger = logging.getLogger("ConversationStore")

@dataclass
class StoredMessage:
    role: str
    content: str
    timestamp: str
    rich: bool = False

@dataclass
class SessionData:
    session_id: str
    created: str
    messages: List[StoredMessage]

class ConversationStore:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.sessions_dir = self.base_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.pointer_file = self.sessions_dir / "last_session"
        self.session: Optional[SessionData] = None
        self._dirty = False
        self._lock = Lock()

    # --- Session Lifecycle -------------------------------------------------
    def start_new_session(self) -> SessionData:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = SessionData(session_id=session_id, created=datetime.utcnow().isoformat(), messages=[])
        self._write_pointer()
        self._persist()
        logger.info(f"Started new session {session_id}")
        return self.session

    def load_last_session(self) -> Optional[SessionData]:
        if not self.pointer_file.exists():
            return None
        try:
            sid = self.pointer_file.read_text(encoding="utf-8").strip()
            if not sid:
                return None
            path = self.sessions_dir / sid / "chat.json"
            if not path.exists():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            msgs = [StoredMessage(**m) for m in data.get("messages", [])]
            self.session = SessionData(session_id=data.get("session_id", sid), created=data.get("created", ""), messages=msgs)
            logger.info(f"Loaded session {self.session.session_id} with {len(msgs)} messages")
            return self.session
        except Exception as e:
            logger.warning(f"Failed to load last session: {e}")
            return None

    def set_messages(self, messages: List[Dict[str, Any]]):
        if not self.session:
            self.start_new_session()
        self.session.messages = [StoredMessage(
            role=m.get("role", "assistant"),
            content=m.get("content", ""),
            timestamp=m.get("timestamp") or datetime.utcnow().strftime("%H:%M:%S"),
            rich=bool(m.get("rich", False))
        ) for m in messages if m.get("content")]
        self._dirty = True
        self._persist()  # full replace (force)

    # --- Message Ops -------------------------------------------------------
    def add_message(self, role: str, content: str, rich: bool = False, timestamp: Optional[str] = None):
        if not self.session:
            self.start_new_session()
        ts = timestamp or datetime.utcnow().strftime("%H:%M:%S")
        self.session.messages.append(StoredMessage(role=role, content=content, timestamp=ts, rich=rich))
        self._dirty = True
        # Defer actual write; external debouncer (MainWindow) will call flush()

    def get_messages(self) -> List[StoredMessage]:
        return list(self.session.messages) if self.session else []

    def update_last_assistant_partial(self, delta: str):
        if not self.session or not delta:
            return
        for m in reversed(self.session.messages):
            if m.role == 'assistant':
                m.content += delta
                self._dirty = True
                return
        # If none found, create a placeholder assistant message
        self.add_message('assistant', delta)

    # --- Persistence -------------------------------------------------------
    def flush(self):
        if not self._dirty:
            return
        with self._lock:
            self._persist()
            self._dirty = False

    def _persist(self):
        if not self.session:
            return
        try:
            session_dir = self.sessions_dir / self.session.session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "session_id": self.session.session_id,
                "created": self.session.created,
                "messages": [asdict(m) for m in self.session.messages]
            }
            (session_dir / "chat.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Persist failed: {e}")

    def _write_pointer(self):
        try:
            self.pointer_file.write_text(self.session.session_id, encoding="utf-8")  # type: ignore[arg-type]
        except Exception as e:
            logger.warning(f"Failed writing pointer: {e}")

__all__ = ["ConversationStore", "StoredMessage", "SessionData"]
