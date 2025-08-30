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
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread
from PySide6.QtWidgets import (
    QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QDockWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFileDialog, QMessageBox,
    QLabel, QProgressBar
)
from PySide6.QtGui import QAction, QIcon, QFont

from ..core.backend_service import BackendService
from ..core.config import get_config_manager
from ..core.models import Repository, FileItem, Operation, Task
from ..core.task_runner import get_workflow_runner
from .code_editor import CodeEditorWidget
from .diff_view import DiffViewWidget
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
        main_logger.info("MainWindow.__init__() called")
        super().__init__()
        self.config_manager = get_config_manager()
        self.current_repository: Optional[Repository] = None
        self.backend: Optional[BackendService] = None
        self.backend_thread: Optional[QThread] = None
        self.task_runner = get_workflow_runner()  # Initialize task runner

        # Initialize message accumulation
        self.current_reasoning = ""
        self.current_message = ""
        self.last_task_id = None

        self.setWindowTitle("AI Development Workbench")
        self.setGeometry(100, 100, 1400, 900)

        # Restore window geometry if available
        geometry = self.config_manager.get_window_geometry()
        if geometry:
            try:
                geom_data = geometry.get('geometry')
                state_data = geometry.get('state')

                # Handle geometry data (could be bytes or string)
                if isinstance(geom_data, str):
                    geom_data = geom_data.encode('latin1')
                if isinstance(state_data, str):
                    state_data = state_data.encode('latin1')

                self.restoreGeometry(geom_data)
                self.restoreState(state_data)
            except Exception as e:
                print(f"Warning: Could not restore window geometry: {e}")

        self._setup_ui()
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
                    "• Browse for the executable manually\n"
                    "• Continue without backend (limited functionality)\n\n"
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
        """Setup the main UI with docks"""
        # Set the code editor as the central widget
        self.code_editor = CodeEditorWidget()
        self.setCentralWidget(self.code_editor)

        # Create docks
        self._create_repository_dock()
        self._create_console_dock()
        self._create_diff_dock()
        self._create_artifacts_dock()

        # Setup dock layout
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        # Tabify the bottom docks
        self.tabifyDockWidget(self.console_dock, self.diff_dock)
        self.tabifyDockWidget(self.diff_dock, self.artifacts_dock)

        # Set initial focus
        self.console_dock.raise_()

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
        """Create the console and prompt input dock"""
        self.console_dock = QDockWidget("Console", self)
        self.console_dock.setObjectName("Console")
        self.console_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        console_widget_container = QWidget()
        console_layout = QVBoxLayout(console_widget_container)

        # Console for output
        self.console_widget = QTextEdit()
        self.console_widget.setReadOnly(True)
        self.console_widget.setFont(QFont("Consolas", 10))
        console_layout.addWidget(self.console_widget)

        # Input area
        input_layout = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(80)
        self.prompt_input.setFont(QFont("Consolas", 10))
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        input_layout.addWidget(self.prompt_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self._send_prompt)
        input_layout.addWidget(send_button)

        console_layout.addLayout(input_layout)
        self.console_dock.setWidget(console_widget_container)

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

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

    def _create_artifacts_dock(self):
        """Create artifacts dock"""
        self.artifacts_dock = QDockWidget("Artifacts", self)
        self.artifacts_dock.setObjectName("Artifacts")
        self.artifacts_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Artifacts list
        self.artifacts_list = QTreeWidget()
        self.artifacts_list.setHeaderLabel("Generated Files")
        self.artifacts_list.itemDoubleClicked.connect(self._on_artifact_double_clicked)

        self.artifacts_dock.setWidget(self.artifacts_list)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.artifacts_dock)

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
        console_dock_action.setText("Console")
        view_menu.addAction(console_dock_action)

        diff_dock_action = self.diff_dock.toggleViewAction()
        diff_dock_action.setText("Diff Viewer")
        view_menu.addAction(diff_dock_action)

        artifacts_dock_action = self.artifacts_dock.toggleViewAction()
        artifacts_dock_action.setText("Artifacts")
        view_menu.addAction(artifacts_dock_action)

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
        """Setup toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setObjectName("Main Toolbar")

        # Repository actions
        open_repo_action = QAction("Open Repo", self)
        open_repo_action.triggered.connect(self._open_repository)
        toolbar.addAction(open_repo_action)

        toolbar.addSeparator()

        # File actions
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_current_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # AI actions
        send_prompt_action = QAction("Send Prompt", self)
        send_prompt_action.triggered.connect(self._send_prompt)
        toolbar.addAction(send_prompt_action)

        toolbar.addSeparator()

        # Task actions
        edit_task_action = QAction("AI Edit", self)
        edit_task_action.triggered.connect(self._run_edit_task)
        toolbar.addAction(edit_task_action)

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()

        # Backend status
        self.backend_status_label = QLabel("Backend: Disconnected")
        self.status_bar.addWidget(self.backend_status_label)

        # Repository status
        self.repo_status_label = QLabel("No repository")
        self.status_bar.addWidget(self.repo_status_label)

        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def _load_initial_state(self):
        """Load initial application state"""
        # Load recent repositories
        recent_repos = self.config_manager.get_recent_repositories(5)
        if recent_repos:
            # Could show recent repos menu here
            pass

    def _open_repository(self):
        """Open repository selection dialog"""
        repo_path = QFileDialog.getExistingDirectory(
            self, "Select Repository Directory"
        )

        if repo_path:
            self._load_repository(repo_path)

    def _load_repository(self, repo_path: str):
        """Load a repository"""
        try:
            # Check if it's a git repository
            git_dir = Path(repo_path) / ".git"
            if not git_dir.exists():
                QMessageBox.warning(
                    self, "Not a Git Repository",
                    f"The selected directory is not a Git repository:\n{repo_path}"
                )
                return

            # Create repository object
            repo_name = Path(repo_path).name
            repo = Repository(
                path=repo_path,
                name=repo_name,
                current_branch="main"  # TODO: Get actual branch
            )

            self.current_repository = repo
            self.config_manager.add_repository(repo)
            self.config_manager.update_repository_last_opened(repo_path)

            # Update UI
            self.repo_info_label.setText(f"Repository: {repo.display_name}")
            self.repo_status_label.setText(f"Repo: {repo_name}")

            # Load repository files
            self._load_repository_files(repo_path)

            # Set working directory for backend operations
            if self.backend and self.backend.running:
                # Ensure path uses forward slashes for JSON compatibility
                normalized_path = repo_path.replace("\\", "/")
                main_logger.info(f"Setting backend working directory to: {normalized_path}")
                override_op = Operation.create_override_turn_context(normalized_path)
                self.backend.send_op(override_op.model_dump())

            # Emit signal
            self.repository_opened.emit(repo_path)

        except Exception as e:
            QMessageBox.critical(
                self, "Error Loading Repository",
                f"Failed to load repository:\n{str(e)}"
            )

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
                        item.setText(0, f"📁 {item_path.name}")
                        # Add dummy child to make it expandable
                        dummy = QTreeWidgetItem(item)
                        dummy.setText(0, "Loading...")
                    else:
                        item.setText(0, f"📄 {item_path.name}")

                    # Store full path
                    item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))

                    if item_path.is_dir():
                        add_items(item, item_path)

            root_item = QTreeWidgetItem(self.repo_tree)
            root_item.setText(0, repo_path_obj.name)
            root_item.setData(0, Qt.ItemDataRole.UserRole, str(repo_path_obj))

            add_items(root_item, repo_path_obj)
            self.repo_tree.expandItem(root_item)

        except Exception as e:
            self.console_widget.append(f"Error loading repository files: {str(e)}")

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
        """Handle request to apply a diff."""
        current_file = self.code_editor.get_current_file_path()
        if not current_file:
            QMessageBox.warning(self, "No File", "An open file is required to apply a patch.")
            return

        selected_diff_text = self.diff_viewer.diff_widget.get_selected_diff_text()
        if not selected_diff_text:
            QMessageBox.information(self, "No Changes Selected", "Please select one or more hunks to apply.")
            return

        try:
            # Get the original content from the editor
            original_content = self.code_editor.editor.toPlainText()
            
            # Create a patch set from the diff text
            patch_set = patch.from_string(selected_diff_text.encode('utf-8'))
            
            # Apply the patch in memory
            patched_content = patch_set.apply(original_content.encode('utf-8'))
            
            if patched_content:
                # Update the editor with the patched content
                self.code_editor.set_text(patched_content.decode('utf-8'))
                self.status_bar.showMessage("Changes applied successfully.", 3000)
                
                # Clear the diff viewer and bring focus to the editor
                self.diff_viewer.clear()
                self.code_editor.editor.setFocus()
            else:
                QMessageBox.critical(self, "Patch Failed", "The selected changes could not be applied.")

        except Exception as e:
            QMessageBox.critical(self, "Error Applying Patch", f"An unexpected error occurred: {e}")

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
                self._add_message("system", "❌ Backend not connected. Please check configuration.")
                return

            main_logger.info("Backend is available, preparing operation")

            # Prepare context
            repo_context = {}
            cwd_path = None
            if self.current_repository:
                repo_context["repository_path"] = self.current_repository.path
                cwd_path = self.current_repository.path
                main_logger.info(f"Repository context: {repo_context}")
            else:
                # Use current working directory as fallback
                import os
                cwd_path = os.getcwd()
                repo_context["repository_path"] = cwd_path
                main_logger.info(f"No repository selected, using current working directory: {cwd_path}")

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
                    self._add_message("system", f"📝 Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user turn operation with file context for: {current_file}")
                else:
                    op = Operation.create_user_turn(prompt, normalized_cwd)
                    self._add_message("system", "💬 Sending general prompt...")
                    main_logger.info("Created user turn operation")
            else:
                # Fallback to user_input if no repository is selected
                if current_file:
                    enhanced_prompt = f"Regarding the file '{Path(current_file).name}': {prompt}"
                    op = Operation.create_user_input(enhanced_prompt)
                    self._add_message("system", f"📝 Sending request for {Path(current_file).name}...")
                    main_logger.info(f"Created user input operation with file context for: {current_file}")
                else:
                    op = Operation.create_user_input(prompt)
                    self._add_message("system", "💬 Sending general prompt...")
                    main_logger.info("Created user input operation")

            op.context = repo_context

            # Log the full operation for debugging
            op_json = op.model_dump_json(indent=2)
            main_logger.info(f"Operation JSON: {op_json}")
            self.console_widget.append(f"<font color='grey'><i>Sending op: {op_json}</i></font>")

            main_logger.info("Calling backend.send_op()")
            result = self.backend.send_op(op.model_dump())
            main_logger.info(f"backend.send_op() returned: {result}")

            self.status_bar.showMessage("⏳ Waiting for AI response...", 0)

        except Exception as e:
            main_logger.error(f"Exception in _send_prompt: {str(e)}", exc_info=True)
            self._add_message("system", f"❌ Error sending prompt: {str(e)}")
            self.status_bar.clearMessage()

    def _add_message(self, role: str, content: str):
        """Add a message to the console"""
        timestamp = time.strftime("%H:%M:%S")
        if role == "user":
            self.console_widget.append(f"<b>[{timestamp}] You:</b> {content}")
        elif role == "assistant":
            self.console_widget.append(f"<b>[{timestamp}] AI:</b> {content}")
        elif role == "system":
            self.console_widget.append(f"<font color='red'><b>[{timestamp}] System:</b> {content}</font>")
        else:
            self.console_widget.append(f"<b>[{timestamp}] {role.title()}:</b> {content}")

        # Auto scroll to bottom
        cursor = self.console_widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.console_widget.setTextCursor(cursor)

    def _start_login(self):
        """Start ChatGPT login process"""
        if self.backend:
            op = Operation.create_login_request()
            self.backend.send_op(op.model_dump())

    def _run_test_task(self):
        """Run tests for the current project."""
        if not self.current_repo:
            QMessageBox.warning(self, "No Repository", "Please select a repository first.")
            return

        # Create a test task
        task = Task(
            id=f"test_{int(time.time())}",
            name="Run Tests",
            type="run_tests",
            parameters={
                "command": ["pytest", "-v"],
                "repository_path": str(self.current_repo.path)
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
            self.current_reasoning += delta

        # Handle reasoning section break (display accumulated reasoning)
        elif event_type == "agent_reasoning_section_break":
            if self.current_reasoning.strip():
                # Clean up the reasoning text (remove markdown formatting)
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    self._add_message("system", f"🤔 {clean_reasoning}")
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
            if self.current_reasoning.strip():
                clean_reasoning = self.current_reasoning.replace("**", "").strip()
                if clean_reasoning:
                    self._add_message("system", f"🤔 {clean_reasoning}")
                self.current_reasoning = ""

        # Handle agent edit file response (the diff)
        elif event_type == "agent_edit_file_response":
            diff = event_obj.get("diff", "")
            file_path = event_obj.get("file_path", "unknown_file")
            if diff:
                self._add_message("system", f"✅ Received diff for {file_path}")
                self.diff_viewer.set_diff_content(diff, file_path)
                self.diff_dock.raise_()  # Bring the diff dock to the front
            else:
                self._add_message("system", f"⚠️ Received an empty diff for {file_path}")

        # Handle login events
        elif event_type == "login_chat_gpt_response":
            auth_url = event_obj.get("auth_url")
            if auth_url:
                import webbrowser
                webbrowser.open(auth_url)
                self._add_message("system", "🔗 Please complete the login in your browser.")

        elif event_type == "login_chat_gpt_complete":
            if event_obj.get("success"):
                self._add_message("system", "✅ Login successful!")
            else:
                error = event_obj.get("error", "Unknown error")
                self._add_message("system", f"❌ Login failed: {error}")

        # Handle task started (clear any previous accumulations)
        elif event_type == "task_started":
            # Clear any accumulated messages from previous tasks
            self.current_reasoning = ""
            self.current_message = ""
            self.last_task_id = task_id

        # Show other events only if they contain useful information
        else:
            # Only show events that might be relevant to the user
            if event_type not in ["mcp_connection_manager"]:
                pretty_event = json.dumps(event_obj, indent=2)
                self._add_message("system", f"📋 Event: {event_type}")

    @Slot(str)
    def _on_backend_error(self, error_message):
        """Handle backend errors"""
        self.console_widget.append(f"<font color='red'><b>Backend Error:</b> {error_message}</font>")
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
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog not implemented yet")

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
        self.console_widget.append(f"<font color='red'><b>Backend Error:</b> {error_message}</font>")
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
            self._add_message("system", f"⚠️ Backend stopped with exit code: {exit_code}")

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
        self._add_message("system", f"🔄 Started task: {task_id}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    @Slot(str, str, object)
    def _on_task_completed(self, workflow_id: str, task_id: str, result):
        """Handle task completed"""
        main_logger.info(f"_on_task_completed: workflow={workflow_id}, task={task_id}, result={result}")
        self._add_message("system", f"✅ Task completed: {task_id}")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Task {task_id} completed successfully", 3000)

    @Slot(str, str, str)
    def _on_task_failed(self, workflow_id: str, task_id: str, error: str):
        """Handle task failed"""
        main_logger.error(f"_on_task_failed: workflow={workflow_id}, task={task_id}, error={error}")
        self._add_message("system", f"❌ Task failed: {task_id} - {error}")
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
        self._add_message("system", f"🚀 Started workflow: {workflow_id}")

    @Slot(str)
    def _on_workflow_completed(self, workflow_id: str):
        """Handle workflow completed"""
        main_logger.info(f"_on_workflow_completed: workflow={workflow_id}")
        self._add_message("system", f"🎉 Workflow completed: {workflow_id}")
        self.status_bar.showMessage("Workflow completed successfully", 3000)

    @Slot(str, str)
    def _on_workflow_failed(self, workflow_id: str, error: str):
        """Handle workflow failed"""
        main_logger.error(f"_on_workflow_failed: workflow={workflow_id}, error={error}")
        self._add_message("system", f"💥 Workflow failed: {workflow_id} - {error}")
        self.status_bar.showMessage(f"Workflow failed: {error}", 5000)
