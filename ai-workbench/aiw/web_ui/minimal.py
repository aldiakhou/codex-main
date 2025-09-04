import sys
import json
import os
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QSplitter
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Slot, QJsonValue, Signal, QTimer, QThread, Qt
from PySide6.QtGui import QFont

# Import our backend service
import sys
import os

# Add the ai-workbench directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_workbench_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, ai_workbench_dir)

try:
    from ai_workbench.aiw.core.backend_service import BackendService
    from ai_workbench.aiw.core.models import Operation, Event, BackendConfig
except ImportError:
    try:
        # Try relative imports
        from ..core.backend_service import BackendService
        from ..core.models import Operation, Event, BackendConfig
    except ImportError:
        # Fallback - create mock classes for testing
        print("Warning: Could not import backend modules. Running in demo mode.")
        
        class MockBackendService:
            def __init__(self, *args, **kwargs):
                pass
        
        class MockOperation:
            @staticmethod
            def create_user_turn(text, cwd):
                return {"id": "mock_op", "op": {"type": "user_turn", "items": [{"type": "text", "text": text}]}}
            
            @staticmethod
            def create_login_request():
                # Deprecated: login is handled via `codex login`, not the proto stream.
                raise NotImplementedError("Login is handled out-of-band via 'codex login'.")
        
        class MockEvent:
            pass
        
        class MockBackendConfig:
            pass
        
        # Assign mock classes
        BackendService = MockBackendService
        Operation = MockOperation
        Event = MockEvent
        BackendConfig = MockBackendConfig

class WebBackend(QObject):
    """
    Enhanced backend class that integrates with the BackendService and provides
    a rich API for the web UI to interact with the AI workbench.
    """
    
    # Signals to communicate with the web UI
    status_changed = Signal(str)  # Connection status
    event_received = Signal(dict)  # Backend events
    log_message = Signal(str)  # Log messages
    operation_progress = Signal(str, int, str)  # operation_id, progress, message
    
    def __init__(self, backend_service=None):
        super().__init__()
        self.backend_service = backend_service
        self.operation_counter = 0
        
        # Connect to backend service signals if available
        if self.backend_service:
            self._connect_backend_signals()
    
    def _connect_backend_signals(self):
        """Connect to the BackendService signals"""
        if self.backend_service:
            self.backend_service.new_event.connect(self._handle_backend_event)
            self.backend_service.connection_status_changed.connect(self.status_changed.emit)
            self.backend_service.backend_error.connect(self._handle_backend_error)
            self.backend_service.operation_progress.connect(self._handle_operation_progress)
    
    @Slot(str)
    def send_user_input(self, text):
        """Send user input to the backend service"""
        if not self.backend_service:
            self.log_message.emit("Backend service not available")
            return
        
        try:
            # Create a user turn operation
            cwd = os.getcwd()
            operation = Operation.create_user_turn(text, cwd)
            
            if self.backend_service.send_op(operation.model_dump()):
                self.log_message.emit(f"Sent operation: {operation.id}")
                self.operation_progress.emit(operation.id, 0, "Operation sent to backend")
            else:
                self.log_message.emit("Failed to send operation")
                
        except Exception as e:
            self.log_message.emit(f"Error sending operation: {str(e)}")
    
    @Slot(str)
    def send_login_request(self):
        """Trigger Codex login flow (opens browser)"""
        if not self.backend_service:
            self.log_message.emit("Backend service not available")
            return
        
        try:
            # Run login using the backend helper; progress will be reported via operation_progress signal.
            self.backend_service.login_with_chatgpt()
            self.log_message.emit("Login initiated; complete in the browser window")
        except Exception as e:
            self.log_message.emit(f"Error sending login request: {str(e)}")
    
    @Slot()
    def start_backend(self):
        """Start the backend service"""
        if not self.backend_service:
            self.log_message.emit("Backend service not available")
            return
        
        try:
            self.backend_service.start()
            self.log_message.emit("Backend service started")
        except Exception as e:
            self.log_message.emit(f"Error starting backend: {str(e)}")
    
    @Slot()
    def stop_backend(self):
        """Stop the backend service"""
        if not self.backend_service:
            return
        
        try:
            self.backend_service.stop()
            self.log_message.emit("Backend service stopped")
        except Exception as e:
            self.log_message.emit(f"Error stopping backend: {str(e)}")
    
    @Slot(str)
    def set_working_directory(self, path):
        """Set the working directory for operations"""
        try:
            if os.path.exists(path):
                os.chdir(path)
                self.log_message.emit(f"Working directory changed to: {path}")
            else:
                self.log_message.emit(f"Directory does not exist: {path}")
        except Exception as e:
            self.log_message.emit(f"Error changing directory: {str(e)}")
    
    @Slot()
    def get_current_directory(self):
        """Get the current working directory"""
        return os.getcwd()
    
    @Slot()
    def get_system_info(self):
        """Get system information"""
        import platform
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "current_directory": os.getcwd()
        }
        return info
    
    def _handle_backend_event(self, event):
        """Handle events from the backend service"""
        self.event_received.emit(event)
    
    def _handle_backend_error(self, error_message):
        """Handle errors from the backend service"""
        self.log_message.emit(f"Backend Error: {error_message}")
    
    def _handle_operation_progress(self, operation_id, progress, message):
        """Handle operation progress updates"""
        self.operation_progress.emit(operation_id, progress, message)


