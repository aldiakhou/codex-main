#!/usr/bin/env python3
"""
Test script for Phase 1 implementation
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        import aiw.core.models
        print("✓ aiw.core.models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.core.models: {e}")
        return False

    try:
        import aiw.core.config
        print("✓ aiw.core.config imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.core.config: {e}")
        return False

    try:
        import aiw.ui.main_window
        print("✓ aiw.ui.main_window imported successfully")
    except Exception as e:
        print(f"✗ Failed to import aiw.ui.main_window: {e}")
        return False

    return True

def test_models():
    """Test the data models"""
    print("\nTesting data models...")

    try:
        from aiw.core.models import Repository, Config, Operation

        # Test Repository model
        repo = Repository(path="/test/path", name="test-repo")
        print(f"✓ Repository created: {repo.display_name}")

        # Test Operation creation
        op = Operation.create_user_input("Hello AI")
        print(f"✓ Operation created: {op.id}")

        return True
    except Exception as e:
        print(f"✗ Failed to test models: {e}")
        return False

def test_config():
    """Test the configuration system"""
    print("\nTesting configuration system...")

    try:
        from aiw.core.config import ConfigManager

        # Create a temporary config for testing
        config_manager = ConfigManager()
        config = config_manager.config
        print(f"✓ Config loaded: version {config.version}")

        return True
    except Exception as e:
        print(f"✗ Failed to test config: {e}")
        return False

def main():
    """Run all tests"""
    print("=== AI Development Workbench Phase 1 Test ===\n")

    success = True

    success &= test_imports()
    success &= test_models()
    success &= test_config()

    print(f"\n{'='*50}")
    if success:
        print("🎉 All tests passed! Phase 1 implementation is working.")
        print("\nNext steps:")
        print("1. Run 'python main.py' to start the application")
        print("2. Try opening a Git repository")
        print("3. Test the dock-based UI layout")
        print("4. Continue with Phase 1.2-1.4 implementation")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
