import json
import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog

# Support direct run and package run
try:
    from ..core.backend_service import BackendService  # type: ignore
    from ..core.models import Operation  # type: ignore
    from ..core.config import get_config_manager  # type: ignore
except Exception:
    # Running as a script: add the ai-workbench directory to sys.path
    pkg_root = Path(__file__).resolve().parents[2]  # .../ai-workbench
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from aiw.core.backend_service import BackendService  # type: ignore
    from aiw.core.models import Operation  # type: ignore
    from aiw.core.config import get_config_manager  # type: ignore


class WebBridge(QObject):
    """Bridge exposed to JS via QWebChannel."""
    status_changed = Signal(str)
    event_received = Signal(dict)
    log_message = Signal(str)
    operation_progress = Signal(str, int, str)

    def __init__(self, backend: BackendService):
        super().__init__()
        self.backend = backend
        self.backend.new_event.connect(self._on_backend_event)
        self.backend.connection_status_changed.connect(self.status_changed.emit)
        self.backend.backend_error.connect(self._on_backend_error)
        self.backend.operation_progress.connect(self.operation_progress.emit)

    # Lifecycle
    @Slot()
    def start_backend(self):
        self.log_message.emit("Starting backend...")
        self.backend.start()

    @Slot()
    def stop_backend(self):
        self.log_message.emit("Stopping backend...")
        self.backend.stop()

    @Slot(str)
    def login(self, api_key: str = ""):
        self.log_message.emit("Initiating login...")
        self.backend.login_with_chatgpt(api_key or None)

    # Conversation ops
    @Slot(str)
    def send_user_turn_json(self, payload: str):
        try:
            data = json.loads(payload)
            text = data.get("text", "")
            cwd = data.get("cwd") or os.getcwd()
            approval = data.get("approval_policy", "on-request")
            sandbox_mode = data.get("sandbox_mode", "read-only")
            model = data.get("model", "gpt-5")
            effort = data.get("effort", "medium")
            summary = data.get("summary", "auto")
            op = Operation.create_user_turn_ex(
                text=text,
                cwd=cwd,
                approval_policy=approval,
                sandbox_mode=sandbox_mode,
                model=model,
                effort=effort,
                summary=summary,
            )
            if not self.backend.send_op(op.model_dump()):
                self.log_message.emit("Failed to send user_turn")
        except Exception as e:
            self.log_message.emit(f"send_user_turn_json error: {e}")

    @Slot()
    def interrupt(self):
        op = Operation.create_interrupt()
        self.backend.send_op(op.model_dump())

    @Slot(str, str)
    def exec_approval(self, target_event_id: str, decision: str):
        op = Operation.create_exec_approval(target_event_id, decision)
        self.backend.send_op(op.model_dump())

    @Slot(str, str)
    def patch_approval(self, target_event_id: str, decision: str):
        op = Operation.create_patch_approval(target_event_id, decision)
        self.backend.send_op(op.model_dump())

    # Utility
    @Slot(str, result=str)
    def list_dir(self, path: str) -> str:
        try:
            p = Path(path or os.getcwd())
            items = []
            for entry in p.iterdir():
                try:
                    items.append({
                        "name": entry.name,
                        "path": str(entry.resolve()),
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None,
                    })
                except Exception:
                    continue
            return json.dumps({"ok": True, "items": items})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    def _on_backend_event(self, event: dict):
        try:
            if isinstance(event, dict) and "msg" in event and isinstance(event["msg"], dict):
                msg_type = event["msg"].get("type", "")
                flat = {"id": event.get("id", ""), "type": msg_type, **event["msg"]}
                self.event_received.emit(flat)
            else:
                self.event_received.emit(event)
        except Exception as e:
            self.log_message.emit(f"Event parse error: {e}")

    def _on_backend_error(self, message: str):
        self.log_message.emit(f"Backend error: {message}")

    # --- Settings / Config -------------------------------------------------
    @Slot(result=str)
    def get_backend_config(self) -> str:
        """Return backend config as a JSON string."""
        try:
            cfg = get_config_manager().config
            data = cfg.backend.model_dump()
            return json.dumps({"ok": True, "backend": data})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(str, result=str)
    def set_backend_config(self, payload: str) -> str:
        """Update backend config from a JSON string (codex_path, profile, timeout, max_retries, log_level)."""
        try:
            data = json.loads(payload)
            allowed = {k: v for k, v in data.items() if k in {"codex_path", "profile", "timeout", "max_retries", "log_level"}}
            if not allowed:
                return json.dumps({"ok": False, "error": "no valid keys"})
            cm = get_config_manager()
            cm.update_backend_config(**allowed)
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(result=str)
    def detect_codex_path(self) -> str:
        try:
            cm = get_config_manager()
            p = cm.get_codex_path()
            return json.dumps({"ok": bool(p), "codex_path": p})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(result=str)
    def browse_for_codex(self) -> str:
        try:
            path, _ = QFileDialog.getOpenFileName(None, "Select Codex executable", "", "Executable (*.exe);;All Files (*)")
            if not path:
                return json.dumps({"ok": False, "cancelled": True})
            return json.dumps({"ok": True, "codex_path": path})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Workbench")
        self.resize(1400, 900)

        cfg = get_config_manager().config
        codex_path = cfg.backend.codex_path or "codex"
        self.backend = BackendService(
            codex_executable_path=codex_path,
            profile=cfg.backend.profile,
        )

        self.webview = QWebEngineView(self)
        self.setCentralWidget(self.webview)
        # Allow local file:// HTML to load remote CDN resources (Tailwind, fonts)
        s = self.webview.settings()
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)

        # WebChannel
        self.channel = QWebChannel(self.webview.page())
        self.bridge = WebBridge(self.backend)
        self.channel.registerObject("backend", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # Load UI assets
        assets_dir = Path(__file__).parent / "assets"
        index_html = assets_dir / "index.html"
        self.webview.load(QUrl.fromLocalFile(str(index_html.resolve())))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
