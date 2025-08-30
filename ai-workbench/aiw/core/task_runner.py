"""
Task runner system for AI Development Workbench
"""
import time
import threading
import logging
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
from PySide6.QtCore import QObject, Signal, QThread, QTimer

from ..core.models import Task, Workflow, Run

# Set up logging
task_logger = logging.getLogger('task_runner')
task_logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler('ai_workbench_debug.log', mode='a')
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
task_logger.addHandler(file_handler)
task_logger.addHandler(console_handler)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult:
    """Result of a task execution"""

    def __init__(self, success: bool, output: Any = None, error: str = None):
        self.success = success
        self.output = output
        self.error = error
        self.execution_time = 0.0


class TaskRunner(QThread):
    """Thread for running tasks"""

    # Signals
    task_started = Signal(str)  # task_id
    task_completed = Signal(str, object)  # task_id, result
    task_failed = Signal(str, str)  # task_id, error
    task_progress = Signal(str, int, str)  # task_id, progress, message

    def __init__(self, task: Task, context: Dict[str, Any]):
        super().__init__()
        self.task = task
        self.context = context
        self.cancelled = False
        task_logger.info(f"TaskRunner initialized: task_id={task.id}, type={task.type}, parameters={task.parameters}")

    def cancel(self):
        """Cancel the task execution"""
        task_logger.info(f"TaskRunner.cancel: task_id={self.task.id}")
        self.cancelled = True

    def run(self):
        """Execute the task"""
        task_logger.info(f"TaskRunner.run: Starting task execution for task_id={self.task.id}")
        try:
            self.task_started.emit(self.task.id)

            # Execute the task based on its type
            result = self._execute_task()
            task_logger.info(f"TaskRunner.run: Task execution completed for task_id={self.task.id}, success={result.success}")

            if self.cancelled:
                task_logger.warning(f"TaskRunner.run: Task cancelled for task_id={self.task.id}")
                self.task_failed.emit(self.task.id, "Task was cancelled")
            elif result.success:
                task_logger.info(f"TaskRunner.run: Task completed successfully for task_id={self.task.id}")
                self.task_completed.emit(self.task.id, result)
            else:
                task_logger.error(f"TaskRunner.run: Task failed for task_id={self.task.id}, error={result.error}")
                self.task_failed.emit(self.task.id, result.error or "Task failed")

        except Exception as e:
            task_logger.error(f"TaskRunner.run: Exception during task execution for task_id={self.task.id}, error={str(e)}")
            self.task_failed.emit(self.task.id, str(e))

    def _execute_task(self) -> TaskResult:
        """Execute the specific task type"""
        task_type = self.task.type
        task_logger.info(f"TaskRunner._execute_task: Executing task type '{task_type}' for task_id={self.task.id}")

        if task_type == "run_tests":
            return self._execute_run_tests()
        elif task_type == "apply_patch":
            return self._execute_apply_patch()
        elif task_type == "analyze_code":
            return self._execute_analyze_code()
        else:
            task_logger.error(f"TaskRunner._execute_task: Unknown task type '{task_type}' for task_id={self.task.id}")
            return TaskResult(False, error=f"Unknown task type: {task_type}")

    def _execute_edit_file(self) -> TaskResult:
        """Execute file editing task"""
        try:
            file_path = self.task.parameters.get("file_path")
            instruction = self.task.parameters.get("instruction")

            if not file_path or not instruction:
                return TaskResult(False, error="Missing file_path or instruction")

            # Simulate AI processing
            self.task_progress.emit(self.task.id, 25, "Analyzing file...")
            time.sleep(0.5)

            self.task_progress.emit(self.task.id, 50, "Generating changes...")
            time.sleep(0.5)

            # In a real implementation, this would call the AI backend
            # For now, we'll simulate a simple edit
            self.task_progress.emit(self.task.id, 75, "Applying changes...")
            time.sleep(0.5)

            self.task_progress.emit(self.task.id, 100, "Complete")

            return TaskResult(True, output={"changes_applied": True})

        except Exception as e:
            return TaskResult(False, error=str(e))

    def _execute_run_tests(self) -> TaskResult:
        """Execute test running task"""
        task_logger.info(f"TaskRunner._execute_run_tests: Starting test execution for task_id={self.task.id}")
        try:
            test_command = self.task.parameters.get("command", ["pytest", "-v"])
            task_logger.debug(f"TaskRunner._execute_run_tests: Test command: {test_command}")

            self.task_progress.emit(self.task.id, 10, "Starting tests...")

            # In a real implementation, this would run the test command
            # For simulation, we'll just wait
            for i in range(20, 100, 20):
                if self.cancelled:
                    task_logger.info(f"TaskRunner._execute_run_tests: Test execution cancelled for task_id={self.task.id}")
                    break
                self.task_progress.emit(self.task.id, i, f"Running tests... {i}%")
                time.sleep(0.2)

            if self.cancelled:
                task_logger.warning(f"TaskRunner._execute_run_tests: Test execution cancelled for task_id={self.task.id}")
                return TaskResult(False, error="Cancelled")

            self.task_progress.emit(self.task.id, 100, "Tests completed")
            task_logger.info(f"TaskRunner._execute_run_tests: Test execution completed for task_id={self.task.id}")

            # Simulate test results
            result = TaskResult(True, output={
                "tests_run": 10,
                "tests_passed": 8,
                "tests_failed": 2
            })
            task_logger.debug(f"TaskRunner._execute_run_tests: Test results: {result.output}")
            return result

        except Exception as e:
            task_logger.error(f"TaskRunner._execute_run_tests: Exception during test execution for task_id={self.task.id}, error={str(e)}")
            return TaskResult(False, error=str(e))

    def _execute_apply_patch(self) -> TaskResult:
        """Execute patch application task"""
        try:
            patch_content = self.task.parameters.get("patch")

            if not patch_content:
                return TaskResult(False, error="No patch content provided")

            self.task_progress.emit(self.task.id, 25, "Validating patch...")
            time.sleep(0.3)

            self.task_progress.emit(self.task.id, 50, "Applying patch...")
            time.sleep(0.5)

            self.task_progress.emit(self.task.id, 75, "Verifying changes...")
            time.sleep(0.3)

            self.task_progress.emit(self.task.id, 100, "Patch applied successfully")

            return TaskResult(True, output={"patch_applied": True})

        except Exception as e:
            return TaskResult(False, error=str(e))

    def _execute_analyze_code(self) -> TaskResult:
        """Execute code analysis task"""
        try:
            file_path = self.task.parameters.get("file_path")

            if not file_path:
                return TaskResult(False, error="No file path provided")

            self.task_progress.emit(self.task.id, 20, "Analyzing code structure...")
            time.sleep(0.4)

            self.task_progress.emit(self.task.id, 50, "Checking for issues...")
            time.sleep(0.6)

            self.task_progress.emit(self.task.id, 80, "Generating report...")
            time.sleep(0.4)

            self.task_progress.emit(self.task.id, 100, "Analysis complete")

            # Simulate analysis results
            return TaskResult(True, output={
                "issues_found": 3,
                "complexity_score": 7.2,
                "suggestions": ["Consider breaking down large function", "Add more comments"]
            })

        except Exception as e:
            return TaskResult(False, error=str(e))


