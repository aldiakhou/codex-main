import json
import os
import sys
from PySide6.QtCore import QObject, QProcess, Signal, QThread

class BackendService(QObject):
    # Signals to communicate with the GUI thread
    new_event = Signal(dict)
    backend_started = Signal()
    backend_stopped = Signal(int)
    backend_error = Signal(str)

    def __init__(self, codex_executable_path: str, parent=None):
        super().__init__(parent)
        self.process = None
        self.codex_executable_path = codex_executable_path

    def start(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            print("Backend service is already running.")
            return

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)

        # Connect signals
        self.process.readyReadStandardOutput.connect(self._on_ready_read)
        self.process.started.connect(self.backend_started)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

        # Start the process
        print(f"Starting backend: {self.codex_executable_path}")
        self.process.start(self.codex_executable_path, ["proto"])

    def stop(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()

    def send_op(self, op: dict):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            message = json.dumps(op)
            self.process.write(f"{message}\n".encode('utf-8'))
        else:
            self.backend_error.emit("Backend service not running. Cannot send operation.")

    def _on_ready_read(self):
        while self.process.canReadLine():
            line = self.process.readLine().data().decode('utf-8').strip()
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
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from backend: {e}\nLine: {line}", file=sys.stderr)

    def _on_finished(self, exit_code):
        self.backend_stopped.emit(exit_code)
        print(f"Backend process finished with exit code: {exit_code}")

    def _on_error(self, error: QProcess.ProcessError):
        error_string = self.process.errorString()
        self.backend_error.emit(f"Backend process error: {error_string}")
        print(f"Backend process error: {error_string}", file=sys.stderr)
