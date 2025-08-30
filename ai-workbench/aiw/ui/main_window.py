"""
Enhanced main window with dock-based layout for AI Development Workbench
"""
import json
import os
import time
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal, Slot, QTimer
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


class MainWindow(QMainWindow):
    """Enhanced main window with dock-based layout"""

    # Signals
    repository_opened = Signal(str)  # repository path
    file_selected = Signal(str)     # file path

    def __init__(self):
        super().__init__()
        self.config_manager = get_config_manager()
        self.current_repository: Optional[Repository] = None
        self.backend: Optional[BackendService] = None

        # Initialize task runner
        self.task_runner = get_workflow_runner()
        self._connect_task_signals()

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
        """Initialize the backend service"""
        codex_path = self.config_manager.get_codex_path()
        if not codex_path:
            QMessageBox.warning(
                self, "Codex Not Found",
                "Codex executable not found. Please configure the path in settings."
            )
            return

        self.backend = BackendService(codex_path)
        self.backend.new_event.connect(self._on_backend_event)
        self.backend.backend_error.connect(self._on_backend_error)
        self.backend.backend_started.connect(self._on_backend_started)
        self.backend.backend_stopped.connect(self._on_backend_stopped)
        self.backend.start()

    def _setup_ui(self):
        """Setup the main UI with docks"""
        # Create central widget with chat interface
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)

        # Console for output
        self.console_widget = QTextEdit()
        self.console_widget.setReadOnly(True)
        self.console_widget.setFont(QFont("Consolas", 10))
        central_layout.addWidget(self.console_widget)

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

        central_layout.addLayout(input_layout)
        self.setCentralWidget(central_widget)

        # Create docks
        self._create_repository_dock()
        self._create_editor_dock()
        self._create_diff_dock()
        self._create_artifacts_dock()

        # Setup dock layout
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)

    def _create_repository_dock(self):
        """Create repository explorer dock"""
        self.repo_dock = QDockWidget("Repository", self)
        self.repo_dock.setObjectName("Repository")
        self.repo_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)

        # Repository tree widget
        self.repo_tree = QTreeWidget()
        self.repo_tree.setHeaderLabel("Files")
        self.repo_tree.itemDoubleClicked.connect(self._on_file_double_clicked)

        # Repository actions
        repo_widget = QWidget()
        repo_layout = QVBoxLayout(repo_widget)

        # Repository info label
        self.repo_info_label = QLabel("No repository opened")
        repo_layout.addWidget(self.repo_info_label)

        repo_layout.addWidget(self.repo_tree)
        self.repo_dock.setWidget(repo_widget)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.repo_dock)

    def _create_editor_dock(self):
        """Create code editor dock"""
        self.editor_dock = QDockWidget("Editor", self)
        self.editor_dock.setObjectName("Editor")
        self.editor_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        # Enhanced code editor widget
        self.code_editor = CodeEditorWidget()

        # Editor actions
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        # File info label
        self.editor_file_label = QLabel("No file selected")
        editor_layout.addWidget(self.editor_file_label)

        editor_layout.addWidget(self.code_editor)
        self.editor_dock.setWidget(editor_widget)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.editor_dock)

    def _create_diff_dock(self):
        """Create diff viewer dock"""
        self.diff_dock = QDockWidget("Diff", self)
        self.diff_dock.setObjectName("Diff")
        self.diff_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)

        # Enhanced diff viewer widget
        self.diff_viewer = DiffViewWidget()

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

        # Tabify with diff dock
        self.tabifyDockWidget(self.diff_dock, self.artifacts_dock)

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

        editor_dock_action = self.editor_dock.toggleViewAction()
        editor_dock_action.setText("Code Editor")
        view_menu.addAction(editor_dock_action)

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

        test_task_action = QAction("Run &Tests", self)
        test_task_action.triggered.connect(self._run_test_task)
        tools_menu.addAction(test_task_action)

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

        run_tests_action = QAction("Run Tests", self)
        run_tests_action.triggered.connect(self._run_test_task)
        toolbar.addAction(run_tests_action)

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

    def _on_file_double_clicked(self, item, column):
        """Handle file double-click in repository tree"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path and Path(file_path).is_file():
            self._load_file_into_editor(file_path)

    def _load_file_into_editor(self, file_path: str):
        """Load a file into the code editor"""
        success = self.code_editor.load_file(file_path)
        if success:
            self.editor_file_label.setText(f"File: {self.code_editor.editor.get_current_file_name()}")
            self.file_selected.emit(file_path)
        else:
            self.editor_file_label.setText("Failed to load file")

    def _on_artifact_double_clicked(self, item, column):
        """Handle artifact double-click"""
        # TODO: Implement artifact viewing
        pass

    def _send_prompt(self):
        """Send a prompt to the AI backend."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return

        # Clear any accumulated messages from previous interactions
        self.current_reasoning = ""
        self.current_message = ""

        # Add user message to chat
        self._add_message("user", prompt)

        # Clear input
        self.prompt_input.clear()

        # Send to backend
        try:
            if self.backend:
                op = Operation.create_user_input(prompt)
                self.backend.send_op(op.model_dump())
                self._add_message("system", "⏳ Sending prompt to AI backend...")
            else:
                self._add_message("system", "❌ Backend not connected. Please check Codex configuration.")
        except Exception as e:
            self._add_message("system", f"❌ Error sending prompt: {str(e)}")

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

    def _run_edit_task(self):
        """Run an AI edit task on the current file."""
        if not self.code_editor.current_file:
            QMessageBox.warning(self, "No File Selected", "Please open a file in the code editor first.")
            return

        # Get the current file content
        file_path = self.code_editor.current_file
        content = self.code_editor.get_text()
        prompt = "Please improve this code"  # This could be made configurable

        # Create an edit task
        task = Task(
            id=f"edit_{int(time.time())}",
            name="AI Edit Task",
            type="edit_file",
            parameters={
                "file_path": file_path,
                "instruction": prompt,
                "content": content
            }
        )

        # Run the task
        self.task_runner.run_single_task(task)

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
        event_obj = event.get("msg", {})
        event_type = event_obj.get("type")
        task_id = event.get("id", "")

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

    @Slot(int)
    def _on_backend_stopped(self, exit_code):
        """Handle backend stopped"""
        self.backend_status_label.setText("Backend: Disconnected")

    def _connect_task_signals(self):
        """Connect task runner signals"""
        self.task_runner.task_started.connect(self._on_task_started)
        self.task_runner.task_completed.connect(self._on_task_completed)
        self.task_runner.task_failed.connect(self._on_task_failed)
        self.task_runner.task_progress.connect(self._on_task_progress)

    def _on_task_started(self, workflow_id: str, task_id: str):
        """Handle task started"""
        self.console_widget.append(f"<b>Task Started:</b> {task_id}")
        self.status_bar.showMessage(f"Running task: {task_id}")
        self.progress_bar.setVisible(True)

    def _on_task_completed(self, workflow_id: str, task_id: str, result):
        """Handle task completed"""
        self.console_widget.append(f"<b>Task Completed:</b> {task_id}")
        self.status_bar.showMessage(f"Task completed: {task_id}", 3000)
        self.progress_bar.setVisible(False)

        # Display results in diff viewer if applicable
        if hasattr(result, 'output') and result.output:
            output_text = str(result.output)
            self.diff_viewer.set_diff_content(output_text, "Task Results")

    def _on_task_failed(self, workflow_id: str, task_id: str, error: str):
        """Handle task failed"""
        self.console_widget.append(f"<font color='red'><b>Task Failed:</b> {task_id} - {error}</font>")
        self.status_bar.showMessage(f"Task failed: {task_id}", 5000)
        self.progress_bar.setVisible(False)

    def _on_task_progress(self, workflow_id: str, task_id: str, progress: int, message: str):
        """Handle task progress"""
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(f"{task_id}: {message}")

    def _run_edit_task(self):
        """Run an edit file task"""
        current_file = self.code_editor.get_current_file_path()
        if not current_file:
            QMessageBox.warning(self, "No File Selected", "Please select a file to edit first.")
            return

        # Get instruction from user
        from PySide6.QtWidgets import QInputDialog
        import time

        instruction, ok = QInputDialog.getText(
            self, "Edit Instruction",
            "Enter your edit instruction:"
        )

        if ok and instruction:
            task = Task(
                id=f"edit_{int(time.time())}",
                name="Edit File",
                type="edit_file",
                parameters={
                    "file_path": current_file,
                    "instruction": instruction
                }
            )

            context = {"repository_path": self.current_repository.path if self.current_repository else ""}
            self.task_runner.run_single_task(task, context)

    def _run_test_task(self):
        """Run a test task"""
        if not self.current_repository:
            QMessageBox.warning(self, "No Repository", "Please open a repository first.")
            return

        import time
        task = Task(
            id=f"test_{int(time.time())}",
            name="Run Tests",
            type="run_tests",
            parameters={
                "command": ["pytest", "-v"]
            }
        )

        context = {"repository_path": self.current_repository.path}
        self.task_runner.run_single_task(task, context)

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

        # Stop backend
        if self.backend:
            self.backend.stop()

        event.accept()
