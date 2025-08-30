#!/usr/bin/env python3
"""
Test script for Phase 2 components
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all components can be imported"""
    print("=== AI Development Workbench Phase 2 Test ===")

    print("\nTesting imports...")
    try:
        from aiw.core.models import Repository, Task, Operation
        print("✓ aiw.core.models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.core.models: {e}")
        return False

    try:
        from aiw.core.config import get_config_manager
        print("✓ aiw.core.config imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.core.config: {e}")
        return False

    try:
        from aiw.core.task_runner import get_workflow_runner
        print("✓ aiw.core.task_runner imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.core.task_runner: {e}")
        return False

    try:
        from aiw.ui.main_window import MainWindow
        print("✓ aiw.ui.main_window imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.ui.main_window: {e}")
        return False

    try:
        from aiw.ui.code_editor import CodeEditorWidget
        print("✓ aiw.ui.code_editor imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.ui.code_editor: {e}")
        return False

    try:
        from aiw.ui.diff_view import DiffViewWidget
        print("✓ aiw.ui.diff_view imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.ui.diff_view: {e}")
        return False

    return True

def test_components():
    """Test component instantiation"""
    print("\nTesting component instantiation...")

    try:
        from aiw.core.models import Repository, Task
        from aiw.core.config import get_config_manager
        from aiw.core.task_runner import get_workflow_runner

        # Test repository creation
        repo = Repository(name="test-repo", path="/tmp/test")
        print("✓ Repository created successfully")

        # Test task creation
        task = Task(
            id="test_task",
            name="Test Task",
            type="edit_file",
            parameters={
                "file_path": "/tmp/test.py",
                "instruction": "Improve this code",
                "content": "print('hello')"
            }
        )
        print("✓ Task created successfully")

        # Test config manager
        config = get_config_manager()
        print("✓ Config manager created successfully")

        # Test task runner
        runner = get_workflow_runner()
        print("✓ Task runner created successfully")

        return True

    except Exception as e:
        print(f"✗ Component instantiation failed: {e}")
        return False

def main():
    """Main test function"""
    success = test_imports()
    if success:
        success = test_components()

    if success:
        print("\n==================================================")
        print("🎉 All tests passed! Phase 2 implementation is working.")
        print("\nNext steps:")
        print("1. The GUI application should start successfully")
        print("2. Try opening a repository and loading files")
        print("3. Test the code editor with syntax highlighting")
        print("4. Test the diff viewer with sample patches")
        print("5. Try the AI Edit and Run Tests toolbar buttons")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
