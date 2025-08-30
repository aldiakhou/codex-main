#!/usr/bin/env python3
"""
Quick test for the code editor component
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_code_editor():
    """Test the code editor component specifically"""
    print("Testing Code Editor Component...")

    try:
        from aiw.ui.code_editor import CodeEditorWidget

        # Create a code editor widget
        editor = CodeEditorWidget()
        print("✓ CodeEditorWidget created successfully")

        # Test setting some text
        test_code = """def hello_world():
    print("Hello, World!")
    return True"""
        editor.set_text(test_code)
        print("✓ Text set successfully")

        # Test getting text back
        retrieved_text = editor.get_text()
        if retrieved_text == test_code:
            print("✓ Text retrieval works correctly")
        else:
            print("✗ Text retrieval failed")
            return False

        # Test line number area width calculation
        width = editor.editor.line_number_area_width()
        if width > 0:
            print(f"✓ Line number area width calculated: {width}")
        else:
            print("✗ Line number area width calculation failed")
            return False

        return True

    except Exception as e:
        print(f"✗ Code editor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_code_editor():
        print("\n🎉 Code editor test passed!")
    else:
        print("\n❌ Code editor test failed!")
        sys.exit(1)