class MainWindow(QMainWindow):
    """
    Enhanced main application window with full backend integration and modern UI.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Workbench - Web UI")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize backend service
        self.backend_service = None
        self.init_backend_service()

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Create web view
        self.webview = QWebEngineView()
        splitter.addWidget(self.webview)

        # Create control panel
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)

        # Set splitter sizes (40% web view, 60% control panel)
        splitter.setSizes([480, 720])

        # Set up QWebChannel
        self.setup_web_channel()

        # Load the HTML content
        self.load_html_content()

        # Set up status bar
        self.statusBar().showMessage("Ready")
    
    def init_backend_service(self):
        """Initialize the backend service"""
        try:
            # Create a default backend configuration
            config = BackendConfig()
            
            # You can customize the codex path here
            codex_path = config.codex_path or "codex"  # Default to "codex" in PATH
            
            # Initialize backend service
            self.backend_service = BackendService(
                codex_executable_path=codex_path,
                profile=config.profile,
                custom_env=config.environment_variables
            )
            
            print(f"Backend service initialized with codex path: {codex_path}")
            
        except Exception as e:
            print(f"Error initializing backend service: {e}")
            self.backend_service = None
    
    def create_control_panel(self):
        """Create the control panel with backend controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Backend Control Panel")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        # Backend controls
        controls_group = QWidget()
        controls_layout = QHBoxLayout(controls_group)

        self.start_btn = QPushButton("Start Backend")
        self.start_btn.clicked.connect(self.start_backend)
        controls_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Backend")
        self.stop_btn.clicked.connect(self.stop_backend)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        controls_layout.addWidget(self.login_btn)

        layout.addWidget(controls_group)

        # Log output
        log_label = QLabel("Backend Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_output)

        # Status
        self.status_label = QLabel("Status: Disconnected")
        layout.addWidget(self.status_label)

        return panel
    
    def setup_web_channel(self):
        """Set up the QWebChannel for communication with the web UI"""
        self.channel = QWebChannel()
        self.web_backend = WebBackend(self.backend_service)
        
        # Connect signals from web backend to UI
        self.web_backend.status_changed.connect(self.update_status)
        self.web_backend.log_message.connect(self.add_log_message)
        self.web_backend.event_received.connect(self.handle_backend_event)
        self.web_backend.operation_progress.connect(self.handle_operation_progress)
        
        # Register the backend object
        self.channel.registerObject("backend", self.web_backend)
        self.webview.page().setWebChannel(self.channel)
    
    def load_html_content(self):
        """Load the enhanced HTML content with Tailwind CSS"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Workbench - Web UI</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                body {
                    font-family: 'Inter', sans-serif;
                }
                .gradient-bg {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .glass-effect {
                    backdrop-filter: blur(10px);
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .message-bubble {
                    max-width: 80%;
                    word-wrap: break-word;
                }
                .typing-indicator {
                    display: inline-flex;
                    align-items: center;
                    padding: 8px 12px;
                    background: #e5e7eb;
                    border-radius: 18px;
                }
                .typing-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #6b7280;
                    margin: 0 2px;
                    animation: typing 1.4s infinite;
                }
                .typing-dot:nth-child(2) {
                    animation-delay: 0.2s;
                }
                .typing-dot:nth-child(3) {
                    animation-delay: 0.4s;
                }
                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                    }
                    30% {
                        transform: translateY(-10px);
                    }
                }
            </style>
        </head>
        <body class="bg-gray-50 min-h-screen">
            <!-- Header -->
            <header class="gradient-bg text-white shadow-lg">
                <div class="container mx-auto px-6 py-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <i class="fas fa-robot text-2xl"></i>
                            <h1 class="text-2xl font-bold">AI Workbench</h1>
                        </div>
                        <div class="flex items-center space-x-4">
                            <div id="connection-status" class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                                <span class="text-sm">Disconnected</span>
                            </div>
                            <button id="theme-toggle" class="p-2 rounded-lg hover:bg-white hover:bg-opacity-20 transition-colors">
                                <i class="fas fa-moon"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <div class="container mx-auto px-6 py-8">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Chat Interface -->
                    <div class="lg:col-span-2">
                        <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                            <div class="p-4 border-b border-gray-200">
                                <h2 class="text-xl font-semibold text-gray-800">
                                    <i class="fas fa-comments mr-2"></i>AI Assistant
                                </h2>
                            </div>
                            
                            <!-- Messages Container -->
                            <div id="messages-container" class="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
                                <div class="flex justify-start">
                                    <div class="message-bubble bg-white p-3 rounded-lg shadow">
                                        <p class="text-gray-800">Hello! I'm your AI assistant. How can I help you today?</p>
                                        <span class="text-xs text-gray-500 mt-1 block">System • Just now</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Input Area -->
                            <div class="p-4 border-t border-gray-200 bg-white">
                                <div class="flex space-x-2">
                                    <input 
                                        type="text" 
                                        id="user-input" 
                                        placeholder="Type your message here..."
                                        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        onkeypress="if(event.key==='Enter') sendMessage()"
                                    >
                                    <button 
                                        onclick="sendMessage()"
                                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        <i class="fas fa-paper-plane mr-2"></i>Send
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Control Panel -->
                    <div class="space-y-6">
                        <!-- Backend Status -->
                        <div class="bg-white rounded-xl shadow-lg p-6">
                            <h3 class="text-lg font-semibold text-gray-800 mb-4">
                                <i class="fas fa-server mr-2"></i>Backend Status
                            </h3>
                            <div id="backend-status" class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-gray-600">Connection:</span>
                                    <span id="connection-text" class="text-red-600 font-medium">Disconnected</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-gray-600">Operations:</span>
                                    <span id="operations-count" class="text-gray-800 font-medium">0</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-gray-600">Last Activity:</span>
                                    <span id="last-activity" class="text-gray-800 font-medium">Never</span>
                                </div>
                            </div>
                        </div>

                        <!-- Quick Actions -->
                        <div class="bg-white rounded-xl shadow-lg p-6">
                            <h3 class="text-lg font-semibold text-gray-800 mb-4">
                                <i class="fas fa-bolt mr-2"></i>Quick Actions
                            </h3>
                            <div class="space-y-2">
                                <button 
                                    onclick="startBackend()"
                                    class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                >
                                    <i class="fas fa-play mr-2"></i>Start Backend
                                </button>
                                <button 
                                    onclick="stopBackend()"
                                    class="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    <i class="fas fa-stop mr-2"></i>Stop Backend
                                </button>
                                <button 
                                    onclick="login()"
                                    class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                                >
                                    <i class="fas fa-sign-in-alt mr-2"></i>Login
                                </button>
                                <button 
                                    onclick="getSystemInfo()"
                                    class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    <i class="fas fa-info-circle mr-2"></i>System Info
                                </button>
                            </div>
                        </div>

                        <!-- Working Directory -->
                        <div class="bg-white rounded-xl shadow-lg p-6">
                            <h3 class="text-lg font-semibold text-gray-800 mb-4">
                                <i class="fas fa-folder mr-2"></i>Working Directory
                            </h3>
                            <div class="space-y-3">
                                <input 
                                    type="text" 
                                    id="working-dir" 
                                    placeholder="Enter directory path..."
                                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                <button 
                                    onclick="setWorkingDirectory()"
                                    class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                                >
                                    <i class="fas fa-folder-open mr-2"></i>Set Directory
                                </button>
                                <div id="current-dir" class="text-sm text-gray-600 bg-gray-100 p-2 rounded-lg">
                                    Current: Loading...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Global variables
                let backend = null;
                let operationsCount = 0;
                let isProcessing = false;

                // Initialize QWebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    backend = channel.objects.backend;
                    
                    // Connect to signals
                    backend.status_changed.connect(updateConnectionStatus);
                    backend.log_message.connect(addLogMessage);
                    backend.event_received.connect(handleBackendEvent);
                    backend.operation_progress.connect(handleOperationProgress);
                    
                    // Initialize UI
                    updateConnectionStatus('disconnected');
                    getCurrentDirectory();
                });

                // Connection status handling
                function updateConnectionStatus(status) {
                    const statusElement = document.getElementById('connection-status');
                    const statusText = document.getElementById('connection-text');
                    
                    statusElement.className = 'flex items-center space-x-2';
                    
                    if (status === 'connected') {
                        statusElement.innerHTML = '<div class="w-3 h-3 bg-green-500 rounded-full"></div><span class="text-sm">Connected</span>';
                        statusText.textContent = 'Connected';
                        statusText.className = 'text-green-600 font-medium';
                    } else if (status === 'connecting') {
                        statusElement.innerHTML = '<div class="w-3 h-3 bg-yellow-500 rounded-full"></div><span class="text-sm">Connecting</span>';
                        statusText.textContent = 'Connecting';
                        statusText.className = 'text-yellow-600 font-medium';
                    } else {
                        statusElement.innerHTML = '<div class="w-3 h-3 bg-red-500 rounded-full"></div><span class="text-sm">Disconnected</span>';
                        statusText.textContent = 'Disconnected';
                        statusText.className = 'text-red-600 font-medium';
                    }
                }

                // Message handling
                function sendMessage() {
                    const input = document.getElementById('user-input');
                    const message = input.value.trim();
                    
                    if (!message || !backend || isProcessing) return;
                    
                    // Add user message to chat
                    addMessageToChat(message, 'user');
                    
                    // Clear input
                    input.value = '';
                    
                    // Show typing indicator
                    showTypingIndicator();
                    
                    // Send to backend
                    isProcessing = true;
                    backend.send_user_input(message);
                }

                function addMessageToChat(message, sender) {
                    const container = document.getElementById('messages-container');
                    const messageDiv = document.createElement('div');
                    
                    const isUser = sender === 'user';
                    const alignClass = isUser ? 'justify-end' : 'justify-start';
                    const bgClass = isUser ? 'bg-blue-600 text-white' : 'bg-white text-gray-800';
                    
                    messageDiv.className = `flex ${alignClass}`;
                    messageDiv.innerHTML = `
                        <div class="message-bubble ${bgClass} p-3 rounded-lg shadow">
                            <p>${escapeHtml(message)}</p>
                            <span class="text-xs ${isUser ? 'text-blue-200' : 'text-gray-500'} mt-1 block">
                                ${isUser ? 'You' : 'AI Assistant'} • Just now
                            </span>
                        </div>
                    `;
                    
                    container.appendChild(messageDiv);
                    container.scrollTop = container.scrollHeight;
                }

                function showTypingIndicator() {
                    const container = document.getElementById('messages-container');
                    const typingDiv = document.createElement('div');
                    typingDiv.id = 'typing-indicator';
                    typingDiv.className = 'flex justify-start';
                    typingDiv.innerHTML = `
                        <div class="typing-indicator">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    `;
                    
                    container.appendChild(typingDiv);
                    container.scrollTop = container.scrollHeight;
                }

                function hideTypingIndicator() {
                    const indicator = document.getElementById('typing-indicator');
                    if (indicator) {
                        indicator.remove();
                    }
                    isProcessing = false;
                }

                // Backend event handling
                function handleBackendEvent(event) {
                    hideTypingIndicator();
                    
                    if (event.msg && event.msg.type === 'agent_message') {
                        // Add AI response to chat
                        const content = event.msg.content || 'No content';
                        addMessageToChat(content, 'ai');
                    }
                    
                    // Update last activity
                    document.getElementById('last-activity').textContent = new Date().toLocaleTimeString();
                }

                function handleOperationProgress(operationId, progress, message) {
                    const progressText = `${progress}% - ${message}`;
                    console.log(`Operation ${operationId}: ${progressText}`);
                }

                // Backend control functions
                function startBackend() {
                    if (backend) {
                        backend.start_backend();
                    }
                }

                function stopBackend() {
                    if (backend) {
                        backend.stop_backend();
                    }
                }

                function login() {
                    if (backend) {
                        backend.send_login_request();
                    }
                }

                function getSystemInfo() {
                    if (backend) {
                        const info = backend.get_system_info();
                        alert(JSON.stringify(info, null, 2));
                    }
                }

                function setWorkingDirectory() {
                    const path = document.getElementById('working-dir').value;
                    if (backend && path) {
                        backend.set_working_directory(path);
                        getCurrentDirectory();
                    }
                }

                function getCurrentDirectory() {
                    if (backend) {
                        const currentDir = backend.get_current_directory();
                        document.getElementById('current-dir').textContent = `Current: ${currentDir}`;
                        document.getElementById('working-dir').value = currentDir;
                    }
                }

                // Utility functions
                function escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }

                function addLogMessage(message) {
                    console.log('Backend:', message);
                }

                // Theme toggle
                document.getElementById('theme-toggle').addEventListener('click', function() {
                    document.body.classList.toggle('dark');
                    const icon = this.querySelector('i');
                    icon.classList.toggle('fa-moon');
                    icon.classList.toggle('fa-sun');
                });

                // Initialize on load
                document.addEventListener('DOMContentLoaded', function() {
                    const input = document.getElementById('user-input');
                    input.focus();
                });
            </script>
        </body>
        </html>
        """
        
        self.webview.setHtml(html_content)
    
    def update_status(self, status):
        """Update the connection status"""
        self.status_label.setText(f"Status: {status.capitalize()}")
        self.statusBar().showMessage(f"Backend status: {status}")
        
        # Update button states
        if status == "connected":
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.login_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.login_btn.setEnabled(False)
    
    def add_log_message(self, message):
        """Add a message to the log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
    
    def handle_backend_event(self, event):
        """Handle events from the backend"""
        self.add_log_message(f"Event received: {event}")
    
    def handle_operation_progress(self, operation_id, progress, message):
        """Handle operation progress updates"""
        self.add_log_message(f"Operation {operation_id}: {progress}% - {message}")
    
    def start_backend(self):
        """Start the backend service"""
        if self.web_backend:
            self.web_backend.start_backend()
    
    def stop_backend(self):
        """Stop the backend service"""
        if self.web_backend:
            self.web_backend.stop_backend()
    
    def login(self):
        """Start Codex login flow"""
        if self.web_backend:
            self.web_backend.send_login_request()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("AI Workbench Web UI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AI Workbench")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())
