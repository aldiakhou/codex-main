import json
import os
import sys
import time
import threading
import subprocess
import logging
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QElapsedTimer

# Set up logging
import io
import codecs

class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)
        if stream is None:
            stream = sys.stdout
        # Wrap the stream with UTF-8 encoding
        self.stream = codecs.getwriter('utf-8')(stream.buffer) if hasattr(stream, 'buffer') else stream

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        UTF8StreamHandler(sys.stdout),
        logging.FileHandler('ai_workbench_debug.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('BackendService')
logger.setLevel(logging.INFO)

class BackendService(QObject):
    # Signals to communicate with the GUI thread
    new_event = Signal(dict)
    backend_started = Signal()
    backend_stopped = Signal(int)
    backend_error = Signal(str)
    connection_status_changed = Signal(str)  # "connecting", "connected", "disconnected", "error"
    operation_progress = Signal(str, int, str)  # operation_id, progress_percent, status_message
    operation_cleanup = Signal(str)  # operation_id to cleanup

    def __init__(self, codex_executable_path: str, profile: str = None, custom_env: Dict[str, str] = None, parent=None):
        super().__init__(parent)
        self.codex_executable_path = codex_executable_path
        self.profile = profile
        self.custom_env = custom_env or {}
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self._attempt_reconnect)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._send_heartbeat)
        self.last_activity = QElapsedTimer()
        self.pending_operations = {}  # Track operations and their progress
        self.running = False

    def start(self):
        """Start the backend service with improved error handling"""
        logger.info("BackendService.start() called")
        if self.running:
            logger.info("Backend service is already running.")
            return

        logger.info("Emitting connection_status_changed: connecting")
        self.connection_status_changed.emit("connecting")
        self._start_process()

    def _start_process(self):
        """Internal method to start the process using subprocess"""
        try:
            logger.info(f"Starting backend process: {self.codex_executable_path}")
            logger.info(f"Executable exists: {os.path.exists(self.codex_executable_path)}")

            # Build command with optional profile
            cmd = [self.codex_executable_path]
            if self.profile:
                cmd.extend(["-p", self.profile])
                logger.info(f"Using profile: {self.profile}")
            cmd.append("proto")
            
            logger.info(f"Full command: {' '.join(cmd)}")

            # Build environment with custom variables
            process_env = dict(os.environ)
            process_env["RUST_BACKTRACE"] = "1"
            
            # Add custom environment variables
            if self.custom_env:
                process_env.update(self.custom_env)
                logger.info(f"Added custom environment variables: {list(self.custom_env.keys())}")
            
            # Start the process with pipes
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )

            logger.info(f"Process started with PID: {self.process.pid}")
            self.running = True
            self.connection_attempts = 0

            # Start threads to read stdout and stderr
            self.stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)

            self.stdout_thread.start()
            self.stderr_thread.start()

            # Start heartbeat timer
            self.heartbeat_timer.start(30000)
            self.last_activity.start()

            # Set up timeout for process startup
            QTimer.singleShot(10000, self._check_startup_timeout)

        except Exception as e:
            logger.error(f"Failed to start backend process: {str(e)}", exc_info=True)
            self.connection_status_changed.emit("error")
            self.backend_error.emit(f"Failed to start backend process: {str(e)}")

    def _check_startup_timeout(self):
        """Check if the process failed to start within timeout"""
        if not self.running or self.process.poll() is not None:
            print("Backend startup timeout - process may be hanging")
            self.connection_status_changed.emit("error")
            self.backend_error.emit("Backend startup timeout. The process may be hanging or unresponsive.")

    def _read_stdout(self):
        """Read from stdout in a separate thread"""
        logger.info("Stdout reader started")
        try:
            while self.running and self.process:
                line = self.process.stdout.readline()
                if not line:
                    logger.debug("stdout closed")
                    break
                line = line.strip()
                if line:
                    logger.debug(f"Received from backend stdout: {line}")
                    # Skip log messages that start with timestamp and contain log levels
                    if (line.startswith('20') and ('INFO' in line or 'WARN' in line or 'ERROR' in line or 'DEBUG' in line)):
                        continue
                    # Skip empty lines or lines that don't look like JSON
                    if not line or not (line.startswith('{') or line.startswith('[')):
                        continue
                    try:
                        event = json.loads(line)
                        # Log only important event types at INFO level
                        etype = ''
                        if isinstance(event, dict):
                            etype = event.get('msg', {}).get('type', '')
                        if etype in { 'agent_message', 'apply_patch_approval_request', 'exec_approval_request', 'login_chat_gpt_response', 'login_chat_gpt_complete', 'session_configured', 'error' }:
                            logger.info(f"Event: {etype}")
                        else:
                            logger.debug(f"Event: {etype or 'unknown'}")
                        # Emit signal in the main thread
                        self.new_event.emit(event)

                        # Update operation progress if this is a response
                        if isinstance(event, dict) and "id" in event:
                            operation_id = event["id"]
                            if operation_id in self.pending_operations:
                                self.operation_progress.emit(operation_id, 100, "Operation completed")
                                # Clean up completed operation after a delay
                                self.operation_cleanup.emit(operation_id)

                        # Update last activity
                        self.last_activity.restart()

                        # Check if this is the session configured event
                        if isinstance(event, dict) and event.get("msg", {}).get("type") == "session_configured":
                            logger.info("Session configured event received - backend is ready")
                            self.backend_started.emit()
                            self.connection_status_changed.emit("connected")

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from backend: {e}\nLine: {line}", exc_info=True)
                        self.backend_error.emit(f"Backend communication error: Invalid JSON received")

        except Exception as e:
            if self.running:
                logger.error(f"Error reading stdout: {e}", exc_info=True)

    def _read_stderr(self):
        """Read from stderr in a separate thread"""
        logger.info("Stderr reader started")
        try:
            while self.running and self.process:
                line = self.process.stderr.readline()
                if not line:
                    break
                line = line.strip()
                if line:
                    # Only elevate lines that look like errors
                    lvl = logging.WARNING if ("error" in line.lower() or "failed" in line.lower()) else logging.DEBUG
                    logger.log(lvl, f"backend: {line}")
                    # Emit error signal for significant errors
                    if "error" in line.lower() or "failed" in line.lower():
                        self.backend_error.emit(f"Backend error: {line}")

        except Exception as e:
            if self.running:
                logger.error(f"Error reading stderr: {e}", exc_info=True)

    def _check_startup_timeout(self):
        """Check if the process failed to start within timeout"""
        logger.debug("_check_startup_timeout called")
        if not self.running or (self.process and self.process.poll() is not None):
            logger.warning("Backend startup timeout - process may be hanging or failed to start")
            self.connection_status_changed.emit("error")
            self.backend_error.emit("Backend startup timeout. The process may be hanging or unresponsive.")
        else:
            logger.info("Backend startup timeout check passed - process appears to be running")

    def stop(self):
        """Stop the backend service gracefully"""
        logger.info("BackendService.stop() called")
        if not self.running:
            logger.info("Backend service is not running")
            return

        logger.info("Stopping backend service...")
        self.connection_status_changed.emit("disconnected")
        self.running = False

        # Stop timers
        self.reconnect_timer.stop()
        self.heartbeat_timer.stop()

        # Terminate process gracefully
        if self.process:
            try:
                logger.info("Terminating backend process")
                self.process.terminate()
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5.0)
                    logger.info("Backend process terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Backend didn't respond to terminate, forcing kill")
                    self.process.kill()
                    self.process.wait()
                    logger.info("Backend process force killed")
            except Exception as e:
                logger.error(f"Error stopping process: {e}", exc_info=True)

        # Wait for threads to finish
        if self.stdout_thread and self.stdout_thread.is_alive():
            logger.debug("Waiting for stdout thread to finish")
            self.stdout_thread.join(timeout=2.0)
        if self.stderr_thread and self.stderr_thread.is_alive():
            logger.debug("Waiting for stderr thread to finish")
            self.stderr_thread.join(timeout=2.0)

        # Clean up pending operations
        for op_id in list(self.pending_operations.keys()):
            logger.debug(f"Cancelling pending operation: {op_id}")
            self.operation_progress.emit(op_id, -1, f"Operation cancelled")
            self._cleanup_operation(op_id)

    def send_op(self, op: dict):
        """Send an operation to the backend with error handling"""
        logger.info(f"send_op called with operation: {op}")
        if not self.running or not self.process or self.process.poll() is not None:
            error_msg = "Backend service not running. Cannot send operation."
            logger.error(error_msg)
            self.backend_error.emit(error_msg)
            return False

        try:
            # Track the operation
            operation_id = op.get("id", "unknown")
            logger.debug(f"Tracking operation with ID: {operation_id}")
            self.pending_operations[operation_id] = {
                "start_time": time.time(),
                "op": op
            }

            # Send progress update
            self.operation_progress.emit(operation_id, 0, "Sending operation...")

            # Create submission structure without context field
            submission = {
                "id": op.get("id"),
                "op": op.get("op")
            }
            message = json.dumps(submission) + "\n"
            logger.debug(f"Sending message to backend: {message.strip()}")
            self.process.stdin.write(message)
            self.process.stdin.flush()

            # Update last activity
            self.last_activity.restart()

            logger.info(f"Operation {operation_id} sent successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to send operation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.backend_error.emit(error_msg)
            return False

    def _on_ready_read(self):
        """Handle standard output from the backend"""
        while self.process.canReadLine():
            line = self.process.readLine().data().decode('utf-8', errors='replace').strip()
            if line:
                # Skip log messages that start with timestamp and contain log levels
                if (line.startswith('20') and ('INFO' in line or 'WARN' in line or 'ERROR' in line or 'DEBUG' in line)):
                    continue
                # Skip empty lines or lines that don't look like JSON
                if not line or not (line.startswith('{') or line.startswith('[')):
                    continue
                try:
                    event = json.loads(line)
                    self.new_event.emit(event)

                    # Update operation progress if this is a response
                    if isinstance(event, dict) and "id" in event:
                        operation_id = event["id"]
                        if operation_id in self.pending_operations:
                            self.operation_progress.emit(operation_id, 100, "Operation completed")
                            # Clean up completed operation after a delay
                            self.operation_cleanup.emit(operation_id)

                    # Update last activity
                    self.last_activity.restart()

                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from backend: {e}\nLine: {line}", file=sys.stderr)
                    self.backend_error.emit(f"Backend communication error: Invalid JSON received")

    def _on_ready_read_error(self):
        """Handle standard error output from the backend"""
        if self.process:
            error_data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
            if error_data.strip():
                print(f"Backend stderr: {error_data}", file=sys.stderr)
                # Emit error signal for significant errors
                if "error" in error_data.lower() or "failed" in error_data.lower():
                    self.backend_error.emit(f"Backend error: {error_data.strip()}")

    def _on_process_started(self):
        """Handle successful process startup"""
        print("Backend process started successfully")
        self.connection_attempts = 0
        self.connection_status_changed.emit("connected")
        self.backend_started.emit()

        # Start heartbeat timer (check every 30 seconds)
        self.heartbeat_timer.start(30000)

        # Reset last activity timer
        self.last_activity.start()

        # Send an initial newline to stdin to ensure the pipe is established
        # This helps with protocol mode initialization
        if self.process:
            self.process.write(b"\n")

    def _attempt_reconnect(self):
        """Attempt to reconnect to the backend"""
        self.reconnect_timer.stop()
        if self.connection_attempts < self.max_connection_attempts:
            print(f"Reconnecting to backend (attempt {self.connection_attempts + 1})")
            self.start()
        else:
            self.backend_error.emit("Failed to reconnect to backend after multiple attempts")

    def _send_heartbeat(self):
        """Send a heartbeat to check if backend is responsive"""
        if self.last_activity.elapsed() > 60000:  # No activity for 1 minute
            print("Backend appears unresponsive, sending heartbeat check")
            # Could send a simple ping operation here if needed

    def _cleanup_operation(self, operation_id: str):
        """Clean up a completed operation"""
        if operation_id in self.pending_operations:
            del self.pending_operations[operation_id]

    def is_connected(self) -> bool:
        """Check if backend is currently connected"""
        return self.running and self.process and self.process.poll() is None

    def get_connection_status(self) -> str:
        """Get current connection status"""
        if not self.running:
            return "disconnected"
        elif self.process and self.process.poll() is None:
            return "connected"
        else:
            return "error"
