"""Tests for the MainWindow and AI workflow integration.
"""
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Add the project root to the Python path to allow imports.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiw.core.models import Operation
from aiw.ui.main_window import MainWindow

# --- Fixtures ---

@pytest.fixture
def app(qapp):
    """Pytest fixture to create the main application."""
    # The qapp fixture is provided by pytest-qt
    return qapp

@pytest.fixture
def window(app):
    """Pytest fixture to create the main window, mocking the backend."""
    with patch('aiw.ui.main_window.BackendService') as MockBackend:
        # Prevent the backend from actually starting
        MockBackend.return_value.start.return_value = None
        
        win = MainWindow()
        win.backend = MockBackend() # Attach the mock to the window instance
        yield win

# --- Model Tests ---

def test_create_edit_file_operation():
    """Test the creation of an 'edit_file' operation."""
    file_path = "/path/to/file.py"
    instruction = "Refactor this function"
    op = Operation.create_edit_file_operation(file_path, instruction)

    assert op.op['type'] == 'edit_file'
    assert op.op['file_path'] == file_path
    assert op.op['instruction'] == instruction
    assert op.id.startswith("edit_file_")

# --- Main Window Tests ---

def test_initial_ui_setup(window):
    """Test that the main window initializes with the correct layout."""
    # The central widget should be the code editor
    assert window.centralWidget() == window.code_editor
    
    # Check that all the required docks are present
    assert window.repo_dock is not None
    assert window.console_dock is not None
    assert window.diff_dock is not None
    assert window.artifacts_dock is not None

def test_send_prompt_without_file(window):
    """Test sending a prompt when no file is open."""
    prompt_text = "Hello, what can you do?"
    window.prompt_input.setPlainText(prompt_text)
    
    window._send_prompt()

    # It should create a standard 'user_input' operation
    window.backend.send_op.assert_called_once()
    call_args = window.backend.send_op.call_args[0][0]
    assert call_args['op']['type'] == 'user_input'
    assert call_args['op']['items'][0]['text'] == prompt_text

def test_send_prompt_with_file_open(window):
    """Test sending a prompt when a file is open in the editor."""
    file_path = "/test/file.py"
    prompt_text = "Add a docstring to this function"
    
    # Simulate an open file
    window.code_editor.get_current_file_path = Mock(return_value=file_path)
    
    window.prompt_input.setPlainText(prompt_text)
    window._send_prompt()

    # It should create an 'edit_file' operation
    window.backend.send_op.assert_called_once()
    call_args = window.backend.send_op.call_args[0][0]
    assert call_args['op']['type'] == 'edit_file'
    assert call_args['op']['file_path'] == file_path
    assert call_args['op']['instruction'] == prompt_text

def test_handle_diff_event(window):
    """Test the handler for an incoming diff event from the backend."""
    file_path = "/test/file.py"
    diff_text = "--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-Hello\n+Hello, world!"
    
    # Mock the diff viewer's method to check if it gets called
    window.diff_viewer.set_diff_content = Mock()
    
    # Simulate a backend event
    event = {
        "id": "some_task_id",
        "msg": {
            "type": "agent_edit_file_response",
            "file_path": file_path,
            "diff": diff_text
        }
    }
    
    window._on_backend_event(event)
    
    # Assert that the diff viewer was updated with the correct content
    window.diff_viewer.set_diff_content.assert_called_once_with(diff_text, file_path)

    # In a tabbed dock setup, isVisible() can be false. 
    # A better check is to see if the dock's tab was raised.
    # We can't directly check the active tab, so we'll mock `raise_` and check that it was called.
    window.diff_dock.raise_ = Mock()
    window._on_backend_event(event)
    window.diff_dock.raise_.assert_called_once()

def test_load_file_into_editor(window, qtbot):
    """Test that loading a file works and emits the correct signal."""
    mock_file_path = "/fake/path/main.py"
    mock_content = "print('hello world')"

    # Patch 'open' to simulate reading a file
    with patch('builtins.open', unittest.mock.mock_open(read_data=mock_content)) as mock_file:
        # Use qtbot to wait for the signal to be emitted
        with qtbot.waitSignal(window.file_selected, timeout=1000) as blocker:
            window._load_file_into_editor(mock_file_path)
        
        # Check that the signal was emitted with the correct path
        assert blocker.args == [mock_file_path]
        
        # Check that the editor's content was set
        assert window.code_editor.editor.toPlainText() == mock_content
