import json
import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QUrl, Qt
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtGui import QIcon, QColor
import re
from typing import Dict, Any

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
        # Cache: servers and errors for UI
        self._server_errors: dict[str, str] = {}

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
            # Use platform-appropriate filter: Windows shows .exe, others show all files
            filter_str = "Executable (*.exe);;All Files (*)" if sys.platform.startswith('win') else "All Files (*)"
            path, _ = QFileDialog.getOpenFileName(None, "Select Codex executable", "", filter_str)
            if not path:
                return json.dumps({"ok": False, "cancelled": True})
            return json.dumps({"ok": True, "codex_path": path})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    # --- Graph builder -----------------------------------------------------
    @Slot(str, result=str)
    def build_graph(self, root: str) -> str:
        """Build a simple Markdown content graph with backlinks from a root folder.

        - Nodes: markdown files (.md)
        - Edges: links via markdown [text](path) or Obsidian-style [[note]] / [[path|alias]]
        """
        try:
            root_path = Path(root or ".").resolve()
            if not root_path.exists() or not root_path.is_dir():
                return json.dumps({"ok": False, "error": f"invalid root: {root_path}"})

            files = [p for p in root_path.rglob("*.md") if p.is_file()]
            # Map slugs to paths (basename without extension, lowercase)
            slug_map: Dict[str, Path] = {}
            for p in files:
                slug = p.stem.lower()
                slug_map.setdefault(slug, p)

            link_pat = re.compile(r"\[[^\]]*\]\(([^\)]+)\)")
            obs_pat = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")

            nodes = []
            edges = []
            id_map: Dict[Path, str] = {}
            for p in files:
                nid = str(p)
                id_map[p] = nid
                nodes.append({"data": {"id": nid, "label": p.name}})

            for p in files:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                src = id_map[p]
                # Standard markdown links
                for target in link_pat.findall(text):
                    t = target.strip()
                    if t.startswith("http:") or t.startswith("https:"):
                        continue
                    tpath = (p.parent / t).with_suffix(".md") if not t.endswith(".md") else (p.parent / t)
                    tpath = tpath.resolve()
                    if tpath in id_map:
                        edges.append({"data": {"source": src, "target": id_map[tpath]}})
                # Obsidian wiki-links
                for inner in obs_pat.findall(text):
                    slug = inner.strip().lower()
                    tpath = None
                    if (p.parent / (slug + ".md")).exists():
                        tpath = (p.parent / (slug + ".md")).resolve()
                    elif slug in slug_map:
                        tpath = slug_map[slug].resolve()
                    if tpath and tpath in id_map:
                        edges.append({"data": {"source": src, "target": id_map[tpath]}})

            return json.dumps({"ok": True, "nodes": nodes, "edges": edges})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    # --- MCP Tools / History ----------------------------------------------
    @Slot()
    def list_mcp_tools(self):
        op = Operation.create_list_mcp_tools()
        self.backend.send_op(op.model_dump())

    @Slot()
    def get_history(self):
        op = Operation.create_get_history()
        self.backend.send_op(op.model_dump())

    @Slot(str, result=str)
    def read_file(self, path: str) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return json.dumps({"ok": False, "error": "not found"})
            text = p.read_text(encoding="utf-8", errors="replace")
            return json.dumps({"ok": True, "path": str(p), "content": text})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    def _on_backend_event(self, event: dict):
        try:
            if isinstance(event, dict) and "msg" in event and isinstance(event["msg"], dict):
                msg_type = event["msg"].get("type", "")
                flat = {"id": event.get("id", ""), "type": msg_type, **event["msg"]}
                # Track server error messages for display
                if msg_type == "error":
                    msg = event["msg"].get("message", "")
                    # crude extract: MCP client for `name` failed to start: ...
                    import re
                    m = re.search(r"MCP client for `([^`]+)` failed to start: (.*)", msg)
                    if m:
                        self._server_errors[m.group(1)] = m.group(2)
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

    # --- File write (Save) -------------------------------------------------
    @Slot(str, str, result=str)
    def write_file(self, path: str, content: str) -> str:
        try:
            p = Path(path)
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            # update recent files
            try:
                get_config_manager().add_recent_file(str(p))
            except Exception:
                pass
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(str)
    def add_recent_file(self, path: str):
        try:
            get_config_manager().add_recent_file(path)
        except Exception:
            pass

    @Slot(result=str)
    def get_recent_files(self) -> str:
        try:
            files = get_config_manager().get_recent_files()
            return json.dumps({"ok": True, "files": files, "last": get_config_manager().get_last_active_file()})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    # --- Layout state (resizable panes) ------------------------------------
    @Slot(result=str)
    def get_layout_state(self) -> str:
        try:
            st = get_config_manager().get_layout_state() or {}
            return json.dumps({"ok": True, "state": st})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(str)
    def set_layout_state(self, payload: str):
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                get_config_manager().set_layout_state(data)
        except Exception:
            pass

    # --- MCP Servers management -------------------------------------------
    @Slot(result=str)
    def get_mcp_servers(self) -> str:
        try:
            from ..core.config import get_config_manager
            cm = get_config_manager()
            servers = {name: s.model_dump() for name, s in cm.get_mcp_servers().items()}
            return json.dumps({"ok": True, "servers": servers, "errors": self._server_errors})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(str, result=str)
    def upsert_mcp_server(self, payload: str) -> str:
        try:
            from ..core.config import get_config_manager
            from ..core.models import MCPServerConfig
            data = json.loads(payload)
            server = MCPServerConfig(**data)
            cm = get_config_manager()
            cm.upsert_mcp_server(server)
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot(str, result=str)
    def delete_mcp_server(self, name: str) -> str:
        try:
            from ..core.config import get_config_manager
            cm = get_config_manager()
            cm.remove_mcp_server(name)
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

    @Slot()
    def restart_backend(self):
        try:
            self.backend.stop()
        except Exception:
            pass
        self.backend.start()

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