class WorkflowRunner(QObject):
    """Manages execution of workflows and tasks"""

    # Signals
    workflow_started = Signal(str)  # workflow_id
    workflow_completed = Signal(str)  # workflow_id
    workflow_failed = Signal(str, str)  # workflow_id, error

    task_started = Signal(str, str)  # workflow_id, task_id
    task_completed = Signal(str, str, object)  # workflow_id, task_id, result
    task_failed = Signal(str, str, str)  # workflow_id, task_id, error
    task_progress = Signal(str, str, int, str)  # workflow_id, task_id, progress, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_runners: Dict[str, TaskRunner] = {}
        self.workflow_contexts: Dict[str, Dict[str, Any]] = {}
        task_logger.info("WorkflowRunner initialized")

    def run_workflow(self, workflow: Workflow, initial_context: Dict[str, Any] = None):
        """Run a complete workflow"""
        workflow_id = workflow.id
        context = initial_context or {}
        task_logger.info(f"WorkflowRunner.run_workflow: Starting workflow {workflow_id} with {len(workflow.tasks)} tasks")

        self.workflow_contexts[workflow_id] = context
        self.workflow_started.emit(workflow_id)

        # Start executing tasks sequentially
        self._run_next_task(workflow, 0, context)

    def run_single_task(self, task: Task, context: Dict[str, Any] = None):
        """Run a single task"""
        context = context or {}
        workflow_id = f"single_{task.id}"
        task_logger.info(f"WorkflowRunner.run_single_task: Starting single task {task.id} as workflow {workflow_id}")

        self.workflow_contexts[workflow_id] = context
        self.workflow_started.emit(workflow_id)

        self._execute_task(workflow_id, task, context)

    def cancel_workflow(self, workflow_id: str):
        """Cancel a running workflow"""
        task_logger.info(f"WorkflowRunner.cancel_workflow: Cancelling workflow {workflow_id}")
        if workflow_id in self.active_runners:
            self.active_runners[workflow_id].cancel()
        else:
            task_logger.warning(f"WorkflowRunner.cancel_workflow: No active runner found for workflow {workflow_id}")

    def _run_next_task(self, workflow: Workflow, task_index: int, context: Dict[str, Any]):
        """Execute the next task in the workflow"""
        task_logger.debug(f"WorkflowRunner._run_next_task: workflow={workflow.id}, task_index={task_index}, total_tasks={len(workflow.tasks)}")
        if task_index >= len(workflow.tasks):
            # Workflow completed
            task_logger.info(f"WorkflowRunner._run_next_task: Workflow {workflow.id} completed")
            self.workflow_completed.emit(workflow.id)
            return

        task = workflow.tasks[task_index]
        task_logger.info(f"WorkflowRunner._run_next_task: Executing task {task.id} (index {task_index}) in workflow {workflow.id}")
        self._execute_task(workflow.id, task, context)

    def _execute_task(self, workflow_id: str, task: Task, context: Dict[str, Any]):
        """Execute a single task"""
        task_logger.info(f"WorkflowRunner._execute_task: Creating runner for task {task.id} in workflow {workflow_id}")
        # Create task runner
        runner = TaskRunner(task, context)
        self.active_runners[workflow_id] = runner

        # Connect signals
        runner.task_started.connect(lambda tid: self._on_task_started(workflow_id, tid))
        runner.task_completed.connect(lambda tid, result: self._on_task_completed(workflow_id, tid, result))
        runner.task_failed.connect(lambda tid, error: self._on_task_failed(workflow_id, tid, error))
        runner.task_progress.connect(lambda tid, progress, msg: self._on_task_progress(workflow_id, tid, progress, msg))

        # Start the task
        task_logger.info(f"WorkflowRunner._execute_task: Starting task runner for task {task.id} in workflow {workflow_id}")
        runner.start()

    def _on_task_started(self, workflow_id: str, task_id: str):
        """Handle task started"""
        task_logger.info(f"WorkflowRunner._on_task_started: Task {task_id} started in workflow {workflow_id}")
        self.task_started.emit(workflow_id, task_id)

    def _on_task_completed(self, workflow_id: str, task_id: str, result: TaskResult):
        """Handle task completed"""
        task_logger.info(f"WorkflowRunner._on_task_completed: Task {task_id} completed in workflow {workflow_id}, success={result.success}")
        self.task_completed.emit(workflow_id, task_id, result)

        # Clean up runner
        if workflow_id in self.active_runners:
            del self.active_runners[workflow_id]
            task_logger.debug(f"WorkflowRunner._on_task_completed: Cleaned up runner for workflow {workflow_id}")

        # For single tasks, mark workflow as completed
        if workflow_id.startswith("single_"):
            task_logger.info(f"WorkflowRunner._on_task_completed: Single task workflow {workflow_id} completed")
            self.workflow_completed.emit(workflow_id)

    def _on_task_failed(self, workflow_id: str, task_id: str, error: str):
        """Handle task failed"""
        task_logger.error(f"WorkflowRunner._on_task_failed: Task {task_id} failed in workflow {workflow_id}, error={error}")
        self.task_failed.emit(workflow_id, task_id, error)

        # Clean up runner
        if workflow_id in self.active_runners:
            del self.active_runners[workflow_id]
            task_logger.debug(f"WorkflowRunner._on_task_failed: Cleaned up runner for workflow {workflow_id}")

        # For single tasks, mark workflow as failed
        if workflow_id.startswith("single_"):
            task_logger.error(f"WorkflowRunner._on_task_failed: Single task workflow {workflow_id} failed")
            self.workflow_failed.emit(workflow_id, error)

    def _on_task_progress(self, workflow_id: str, task_id: str, progress: int, message: str):
        """Handle task progress"""
        task_logger.debug(f"WorkflowRunner._on_task_progress: Task {task_id} progress in workflow {workflow_id}: {progress}% - {message}")
        self.task_progress.emit(workflow_id, task_id, progress, message)


# Global workflow runner instance
_workflow_runner: Optional[WorkflowRunner] = None


def get_workflow_runner() -> WorkflowRunner:
    """Get the global workflow runner instance"""
    global _workflow_runner
    if _workflow_runner is None:
        task_logger.info("get_workflow_runner: Creating new global WorkflowRunner instance")
        _workflow_runner = WorkflowRunner()
    else:
        task_logger.debug("get_workflow_runner: Returning existing global WorkflowRunner instance")
    return _workflow_runner
