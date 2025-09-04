"""
Enhanced main window with dock-based layout for AI Development Workbench
"""
import json
import os
import time
import logging
import sys
import difflib
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QSize
from PySide6.QtWidgets import (
    QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QDockWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QStyle,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox,
    QLabel, QProgressBar, QTextBrowser, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QInputDialog
)
from PySide6.QtGui import QAction, QIcon, QFont, QPixmap, QPainter, QColor, QLinearGradient
from .icons import make_icon
from .design_system import apply_theme as legacy_apply_theme
from .theme_manager import apply_theme as tokens_apply_theme
try:
    from shiboken6 import isValid as _is_qobj_valid
except Exception:  # fallback if shiboken import fails
    def _is_qobj_valid(obj):  # type: ignore
        try:
            return obj is not None
        except Exception:
            return False

from ..core.backend_service import BackendService
from ..core.codex_config_manager import get_codex_config_manager  # NEW: to inspect codex config
from ..core.config import get_config_manager
from ..core.models import Repository, FileItem, Operation, Task
from ..core.task_runner import get_workflow_runner
from .code_editor import CodeEditorWidget
from .diff_view import DiffViewWidget
from .components.chat.chat_view import ChatView
from .components.file_tree import FileTree
from .components.quick_switcher import QuickSwitcher
from .components.search_panel import SearchPanel
from .layout.pane_manager import PaneManager
from .settings_dialog import SettingsDialog
from .services.event_bus import GLOBAL_EVENT_BUS
from ..core.conversation_store import ConversationStore, StoredMessage
from .motion.anim import fade_in_widget, animate_height_toggle
import patch

# Set up logging for main window
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_workbench_main_debug.log', mode='w')
    ]
)
main_logger = logging.getLogger('MainWindow')


