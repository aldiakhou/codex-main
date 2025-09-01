"""
Enhanced main window with dock-based layout for AI Development Workbench
"""
import json
import os
import time
import logging
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QSize
from PySide6.QtWidgets import (
    QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QDockWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QStyle,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox,
    QLabel, QProgressBar
)
from PySide6.QtGui import QAction, QIcon, QFont
from .design_system import apply_theme

from ..core.backend_service import BackendService
from ..core.config import get_config_manager
from ..core.models import Repository, FileItem, Operation, Task
from ..core.task_runner import get_workflow_runner
from .code_editor import CodeEditorWidget
from .diff_view import DiffViewWidget
from .chat_console import ChatConsole
from .settings_dialog import SettingsDialog
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
        self.show_raw_reasoning = True
        self.token_stats = {"input": 0, "output": 0, "total": 0}
        self.conversation_messages = []

        # Window basics
        self.setWindowTitle("AI Development Workbench")
        self.setGeometry(100, 100, 1400, 900)

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
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_backend()
        self._load_initial_state()

    def _setup_backend(self):
        """Initialize the backend service with improved error handling"""
        main_logger.info("_setup_backend() called")
        codex_path = self.config_manager.get_codex_path()
        main_logger.info(f"Codex path from config: {codex_path}")

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
        self.backend_thread = QThread()
        self.backend = BackendService(codex_path)
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
        """Setup the main UI with docks (focus on workspace)."""
        # Central editor
        self.code_editor = CodeEditorWidget()
        self.setCentralWidget(self.code_editor)

        # Docks
        self._create_repository_dock()
        self._create_console_dock()
        self._create_diff_dock()
        self._create_artifacts_dock()
        self._create_exec_log_dock()
        self._create_plan_dock()
        self._create_token_dock()

        # Corner layout
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        # Hide optional docks initially
        for dock in (self.console_dock, self.artifacts_dock, self.exec_log_dock, self.plan_dock):
            dock.hide()
        self.token_dock.hide()

    def _create_repository_dock(self):
        """Create repository explorer dock"""
        self.repo_dock = QDockWidget("Repository", self)
        self.repo_dock.setObjectName("Repository")
        self.repo_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        # Repository tree widget
        self.repo_tree = QTreeWidget()
        self.repo_tree.setHeaderLabel("Files")
        self.repo_tree.itemClicked.connect(self._on_file_clicked) # Changed to single click

        # Repository actions
        repo_widget = QWidget()
        repo_layout = QVBoxLayout(repo_widget)

        # Repository info label
        self.repo_info_label = QLabel("No repository opened")
        repo_layout.addWidget(self.repo_info_label)

        repo_layout.addWidget(self.repo_tree)
        self.repo_dock.setWidget(repo_widget)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.repo_dock)

    def _create_console_dock(self):
        """Create the assistant (chat) dock with compact styling"""
        self.console_dock = QDockWidget("Assistant", self)
        self.console_dock.setObjectName("Console")
        self.console_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.console_dock.setMinimumWidth(340)

        console_widget_container = QWidget()
        console_layout = QVBoxLayout(console_widget_container)

        # Chat console
        self.chat_console = ChatConsole()
        self.chat_console.setMinimumWidth(320)
        console_layout.addWidget(self.chat_console)

        # Input area
        input_layout = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(60)
        self.prompt_input.setFont(QFont("Consolas", 10))
        self.prompt_input.setPlaceholderText("Ask the AI...")
        input_layout.addWidget(self.prompt_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self._send_prompt)
        input_layout.addWidget(send_button)

        console_layout.addLayout(input_layout)
        self.console_dock.setWidget(console_widget_container)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.console_dock)

    def _create_diff_dock(self):
        """Create diff viewer dock"""
        self.diff_dock = QDockWidget("Diff", self)
        self.diff_dock.setObjectName("Diff")
        self.diff_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Enhanced diff viewer widget
        self.diff_viewer = DiffViewWidget()
        self.diff_viewer.diff_widget.apply_requested.connect(self._on_apply_diff)

        self.diff_dock.setWidget(self.diff_viewer)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.diff_dock)

    def _create_exec_log_dock(self):
        """Create execution log dock for streaming command output"""
        self.exec_log_dock = QDockWidget("Exec Output", self)
        self.exec_log_dock.setObjectName("ExecOutput")
        self.exec_log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        from PySide6.QtWidgets import QTextBrowser
        self.exec_output_view = QTextBrowser()
        self.exec_output_view.setOpenExternalLinks(True)
        self.exec_output_view.setStyleSheet("QTextBrowser { font-family: 'Cascadia Code', Consolas, monospace; font-size: 11px; }")
        self.exec_log_dock.setWidget(self.exec_output_view)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.exec_log_dock)

    def _create_plan_dock(self):
        """Create plan/update dock"""
        self.plan_dock = QDockWidget("Plan", self)
        self.plan_dock.setObjectName("Plan")
        self.plan_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        from PySide6.QtWidgets import QListWidget
        self.plan_list = QListWidget()
        self.plan_list.setStyleSheet("QListWidget { font-family: 'Cascadia Code', Consolas, monospace; }")
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

    def _setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_repo_action = QAction("&Open Repository...", self)
        open_repo_action.triggered.connect(self._open_repository)
        file_menu.addAction(open_repo_action)

        file_menu.addSeparator()

        save_file_action = QAction("&Save", self)
        save_file_action.setShortcut("Ctrl+S")
        save_file_action.triggered.connect(self._save_current_file)
        file_menu.addAction(save_file_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Dock visibility actions
        repo_dock_action = self.repo_dock.toggleViewAction()
        repo_dock_action.setText("Repository Explorer")
        view_menu.addAction(repo_dock_action)

        console_dock_action = self.console_dock.toggleViewAction()
        console_dock_action.setText("Assistant")
        view_menu.addAction(console_dock_action)

        diff_dock_action = self.diff_dock.toggleViewAction()
        diff_dock_action.setText("Diff Viewer")
        view_menu.addAction(diff_dock_action)

        artifacts_dock_action = self.artifacts_dock.toggleViewAction()
        artifacts_dock_action.setText("Artifacts")
        view_menu.addAction(artifacts_dock_action)

        # Theme toggle
        view_menu.addSeparator()
        from PySide6.QtGui import QActionGroup
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        theme_dark = QAction("Dark Theme", self, checkable=True)
        theme_light = QAction("Light Theme", self, checkable=True)
        theme_group.addAction(theme_dark)
        theme_group.addAction(theme_light)
        view_menu.addAction(theme_dark)
        view_menu.addAction(theme_light)

        # Raw reasoning toggle
        self.raw_reasoning_action = QAction("Show Raw Reasoning", self, checkable=True)
        self.raw_reasoning_action.setChecked(True)
        self.raw_reasoning_action.triggered.connect(self._toggle_raw_reasoning)
        view_menu.addAction(self.raw_reasoning_action)

        # Token dock toggle
        token_dock_action = self.token_dock.toggleViewAction()
        token_dock_action.setText("Token Usage")
        view_menu.addAction(token_dock_action)

        view_menu.addSeparator()
        history_action = QAction("Load Conversation History", self)
        history_action.triggered.connect(self._request_conversation_history)
        view_menu.addAction(history_action)

        # Initialize checked state
        current_theme = getattr(self.config_manager.config.ui, 'theme', 'system')
        if current_theme == 'light':
            theme_light.setChecked(True)
        else:
            theme_dark.setChecked(True)

        theme_dark.triggered.connect(lambda: self._set_theme('dark'))
        theme_light.triggered.connect(lambda: self._set_theme('light'))

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        login_action = QAction("Login with ChatGPT", self)
        login_action.triggered.connect(self._start_login)
        tools_menu.addAction(login_action)

        tools_menu.addSeparator()

        edit_task_action = QAction("&Edit File with AI", self)
        edit_task_action.triggered.connect(self._run_edit_task)
        tools_menu.addAction(edit_task_action)

    def _setup_toolbar(self):
        """Setup toolbar with project, file, AI and control actions."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))

        def add(action: QAction, handler):
            action.triggered.connect(handler)
            toolbar.addAction(action)
            return action

        # Repo
        add(QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), "Open Repo", self), self._open_repository)
        toolbar.addSeparator()

        # File
        add(QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save", self), self._save_current_file)
        view_diff = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "View Changes", self)
        view_diff.setToolTip("Show unsaved changes for current file")
        add(view_diff, self._show_local_diff)
        toolbar.addSeparator()

        # AI
        add(QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Send", self), self._send_prompt)
        toolbar.addSeparator()

        # Tasks
        add(QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "AI Edit", self), self._run_edit_task)

        # Interrupt
        interrupt = QAction("Interrupt", self)
        interrupt.setToolTip("Interrupt current AI turn")
        add(interrupt, self._send_interrupt)

        # Quick reasoning toggle
        rr = QAction("Reasoning", self)
        rr.setCheckable(True)
        rr.setChecked(True)
        rr.triggered.connect(self._toggle_raw_reasoning)
        toolbar.addAction(rr)

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
            self.diff_viewer.set_diff_content(diff_text, current_file)
            self.diff_dock.raise_()
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
        pass  # Placeholder (initial state logic if needed later)

    def _load_repository_files(self, repo_path: str):
        """Load repository files into tree view"""
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

            # Populate tree
            self._load_repository_files(str(repo_path))

            # Emit signal
            self.repository_opened.emit(str(repo_path))

            # Persist to config (recent repositories list)
            try:
                cfg = self.config_manager.config
                # Deduplicate existing entries
                existing = [r for r in cfg.repositories if r.path != str(repo_path)]
                existing.insert(0, self.current_repository)  # most recent first
                # Keep only a handful
                cfg.repositories = existing[:10]
                self.config_manager.save_config()
            except Exception:
                pass

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
        """Load a file into the code editor"""
        success = self.code_editor.load_file(file_path)
        if success:
            self.file_selected.emit(file_path)

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

        self._add_message("user", prompt)
        self.prompt_input.clear()

        try:
            if not self.backend:
                main_logger.error("Backend is None")
                self._add_message("system", "âŒ Backend not connected. Please check configuration.")
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
                    self._add_message("system", f"ðŸ“ Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user turn operation with file context for: {current_file}")
                    main_logger.info(f"Working directory context: {normalized_cwd}")
                else:
                    op = Operation.create_user_turn(prompt, normalized_cwd)
                    self._add_message("system", "ðŸ’¬ Sending general prompt...")
                    main_logger.info(f"Created user turn operation with working directory: {normalized_cwd}")
            else:
                # Fallback to user_input if no repository is selected
                if current_file:
                    enhanced_prompt = f"Regarding the file '{Path(current_file).name}': {prompt}"
                    op = Operation.create_user_input(enhanced_prompt)
                    self._add_message("system", f"ðŸ“ Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user input operation with file context for: {current_file}")
                else:
                    op = Operation.create_user_input(prompt)
                    self._add_message("system", "ðŸ’¬ Sending general prompt...")
                    main_logger.info("Created user input operation")

            op.context = repo_context

            # Log the full operation for debugging
            op_json = op.model_dump_json(indent=2)
            main_logger.info(f"Operation JSON: {op_json}")
            self._add_message("system", f"<i>Sending op:</i> <pre>{op_json}</pre>", rich=True)

            main_logger.info("Calling backend.send_op()")
            result = self.backend.send_op(op.model_dump())
            main_logger.info(f"backend.send_op() returned: {result}")
            # Ensure clean status text (overrides any prior emoji-laden message)
            self.status_bar.showMessage("Waiting for AI response...", 0)

            self.status_bar.showMessage("â³ Waiting for AI response...", 0)

        except Exception as e:
            main_logger.error(f"Exception in _send_prompt: {str(e)}", exc_info=True)
            self._add_message("system", f"âŒ Error sending prompt: {str(e)}")
            self.status_bar.clearMessage()

    def _add_message(self, role: str, content: str, rich: bool = False):
        """Add a bubble-styled message to the chat console."""
        # Normalize roles to our three styles
        norm_role = role
        if role not in ("user", "assistant", "system"):
            norm_role = "assistant" if role == "agent" else "system"
        self.chat_console.add_message(norm_role, content, rich=rich)

    def _apply_theme(self):
        """Apply project design system theme (compact, editor-first)."""
        try:
            theme = getattr(self.config_manager.config.ui, 'theme', 'dark')
            apply_theme(self, theme=theme if theme in ("dark", "light") else "dark", base_font_pt=10.0)
        except Exception as e:
            main_logger.warning(f"Failed to apply theme: {e}")

    def _set_theme(self, theme: str):
        try:
            self.config_manager.config.ui.theme = theme
            self.config_manager.save_config()
        except Exception:
            pass
        self._apply_theme()

    def _start_login(self):
        """Start ChatGPT login process"""
        if self.backend:
            op = Operation.create_login_request()
            self.backend.send_op(op.model_dump())

    def _run_test_task(self):
        """Run tests for the current project."""
        if not self.current_repository:
            QMessageBox.warning(self, "No Repository", "Please select a repository first.")
            return

        # Create a test task
        task = Task(
            id=f"test_{int(time.time())}",
            name="Run Tests",
            type="run_tests",
            parameters={
                "command": ["pytest", "-v"],
                "repository_path": str(self.current_repository.path)
            }
        )

        # Run the task
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

        # Handle reasoning deltas (accumulate them)
        if event_type == "agent_reasoning_delta":
            delta = event_obj.get("delta", "")
            if self.show_raw_reasoning:
                self.current_reasoning += delta

        # Handle reasoning section break (display accumulated reasoning)
        elif event_type == "agent_reasoning_section_break":
            if self.show_raw_reasoning and self.current_reasoning.strip():
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    self._add_message("system", f"ðŸ¤” {clean_reasoning}")
                self.current_reasoning = ""

        # Handle message deltas (accumulate them)
        elif event_type == "agent_message_delta":
            delta = event_obj.get("delta", "")
            self.current_message += delta

        # Handle task completion (display accumulated message)
        elif event_type == "task_complete":
            if self.current_message.strip():
                self._add_message("assistant", self.current_message.strip())
                self.current_message = ""
            if self.show_raw_reasoning and self.current_reasoning.strip():
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    self._add_message("system", f"ðŸ¤” {clean_reasoning}")
                self.current_reasoning = ""

        # Handle unified diff for the entire turn (codex-rs EventMsg::TurnDiff)
        elif event_type == "turn_diff":
            unified_diff = event_obj.get("unified_diff", "")
            if unified_diff:
                self._add_message("system", "Received changes for this turn.")
                self.diff_viewer.set_diff_content(unified_diff, "")
                self.diff_dock.raise_()
            else:
                self._add_message("system", "No changes in this turn.")

        # Handle agent edit file response (the diff)
        elif event_type == "agent_edit_file_response":
            diff = event_obj.get("diff", "")
            file_path = event_obj.get("file_path", "unknown_file")
            if diff:
                self._add_message("system", f"âœ… Received diff for {file_path}")
                self.diff_viewer.set_diff_content(diff, file_path)
                self.diff_dock.raise_()  # Bring the diff dock to the front
            else:
                self._add_message("system", f"âš ï¸ Received an empty diff for {file_path}")

        # Handle login events
        elif event_type == "login_chat_gpt_response":
            auth_url = event_obj.get("auth_url")
            if auth_url:
                import webbrowser
                webbrowser.open(auth_url)
                self._add_message("system", "ðŸ”— Please complete the login in your browser.")

        elif event_type == "login_chat_gpt_complete":
            if event_obj.get("success"):
                self._add_message("system", "âœ… Login successful!")
            else:
                error = event_obj.get("error", "Unknown error")
                self._add_message("system", f"âŒ Login failed: {error}")

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
                    self.diff_viewer.set_diff_content("\n".join(combined), "")
                    self.diff_dock.raise_()
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
            self._handle_plan_update(event_obj)
        elif event_type == "web_search_begin":
            self._add_message("system", "🔍 Web search started")
        elif event_type == "web_search_end":
            query = event_obj.get("query", "")
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
                self._add_message("system", "✅ Patch applied successfully")
            else:
                self._add_message("system", f"❌ Patch apply failed: {stderr[:200]}")
            if stdout:
                self._add_message("system", f"<details><summary>Patch output</summary><pre>{stdout[:4000]}</pre></details>", rich=True)
            if stderr and not success:
                self._add_message("system", f"<details><summary>Patch errors</summary><pre>{stderr[:4000]}</pre></details>", rich=True)
        except Exception as e:
            main_logger.error(f"Error in patch_apply_end: {e}")

    def _handle_exec_command_begin(self, event_obj):
        try:
            cmd = event_obj.get("command") or ' '.join(event_obj.get("argv", []))
            self.exec_output_view.clear()
            self.exec_log_dock.show()
            self._add_message("system", f"🛠️ Exec started: <code>{cmd}</code>")
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
                self._add_message("system", "✅ Exec finished successfully")
            else:
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
            else:
                text = event_obj.get('text', '')
                if text:
                    self._add_message('system', f"🧠 {text}")
        except Exception as e:
            main_logger.error(f"Error in raw reasoning handler: {e}")

    def _handle_stream_error(self, event_obj):
        try:
            message = event_obj.get('message', 'Unknown stream error')
            self._add_message('system', f"❌ Stream error: {message}")
        except Exception as e:
            main_logger.error(f"Error in stream_error handler: {e}")

    def _handle_turn_aborted(self, event_obj):
        try:
            reason = event_obj.get('reason', 'interrupted')
            self._add_message('system', f"⛔ Turn aborted: {reason}")
        except Exception as e:
            main_logger.error(f"Error in turn_aborted handler: {e}")

    def _send_interrupt(self):
        try:
            if not self.backend:
                return
            op = Operation.create_interrupt()
            self.backend.send_op(op.model_dump())
            self._add_message('system', '⛔ Interrupt sent')
        except Exception as e:
            main_logger.error(f"Error sending interrupt: {e}")

    @Slot(str)
    def _on_backend_error(self, error_message):
        """Handle backend errors"""
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
            if dlg.apply_and_restart_requested:
                self._restart_backend()
            else:
                # No restart requested; config changes will apply on next start
                self.status_bar.showMessage("Settings saved", 3000)

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

        # Stop backend thread
        if self.backend_thread:
            self.backend.stop()
            self.backend_thread.quit()
            self.backend_thread.wait()

        event.accept()

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

            # Display the approval request
            self._add_message("system", "ðŸ”„ <b>AI wants to make changes:</b>")

            # Show each file and its changes
            for file_path, change_info in changes.items():
                if "update" in change_info:
                    update_info = change_info["update"]
                    unified_diff = update_info.get("unified_diff", "")

                    self._add_message("system", f"ðŸ“ File: <code>{file_path}</code>")
                    self._add_message("system", f"<pre>{unified_diff}</pre>")

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
                self._add_message("system", "Changes approved")
                return
            if clicked_button == reject_button:
                self._send_patch_approval_response(submission_id, False, False)
                self._add_message("system", "Changes rejected")
                return
            if clicked_button == auto_approve_button:
                self._send_patch_approval_response(submission_id, True, True)
                self._add_message("system", "Changes approved (auto-approve enabled)")
                return

            # Handle the response
            if result == QMessageBox.AcceptRole:
                # User approved
                self._send_patch_approval_response(submission_id, True, False)
                self._add_message("system", "âœ… Changes approved")
            elif result == QMessageBox.RejectRole:
                # User rejected
                self._send_patch_approval_response(submission_id, False, False)
                self._add_message("system", "âŒ Changes rejected")
            elif msg_box.clickedButton() == auto_approve_button:
                # User chose auto-approve
                self._send_patch_approval_response(submission_id, True, True)
                self._add_message("system", "âœ… Changes approved (auto-approve enabled)")

        except Exception as e:
            main_logger.error(f"Error handling patch approval request: {e}", exc_info=True)
            self._add_message("system", f"âŒ Error processing approval request: {e}")

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

            # Display the approval request
            self._add_message("system", "âš¡ <b>AI wants to run a command:</b>")
            self._add_message("system", f"ðŸ’» Command: <code>{command_str}</code>")
            if cwd:
                self._add_message("system", f"ðŸ“ Directory: <code>{cwd}</code>")

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
                # User approved
                main_logger.info("User approved the command")
                self._send_exec_approval_response(submission_id, True, False)
                self._add_message("system", "âœ… Command approved and executing...")
            elif clicked_button == reject_button:
                # User rejected
                main_logger.info("User rejected the command")
                self._send_exec_approval_response(submission_id, False, False)
                self._add_message("system", "âŒ Command rejected")
            elif clicked_button == auto_approve_button:
                # User chose auto-approve
                main_logger.info("User chose auto-approve")
                self._send_exec_approval_response(submission_id, True, True)
                self._add_message("system", "âœ… Command approved (auto-approve enabled)")
            else:
                main_logger.warning(f"Unknown dialog result: {result}, clicked button: {clicked_button}")

        except Exception as e:
            main_logger.error(f"Error handling exec approval request: {e}", exc_info=True)
            self._add_message("system", f"âŒ Error processing command approval request: {e}")

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

            self._add_message("system", f"ðŸ”§ AI calling: <code>{tool_info}</code>")

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

                self._add_message("system", f"ðŸ”§ AI finished: <code>{tool_info}</code>")
            elif "Err" in result:
                error = result.get("Err", "Unknown error")
                self._add_message("system", f"âŒ Tool call failed: <code>{server}.{tool}</code> - {error}")
            else:
                self._add_message("system", f"âœ… Tool call completed: <code>{server}.{tool}</code>")

        except Exception as e:
            main_logger.error(f"Error handling MCP tool call end: {e}", exc_info=True)

    def _handle_token_count(self, event_obj):
        """Handle token count updates"""
        try:
            msg = event_obj.get("msg", {})
            input_tokens = msg.get("input_tokens", 0)
            output_tokens = msg.get("output_tokens", 0)
            total_tokens = msg.get("total_tokens", 0)
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
            for m in messages:
                role = m.get("role", "assistant")
                content = m.get("content", "")
                self._add_message(role, content)
        except Exception as e:
            main_logger.error(f"Error applying conversation history: {e}")