class WindowBridge(QObject):
    """Expose basic window controls to the Web UI via QWebChannel."""
    def __init__(self, window: QMainWindow):
        super().__init__()
        self._win = window

    @Slot()
    def minimize(self):
        try:
            self._win.showMinimized()
        except Exception:
            pass

    @Slot()
    def maximize_restore(self):
        try:
            if self._win.isMaximized():
                self._win.showNormal()
            else:
                self._win.showMaximized()
        except Exception:
            pass

    @Slot()
    def close(self):
        try:
            self._win.close()
        except Exception:
            pass

    @Slot(int, int)
    def move_by(self, dx: int, dy: int):
        try:
            g = self._win.geometry()
            self._win.setGeometry(g.x() + int(dx), g.y() + int(dy), g.width(), g.height())
        except Exception:
            pass

    @Slot(str, int, int)
    def resize_edge(self, edge: str, dx: int, dy: int):
        """Resize window by deltas from the specified edge (left/right/top/bottom and corners)."""
        try:
            g = self._win.geometry()
            x, y, w, h = g.x(), g.y(), g.width(), g.height()
            dx = int(dx); dy = int(dy)
            min_w = max(720, self._win.minimumWidth())
            min_h = max(480, self._win.minimumHeight())
            edge = str(edge or '').lower()
            if 'left' in edge:
                new_x = x + dx
                new_w = w - dx
                if new_w < min_w:
                    new_x = x + (w - min_w)
                    new_w = min_w
                x, w = new_x, new_w
            if 'right' in edge:
                new_w = w + dx
                if new_w < min_w:
                    new_w = min_w
                w = new_w
            if 'top' in edge:
                new_y = y + dy
                new_h = h - dy
                if new_h < min_h:
                    new_y = y + (h - min_h)
                    new_h = min_h
                y, h = new_y, new_h
            if 'bottom' in edge:
                new_h = h + dy
                if new_h < min_h:
                    new_h = min_h
                h = new_h
            self._win.setGeometry(x, y, w, h)
        except Exception:
            pass

    @Slot(str)
    def snap(self, where: str):
        """Snap window to screen regions (left/right halves, maximize)."""
        try:
            screen = QApplication.primaryScreen()
            if not screen:
                return
            ag = screen.availableGeometry()
            if not ag:
                return
            where = (where or '').lower()
            if where == 'left':
                self._win.setGeometry(ag.x(), ag.y(), int(ag.width() / 2), ag.height())
            elif where == 'right':
                self._win.setGeometry(ag.x() + int(ag.width() / 2), ag.y(), int(ag.width() / 2), ag.height())
            elif where in ('top', 'maximize'):
                # maximize to available geometry (taskbar-aware)
                self._win.setGeometry(ag.x(), ag.y(), ag.width(), ag.height())
            elif where == 'restore':
                self._win.showNormal()
        except Exception:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Workbench")
        self.resize(1400, 900)
        # Frameless window with transparent background for custom chrome
        try:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        except Exception:
            pass

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
        # Transparent page background so the app chrome blends
        try:
            self.webview.setAttribute(Qt.WA_TranslucentBackground, True)
            self.webview.setStyleSheet("background: transparent;")
            self.webview.page().setBackgroundColor(QColor(0, 0, 0, 0))
        except Exception:
            pass

        # WebChannel
        self.channel = QWebChannel(self.webview.page())
        self.bridge = WebBridge(self.backend)
        self.channel.registerObject("backend", self.bridge)
        # Window control bridge
        self.window_bridge = WindowBridge(self)
        self.channel.registerObject("window", self.window_bridge)
        self.webview.page().setWebChannel(self.channel)

        # Load UI assets
        assets_dir = Path(__file__).parent / "assets"
        index_html = assets_dir / "index.html"
        self.webview.load(QUrl.fromLocalFile(str(index_html.resolve())))

        # Set window icon (SVG)
        try:
            icon_path = assets_dir / "img" / "aiw_icon.svg"
            if icon_path.exists():
                app_icon = QIcon(str(icon_path))
                self.setWindowIcon(app_icon)
                QApplication.instance().setWindowIcon(app_icon)
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