class MainWindow(QMainWindow):
    """Enhanced main window with dock-based layout"""

    # Signals
    repository_opened = Signal(str)  # repository path
    file_selected = Signal(str)     # file path

    def __init__(self):
        """Initialize main window and restore geometry/state."""
        main_logger.info("MainWindow.__init__() called")
        super().__init__()
        # Core services
        self.config_manager = get_config_manager()
        self.current_repository: Optional[Repository] = None
        self.backend: Optional[BackendService] = None
        self.backend_thread: Optional[QThread] = None
        self.task_runner = get_workflow_runner()

        # Streaming accumulation buffers
        self.current_reasoning = ""
        self.current_message = ""
        self.last_task_id = None

        # Feature state
        self.show_raw_reasoning = True  # legacy flag
        self.reasoning_panel_visible = True
        self.token_stats = {"input": 0, "output": 0, "total": 0}
        self.conversation_messages = []
        self.chat_as_tab = True
        self.diff_as_tab = True

        # Initialize conversation store first
        self._init_conversation_store()

        # Window basics
        self.setWindowTitle("AI Development Workbench")
        self._apply_app_icon()
        self.setGeometry(100, 100, 1400, 900)
        self._update_window_title()

        # Restore window geometry if available
        try:
            geometry = self.config_manager.get_window_geometry()
            if geometry:
                geom_data = geometry.get('geometry')
                state_data = geometry.get('state')
                if isinstance(geom_data, str):
                    geom_data = geom_data.encode('latin1')
                if isinstance(state_data, str):
                    state_data = state_data.encode('latin1')
                if geom_data:
                    self.restoreGeometry(geom_data)
                if state_data:
                    self.restoreState(state_data)
        except Exception as e:
            main_logger.warning(f"Could not restore window geometry: {e}")

        # Build UI
        self._setup_ui()
        self._apply_theme()
        # Hook pane manager signals for unsaved-close confirmation and dirty tabs
        try:
            self.pane_manager.before_close_unsaved.connect(self._confirm_close_unsaved)
        except Exception:
            pass
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_backend()
        self._load_initial_state()

    def _apply_app_icon(self):
        """Create and apply a modern-looking window icon at runtime.

        Avoids external assets; paints a soft gradient square with a subtle
        glyph so the app feels like an Electron/Tailwind tool.
        """
        try:
            size = 256
            pm = QPixmap(size, size)
            pm.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pm)
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

            # Gradient background
            grad = QLinearGradient(0, 0, size, size)
            grad.setColorAt(0.0, QColor('#1e293b'))   # slate-800
            grad.setColorAt(1.0, QColor('#0ea5e9'))   # sky-500
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            radius = int(size * 0.18)
            painter.drawRoundedRect(0, 0, size, size, radius, radius)

            # Accent corner chip
            painter.setBrush(QColor('#22c55e'))  # green-500
            chip = int(size * 0.22)
            painter.drawRoundedRect(size - chip - 14, 14, chip, chip, 16, 16)

            # Monogram
            painter.setPen(QColor('white'))
            f = QFont('Cascadia Code', int(size * 0.28))
            f.setWeight(QFont.Weight.DemiBold)
            painter.setFont(f)
            painter.drawText(pm.rect(), int(Qt.AlignmentFlag.AlignCenter), 'AI')
            painter.end()

            self.setWindowIcon(QIcon(pm))
        except Exception:
            # Fallback to default icon silently
            pass

    def _init_chat_controls(self, chat_view: ChatView):
        """Populate chat toolbar controls: model options and temperature.

        - Model selector: list from codex config (default + providers).
        - Temperature slider override applied in _send_prompt.
        """
        try:
            cfg = get_codex_config_manager().load()
            models = []
            if getattr(self, 'current_profile', None) and cfg.profiles:
                prof = cfg.profiles.get(self.current_profile) or {}
                m = prof.get('model')
                if m:
                    models.append(m)
            if cfg.model and cfg.model not in models:
                models.append(cfg.model)
            for name in sorted(cfg.model_providers.keys()):
                if name not in models:
                    models.append(name)
            if not models:
                models = ["<default>"]
            chat_view.model_combo.clear()
            chat_view.model_combo.addItems(models)
            pre = models[0]
            if cfg.model and cfg.model in models:
                pre = cfg.model
            idx = chat_view.model_combo.findText(pre)
            if idx >= 0:
                chat_view.model_combo.setCurrentIndex(idx)
            chat_view.model_combo.setEnabled(True)
            def on_model_changed(i: int):
                try:
                    text = chat_view.model_combo.currentText()
                    self._model_override = None if text == "<default>" else text
                except Exception:
                    pass
            chat_view.model_combo.currentIndexChanged.connect(on_model_changed)
        except Exception as e:
            main_logger.warning(f"_init_chat_controls failed: {e}")

    def _update_window_title(self):
        """Update window title to show active session"""
        base_title = "AI Development Workbench"
        if self.conversation_store and self.conversation_store.session:
            session_id = self.conversation_store.session.session_id
            self.setWindowTitle(f"{base_title} - Session: {session_id}")
        else:
            self.setWindowTitle(base_title)

    def _setup_backend(self):
        """Initialize the backend service with improved error handling"""
        main_logger.info("_setup_backend() called")
        codex_path = self.config_manager.get_codex_path()
        main_logger.info(f"Codex path from config: {codex_path}")

        # --- Extra diagnostics for model/provider configuration ---
        try:
            codex_cfg_mgr = get_codex_config_manager()
            codex_cfg = codex_cfg_mgr.load()
            main_logger.info(
                "Codex config loaded from %s (model=%s, provider=%s, provider_ids=%s)",
                codex_cfg_mgr.config_path,
                codex_cfg.model,
                codex_cfg.model_provider,
                list(sorted(codex_cfg.model_providers.keys())),
            )
            if codex_cfg.model_provider and codex_cfg.model_provider not in codex_cfg.model_providers:
                main_logger.warning(
                    "Configured model_provider '%s' not present in model_providers map; backend will error.",
                    codex_cfg.model_provider,
                )
                # Surface a UI message so user sees immediately
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {
                        'role': 'system',
                        'content': f"⚠️ Provider '{codex_cfg.model_provider}' not found in config. Open Settings → Providers to add it.",
                    })
                except Exception:
                    self._add_message('system', f"⚠️ Provider '{codex_cfg.model_provider}' not found in config.")
        except Exception as e:
            main_logger.warning(f"Could not load Codex config for diagnostics: {e}")

        if not codex_path:
            # Try auto-detection one more time
            main_logger.info("No codex path configured, trying auto-detection")
            self.config_manager._auto_detect_codex_path()
            codex_path = self.config_manager.get_codex_path()
            main_logger.info(f"Auto-detected codex path: {codex_path}")

            if not codex_path:
                main_logger.warning("No codex executable found")
                result = QMessageBox.question(
                    self, "Codex Not Found",
                    "Codex executable not found. Would you like to:\n\n"
                    "â€¢ Browse for the executable manually\n"
                    "â€¢ Continue without backend (limited functionality)\n\n"
                    "Note: You can also install Codex CLI from https://github.com/openai/codex",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )

                if result == QMessageBox.StandardButton.Yes:
                    codex_path, _ = QFileDialog.getOpenFileName(
                        self, "Select Codex Executable",
                        "", "Executable files (*.*);;All files (*.*)"
                    )
                    if codex_path:
                        self.config_manager.config.backend.codex_path = codex_path
                        self.config_manager.save_config()
                        main_logger.info(f"User selected codex path: {codex_path}")
                    else:
                        return
                elif result == QMessageBox.StandardButton.No:
                    # Continue without backend
                    self.backend_status_label.setText("Backend: Not configured")
                    main_logger.info("User chose to continue without backend")
                    return
                else:
                    return

        # Move backend to a new thread
        main_logger.info("Setting up backend thread")
        
        # Get current profile from codex config
        self.current_profile = None
        try:
            codex_cfg_mgr = get_codex_config_manager()
            codex_cfg = codex_cfg_mgr.load()
            self.current_profile = codex_cfg.profile
            if self.current_profile:
                main_logger.info(f"Using profile: {self.current_profile}")
            else:
                main_logger.info("No profile configured, using default settings")
        except Exception as e:
            main_logger.warning(f"Could not load profile from config: {e}")
        
        # Get custom environment variables from AI Workbench config
        custom_env = self.config_manager.config.backend.environment_variables
        if custom_env:
            main_logger.info(f"Using custom environment variables: {list(custom_env.keys())}")
        
        self.backend_thread = QThread()
        self.backend = BackendService(codex_path, profile=self.current_profile, custom_env=custom_env)
        self.backend.moveToThread(self.backend_thread)

        # Connect signals across threads
        self.backend_thread.started.connect(self.backend.start)
        self.backend.new_event.connect(self._on_backend_event)
        self.backend.backend_error.connect(self._on_backend_error)
        self.backend.backend_started.connect(self._on_backend_started)
        self.backend.backend_stopped.connect(self._on_backend_stopped)
        self.backend.connection_status_changed.connect(self._on_connection_status_changed)
        self.backend.operation_progress.connect(self._on_operation_progress)
        self.backend.operation_cleanup.connect(self._on_operation_cleanup)

        # Connect task runner signals
        self.task_runner.task_started.connect(self._on_task_started)
        self.task_runner.task_completed.connect(self._on_task_completed)
        self.task_runner.task_failed.connect(self._on_task_failed)
        self.task_runner.task_progress.connect(self._on_task_progress)
        self.task_runner.workflow_started.connect(self._on_workflow_started)
        self.task_runner.workflow_completed.connect(self._on_workflow_completed)
        self.task_runner.workflow_failed.connect(self._on_workflow_failed)

        main_logger.info("Starting backend thread")
        self.backend_thread.start()

    def _setup_ui(self):
        """Setup the main UI: central tab manager + optional docks."""
        # Central split-pane manager (no default tab; create editor explicitly)
        self.pane_manager = PaneManager(parent=self, create_default=False)
        self.setCentralWidget(self.pane_manager)

        # Tab factories (some created lazily) - with theme applied post-creation
        self._tab_factories = {
            'editor': lambda: self._create_themed_code_editor(),
            'diff': lambda: self._create_diff_tab_widget(),
            'plan': lambda: self._create_plan_tab_widget(),
        }
        # Create the primary editor tab explicitly; keep a strong reference
        self.code_editor = self.pane_manager.ensure_tab('editor', 'Editor', self._tab_factories['editor'])

        # Try restoring previous layout (split tree + tabs)
        try:
            layout_state = self.config_manager.get_layout_state()
            if layout_state:
                self.pane_manager.restore(layout_state.get('panes'), self._tab_factories)
        except Exception as e:
            main_logger.warning(f"Could not restore pane layout: {e}")

        # Event bus handlers
        self._register_event_bus_handlers()

        # Always create repository dock
        self._create_repository_dock()

        # Restore last opened repository (session persistence)
        try:
            self._restore_last_repository()
        except Exception as e:
            main_logger.warning(f"Could not restore last repository: {e}")

        # Chat: tab or dock
        if self.chat_as_tab:
            self._tab_factories['chat'] = lambda: self._create_chat_tab_widget()
            chat_wrapper = self.pane_manager.ensure_tab('chat', 'Chat', self._tab_factories['chat'])
            # self.chat_view was set in _create_chat_tab_widget to the actual ChatView
            # chat_wrapper is the container QWidget returned by the factory
            self.chat_console = self.chat_view  # backcompat
        else:
            self._create_console_dock()

        # Diff: tab or dock
        if not self.diff_as_tab:
            self._create_diff_dock()

        # Other docks
        self._create_artifacts_dock()
        self._create_exec_log_dock()
        self._create_token_dock()

        # Corner priorities
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

    # --- Tab factory helpers (diff, plan migrated from docks) --------------
    def _create_themed_code_editor(self):
        """Create a code editor widget with proper theme"""
        widget = CodeEditorWidget()
        current_theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
        widget.set_theme(current_theme)
        return widget

    def _get_or_create_diff_viewer(self):
        """Get the diff viewer, creating it if necessary"""
        if hasattr(self, 'diff_viewer') and self.diff_viewer is not None:
            return self.diff_viewer
        
        # Create diff viewer if it doesn't exist
        try:
            self.diff_viewer = DiffViewWidget()
            current_theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
            self.diff_viewer.set_theme(current_theme)
            self.diff_viewer.diff_widget.apply_requested.connect(self._on_apply_diff)
            main_logger.info("Created diff viewer on demand")
            return self.diff_viewer
        except Exception as e:
            main_logger.error(f"Failed to create diff viewer: {e}")
            from PySide6.QtWidgets import QLabel
            self.diff_viewer = QLabel("Diff unavailable")
            return self.diff_viewer

    def _create_diff_tab_widget(self):
        """Return a diff viewer widget suitable for a tab with theme support.
        Reuses existing instance if a legacy dock already created it."""
        if hasattr(self, 'diff_viewer') and self.diff_viewer is not None:
            return self.diff_viewer
        try:
            self.diff_viewer = DiffViewWidget()
            current_theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
            self.diff_viewer.set_theme(current_theme)
        except Exception as e:
            main_logger.error(f"Failed to create DiffViewWidget: {e}")
            from PySide6.QtWidgets import QLabel
            self.diff_viewer = QLabel("Diff unavailable")
        return self.diff_viewer

    def _create_plan_tab_widget(self):
        """Return a plan list widget for the plan tab."""
        if hasattr(self, 'plan_list') and self.plan_list is not None:
            return self.plan_list
        try:
            from PySide6.QtWidgets import QListWidget
            self.plan_list = QListWidget()
            self.plan_list.setObjectName("planList")
        except Exception as e:
            main_logger.error(f"Failed to create plan list widget: {e}")
            from PySide6.QtWidgets import QLabel
            self.plan_list = QLabel("Plan unavailable")
        return self.plan_list

        # Hide optional docks initially
        for dock in (self.console_dock, self.artifacts_dock, self.exec_log_dock, self.plan_dock):
            dock.hide()
        self.token_dock.hide()

    def _register_event_bus_handlers(self):
        """Subscribe lightweight adapters to GLOBAL_EVENT_BUS."""
        try:
            GLOBAL_EVENT_BUS.subscribe('chat.message', lambda m: self._add_message(m.get('role', 'assistant'), m.get('content', ''), rich=m.get('rich', False)))
            GLOBAL_EVENT_BUS.subscribe('diff.update', lambda p: self._eventbus_diff_update(p))
            GLOBAL_EVENT_BUS.subscribe('plan.update', lambda p: self._handle_plan_update(p))
            GLOBAL_EVENT_BUS.subscribe('tokens.update', lambda p: self._handle_token_count(p))
            GLOBAL_EVENT_BUS.subscribe('exec.begin', lambda p: self._handle_exec_command_begin(p))
            GLOBAL_EVENT_BUS.subscribe('exec.output', lambda p: self._handle_exec_command_output_delta(p))
            GLOBAL_EVENT_BUS.subscribe('exec.end', lambda p: self._handle_exec_command_end(p))
        except Exception as e:
            main_logger.warning(f"Event bus registration failed: {e}")

    def _eventbus_diff_update(self, payload):
        try:
            diff_text = payload.get('diff') or payload.get('unified_diff') or ''
            file_path = payload.get('file_path', '')
            if diff_text:
                self._get_or_create_diff_viewer().set_diff_content(diff_text, file_path)
                self._show_diff_viewer()
        except Exception:
            pass
    # (no dock creation here; this helper only updates diff content)

    # Docks were inadvertently placed here previously; restored to _setup_ui.

    def _create_repository_dock(self):
        """Create repository explorer dock"""
        self.repo_dock = QDockWidget("Repository", self)
        self.repo_dock.setObjectName("Repository")
        self.repo_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        # Repository actions
        repo_widget = QWidget()
        repo_layout = QVBoxLayout(repo_widget)

        # Repository info label
        self.repo_info_label = QLabel("No repository opened")
        repo_layout.addWidget(self.repo_info_label)

        # File tree component
        default_root = str(Path.cwd())
        try:
            if getattr(self, 'current_repository', None) and self.current_repository:
                default_root = self.current_repository.path
        except Exception:
            pass
        self.file_tree = FileTree(root=default_root)
        self.file_tree.file_open_requested.connect(lambda p: self._load_file_into_editor(p))
        repo_layout.addWidget(self.file_tree)
        self.repo_dock.setWidget(repo_widget)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.repo_dock)

    def _create_console_dock(self):
        """Create the assistant (chat) dock with ChatView UI."""
        self.console_dock = QDockWidget("Assistant", self)
        self.console_dock.setObjectName("Console")
        self.console_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.console_dock.setMinimumWidth(340)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(4, 4, 4, 4)

        # Reasoning panel (live)
        self.reasoning_view = QTextBrowser()
        self.reasoning_view.setObjectName("ReasoningView")
        # Styled via QSS (#ReasoningView)
        self.reasoning_view.setMaximumHeight(120)
        self.reasoning_view.setVisible(self.reasoning_panel_visible)
        self.reasoning_view.setHtml("<b>Reasoning</b><br><i>Waiting...</i>")
        vbox.addWidget(self.reasoning_view)

        # Chat view
        self.chat_view = ChatView()
        try:
            self.chat_view.apply_patch_requested.connect(lambda raw: self._inline_apply_patch(raw))
            self.chat_view.explain_requested.connect(lambda raw: self._inline_explain(raw))
            self.chat_view.refine_requested.connect(lambda raw: self._inline_refine(raw))
            self.chat_view.temperature_changed.connect(lambda t: setattr(self, '_temp_override', t))
            self.chat_view.reasoning_toggle.connect(self._toggle_raw_reasoning)
            self._init_chat_controls(self.chat_view)
        except Exception:
            pass
        self.chat_view.setMinimumWidth(320)
        vbox.addWidget(self.chat_view)
        # Backward compatibility alias (legacy code expects chat_console)
        self.chat_console = self.chat_view

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(60)
        self.prompt_input.setFont(QFont("Cascadia Code", 11))
        self.prompt_input.setPlaceholderText("Ask the AI...")
        input_layout.addWidget(self.prompt_input, 1)

        send_button = QPushButton("Send")
        send_button.setObjectName("SendPromptButton")
        send_button.clicked.connect(self._send_prompt)
        input_layout.addWidget(send_button)

        vbox.addLayout(input_layout)
        self.console_dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.console_dock)
        # Optional motion fade-in for dock
        try:
            if getattr(self.config_manager.config.ui, 'animations_enabled', True) and not getattr(self.config_manager.config.ui, 'prefers_reduced_motion', False):
                fade_in_widget(self.console_dock)
                try:
                    self.console_dock.visibilityChanged.connect(
                        lambda vis: fade_in_widget(self.console_dock) if vis else None
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _create_chat_tab_widget(self):
        """Factory returning chat view widget for tab mode."""
        try:
            if hasattr(self, '_actual_chat_view') and self._actual_chat_view is not None:
                # Ensure the stored ChatView and its wrapper are still valid; otherwise rebuild
                wrapper = getattr(self._actual_chat_view, '_wrapper', None)
                if _is_qobj_valid(self._actual_chat_view) and _is_qobj_valid(wrapper):
                    return wrapper
                else:
                    self._actual_chat_view = None
        except Exception:
            pass
        cv = ChatView()
        try:
            cv.apply_patch_requested.connect(lambda raw: self._inline_apply_patch(raw))
            cv.explain_requested.connect(lambda raw: self._inline_explain(raw))
            cv.refine_requested.connect(lambda raw: self._inline_refine(raw))
            cv.temperature_changed.connect(lambda t: setattr(self, "_temp_override", t))
            cv.reasoning_toggle.connect(self._toggle_raw_reasoning)
            self._init_chat_controls(cv)
        except Exception:
            pass
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(4,4,4,4)
        # Reasoning panel for tab mode
        self.reasoning_view = QTextBrowser()
        self.reasoning_view.setObjectName("ReasoningView")
        # Styled via QSS (#ReasoningView)
        self.reasoning_view.setMaximumHeight(120)
        self.reasoning_view.setVisible(self.reasoning_panel_visible)
        self.reasoning_view.setHtml("<b>Reasoning</b><br><i>Waiting...</i>")
        layout.addWidget(self.reasoning_view)
        layout.addWidget(cv, 1)
        input_bar = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(60)
        self.prompt_input.setFont(QFont("Cascadia Code", 11))
        self.prompt_input.setPlaceholderText("Ask the AI...")
        input_bar.addWidget(self.prompt_input, 1)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_prompt)
        input_bar.addWidget(send_btn)
        layout.addLayout(input_bar)
        # Store the actual ChatView reference in a separate variable
        self._actual_chat_view = cv
        self.chat_view = cv  # This will get overwritten by pane manager
        self.chat_console = cv
        # Store reference to the wrapper on the ChatView for later retrieval
        cv._wrapper = wrapper
        return wrapper

    def _create_diff_dock(self):
        """Create diff viewer dock with theme support"""
        self.diff_dock = QDockWidget("Diff", self)
        self.diff_dock.setObjectName("Diff")
        self.diff_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Enhanced diff viewer widget with theme
        self.diff_viewer = DiffViewWidget()
        current_theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
        self.diff_viewer.set_theme(current_theme)
        self.diff_viewer.diff_widget.apply_requested.connect(self._on_apply_diff)

        self.diff_dock.setWidget(self.diff_viewer)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.diff_dock)
        try:
            if getattr(self.config_manager.config.ui, 'animations_enabled', True) and not getattr(self.config_manager.config.ui, 'prefers_reduced_motion', False):
                fade_in_widget(self.diff_dock)
                try:
                    self.diff_dock.visibilityChanged.connect(
                        lambda vis: fade_in_widget(self.diff_dock) if vis else None
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _show_diff_viewer(self):
        """Safely show the diff viewer in either dock or tab mode"""
        try:
            if hasattr(self, 'diff_dock') and self.diff_dock:
                # Dock mode - bring to front
                self.diff_dock.raise_()
                self.diff_dock.show()
            elif self.diff_as_tab and hasattr(self, 'pane_manager'):
                # Tab mode - ensure via pane manager
                self.pane_manager.ensure_tab('diff', 'Diff', self._tab_factories['diff'])
        except Exception as e:
            main_logger.error(f"Failed to show diff viewer: {e}")

    def _create_plan_dock(self):
        """Create plan/update dock"""
        self.plan_dock = QDockWidget("Plan", self)
        self.plan_dock.setObjectName("Plan")
        self.plan_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        from PySide6.QtWidgets import QListWidget
        self.plan_list = QListWidget()
        # Styled via QSS (#planList)
        self.plan_dock.setWidget(self.plan_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.plan_dock)

    def _create_token_dock(self):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
        self.token_dock = QDockWidget("Tokens", self)
        self.token_dock.setObjectName("Tokens")
        container = QWidget()
        layout = QVBoxLayout(container)
        grid = QGridLayout()
        self._token_value_labels = {}
        for i, key in enumerate(["Input", "Output", "Total"]):
            name_lbl = QLabel(key + ":")
            val_lbl = QLabel("0")
            grid.addWidget(name_lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
            self._token_value_labels[key.lower()] = val_lbl
        layout.addLayout(grid)
        container.setLayout(layout)
        self.token_dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.token_dock)

    def _create_artifacts_dock(self):
        """Create artifacts dock"""
        self.artifacts_dock = QDockWidget("Artifacts", self)
        self.artifacts_dock.setObjectName("Artifacts")
        self.artifacts_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        # Artifacts list
        self.artifacts_list = QTreeWidget()
        self.artifacts_list.setHeaderLabel("Generated Files")
        self.artifacts_list.itemDoubleClicked.connect(self._on_artifact_double_clicked)

        self.artifacts_dock.setWidget(self.artifacts_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.artifacts_dock)
        self.artifacts_dock.hide()

    def _create_exec_log_dock(self):
        """Create execution log dock for streaming command output."""
        try:
            self.exec_log_dock = QDockWidget("Exec Output", self)
            self.exec_log_dock.setObjectName("ExecOutput")
            self.exec_log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
            from PySide6.QtWidgets import QTextBrowser
            self.exec_output_view = QTextBrowser()
            self.exec_output_view.setOpenExternalLinks(True)
            self.exec_output_view.setObjectName("execOutputView")
            # Styled via QSS (#execOutputView)
            self.exec_log_dock.setWidget(self.exec_output_view)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.exec_log_dock)
            self.exec_log_dock.hide()
        except Exception as e:
            main_logger.error(f"Failed to create exec log dock: {e}")

    def _init_conversation_store(self):
        try:
            base = self.config_manager.config_dir
            self.conversation_store = ConversationStore(base)
            loaded = self.conversation_store.load_last_session()
            if loaded:
                # UI hydration will happen in _load_initial_state once chat_view is ready
                pass
            else:
                # New session: add marker after session start
                self.conversation_store.start_new_session()
                try:
                    self._add_message('system', f"Session started: {self.conversation_store.session.session_id}")
                except Exception:
                    pass
        except Exception as e:
            main_logger.warning(f"Conversation store init failed: {e}")

        # Setup debounce timer
        self._conversation_flush_timer = QTimer(self)
        self._conversation_flush_timer.setInterval(1500)
        self._conversation_flush_timer.setSingleShot(True)
        self._conversation_flush_timer.timeout.connect(self._flush_conversation_store)
        self._update_window_title()  # Update title with session info

    def _schedule_conversation_flush(self):
        try:
            if self._conversation_flush_timer:
                self._conversation_flush_timer.start()
        except Exception:
            pass

    def _flush_conversation_store(self):
        try:
            if self.conversation_store:
                self.conversation_store.flush()
        except Exception:
            pass

    def _setup_menus(self):
        """Setup menu bar (File, View, Tools)."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        act = QAction("&Open Repository...", self); act.triggered.connect(self._open_repository); file_menu.addAction(act)
        act = QAction("Open &File...", self); act.triggered.connect(self._open_file_dialog); file_menu.addAction(act)
        file_menu.addSeparator()
        act = QAction("&Save", self); act.setShortcut("Ctrl+S"); act.triggered.connect(self._save_current_file); file_menu.addAction(act)
        act = QAction("Save &As...", self); act.triggered.connect(self._save_file_as); file_menu.addAction(act)
        file_menu.addSeparator()
        act = QAction("&Settings...", self); act.triggered.connect(self._show_settings); file_menu.addAction(act)
        file_menu.addSeparator()
        export_md = QAction("Export Transcript (Markdown)...", self)
        export_md.triggered.connect(self._export_transcript_markdown)
        file_menu.addAction(export_md)
        file_menu.addSeparator()
        switch_sessions = QAction("Switch Session...", self); switch_sessions.triggered.connect(self._show_session_switcher); file_menu.addAction(switch_sessions)
        act = QAction("E&xit", self); act.triggered.connect(self.close); file_menu.addAction(act)

        # View menu
        view_menu = menubar.addMenu("&View")
        repo_toggle = self.repo_dock.toggleViewAction(); repo_toggle.setText("Repository Explorer"); view_menu.addAction(repo_toggle)
        # Search panel tab
        open_search_tab = QAction("Show Search Panel", self); open_search_tab.triggered.connect(lambda: self.pane_manager.ensure_search(str(Path.cwd()))); view_menu.addAction(open_search_tab)
        if hasattr(self, 'console_dock') and self.console_dock is not None:
            chat_toggle = self.console_dock.toggleViewAction(); chat_toggle.setText("Assistant"); view_menu.addAction(chat_toggle)
        else:
            open_chat_tab = QAction("Show Chat Tab", self); open_chat_tab.triggered.connect(lambda: self.pane_manager.ensure_tab('chat','Chat', self._tab_factories.get('chat', self._create_chat_tab_widget))); view_menu.addAction(open_chat_tab)
        if hasattr(self, 'diff_dock') and self.diff_dock is not None:
            diff_toggle = self.diff_dock.toggleViewAction(); diff_toggle.setText("Diff Viewer"); view_menu.addAction(diff_toggle)
        else:
            open_diff_tab = QAction("Show Diff Tab", self); open_diff_tab.triggered.connect(lambda: self.pane_manager.ensure_tab('diff','Diff', self._tab_factories['diff'])); view_menu.addAction(open_diff_tab)
        artifacts_toggle = self.artifacts_dock.toggleViewAction(); artifacts_toggle.setText("Artifacts"); view_menu.addAction(artifacts_toggle)
        token_toggle = self.token_dock.toggleViewAction(); token_toggle.setText("Token Usage"); view_menu.addAction(token_toggle)
        if hasattr(self, 'exec_log_dock'):
            exec_toggle = self.exec_log_dock.toggleViewAction(); exec_toggle.setText("Exec Output"); view_menu.addAction(exec_toggle)

        view_menu.addSeparator()
        t_chat = QAction("Toggle Chat Tab/Dock", self); t_chat.triggered.connect(self._toggle_chat_mode); view_menu.addAction(t_chat)
        t_diff = QAction("Toggle Diff Tab/Dock", self); t_diff.triggered.connect(self._toggle_diff_mode); view_menu.addAction(t_diff)
        toggle_reasoning = QAction("Toggle Reasoning Panel", self); toggle_reasoning.triggered.connect(self._toggle_reasoning_panel); view_menu.addAction(toggle_reasoning)

        view_menu.addSeparator()
        # Split/Reset layout actions
        split_h = QAction("Split Horizontally", self)
        split_h.triggered.connect(lambda: self.pane_manager.split_current(Qt.Orientation.Horizontal))
        view_menu.addAction(split_h)

        split_v = QAction("Split Vertically", self)
        split_v.triggered.connect(lambda: self.pane_manager.split_current(Qt.Orientation.Vertical))
        view_menu.addAction(split_v)

        reset_layout = QAction("Reset Layout", self)
        reset_layout.triggered.connect(self._reset_layout)
        view_menu.addAction(reset_layout)

        view_menu.addSeparator()
        from PySide6.QtGui import QActionGroup
        theme_group = QActionGroup(self); theme_group.setExclusive(True)
        theme_dark = QAction("Dark Theme", self, checkable=True)
        theme_light = QAction("Light Theme", self, checkable=True)
        theme_group.addAction(theme_dark); theme_group.addAction(theme_light)
        view_menu.addAction(theme_dark); view_menu.addAction(theme_light)
        current_theme = getattr(self.config_manager.config.ui, 'theme', 'system')
        (theme_light if current_theme == 'light' else theme_dark).setChecked(True)
        theme_dark.triggered.connect(lambda: self._set_theme('dark'))
        theme_light.triggered.connect(lambda: self._set_theme('light'))

        self.raw_reasoning_action = QAction("Show Raw Reasoning", self, checkable=True)
        self.raw_reasoning_action.setChecked(self.show_raw_reasoning)
        self.raw_reasoning_action.triggered.connect(self._toggle_raw_reasoning)
        view_menu.addAction(self.raw_reasoning_action)

        view_menu.addSeparator()
        history_action = QAction("Load Conversation History", self); history_action.triggered.connect(self._request_conversation_history); view_menu.addAction(history_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        login_action = QAction("Login with ChatGPT", self); login_action.triggered.connect(self._start_login); tools_menu.addAction(login_action)
        tools_menu.addSeparator()
        edit_task_action = QAction("&Edit File with AI", self); edit_task_action.triggered.connect(self._run_edit_task); tools_menu.addAction(edit_task_action)
        from .shortcuts import get_shortcut
        palette_action = QAction("Command Palette", self)
        sc = get_shortcut('command.palette')
        if sc:
            palette_action.setShortcut(sc)
        palette_action.triggered.connect(self._open_command_palette)
        tools_menu.addAction(palette_action)
        # Quick Switcher
        quick_action = QAction("Quick Switch (Ctrl+P)", self)
        quick_action.setShortcut("Ctrl+P")
        quick_action.triggered.connect(self._open_quick_switcher)
        tools_menu.addAction(quick_action)

    def _open_quick_switcher(self):
        try:
            recent = []
            try:
                recent = [p for p in self.pane_manager.get_open_files()]
            except Exception:
                pass
            qs = QuickSwitcher(str(Path.cwd()), recent=recent, parent=self)
            qs.open_requested.connect(lambda p: self._load_file_into_editor(p))
            qs.exec()
        except Exception as e:
            main_logger.error(f"Quick Switcher failed: {e}")
    
    def _confirm_close_unsaved(self, file_path: str):
        """Prompt the user to save/discard/cancel when closing a dirty tab.
        Updates tab title star and saves when requested.
        """
        try:
            from PySide6.QtWidgets import QMessageBox
            # Identify current tab widget
            current_widget = self.pane_manager._active_stack.tab_widget.currentWidget()
            tab_id = self.pane_manager._get_tab_id_for_widget(current_widget)
            if not tab_id or tab_id not in self.pane_manager._tabs:
                return
            tab = self.pane_manager._tabs[tab_id]
            title = Path(tab.file_path or 'Untitled').name
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText(f"Save changes to {title}?")
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            save_btn = msg.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
            discard_btn = msg.addButton("Don't Save", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setDefaultButton(save_btn)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked is save_btn:
                # Delegate save to PaneManager
                try:
                    self.pane_manager.save_current_tab()
                except Exception:
                    pass
                # Clear star
                try:
                    idx = self.pane_manager._active_stack.tab_widget.currentIndex()
                    base = Path(tab.file_path or 'Untitled').name
                    self.pane_manager._active_stack.tab_widget.setTabText(idx, base)
                    tab.is_modified = False
                except Exception:
                    pass
            elif clicked is discard_btn:
                # Clear star without saving; PaneManager will proceed to close
                try:
                    idx = self.pane_manager._active_stack.tab_widget.currentIndex()
                    base = Path(tab.file_path or 'Untitled').name
                    self.pane_manager._active_stack.tab_widget.setTabText(idx, base)
                    tab.is_modified = False
                except Exception:
                    pass
            else:
                # Cancel: re-add star to indicate still modified
                try:
                    idx = self.pane_manager._active_stack.tab_widget.currentIndex()
                    base = Path(tab.file_path or 'Untitled').name + "*"
                    self.pane_manager._active_stack.tab_widget.setTabText(idx, base)
                    tab.is_modified = True
                except Exception:
                    pass
        except Exception as e:
            main_logger.error(f"Failed to confirm unsaved close: {e}")

    def _open_file_dialog(self):
        """Open a file from disk and display it in an editor tab."""
        try:
            start_dir = None
            try:
                if self.current_repository and self.current_repository.path:
                    start_dir = self.current_repository.path
            except Exception:
                pass
            if not start_dir:
                start_dir = str(Path.cwd())
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", str(start_dir))
            if file_path:
                self._load_file_into_editor(file_path)
        except Exception as e:
            main_logger.error(f"File open failed: {e}")

    def _load_repository_files(self, repo_path: str):
        """Set FileTree root and update repository label."""
        try:
            if hasattr(self, 'file_tree') and self.file_tree:
                self.file_tree.set_root(repo_path)
            if hasattr(self, 'repo_info_label') and self.repo_info_label:
                self.repo_info_label.setText(f"Repository: {Path(repo_path).name}")
        except Exception as e:
            self._add_message("system", f"Error loading repository files: {str(e)}")

    # --- Mode toggle handlers -----------------------------------------------
    def _toggle_chat_mode(self):
        """Switch chat between dock and tab modes."""
        try:
            if self.chat_as_tab:
                # Switch to dock mode: remove tab if present, create dock
                self.chat_as_tab = False
                # Close tab if exists
                if 'chat' in self.pane_manager.list_tabs():
                    self.pane_manager.close_tab('chat')
                # Clear any cached ChatView from tab mode to avoid using a deleted QObject
                try:
                    if hasattr(self, '_actual_chat_view'):
                        self._actual_chat_view = None
                except Exception:
                    pass
                self._create_console_dock()
            else:
                # Switch to tab mode
                self.chat_as_tab = True
                if hasattr(self, 'console_dock') and self.console_dock:
                    try:
                        self.console_dock.hide()
                        self.console_dock.setParent(None)
                        self.console_dock.deleteLater()
                    except Exception:
                        pass
                    self.console_dock = None
                self._tab_factories['chat'] = lambda: self._create_chat_tab_widget()
                self.pane_manager.ensure_tab('chat', 'Chat', self._tab_factories['chat'])
        except Exception as e:
            main_logger.error(f"Failed toggling chat mode: {e}")

    def _toggle_diff_mode(self):
        """Switch diff between dock and tab modes."""
        try:
            if self.diff_as_tab:
                # Switch to dock mode
                self.diff_as_tab = False
                if 'diff' in self.pane_manager.list_tabs():
                    self.pane_manager.close_tab('diff')
                self._create_diff_dock()
            else:
                self.diff_as_tab = True
                if hasattr(self, 'diff_dock') and self.diff_dock:
                    try:
                        self.diff_dock.hide()
                        self.diff_dock.setParent(None)
                        self.diff_dock.deleteLater()
                    except Exception:
                        pass
                self._tab_factories['diff'] = lambda: self._create_diff_tab_widget()
                self.pane_manager.ensure_tab('diff', 'Diff', self._tab_factories['diff'])
        except Exception as e:
            main_logger.error(f"Failed toggling diff mode: {e}")

    def _reset_layout(self):
        """Reset pane layout to a single stack and reopen base tabs."""
        try:
            # Reset panes to a single empty stack
            self.pane_manager.restore({'type': 'stack', 'tabs': []}, self._tab_factories)
            # Ensure primary tabs
            self.code_editor = self.pane_manager.ensure_tab('editor', 'Editor', self._tab_factories['editor'])
            if self.chat_as_tab:
                self.pane_manager.ensure_tab('chat', 'Chat', self._tab_factories.get('chat', self._create_chat_tab_widget))
            if self.diff_as_tab:
                self.pane_manager.ensure_tab('diff', 'Diff', self._tab_factories['diff'])
            # Persist immediately
            try:
                pane_state = self.pane_manager.serialize()
                dock_visibility = {
                    'repository': self.repo_dock.isVisible() if hasattr(self, 'repo_dock') else False,
                    'assistant': self.console_dock.isVisible() if hasattr(self, 'console_dock') else False,
                    'diff': self.diff_dock.isVisible() if hasattr(self, 'diff_dock') else False,
                    'artifacts': self.artifacts_dock.isVisible() if hasattr(self, 'artifacts_dock') else False,
                    'exec': self.exec_log_dock.isVisible() if hasattr(self, 'exec_log_dock') else False,
                    'plan': self.plan_dock.isVisible() if hasattr(self, 'plan_dock') else False,
                    'tokens': self.token_dock.isVisible() if hasattr(self, 'token_dock') else False,
                }
                self.config_manager.set_layout_state({'panes': pane_state, 'docks': dock_visibility})
            except Exception:
                pass
            self.status_bar.showMessage("Layout reset", 2000)
        except Exception as e:
            main_logger.error(f"Failed to reset layout: {e}")

    def _setup_toolbar(self):
        """Setup toolbar with project, file, AI and control actions.

        Uses custom theme-aware vector icons for a tailored look.
        """
        theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.toolbar_main = toolbar

        def add(action: QAction, handler):
            action.triggered.connect(handler)
            toolbar.addAction(action)
            return action

        # Repo
        self.action_open_repo = QAction(make_icon('folder-open', theme), "Open Repo", self)
        add(self.action_open_repo, self._open_repository)
        toolbar.addSeparator()

        # File
        self.action_save = QAction(make_icon('save', theme), "Save", self)
        add(self.action_save, self._save_current_file)
        self.action_view_diff = QAction(make_icon('diff', theme), "View Changes", self)
        self.action_view_diff.setToolTip("Show unsaved changes for current file")
        add(self.action_view_diff, self._show_local_diff)
        toolbar.addSeparator()

        # AI
        self.action_send = QAction(make_icon('send', theme), "Send", self)
        add(self.action_send, self._send_prompt)
        toolbar.addSeparator()

        # Tasks (placeholder uses 'diff' icon for now)
        self.action_ai_edit = QAction(make_icon('diff', theme), "AI Edit", self)
        add(self.action_ai_edit, self._run_edit_task)

        # Interrupt
        self.action_interrupt = QAction(make_icon('stop', theme), "Interrupt", self)
        self.action_interrupt.setToolTip("Interrupt current AI turn")
        add(self.action_interrupt, self._send_interrupt)

        # Quick reasoning toggle
        self.action_reasoning = QAction(make_icon('bulb', theme), "Reasoning", self)
        self.action_reasoning.setCheckable(True)
        self.action_reasoning.setChecked(True)
        self.action_reasoning.triggered.connect(self._toggle_raw_reasoning)
        toolbar.addAction(self.action_reasoning)

    def _apply_toolbar_icons(self, theme: str):
        """Refresh toolbar icons when the theme changes."""
        try:
            if hasattr(self, 'action_open_repo'):
                self.action_open_repo.setIcon(make_icon('folder-open', theme))
            if hasattr(self, 'action_save'):
                self.action_save.setIcon(make_icon('save', theme))
            if hasattr(self, 'action_view_diff'):
                self.action_view_diff.setIcon(make_icon('diff', theme))
            if hasattr(self, 'action_send'):
                self.action_send.setIcon(make_icon('send', theme))
            if hasattr(self, 'action_ai_edit'):
                self.action_ai_edit.setIcon(make_icon('diff', theme))
            if hasattr(self, 'action_interrupt'):
                self.action_interrupt.setIcon(make_icon('stop', theme))
            if hasattr(self, 'action_reasoning'):
                self.action_reasoning.setIcon(make_icon('bulb', theme))
        except Exception:
            pass

    def _show_local_diff(self):
        """Show unified diff of unsaved changes in the current editor file."""
        try:
            import difflib
            current_file = self.code_editor.get_current_file_path()
            if not current_file:
                QMessageBox.information(self, "No File", "Open a file in the editor to view changes.")
                return
            before = (self.code_editor.editor.original_content or "").splitlines(keepends=True)
            after = self.code_editor.editor.toPlainText().splitlines(keepends=True)
            from_label = f"a/{Path(current_file).name}"
            to_label = f"b/{Path(current_file).name}"
            diff_lines = list(difflib.unified_diff(before, after, fromfile=from_label, tofile=to_label, n=3))
            diff_text = "".join(diff_lines)
            if not diff_text.strip():
                QMessageBox.information(self, "No Changes", "No unsaved changes to show.")
                return
            self._get_or_create_diff_viewer().set_diff_content(diff_text, current_file)
            self._show_diff_viewer()
        except Exception as e:
            QMessageBox.warning(self, "Diff Error", f"Failed to compute diff: {e}")

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()

        # Backend status
        self.backend_status_label = QLabel("Backend: Disconnected")
        self.status_bar.addWidget(self.backend_status_label)

        # Repository status
        self.repo_status_label = QLabel("No repository")
        self.status_bar.addWidget(self.repo_status_label)

        # Working directory status
        self.cwd_status_label = QLabel("Dir: Project")
        self.status_bar.addWidget(self.cwd_status_label)

        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def _load_initial_state(self):
        """Hydrate UI with any persisted session data after widgets exist."""
        try:
            if getattr(self, 'conversation_store', None) and getattr(self.conversation_store, 'session', None):
                loaded_msgs = self.conversation_store.get_messages()
                if hasattr(self, 'chat_view') and self.chat_view:
                    from .components.chat.chat_view import ChatMessage
                    self.chat_view.set_messages([
                        ChatMessage(role=m.role, content=m.content, timestamp=m.timestamp, rich=m.rich)
                        for m in loaded_msgs
                    ])
        except Exception as e:
            main_logger.warning(f"Initial hydration failed: {e}")

    def _load_repository_files(self, repo_path: str):
        """Load repository files into tree view"""
        # FileTree integration: if new FileTree is present, delegate and return
        try:
            if hasattr(self, 'file_tree') and self.file_tree:
                self.file_tree.set_root(repo_path)
                if hasattr(self, 'repo_info_label') and self.repo_info_label:
                    self.repo_info_label.setText(f"Repository: {Path(repo_path).name}")
                return
        except Exception:
            pass

        # Fallback to legacy repo_tree (kept for backward compatibility)
        self.repo_tree.clear()

        try:
            repo_path_obj = Path(repo_path)

            def add_items(parent_item, path):
                for item_path in sorted(path.iterdir()):
                    if item_path.name.startswith('.'):
                        continue  # Skip hidden files

                    item = QTreeWidgetItem(parent_item)
                    item.setText(0, item_path.name)

                    if item_path.is_dir():
                        item.setText(0, f"ðŸ“ {item_path.name}")
                        # Add dummy child to make it expandable
                        dummy = QTreeWidgetItem(item)
                        dummy.setText(0, "Loading...")
                    else:
                        item.setText(0, f"ðŸ“„ {item_path.name}")

                    # Store full path
                    item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))

                    if item_path.is_dir():
                        add_items(item, item_path)

            root_item = QTreeWidgetItem(self.repo_tree)
            root_item.setText(0, repo_path_obj.name)
            root_item.setData(0, Qt.ItemDataRole.UserRole, str(repo_path_obj))

            add_items(root_item, repo_path_obj)
            self.repo_tree.expandItem(root_item)

            # Post-process: replace emoji prefixes and apply standard icons
            try:
                self._apply_standard_icons_to_repo_tree(root_item)
            except Exception as e2:
                main_logger.warning(f"Icon post-process failed: {e2}")

        except Exception as e:
            self._add_message("system", f"Error loading repository files: {str(e)}")

    def _open_repository(self):
        """Open a repository directory and initialize context.

        - Prompts user to select a directory.
        - Populates repository tree.
        - Updates status / labels.
        - Sends override_turn_context to backend so future turns use this cwd.
        """
        from PySide6.QtWidgets import QFileDialog
        try:
            directory = QFileDialog.getExistingDirectory(self, "Select Repository Directory", "")
            if not directory:
                return

            repo_path = Path(directory).resolve()
            if not repo_path.exists() or not repo_path.is_dir():
                QMessageBox.warning(self, "Invalid Directory", "Selected path is not a directory")
                return

            # Create / store repository model
            self.current_repository = Repository(path=str(repo_path), name=repo_path.name)

            # Update UI
            self.repo_info_label.setText(f"Repository: {repo_path.name}")
            self.repo_status_label.setText(repo_path.name)
            self.cwd_status_label.setText(f"Dir: {repo_path.name}")

            # Populate tree (use FileTree component)
            try:
                if hasattr(self, 'file_tree') and self.file_tree:
                    self.file_tree.set_root(str(repo_path))
            except Exception as e2:
                main_logger.warning(f"Could not update FileTree root: {e2}")

            # Emit signal
            self.repository_opened.emit(str(repo_path))

            # Persist to config (recent repositories list + last opened time)
            try:
                self.config_manager.add_repository(self.current_repository)
                self.config_manager.update_repository_last_opened(str(repo_path))
            except Exception as e:
                main_logger.warning(f"Failed to persist repository: {e}")

            # Inform backend of new working directory
            if self.backend:
                try:
                    op = Operation.create_override_turn_context(str(repo_path))
                    self.backend.send_op(op.model_dump())
                    self._add_message("system", f"📂 Working directory set to <code>{repo_path}</code>", rich=True)
                except Exception as e:
                    main_logger.error(f"Failed to send override_turn_context: {e}")

            self.status_bar.showMessage(f"Opened repository: {repo_path}", 3000)
        except Exception as e:
            main_logger.error(f"_open_repository error: {e}", exc_info=True)
            QMessageBox.critical(self, "Open Repository Failed", f"Could not open repository: {e}")

    def _restore_last_repository(self):
        """Restore the most recently opened repository into the FileTree and status."""
        try:
            recents = self.config_manager.get_recent_repositories(limit=1)
            if not recents:
                return
            repo = recents[0]
            if not repo.path:
                return
            repo_path = Path(repo.path)
            if not repo_path.exists() or not repo_path.is_dir():
                return
            # Set current repository and update UI + FileTree
            self.current_repository = Repository(path=str(repo_path), name=repo_path.name, last_opened=repo.last_opened)
            if hasattr(self, 'repo_info_label') and self.repo_info_label:
                self.repo_info_label.setText(f"Repository: {repo_path.name}")
            if hasattr(self, 'repo_status_label') and self.repo_status_label:
                self.repo_status_label.setText(repo_path.name)
            if hasattr(self, 'cwd_status_label') and self.cwd_status_label:
                self.cwd_status_label.setText(f"Dir: {repo_path.name}")
            if hasattr(self, 'file_tree') and self.file_tree:
                self.file_tree.set_root(str(repo_path))
            # Emit and inform backend context
            try:
                self.repository_opened.emit(str(repo_path))
            except Exception:
                pass
            try:
                if self.backend:
                    op = Operation.create_override_turn_context(str(repo_path))
                    self.backend.send_op(op.model_dump())
            except Exception:
                pass
        except Exception as e:
            main_logger.warning(f"_restore_last_repository failed: {e}")

    def _apply_standard_icons_to_repo_tree(self, item: QTreeWidgetItem):
        """Ensure file tree items use platform icons and clean any mojibake text."""
        stack = [item]
        while stack:
            it = stack.pop()
            text = it.text(0)
            data_path = it.data(0, Qt.ItemDataRole.UserRole)

            if isinstance(text, str) and (text.startswith("ð") or text.startswith("�")):
                # Replace with actual filename if available
                if data_path:
                    it.setText(0, Path(str(data_path)).name)

            # Apply icons based on path/children
            try:
                if data_path and Path(str(data_path)).is_dir():
                    it.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                elif data_path and Path(str(data_path)).is_file():
                    it.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            except Exception:
                pass

            for i in range(it.childCount()):
                stack.append(it.child(i))

    def _on_file_clicked(self, item, column):
        """Handle file click in repository tree"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path and Path(file_path).is_file():
            self._load_file_into_editor(file_path)

    def _load_file_into_editor(self, file_path: str):
        """Load a file into the code editor with safety checks"""
        try:
            pm = getattr(self, 'pane_manager', None)
            if not pm:
                main_logger.warning("PaneManager not initialized; cannot open file tab")
                return
            widget = pm.open_file_tab(file_path)
            if widget and _is_qobj_valid(widget):
                # Track as current editor for legacy flows
                self.code_editor = widget
                self.file_selected.emit(file_path)
        except Exception as e:
            main_logger.error(f"Error loading file into editor: {e}")
            try:
                QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")
            except Exception:
                pass

    def _on_artifact_double_clicked(self, item, column):
        """Handle artifact double-click"""
        # TODO: Implement artifact viewing
        pass

    def _on_apply_diff(self):
        """Apply selected hunks directly to files in the opened repository.
        - Applies per-file; editor does not need to have the file open.
        - Updates the editor if the current file was modified.
        """
        # Collect selected hunks grouped by file
        diffs_by_file = getattr(self.diff_viewer.diff_widget, 'get_selected_diffs_by_file', None)
        if callable(diffs_by_file):
            files_map = diffs_by_file()
        else:
            # Back-compat fallback
            selected = self.diff_viewer.diff_widget.get_selected_diff_text()
            files_map = {}
            if selected:
                # The patch library prefers --- a/.. +++ b/.. headers; ensure a filename
                fake = Path(self.code_editor.get_current_file_path() or "selected.patch").name
                if not selected.lstrip().startswith('---'):
                    selected = f"--- a/{fake}\n+++ b/{fake}\n" + selected
                files_map[fake] = selected

        if not files_map:
            QMessageBox.information(self, "No Changes Selected", "Please select one or more hunks to apply.")
            return

        if not self.current_repository:
            QMessageBox.warning(self, "No Repository", "Open a repository before applying changes.")
            return

        repo_root = Path(self.current_repository.path)
        modified_files = []
        errors = []

        # Apply per-file using in-memory patching to avoid bytes/str issues
        for rel_path, diff_text in files_map.items():
            try:
                # Normalize path separators to POSIX for diff headers
                rel_posix = rel_path.replace('\\', '/')
                dt = diff_text
                if not dt.lstrip().startswith('---'):
                    dt = f"--- a/{rel_posix}\n+++ b/{rel_posix}\n" + dt

                target_path = (repo_root / rel_path).resolve()
                original_bytes = b""
                if target_path.exists():
                    original_bytes = target_path.read_bytes()

                try:
                    pset = patch.fromstring(dt)
                    patched_bytes = pset.apply(original_bytes)
                except AttributeError:
                    # Some versions require bytes in from_string
                    pset = patch.from_string(dt.encode('utf-8'))
                    patched_bytes = pset.apply(original_bytes)

                if not patched_bytes:
                    errors.append(f"{rel_path}: failed to apply selected hunks")
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(patched_bytes)
                modified_files.append(str(target_path))
            except Exception as e:
                errors.append(f"{rel_path}: {e}")

        if modified_files and not errors:
            self.status_bar.showMessage(f"Applied changes to {len(modified_files)} file(s)", 3000)
            # Refresh editor if current file modified
            cur = self.code_editor.get_current_file_path()
            if cur and any(Path(cur).resolve() == Path(p).resolve() for p in modified_files):
                self.code_editor.load_file(cur)
            # Pulse-highlight changed files in tree
            try:
                if hasattr(self, 'file_tree') and self.file_tree:
                    self.file_tree.highlight_paths(modified_files)
            except Exception:
                pass
        else:
            QMessageBox.critical(self, "Patch Failed", "No changes were applied.")

        if errors:
            self._add_message("system", "Some patches failed:\n" + "\n".join(errors))

    def _send_prompt(self):
        """Send a prompt to the AI backend."""
        main_logger.info("_send_prompt() called")
        prompt = self.prompt_input.toPlainText().strip()
        main_logger.info(f"Prompt text: '{prompt}' (length: {len(prompt)})")

        if not prompt:
            main_logger.info("Prompt is empty, returning")
            return

        try:
            GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'user', 'content': prompt})
        except Exception:
            self._add_message("user", prompt)
        self.prompt_input.clear()

        try:
            if not self.backend:
                main_logger.error("Backend is None")
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '❌ Backend not connected. Please check configuration.'})
                except Exception:
                    self._add_message("system", "❌ Backend not connected. Please check configuration.")
                return

            main_logger.info("Backend is available, preparing operation")

            # Prepare context with improved directory detection
            repo_context = {}
            cwd_path = None
            if self.current_repository:
                repo_context["repository_path"] = self.current_repository.path
                cwd_path = self.current_repository.path
                main_logger.info(f"Repository context: {repo_context}")
            else:
                # Improved directory detection logic
                current_file = self.code_editor.get_current_file_path()

                if current_file:
                    # Use directory of currently open file
                    import os
                    from pathlib import Path
                    file_dir = str(Path(current_file).parent)
                    cwd_path = file_dir
                    main_logger.info(f"Using directory of current file: {cwd_path}")
                else:
                    # Use AI Workbench project directory as fallback instead of os.getcwd()
                    import os
                    from pathlib import Path
                    # Get the directory containing the ai-workbench project
                    workbench_dir = Path(__file__).parent.parent.parent  # ai-workbench/aiw/ui/main_window.py -> ai-workbench/
                    cwd_path = str(workbench_dir)
                    main_logger.info(f"No repository or file selected, using AI Workbench directory: {cwd_path}")

                repo_context["repository_path"] = cwd_path

            # Update working directory status
            import os
            from pathlib import Path
            cwd_display = Path(cwd_path).name if len(cwd_path) > 30 else cwd_path
            self.cwd_status_label.setText(f"Dir: {cwd_display}")

            # Determine operation type - use user_turn with working directory
            current_file = self.code_editor.get_current_file_path()
            main_logger.info(f"Current file: {current_file}")

            # Use user_turn operation with working directory
            if cwd_path:
                # Ensure path uses forward slashes for JSON compatibility
                normalized_cwd = cwd_path.replace("\\", "/")
                if current_file:
                    # Include file context in the prompt text
                    enhanced_prompt = f"Regarding the file '{Path(current_file).name}': {prompt}"
                    op = Operation.create_user_turn(enhanced_prompt, normalized_cwd)
                    try:
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"📜 Sending request for {Path(current_file).name}..."})
                    except Exception:
                        self._add_message("system", f"📜 Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user turn operation with file context for: {current_file}")
                    main_logger.info(f"Working directory context: {normalized_cwd}")
                else:
                    op = Operation.create_user_turn(prompt, normalized_cwd)
                    try:
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '💬 Sending general prompt...'})
                    except Exception:
                        self._add_message("system", "💬 Sending general prompt...")
                    main_logger.info(f"Created user turn operation with working directory: {normalized_cwd}")
            else:
                # Fallback to user_input if no repository is selected
                if current_file:
                    enhanced_prompt = f"Regarding the file '{Path(current_file).name}': {prompt}"
                    op = Operation.create_user_input(enhanced_prompt)
                    try:
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"📜 Sending request for {Path(current_file).name}..."})
                    except Exception:
                        self._add_message("system", f"📜 Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user input operation with file context for: {current_file}")
                else:
                    op = Operation.create_user_input(prompt)
                    try:
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '💬 Sending general prompt...'})
                    except Exception:
                        self._add_message("system", "💬 Sending general prompt...")
                    main_logger.info("Created user input operation")

            op.context = repo_context

            # Override model in operation with profile-configured model if available
            try:
                codex_cfg = get_codex_config_manager().load()
                profile_model = None
                
                # Get model from current profile if one is active
                if self.current_profile and codex_cfg.profiles:
                    profile_config = codex_cfg.profiles.get(self.current_profile)
                    profile_model = profile_config.get('model') if profile_config else None
                    if profile_model:
                        main_logger.info(f"Found model '{profile_model}' in profile '{self.current_profile}'")
                
                # Fallback to general config model if no profile model
                if not profile_model and codex_cfg.model:
                    profile_model = codex_cfg.model
                    main_logger.info(f"Using general config model '{profile_model}'")
                
                # Apply model override if we found one
                if profile_model:
                    prev_model = op.op.get('model')
                    op.op['model'] = profile_model
                    if prev_model != profile_model:
                        main_logger.info(
                            f"Replaced operation model '{prev_model}' with configured model '{profile_model}'"
                        )
            except Exception as e:
                main_logger.warning(f"Could not apply configured model override: {e}")

            # Apply UI overrides: model selector and temperature slider
            try:
                # Model selector (takes ultimate precedence if set)
                if getattr(self, '_model_override', None):
                    prev_model = op.op.get('model')
                    op.op['model'] = self._model_override
                    if prev_model != self._model_override:
                        main_logger.info(f"UI model override applied: '{prev_model}' -> '{self._model_override}'")
            except Exception as e:
                main_logger.warning(f"Failed applying UI model override: {e}")

            try:
                # Temperature (0.0 - 1.0); backend may ignore if unsupported
                t = getattr(self, '_temp_override', None)
                if t is not None:
                    op.op['temperature'] = float(t)
                    main_logger.info(f"Applied temperature override: {t}")
            except Exception as e:
                main_logger.warning(f"Failed applying temperature override: {e}")

            # Log the full operation for debugging
            op_json = op.model_dump_json(indent=2)
            main_logger.info(f"Operation JSON: {op_json}")
            # Publish op preview (bus only)
            GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"<i>Sending op:</i> <pre>{op_json}</pre>", 'rich': True})

            main_logger.info("Calling backend.send_op()")
            # Begin streaming indicator immediately
            try:
                if hasattr(self, 'chat_view') and self.chat_view:
                    self.chat_view.set_streaming(True)
            except Exception:
                pass
            result = self.backend.send_op(op.model_dump())
            main_logger.info(f"backend.send_op() returned: {result}")
            self.status_bar.showMessage("Waiting for AI response...", 0)
        except Exception as e:
            main_logger.error(f"Exception in _send_prompt: {str(e)}", exc_info=True)
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Error sending prompt: {str(e)}"})
            except Exception:
                pass
            self.status_bar.clearMessage()

    def _add_message(self, role: str, content: str, rich: bool = False):
        """(Internal) Final render endpoint for chat messages (event bus subscriber)."""
        norm_role = role if role in ("user", "assistant", "system") else ("assistant" if role == "agent" else "system")
        
        # Try the stored actual ChatView first
        if hasattr(self, '_actual_chat_view') and self._actual_chat_view is not None:
            try:
                if _is_qobj_valid(self._actual_chat_view):
                    self._actual_chat_view.add_message(norm_role, content, rich=rich)
                    return
                else:
                    self._actual_chat_view = None
            except Exception as e:
                main_logger.warning(f"Failed to add message to _actual_chat_view: {e}")
        
        try:
            if _is_qobj_valid(getattr(self, 'chat_view', None)):
                self.chat_view.add_message(norm_role, content, rich=rich)
            elif _is_qobj_valid(getattr(self, 'chat_console', None)):
                self.chat_console.add_message(norm_role, content, rich=rich)  # type: ignore[attr-defined]
        except Exception:
            try:
                self.chat_console.add_message(norm_role, content, rich=rich)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _emit_chat(self, role: str, content: str, rich: bool = False):
        """Publish a chat/system message to the event bus (preferred path)."""
        GLOBAL_EVENT_BUS.publish('chat.message', {'role': role, 'content': content, 'rich': rich})

    def _apply_theme(self):
        """Apply new token-based theme; fallback to legacy system if needed."""
        theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
        theme = theme if theme in ("dark", "light") else "dark"
        try:
            tokens_apply_theme(theme)
        except Exception as e:
            main_logger.warning(f"Token theme failed: {e}; falling back to legacy theme")
            try:
                legacy_apply_theme(self, theme=theme, base_font_pt=10.0)
            except Exception as e2:
                main_logger.error(f"Legacy theme failed: {e2}")
        # Refresh toolbar glyphs under the current theme
        self._apply_toolbar_icons(theme)

    def _set_theme(self, theme: str):
        try:
            self.config_manager.config.ui.theme = theme
            self.config_manager.save_config()
        except Exception:
            pass
        self._apply_theme()
        
        # Refresh chat view theme
        try:
            if hasattr(self, 'chat_view') and self.chat_view:
                self.chat_view.refresh_theme()
            if hasattr(self, '_actual_chat_view') and self._actual_chat_view:
                self._actual_chat_view.refresh_theme()
            # Toolbar icons too
            self._apply_toolbar_icons(theme)
        except Exception as e:
            main_logger.error(f"Failed to refresh chat theme: {e}")
            
        # Update enhanced component themes
        try:
            # Update diff viewer theme
            if hasattr(self, 'diff_viewer') and self.diff_viewer:
                self.diff_viewer.set_theme(theme)
                
            # Update all code editor widgets in dock widgets
            for dock in self.findChildren(QDockWidget):
                widget = dock.widget()
                if hasattr(widget, 'set_theme'):
                    widget.set_theme(theme)
                    
            # Update components in the pane manager
            if hasattr(self, 'pane_manager') and self.pane_manager:
                for tab_widget in self.pane_manager.findChildren(QWidget):
                    if hasattr(tab_widget, 'set_theme'):
                        tab_widget.set_theme(theme)
                        
        except Exception as e:
            main_logger.error(f"Failed to update enhanced component themes: {e}")

    def _run_test_task(self):
        """Run tests for the current project."""
        if not self.current_repository:
            QMessageBox.warning(self, "No Repository", "Please select a repository first.")
            return
        task = Task(
            id=f"test_{int(time.time())}",
            name="Run Tests",
            type="run_tests",
            parameters={
                "command": ["pytest", "-v"],
                "repository_path": str(self.current_repository.path)
            }
        )
        self.task_runner.run_single_task(task)

    def _start_login(self):
        """Start ChatGPT login process"""
        if self.backend:
            op = Operation.create_login_request()
            self.backend.send_op(op.model_dump())

    def _save_current_file(self):
        """Save the current file"""
        if self.code_editor.has_changes():
            success = self.code_editor.save_file()
            if success:
                self.status_bar.showMessage("File saved successfully", 3000)
            else:
                self.status_bar.showMessage("Failed to save file", 3000)

    def _save_file_as(self):
        """Save the current file with a new name"""
        from PySide6.QtWidgets import QFileDialog

        current_path = self.code_editor.get_current_file_path()
        if current_path:
            suggested_name = Path(current_path).name
        else:
            suggested_name = "untitled.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As",
            suggested_name,
            "All Files (*.*)"
        )

        if file_path:
            success = self.code_editor.editor.save_file_as(file_path)
            if success:
                self.editor_file_label.setText(f"File: {self.code_editor.editor.get_current_file_name()}")
                self.status_bar.showMessage("File saved successfully", 3000)
            else:
                self.status_bar.showMessage("Failed to save file", 3000)

    @Slot(dict)
    def _on_backend_event(self, event):
        """Handle backend events"""
        main_logger.info(f"_on_backend_event called with event: {event}")
        event_obj = event.get("msg", {})
        event_type = event_obj.get("type")
        task_id = event.get("id", "")
        main_logger.debug(f"Event type: {event_type}, Task ID: {task_id}")

        # Publish raw backend event
        try:
            GLOBAL_EVENT_BUS.publish('backend.raw', event)
        except Exception:
            pass

        # Handle reasoning deltas (accumulate them)
        if event_type == "agent_reasoning_delta":
            delta = event_obj.get("delta", "")
            if self.show_raw_reasoning:
                self.current_reasoning += delta
            try:
                if hasattr(self, 'chat_view'):
                    self.chat_view.set_streaming(True)
            except Exception:
                pass

        # Handle reasoning section break (merge into assistant message)
        elif event_type == "agent_reasoning_section_break":
            if self.show_raw_reasoning and self.current_reasoning.strip():
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    # Add reasoning as part of the current assistant message stream
                    reasoning_text = f"\n\n*Thinking: {clean_reasoning}*\n\n"
                    try:
                        if hasattr(self, 'chat_view'):
                            self.chat_view.append_assistant_delta(reasoning_text)
                        if self.conversation_store:
                            self.conversation_store.update_last_assistant_partial(reasoning_text)
                        self._schedule_conversation_flush()
                    except Exception:
                        pass
                self.current_reasoning = ""

        # Handle message deltas (accumulate them)
        elif event_type == "agent_message_delta":
            delta = event_obj.get("delta", "")
            self.current_message += delta
            try:
                if hasattr(self, 'chat_view'):
                    self.chat_view.set_streaming(True)
            except Exception:
                pass
            try:
                if hasattr(self, 'chat_view'):
                    self.chat_view.append_assistant_delta(delta)
                if self.conversation_store:
                    self.conversation_store.update_last_assistant_partial(delta)
                self._schedule_conversation_flush()
            except Exception:
                pass
            try:
                GLOBAL_EVENT_BUS.publish('chat.streaming_delta', {'delta': delta})
            except Exception:
                pass

        # Handle complete agent messages (direct message without deltas)
        elif event_type == "agent_message":
            message = event_obj.get("message", "")
            if message.strip():
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'assistant', 'content': message})
                except Exception as e:
                    main_logger.error(f"Failed to publish agent_message to event bus: {e}")
                    self._add_message("assistant", message)
            # Stop typing indicator if backend does not send task_complete
            try:
                if hasattr(self, 'chat_view') and self.chat_view:
                    self.chat_view.set_streaming(False)
            except Exception:
                pass

        # Handle task completion (display accumulated message)
        elif event_type == "task_complete":
            try:
                if hasattr(self, "chat_view"):
                    self.chat_view.set_streaming(False)
            except Exception:
                pass
            # Include any final reasoning in the assistant message
            final_content = ""
            if self.current_message.strip():
                final_content = self.current_message.strip()
            if self.show_raw_reasoning and self.current_reasoning.strip():
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    if final_content:
                        final_content += f"\n\n*Final thinking: {clean_reasoning}*"
                    else:
                        final_content = f"*Thinking: {clean_reasoning}*"
            
            if final_content:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'assistant', 'content': final_content})
                except Exception:
                    self._add_message("assistant", final_content)
            
            # Reset accumulators
            self.current_message = ""
            self.current_reasoning = ""

            # If backend doesn't emit token_count, estimate now
            try:
                self._handle_token_count({})
            except Exception:
                pass

        # Handle unified diff for the entire turn (codex-rs EventMsg::TurnDiff)
        elif event_type == "turn_diff":
            unified_diff = event_obj.get("unified_diff", "")
            if unified_diff:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': 'Received changes for this turn.'})
                    GLOBAL_EVENT_BUS.publish('diff.update', {'unified_diff': unified_diff})
                except Exception:
                    self._add_message("system", "Received changes for this turn.")
                self._get_or_create_diff_viewer().set_diff_content(unified_diff, "")
                self._show_diff_viewer()
            else:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': 'No changes in this turn.'})
                except Exception:
                    self._add_message("system", "No changes in this turn.")

        # Handle agent edit file response (the diff)
        elif event_type == "agent_edit_file_response":
            diff = event_obj.get("diff", "")
            file_path = event_obj.get("file_path", "unknown_file")
            if diff:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"✅ Received diff for {file_path}"})
                    GLOBAL_EVENT_BUS.publish('diff.update', {'diff': diff, 'file_path': file_path})
                except Exception:
                    self._add_message("system", f"✅ Received diff for {file_path}")
                self._get_or_create_diff_viewer().set_diff_content(diff, file_path)
                self._show_diff_viewer()  # Bring the diff dock to the front
            else:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"⚠️ Received an empty diff for {file_path}"})
                except Exception:
                    self._add_message("system", f"⚠️ Received an empty diff for {file_path}")

        # Handle login events
        elif event_type == "login_chat_gpt_response":
            auth_url = event_obj.get("auth_url")
            if auth_url:
                import webbrowser
                webbrowser.open(auth_url)
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '🗝️ Please complete the login in your browser.'})
                except Exception:
                    self._add_message("system", "🗝️ Please complete the login in your browser.")

        elif event_type == "login_chat_gpt_complete":
            if event_obj.get("success"):
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Login successful!'})
                except Exception:
                    self._add_message("system", "✅ Login successful!")
            else:
                error = event_obj.get("error", "Unknown error")
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Login failed: {error}"})
                except Exception:
                    self._add_message("system", f"❌ Login failed: {error}")

        # Handle task started (clear any previous accumulations)
        elif event_type == "task_started":
            # Clear any accumulated messages from previous tasks
            self.current_reasoning = ""
            self.current_message = ""
            self.last_task_id = task_id

        # Handle patch approval requests
        elif event_type == "apply_patch_approval_request":
            # Surface diffs in viewer for review
            try:
                changes = event_obj.get("changes", {}) or {}
                combined = []
                for file_path, change in changes.items():
                    if isinstance(change, dict) and "update" in change:
                        udiff = change.get("update", {}).get("unified_diff", "")
                        if udiff:
                            combined.append(f"--- a/{file_path}\n+++ b/{file_path}\n{udiff}\n")
                if combined:
                    self._get_or_create_diff_viewer().set_diff_content("\n".join(combined), "")
                    self._show_diff_viewer()
            except Exception:
                pass
            self._handle_patch_approval_request(event_obj, task_id)

        # Handle exec approval requests
        elif event_type == "exec_approval_request":
            self._handle_exec_approval_request(event_obj, task_id)

        # Handle MCP tool calls
        elif event_type == "mcp_tool_call_begin":
            self._handle_mcp_tool_call_begin(event_obj)

        elif event_type == "mcp_tool_call_end":
            self._handle_mcp_tool_call_end(event_obj)

        # Handle token count updates
        elif event_type == "token_count":
            try:
                GLOBAL_EVENT_BUS.publish('tokens.update', event_obj)
            except Exception:
                pass
            self._handle_token_count(event_obj)

        # Handle session configured
        elif event_type == "session_configured":
            self._handle_session_configured(event_obj)

        elif event_type == "patch_apply_begin":
            self._handle_patch_apply_begin(event_obj)
        elif event_type == "patch_apply_end":
            self._handle_patch_apply_end(event_obj)
        elif event_type == "exec_command_begin":
            self._handle_exec_command_begin(event_obj)
        elif event_type == "exec_command_output_delta":
            self._handle_exec_command_output_delta(event_obj)
        elif event_type == "exec_command_end":
            self._handle_exec_command_end(event_obj)
        elif event_type == "plan_update":
            try:
                GLOBAL_EVENT_BUS.publish('plan.update', event_obj)
            except Exception:
                pass
            self._handle_plan_update(event_obj)
        elif event_type == "web_search_begin":
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '🔍 Web search started'})
            except Exception:
                self._add_message("system", "🔍 Web search started")
        elif event_type == "web_search_end":
            query = event_obj.get("query", "")
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"🔍 Web search finished: {query}"})
            except Exception:
                self._add_message("system", f"🔍 Web search finished: {query}")
        elif event_type in ("agent_reasoning_raw_content", "agent_reasoning_raw_content_delta"):
            self._handle_raw_reasoning(event_type, event_obj)
        elif event_type == "stream_error":
            self._handle_stream_error(event_obj)
        elif event_type == "turn_aborted":
            self._handle_turn_aborted(event_obj)
        elif event_type == "conversation_history":
            messages = event_obj.get("messages", [])
            self._handle_conversation_history(messages)

        # Show other events only if they contain useful information
        else:
            # Only show events that might be relevant to the user, but log them for debugging
            if event_type not in ["mcp_connection_manager", "agent_reasoning_delta", "agent_message_delta"]:
                main_logger.debug(f"Unhandled Event: {event_type}")

    # New handlers
    def _handle_patch_apply_begin(self, event_obj):
        try:
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '📦 Applying patch...'})
            except Exception:
                self._add_message("system", "📦 Applying patch...")
            self.status_bar.showMessage("Applying patch...", 3000)
        except Exception as e:
            main_logger.error(f"Error in patch_apply_begin: {e}")

    def _handle_patch_apply_end(self, event_obj):
        try:
            success = event_obj.get("success")
            stdout = event_obj.get("stdout", "")
            stderr = event_obj.get("stderr", "")
            if success:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Patch applied successfully'})
                except Exception:
                    self._add_message("system", "✅ Patch applied successfully")
            else:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Patch apply failed: {stderr[:200]}"})
                except Exception:
                    self._add_message("system", f"❌ Patch apply failed: {stderr[:200]}")
            if stdout:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"<details><summary>Patch output</summary><pre>{stdout[:4000]}</pre></details>", 'rich': True})
                except Exception:
                    self._add_message("system", f"<details><summary>Patch output</summary><pre>{stdout[:4000]}</pre></details>", rich=True)
            if stderr and not success:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"<details><summary>Patch errors</summary><pre>{stderr[:4000]}</pre></details>", 'rich': True})
                except Exception:
                    self._add_message("system", f"<details><summary>Patch errors</summary><pre>{stderr[:4000]}</pre></details>", rich=True)
        except Exception as e:
            main_logger.error(f"Error in patch_apply_end: {e}")

    def _handle_exec_command_begin(self, event_obj):
        try:
            cmd = event_obj.get("command") or ' '.join(event_obj.get("argv", []))
            self.exec_output_view.clear()
            self.exec_log_dock.show()
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"🛠️ Exec started: <code>{cmd}</code>", 'rich': True})
            except Exception:
                self._add_message("system", f"🛠️ Exec started: <code>{cmd}</code>", rich=True)
            self.exec_output_view.append(f"$ {cmd}\n")
        except Exception as e:
            main_logger.error(f"Error in exec_command_begin: {e}")

    def _handle_exec_command_output_delta(self, event_obj):
        try:
            delta = event_obj.get("delta", "")
            if delta:
                self.exec_output_view.moveCursor(self.exec_output_view.textCursor().End)
                self.exec_output_view.insertPlainText(delta)
        except Exception as e:
            main_logger.error(f"Error in exec_command_output_delta: {e}")

    def _handle_exec_command_end(self, event_obj):
        try:
            exit_code = event_obj.get("exit_code")
            formatted = event_obj.get("formatted_output")
            if formatted:
                self.exec_output_view.append("\n--- formatted output ---\n" + formatted)
            if exit_code == 0:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Exec finished successfully'})
                except Exception:
                    self._add_message("system", "✅ Exec finished successfully")
            else:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"⚠️ Exec ended with code {exit_code}"})
                except Exception:
                    self._add_message("system", f"⚠️ Exec ended with code {exit_code}")
        except Exception as e:
            main_logger.error(f"Error in exec_command_end: {e}")

    def _handle_plan_update(self, event_obj):
        try:
            self.plan_dock.show()
            step = event_obj.get("step") or event_obj.get("description") or event_obj
            from datetime import datetime
            ts = datetime.now().strftime('%H:%M:%S')
            self.plan_list.addItem(f"[{ts}] {step}")
        except Exception as e:
            main_logger.error(f"Error in plan_update: {e}")

    def _handle_raw_reasoning(self, event_type, event_obj):
        try:
            if event_type.endswith('_delta'):
                delta = event_obj.get('delta', '')
                if delta:
                    self.current_reasoning += delta
                    if hasattr(self, 'reasoning_view') and self.reasoning_view.isVisible():
                        safe = delta.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                        self.reasoning_view.moveCursor(self.reasoning_view.textCursor().End)
                        self.reasoning_view.insertHtml(safe)
            else:
                text = event_obj.get('text', '')
                if text:
                    self.current_reasoning += text + "\n"
                    if hasattr(self, 'reasoning_view') and self.reasoning_view.isVisible():
                        safe_full = self.current_reasoning.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                       
                        self.reasoning_view.setHtml(f"<b>Reasoning</b><br><pre style='white-space:pre-wrap;margin:0;'>{safe_full}</pre>")
        except Exception as e:
            main_logger.error(f"Error in raw reasoning handler: {e}")

    # UX helpers
    def _toggle_reasoning_panel(self):
        self.reasoning_panel_visible = not self.reasoning_panel_visible
        if hasattr(self, 'reasoning_view'):
            try:
                if getattr(self.config_manager.config.ui, 'animations_enabled', True) and not getattr(self.config_manager.config.ui, 'prefers_reduced_motion', False):
                    animate_height_toggle(self.reasoning_view, self.reasoning_panel_visible)
                else:
                    self.reasoning_view.setVisible(self.reasoning_panel_visible)
            except Exception:
                self.reasoning_view.setVisible(self.reasoning_panel_visible)

    def _open_command_palette(self):
        try:
            from .command_palette import CommandPalette
            from .shortcuts import get_shortcut
            actions = [
                ("Toggle Theme", lambda: self._set_theme('light' if getattr(self.config_manager.config.ui,'theme','dark')=='dark' else 'dark'), get_shortcut('theme.toggle')),
                ("Focus Chat Input", lambda: (self.prompt_input.setFocus() if hasattr(self,'prompt_input') else None), get_shortcut('chat.focus')),
                ("Toggle Reasoning Panel", self._toggle_reasoning_panel, ''),
            ]
            dlg = CommandPalette(actions, self)
            dlg.exec()
        except Exception as e:
            main_logger.error(f"Failed to open command palette: {e}")

    def _handle_stream_error(self, event_obj):
        try:
            message = event_obj.get('message', 'Unknown stream error')
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Stream error: {message}"})
            except Exception:
                self._add_message('system', f"❌ Stream error: {message}")
        except Exception as e:
            main_logger.error(f"Error in stream_error handler: {e}")

    def _handle_turn_aborted(self, event_obj):
        try:
            reason = event_obj.get('reason', 'interrupted')
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"⛔ Turn aborted: {reason}"})
            except Exception:
                self._add_message('system', f"⛔ Turn aborted: {reason}")
        except Exception as e:
            main_logger.error(f"Error in turn_aborted handler: {e}")

    def _send_interrupt(self):
        try:
            if not self.backend:
                return
            op = Operation.create_interrupt()
            self.backend.send_op(op.model_dump())
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '⛔ Interrupt sent'})
            except Exception:
                self._add_message('system', '⛔ Interrupt sent')
        except Exception as e:
            main_logger.error(f"Error sending interrupt: {e}")

    @Slot(str)
    def _on_backend_error(self, error_message):
        """Handle backend errors"""
        try:
            GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"<b>Backend Error:</b> {error_message}", 'rich': True})
        except Exception:
            self._add_message("system", f"<b>Backend Error:</b> {error_message}", rich=True)
        self.backend_status_label.setText("Backend: Error")

    @Slot()
    def _on_backend_started(self):
        """Handle backend started"""
        self.backend_status_label.setText("Backend: Connected")

    def _run_edit_task(self):
        """Run an AI edit task on the current file."""
        current_file = self.code_editor.get_current_file_path()
        if not current_file:
            QMessageBox.warning(self, "No File Selected", "Please open a file in the code editor first.")
            return

        from PySide6.QtWidgets import QInputDialog
        instruction, ok = QInputDialog.getText(
            self, "AI Edit Instruction",
            "Enter your edit instruction for the current file:"
        )

        if ok and instruction:
            self.prompt_input.setPlainText(instruction)
            self._send_prompt()

    def _show_settings(self):
        """Show settings dialog"""
        dlg = SettingsDialog(self)
        if dlg.exec():
            # Refresh current profile after settings changes
            self._refresh_current_profile()
            
            if dlg.apply_and_restart_requested:
                self._restart_backend()
            else:
                # No restart requested; config changes will apply on next start
                self.status_bar.showMessage("Settings saved", 3000)

    def _refresh_current_profile(self):
        """Refresh the current profile from codex config"""
        try:
            codex_cfg_mgr = get_codex_config_manager()
            codex_cfg = codex_cfg_mgr.load()
            old_profile = self.current_profile
            self.current_profile = codex_cfg.profile
            
            if old_profile != self.current_profile:
                if self.current_profile:
                    main_logger.info(f"Profile changed from '{old_profile}' to '{self.current_profile}'")
                    self.status_bar.showMessage(f"Profile changed to: {self.current_profile}", 3000)
                else:
                    main_logger.info(f"Profile cleared (was '{old_profile}')")
                    self.status_bar.showMessage("Profile cleared", 3000)
        except Exception as e:
            main_logger.warning(f"Could not refresh profile: {e}")

    def _restart_backend(self):
        try:
            # Stop existing backend if running
            if self.backend_thread:
                try:
                    if self.backend:
                        self.backend.stop()
                except Exception:
                    pass
                self.backend_thread.quit()
                self.backend_thread.wait()
                self.backend_thread = None
                self.backend = None

            # Recreate backend with new settings
            self._setup_backend()
            self.status_bar.showMessage("Backend restarting with new settings...", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Restart Failed", f"Could not restart backend: {e}")

    def closeEvent(self, event):
        """Handle application close"""
        # Save window geometry
        geometry = {
            'geometry': self.saveGeometry(),
            'state': self.saveState()
        }
        self.config_manager.set_window_geometry(geometry)

        # Save custom layout (pane tabs + which tab active + optionally dock visibility)
        try:
            pane_state = self.pane_manager.serialize() if hasattr(self, 'pane_manager') else {}
            dock_visibility = {
                'repository': self.repo_dock.isVisible() if hasattr(self, 'repo_dock') else False,
                'assistant': self.console_dock.isVisible() if hasattr(self, 'console_dock') else False,
                'diff': self.diff_dock.isVisible() if hasattr(self, 'diff_dock') else False,
                'artifacts': self.artifacts_dock.isVisible() if hasattr(self, 'artifacts_dock') else False,
                'exec': self.exec_log_dock.isVisible() if hasattr(self, 'exec_log_dock') else False,
                'plan': self.plan_dock.isVisible() if hasattr(self, 'plan_dock') else False,
                'tokens': self.token_dock.isVisible() if hasattr(self, 'token_dock') else False,
            }
            self.config_manager.set_layout_state({'panes': pane_state, 'docks': dock_visibility})
        except Exception as e:
            main_logger.warning(f"Could not persist layout state: {e}")

        # Stop backend thread
        if self.backend_thread:
            self.backend.stop()
            self.backend_thread.quit()
            self.backend_thread.wait()

        try:
            if self.conversation_store:
                self.conversation_store.flush()
        except Exception:
            pass
        super().closeEvent(event)

    # Backend Signal Handlers
    @Slot(str)
    def _on_backend_error(self, error_message):
        """Handle backend errors"""
        main_logger.error(f"_on_backend_error called with message: {error_message}")
        self._add_message("system", f"<b>Backend Error:</b> {error_message}", rich=True)
        self.backend_status_label.setText("Backend: Error")

    @Slot()
    def _on_backend_started(self):
        """Handle backend started"""
        main_logger.info("_on_backend_started called - backend is now connected")
        self.backend_status_label.setText("Backend: Connected")

    @Slot(int)
    def _on_backend_stopped(self, exit_code):
        """Handle backend stopped"""
        main_logger.info(f"_on_backend_stopped called with exit code: {exit_code}")
        self.backend_status_label.setText("Backend: Disconnected")
        if exit_code != 0:
            self._add_message("system", f"âš ï¸ Backend stopped with exit code: {exit_code}")

    @Slot(str)
    def _on_connection_status_changed(self, status: str):
        """Handle backend connection status changes"""
        main_logger.info(f"_on_connection_status_changed called with status: {status}")
        status_messages = {
            "connecting": "Backend: Connecting...",
            "connected": "Backend: Connected",
            "disconnected": "Backend: Disconnected",
            "error": "Backend: Error"
        }

        message = status_messages.get(status, f"Backend: {status}")
        self.backend_status_label.setText(message)

        # Update progress bar based on status
        if status == "connecting":
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_bar.showMessage("Connecting to backend...", 0)
        elif status == "connected":
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("Backend connected successfully", 3000)
        elif status == "error":
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("Backend connection failed", 5000)

    @Slot(str, int, str)
    def _on_operation_progress(self, operation_id: str, progress: int, message: str):
        """Handle operation progress updates"""
        main_logger.debug(f"_on_operation_progress: {operation_id}, progress: {progress}, message: {message}")
        if progress >= 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
            self.status_bar.showMessage(f"{message}", 0)
        else:
            # Negative progress indicates completion/cancellation
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage(f"Operation {operation_id}: {message}", 3000)

    @Slot(str)
    def _on_operation_cleanup(self, operation_id: str):
        """Handle operation cleanup with delay from main thread"""
        main_logger.debug(f"_on_operation_cleanup: {operation_id}")
        # Use QTimer from main thread to clean up operation after delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(5000, lambda: self.backend._cleanup_operation(operation_id))

    # Task Runner Signal Handlers
    @Slot(str, str)
    def _on_task_started(self, workflow_id: str, task_id: str):
        """Handle task started"""
        main_logger.info(f"_on_task_started: workflow={workflow_id}, task={task_id}")
        self._add_message("system", f"ðŸ”„ Started task: {task_id}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    @Slot(str, str, object)
    def _on_task_completed(self, workflow_id: str, task_id: str, result):
        """Handle task completed"""
        main_logger.info(f"_on_task_completed: workflow={workflow_id}, task={task_id}, result={result}")
        self._add_message("system", f"âœ… Task completed: {task_id}")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Task {task_id} completed successfully", 3000)

    @Slot(str, str, str)
    def _on_task_failed(self, workflow_id: str, task_id: str, error: str):
        """Handle task failed"""
        main_logger.error(f"_on_task_failed: workflow={workflow_id}, task={task_id}, error={error}")
        self._add_message("system", f"âŒ Task failed: {task_id} - {error}")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Task {task_id} failed: {error}", 5000)

    @Slot(str, str, int, str)
    def _on_task_progress(self, workflow_id: str, task_id: str, progress: int, message: str):
        """Handle task progress"""
        main_logger.debug(f"_on_task_progress: workflow={workflow_id}, task={task_id}, progress={progress}, message={message}")
        if progress >= 0:
            self.progress_bar.setValue(progress)
            self.status_bar.showMessage(f"{message}", 0)
        else:
            self.progress_bar.setVisible(False)

    @Slot(str)
    def _on_workflow_started(self, workflow_id: str):
        """Handle workflow started"""
        main_logger.info(f"_on_workflow_started: workflow={workflow_id}")
        self._add_message("system", f"ðŸš€ Started workflow: {workflow_id}")

    @Slot(str)
    def _on_workflow_completed(self, workflow_id: str):
        """Handle workflow completed"""
        main_logger.info(f"_on_workflow_completed: workflow={workflow_id}")
        self._add_message("system", f"ðŸŽ‰ Workflow completed: {workflow_id}")
        self.status_bar.showMessage("Workflow completed successfully", 3000)

    @Slot(str, str)
    def _on_workflow_failed(self, workflow_id: str, error: str):
        """Handle workflow failed"""
        main_logger.error(f"_on_workflow_failed: workflow={workflow_id}, error={error}")
        self._add_message("system", f"ðŸ’¥ Workflow failed: {workflow_id} - {error}")
        self.status_bar.showMessage(f"Workflow failed: {error}", 5000)

    def _handle_patch_approval_request(self, event_obj, submission_id):
        """Handle patch approval request from backend"""
        main_logger.info(f"_handle_patch_approval_request: {event_obj}, submission_id: {submission_id}")

        try:
            # event_obj is already the msg part of the event
            call_id = event_obj.get("call_id", "")
            changes = event_obj.get("changes", {})

            if not changes:
                main_logger.warning("No changes found in approval request")
                return

            # Display the approval request via event bus
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '🛠 <b>AI wants to make changes:</b>'})
            except Exception:
                pass

            # Show each file and its changes
            for file_path, change_info in changes.items():
                if "update" in change_info:
                    update_info = change_info["update"]
                    unified_diff = update_info.get("unified_diff", "")
                    try:
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"🗒 File: <code>{file_path}</code>"})
                        GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"<pre>{unified_diff}</pre>", 'rich': True})
                    except Exception:
                        pass

            # Create approval dialog
            from PySide6.QtWidgets import QMessageBox, QPushButton

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Approve Changes")
            msg_box.setText("The AI wants to apply the above changes. Do you approve?")
            msg_box.setDetailedText(f"Call ID: {call_id}")

            # Add custom buttons
            approve_button = msg_box.addButton("Approve", QMessageBox.AcceptRole)
            reject_button = msg_box.addButton("Reject", QMessageBox.RejectRole)
            auto_approve_button = msg_box.addButton("Auto-Approve All", QMessageBox.ActionRole)

            msg_box.setDefaultButton(approve_button)
            result = msg_box.exec()

            # Prefer clickedButton to determine which custom button was chosen
            clicked_button = msg_box.clickedButton()
            if clicked_button == approve_button:
                self._send_patch_approval_response(submission_id, True, False)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': 'Changes approved'})
                return
            if clicked_button == reject_button:
                self._send_patch_approval_response(submission_id, False, False)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': 'Changes rejected'})
                return
            if clicked_button == auto_approve_button:
                self._send_patch_approval_response(submission_id, True, True)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': 'Changes approved (auto-approve enabled)'})
                return

            # Handle the response
            if result == QMessageBox.AcceptRole:
                self._send_patch_approval_response(submission_id, True, False)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Changes approved'})
            elif result == QMessageBox.RejectRole:
                self._send_patch_approval_response(submission_id, False, False)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '❌ Changes rejected'})
            elif msg_box.clickedButton() == auto_approve_button:
                self._send_patch_approval_response(submission_id, True, True)
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Changes approved (auto-approve enabled)'})

        except Exception as e:
            main_logger.error(f"Error handling patch approval request: {e}", exc_info=True)
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Error processing approval request: {e}"})
            except Exception:
                pass

    def _handle_exec_approval_request(self, event_obj, submission_id):
        """Handle exec approval request from backend"""
        main_logger.info(f"_handle_exec_approval_request: {event_obj}, submission_id: {submission_id}")

        try:
            # event_obj is already the msg part of the event
            call_id = event_obj.get("call_id", "")
            command = event_obj.get("command", [])
            cwd = event_obj.get("cwd", "")

            if not command:
                main_logger.warning("No command found in exec approval request")
                return

            main_logger.info(f"Exec approval request - Call ID: {call_id}, Command: {command}, CWD: {cwd}")

            # Format the command for display
            command_str = " ".join(command) if isinstance(command, list) else str(command)

            # Display the approval request via event bus
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '⚡ <b>AI wants to run a command:</b>'})
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"💻 Command: <code>{command_str}</code>"})
                if cwd:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"📁 Directory: <code>{cwd}</code>"})
            except Exception:
                pass

            main_logger.info("About to show exec approval dialog")

            # Create approval dialog
            from PySide6.QtWidgets import QMessageBox, QPushButton

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Approve Command Execution")
            msg_box.setText("The AI wants to execute the above command. Do you approve?")
            msg_box.setDetailedText(f"Call ID: {call_id}\nCommand: {command_str}\nDirectory: {cwd}")
            msg_box.setModal(True)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
            msg_box.show()
            msg_box.raise_()
            msg_box.activateWindow()

            main_logger.info("Exec approval dialog created and shown, about to exec")

            # Add custom buttons
            approve_button = msg_box.addButton("Approve", QMessageBox.AcceptRole)
            reject_button = msg_box.addButton("Reject", QMessageBox.RejectRole)
            auto_approve_button = msg_box.addButton("Auto-Approve All", QMessageBox.ActionRole)

            msg_box.setDefaultButton(approve_button)
            main_logger.info("About to call msg_box.exec()")
            result = msg_box.exec()
            main_logger.info(f"Dialog result: {result}, clicked button: {msg_box.clickedButton()}")

            # Handle the response
            clicked_button = msg_box.clickedButton()
            if result == QMessageBox.AcceptRole or clicked_button == approve_button:
                main_logger.info("User approved the command")
                self._send_exec_approval_response(submission_id, True, False)
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Command approved and executing...'})
                except Exception:
                    pass
            elif clicked_button == reject_button:
                main_logger.info("User rejected the command")
                self._send_exec_approval_response(submission_id, False, False)
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '❌ Command rejected'})
                except Exception:
                    pass
            elif clicked_button == auto_approve_button:
                main_logger.info("User chose auto-approve")
                self._send_exec_approval_response(submission_id, True, True)
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': '✅ Command approved (auto-approve enabled)'})
                except Exception:
                    pass
            else:
                main_logger.warning(f"Unknown dialog result: {result}, clicked button: {clicked_button}")

        except Exception as e:
            main_logger.error(f"Error handling exec approval request: {e}", exc_info=True)
            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Error processing command approval request: {e}"})
            except Exception:
                pass

    def _send_exec_approval_response(self, submission_id: str, approved: bool, auto_approve: bool = False):
        """Send exec approval response back to backend"""
        try:
            from aiw.core.models import Operation
            import time

            # Convert approval response to ReviewDecision
            if approved and auto_approve:
                decision = "approved_for_session"
            elif approved:
                decision = "approved"
            else:
                decision = "denied"

            # Create ExecApproval operation
            op = Operation(
                id=submission_id,  # Use the original submission ID
                op={
                    "type": "exec_approval",
                    "id": submission_id,
                    "decision": decision
                }
            )

            # Send the response
            result = self.backend.send_op(op.model_dump())
            if result:
                main_logger.info(f"Sent exec approval response for submission_id: {submission_id}, decision: {decision}")
            else:
                main_logger.error(f"Failed to send exec approval response for submission_id: {submission_id}")

        except Exception as e:
            main_logger.error(f"Error sending exec approval response: {e}", exc_info=True)

    def _send_patch_approval_response(self, submission_id: str, approved: bool, auto_approve: bool = False):
        """Send approval response back to backend"""
        try:
            from aiw.core.models import Operation

            # Convert approval response to ReviewDecision
            if approved and auto_approve:
                decision = "approved_for_session"
            elif approved:
                decision = "approved"
            else:
                decision = "denied"

            # Create PatchApproval operation
            op = Operation(
                id=submission_id,  # Use the original submission ID
                op={
                    "type": "patch_approval",
                    "id": submission_id,
                    "decision": decision
                }
            )

            main_logger.info(f"Created patch approval response operation: {op.model_dump()}")

            # Send the response
            result = self.backend.send_op(op.model_dump())
            main_logger.info(f"Sent patch approval response: submission_id={submission_id}, decision={decision}, result={result}")
            main_logger.info(f"Full operation sent: {op.model_dump()}")

        except Exception as e:
            main_logger.error(f"Error sending patch approval response: {e}", exc_info=True)
            import traceback
            main_logger.error(f"Traceback: {traceback.format_exc()}")
            if 'op' in locals():
                main_logger.error(f"Operation that failed: {op.model_dump()}")
            self._add_message("system", f"âŒ Error sending approval response: {e}")

    def _handle_mcp_tool_call_begin(self, event_obj):
        """Handle MCP tool call begin event"""
        try:
            msg = event_obj.get("msg", {})
            call_id = msg.get("call_id", "")
            invocation = msg.get("invocation", {})
            server = invocation.get("server", "")
            tool = invocation.get("tool", "")
            arguments = invocation.get("arguments", {})

            # Format the tool call message with relevant arguments
            tool_info = f"{server}.{tool}"

            # Add relevant arguments based on tool type
            if server == "filesystem":
                if tool == "read_text_file" and "path" in arguments:
                    tool_info += f" ðŸ“– {arguments['path']}"
                    if "head" in arguments:
                        tool_info += f" (first {arguments['head']} lines)"
                    elif "tail" in arguments:
                        tool_info += f" (last {arguments['tail']} lines)"
                elif tool == "list_directory" and "path" in arguments:
                    tool_info += f" ðŸ“ {arguments['path']}"
                elif tool in ["write_text_file", "edit_text_file"] and "path" in arguments:
                    tool_info += f" âœï¸ {arguments['path']}"
                elif tool == "create_directory" and "path" in arguments:
                    tool_info += f" ï¿½ {arguments['path']}"
                elif tool == "move_path" and "source" in arguments and "destination" in arguments:
                    tool_info += f" ðŸ“ {arguments['source']} â†’ {arguments['destination']}"
                elif "path" in arguments:
                    tool_info += f" ðŸ“„ {arguments['path']}"
            elif server == "git":
                if tool == "status" and "path" in arguments:
                    tool_info += f" ðŸ“Š {arguments['path']}"
                elif tool == "commit" and "message" in arguments:
                    tool_info += f" ðŸ’¾ {arguments['message'][:50]}..."
                elif "path" in arguments:
                    tool_info += f" ðŸ“„ {arguments['path']}"
            elif server == "run_terminal":
                if tool == "run_command" and "command" in arguments:
                    cmd = arguments['command']
                    # Truncate long commands
                    if len(cmd) > 60:
                        cmd = cmd[:57] + "..."
                    tool_info += f" ðŸ’» {cmd}"

            try:
                GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"🔧 AI calling: <code>{tool_info}</code>"})
            except Exception:
                pass

        except Exception as e:
            main_logger.error(f"Error handling MCP tool call begin: {e}", exc_info=True)

    def _handle_mcp_tool_call_end(self, event_obj):
        """Handle MCP tool call end event"""
        try:
            msg = event_obj.get("msg", {})
            call_id = msg.get("call_id", "")
            invocation = msg.get("invocation", {})
            server = invocation.get("server", "")
            tool = invocation.get("tool", "")
            result = msg.get("result", {})

            # Format completion message
            tool_info = f"{server}.{tool}"

            # Check if the call was successful
            if "Ok" in result:
                # Add result summary for certain tools
                if server == "filesystem":
                    if tool == "read_text_file":
                        if "content" in result.get("Ok", {}):
                            content = result["Ok"]["content"]
                            if isinstance(content, str):
                                lines = len(content.split('\n'))
                                tool_info += f" âœ… Read {lines} lines"
                            else:
                                tool_info += f" âœ… Read content"
                        else:
                            tool_info += f" âœ… Completed"
                    elif tool == "list_directory":
                        if "entries" in result.get("Ok", {}):
                            entries = result["Ok"]["entries"]
                            if isinstance(entries, list):
                                tool_info += f" âœ… Found {len(entries)} items"
                            else:
                                tool_info += f" âœ… Listed directory"
                        else:
                            tool_info += f" âœ… Completed"
                    elif tool in ["write_text_file", "edit_text_file"]:
                        tool_info += f" âœ… File updated"
                    elif tool == "create_directory":
                        tool_info += f" âœ… Directory created"
                    elif tool == "move_path":
                        tool_info += f" âœ… Path moved"
                    else:
                        tool_info += f" âœ… Completed"
                elif server == "git":
                    if tool == "status":
                        tool_info += f" âœ… Status retrieved"
                    elif tool == "commit":
                        tool_info += f" âœ… Changes committed"
                    else:
                        tool_info += f" âœ… Completed"
                elif server == "run_terminal":
                    if tool == "run_command":
                        if "exit_code" in result.get("Ok", {}):
                            exit_code = result["Ok"]["exit_code"]
                            if exit_code == 0:
                                tool_info += f" âœ… Command succeeded"
                            else:
                                tool_info += f" âš ï¸ Command failed (exit code: {exit_code})"
                        else:
                            tool_info += f" âœ… Command completed"
                    else:
                        tool_info += f" âœ… Completed"
                else:
                    tool_info += f" âœ… Completed"

                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"🔧 AI finished: <code>{tool_info}</code>"})
                except Exception:
                    pass
            elif "Err" in result:
                error = result.get("Err", "Unknown error")
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"❌ Tool call failed: <code>{server}.{tool}</code> - {error}"})
                except Exception:
                    pass
            else:
                try:
                    GLOBAL_EVENT_BUS.publish('chat.message', {'role': 'system', 'content': f"✅ Tool call completed: <code>{server}.{tool}</code>"})
                except Exception:
                    pass

        except Exception as e:
            main_logger.error(f"Error handling MCP tool call end: {e}", exc_info=True)

    def _handle_token_count(self, event_obj):
        """Handle token count updates"""
        try:
            # event_obj is already the inner 'msg' payload when routed here
            msg = event_obj or {}
            input_tokens = msg.get("input_tokens", 0)
            output_tokens = msg.get("output_tokens", 0)
            total_tokens = msg.get("total_tokens", 0)

            # Fallback: if totals are missing, approximate from last user/assistant texts
            if (input_tokens == 0 and output_tokens == 0 and total_tokens == 0):
                try:
                    def _est(t: str) -> int:
                        # Rough heuristic ~4 chars per token
                        return (len(t) + 3) // 4
                    last_user = ""
                    last_ai = ""
                    if hasattr(self, 'chat_view') and self.chat_view:
                        for m in reversed(self.chat_view.get_messages()):
                            if not last_ai and m.role == 'assistant':
                                last_ai = m.content or ""
                            elif not last_user and m.role == 'user':
                                last_user = m.content or ""
                            if last_ai and last_user:
                                break
                    input_tokens = _est(last_user) if last_user else 0
                    output_tokens = _est(last_ai) if last_ai else 0
                    total_tokens = input_tokens + output_tokens
                except Exception:
                    pass
            # Persist
            self.token_stats["input"] = input_tokens
            self.token_stats["output"] = output_tokens
            self.token_stats["total"] = total_tokens
            # Update token dock labels
            try:
                self._token_value_labels["input"].setText(str(input_tokens))
                self._token_value_labels["output"].setText(str(output_tokens))
                self._token_value_labels["total"].setText(str(total_tokens))
                if not self.token_dock.isVisible():
                    self.token_dock.show()
            except Exception:
                pass
            # Update status bar with token information (short-lived)
            self.status_bar.showMessage(f"Tokens: {total_tokens} (In: {input_tokens}, Out: {output_tokens})", 3000)
            try:
                self.chat_view.set_token_counts(input_tokens, output_tokens, total_tokens)
            except Exception:
                pass

        except Exception as e:
            main_logger.error(f"Error handling token count: {e}", exc_info=True)

    def _handle_session_configured(self, event_obj):
        """Handle session configured event"""
        try:
            self._add_message("system", "ðŸ”— Backend session configured and ready")
            self.backend_status_label.setText("Backend: Connected")
            self.status_bar.showMessage("Backend ready", 3000)

        except Exception as e:
            main_logger.error(f"Error handling session configured: {e}", exc_info=True)

    # --- Added feature helpers ---
    def _toggle_raw_reasoning(self, checked: bool):
        """Toggle display of raw reasoning tokens."""
        self.show_raw_reasoning = checked
        if hasattr(self, "raw_reasoning_action"):
            self.raw_reasoning_action.setChecked(checked)
        self.status_bar.showMessage(f"Raw reasoning {'enabled' if checked else 'hidden'}", 2000)

    def _request_conversation_history(self):
        """Request conversation history from backend (stub protocol)."""
        try:
            if not self.backend:
                return
            op = Operation(
                id=f"history_{int(time.time())}",
                op={"type": "conversation_history"}
            )
            self.backend.send_op(op.model_dump())
            self._add_message("system", "📜 Requested conversation history (if supported)")
        except Exception as e:
            main_logger.error(f"Error requesting history: {e}")
            self._add_message("system", f"❌ History request failed: {e}")

    def _handle_conversation_history(self, messages):
        """Populate chat console with prior conversation (unused unless backend supplies)."""
        try:
            # Persist messages in the store
            if self.conversation_store:
                self.conversation_store.set_messages(messages)
            # Hydrate chat view directly without re-adding to store
            if hasattr(self, 'chat_view') and self.chat_view:
                from .components.chat.chat_view import ChatMessage
                self.chat_view.set_messages([
                    ChatMessage(role=m.get('role', 'assistant'), content=m.get('content', ''),
                                timestamp=m.get('timestamp'), rich=bool(m.get('rich', False)))
                    for m in messages if m.get('content')
                ])
        except Exception as e:
            main_logger.error(f"Error applying conversation history: {e}")

    def _export_transcript_markdown(self):
        try:
            from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel
            if not self.conversation_store or not self.conversation_store.session:
                return
            # Export options dialog
            dlg = QDialog(self)
            dlg.setWindowTitle("Export Options")
            v = QVBoxLayout(dlg)
            v.addWidget(QLabel("Select roles to include:"))
            cb_user = QCheckBox("User"); cb_user.setChecked(True)
            cb_assistant = QCheckBox("Assistant"); cb_assistant.setChecked(True)
            cb_system = QCheckBox("System"); cb_system.setChecked(True)
            v.addWidget(cb_user); v.addWidget(cb_assistant); v.addWidget(cb_system)
            btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            v.addWidget(btns)
            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)
            if not dlg.exec() or not cb_user.isChecked() and not cb_assistant.isChecked() and not cb_system.isChecked():
                return
            allowed = set()
            if cb_user.isChecked(): allowed.add('user')
            if cb_assistant.isChecked(): allowed.add('assistant')
            if cb_system.isChecked(): allowed.add('system')
            default = f"transcript_{self.conversation_store.session.session_id}.md"
            path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", default, "Markdown Files (*.md)")
            if not path:
                return
            import re
            def html_to_md(text: str) -> str:
                t = text
                # Lists (convert simple <li>)
                t = re.sub(r'<ul>\s*', '', t)
                t = re.sub(r'</ul>', '', t)
                t = re.sub(r'<li>\s*(.*?)\s*</li>', r'* \1\n', t)
                # Links <a href="url">text</a>
                t = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', t)
                # Code blocks
                t = re.sub(r'<pre>(.*?)</pre>', lambda m: '\n```\n' + m.group(1).strip() + '\n```\n', t, flags=re.DOTALL)
                # Inline code
                t = re.sub(r'<code>(.*?)</code>', r'`\1`', t)
                # Bold / italic
                t = re.sub(r'<b>(.*?)</b>', r'**\1**', t)
                t = re.sub(r'<strong>(.*?)</strong>', r'**\1**', t)
                t = re.sub(r'<i>(.*?)</i>', r'*\1*', t)
                t = re.sub(r'<em>(.*?)</em>', r'*\1*', t)
                # Paragraphs / breaks
                t = t.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                t = re.sub(r'</p>', '\n\n', t)
                t = re.sub(r'<p[^>]*>', '', t)
                # Strip residual tags
                t = re.sub(r'<[^>]+>', '', t)
                # Unescape HTML
                t = (t.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'"))
                # Collapse extra newlines
                t = re.sub(r'\n{3,}', '\n\n', t).strip()
                return t
            lines = [f"# Session Transcript {self.conversation_store.session.session_id}", "", f"Started: {self.conversation_store.session.created}", ""]
            for msg in self.conversation_store.get_messages():
                if msg.role not in allowed:
                    continue
                role_title = msg.role.title()
                content = msg.content if not msg.rich else html_to_md(msg.content)
                lines.append(f"## [{msg.timestamp}] {role_title}")
                lines.append("")
                lines.append(content)
                lines.append("")
            from pathlib import Path as _P
            _P(path).write_text("\n".join(lines), encoding='utf-8')
            self.status_bar.showMessage(f"Transcript exported to {path}", 4000)
        except Exception as e:
            main_logger.error(f"Transcript export failed: {e}")
            self.status_bar.showMessage(f"Transcript export failed: {e}", 8000)

    def _show_session_switcher(self):
        if not self.conversation_store:
            return
        try:
            sessions_root = self.conversation_store.sessions_dir
            if not sessions_root.exists():
                return
            dlg = QDialog(self)
            dlg.setWindowTitle("Session Manager")
            dlg.resize(400, 300)
            v = QVBoxLayout(dlg)
            
            # Session list
            listw = QListWidget()
            items = []
            for p in sorted(sessions_root.iterdir(), reverse=True):
                if p.is_dir() and (p / 'chat.json').exists():
                    items.append(p)
            for path in items:
                display_name = path.name
                if self.conversation_store.session and path.name == self.conversation_store.session.session_id:
                    display_name += " (Active)"
                item = QListWidgetItem(display_name)
                item.setData(Qt.UserRole, path.name)  # Store actual session ID
                listw.addItem(item)
            v.addWidget(QLabel("Sessions:"))
            v.addWidget(listw)
            
            # Action buttons
            btn_layout = QHBoxLayout()
            switch_btn = QPushButton("Switch To")
            rename_btn = QPushButton("Rename")
            delete_btn = QPushButton("Delete")
            btn_layout.addWidget(switch_btn)
            btn_layout.addWidget(rename_btn)
            btn_layout.addWidget(delete_btn)
            v.addLayout(btn_layout)
            
            # Dialog buttons
            dialog_btns = QDialogButtonBox(QDialogButtonBox.Cancel)
            v.addWidget(dialog_btns)
            dialog_btns.rejected.connect(dlg.reject)
            
            def switch_session():
                if not listw.currentItem():
                    return
                chosen = listw.currentItem().data(Qt.UserRole)
                self._switch_to_session(chosen)
                dlg.accept()
                
            def rename_session():
                if not listw.currentItem():
                    return
                old_id = listw.currentItem().data(Qt.UserRole)
                new_name, ok = QInputDialog.getText(dlg, "Rename Session", "New session name:", text=old_id)
                if not ok or not new_name.strip():
                    return
                if self._rename_session(old_id, new_name.strip()):
                    # Refresh list
                    listw.clear()
                    for p in sorted(sessions_root.iterdir(), reverse=True):
                        if p.is_dir() and (p / 'chat.json').exists():
                            display_name = p.name
                            if self.conversation_store.session and p.name == self.conversation_store.session.session_id:
                                display_name += " (Active)"
                            item = QListWidgetItem(display_name)
                            item.setData(Qt.UserRole, p.name)
                            listw.addItem(item)
                            
            def delete_session():
                if not listw.currentItem():
                    return
                session_id = listw.currentItem().data(Qt.UserRole)
                if session_id == getattr(self.conversation_store.session, 'session_id', None):
                    QMessageBox.warning(dlg, "Cannot Delete", "Cannot delete the active session.")
                    return
                reply = QMessageBox.question(dlg, "Delete Session", 
                    f"Are you sure you want to delete session '{session_id}'?")
                if reply == QMessageBox.Yes:
                    if self._delete_session(session_id):
                        listw.takeItem(listw.currentRow())
            
            switch_btn.clicked.connect(switch_session)
            rename_btn.clicked.connect(rename_session)
            delete_btn.clicked.connect(delete_session)
            
            dlg.exec()
        except Exception as e:
            main_logger.error(f"Failed showing session switcher: {e}")
            
    def _switch_to_session(self, session_id: str):
        try:
            sessions_root = self.conversation_store.sessions_dir
            target = sessions_root / session_id / 'chat.json'
            import json
            data = json.loads(target.read_text(encoding='utf-8'))
            messages = data.get('messages', [])
            # Replace store session reference
            from ..core.conversation_store import StoredMessage
            self.conversation_store.session.session_id = data.get('session_id', session_id)
            self.conversation_store.session.created = data.get('created', '')
            self.conversation_store.session.messages = [StoredMessage(**m) for m in messages]
            # Hydrate chat view
            from .components.chat.chat_view import ChatMessage
            self.chat_view.set_messages([
                ChatMessage(role=m['role'], content=m['content'], timestamp=m.get('timestamp'), rich=m.get('rich', False))
                for m in messages
            ])
            # Update pointer file
            self.conversation_store._write_pointer()
            self._update_window_title()
            self.status_bar.showMessage(f"Switched to session {session_id}", 4000)
        except Exception as e:
            main_logger.error(f"Failed switching to session {session_id}: {e}")
            
    def _rename_session(self, old_id: str, new_id: str) -> bool:
        try:
            sessions_root = self.conversation_store.sessions_dir
            old_path = sessions_root / old_id
            new_path = sessions_root / new_id
            if new_path.exists():
                QMessageBox.warning(self, "Rename Failed", f"Session '{new_id}' already exists.")
                return False
            old_path.rename(new_path)
            # Update chat.json session_id field
            chat_file = new_path / 'chat.json'
            import json
            data = json.loads(chat_file.read_text(encoding='utf-8'))
            data['session_id'] = new_id
            chat_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            # Update active session if it's the one being renamed
            if self.conversation_store.session and self.conversation_store.session.session_id == old_id:
                self.conversation_store.session.session_id = new_id
                self.conversation_store._write_pointer()
                self._update_window_title()
            self.status_bar.showMessage(f"Session renamed to {new_id}", 3000)
            return True
        except Exception as e:
            main_logger.error(f"Failed renaming session {old_id} to {new_id}: {e}")
            QMessageBox.critical(self, "Rename Failed", f"Failed to rename session: {e}")
            return False
            
    def _delete_session(self, session_id: str) -> bool:
        try:
            sessions_root = self.conversation_store.sessions_dir
            session_path = sessions_root / session_id
            import shutil
            shutil.rmtree(session_path)
            self.status_bar.showMessage(f"Session {session_id} deleted", 3000)
            return True
        except Exception as e:
            main_logger.error(f"Failed deleting session {session_id}: {e}")
            QMessageBox.critical(self, "Delete Failed", f"Failed to delete session: {e}")
            return False
















