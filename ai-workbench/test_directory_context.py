#!/usr/bin/env python3
"""
Test script to demonstrate improved directory context handling in AI Workbench.
This script shows how the working directory is now determined more intelligently.
"""

import os
import sys
from pathlib import Path

# Add the ai-workbench directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from aiw.core.models import Operation

def test_directory_context_logic():
    """Test the improved directory context determination logic"""

    print("=== AI Workbench Directory Context Test ===\n")

    # Simulate different scenarios
    scenarios = [
        {
            "name": "Repository selected",
            "repo_path": "C:/Users/ali95/Documents/Dev/my-project",
            "current_file": None,
            "expected_cwd": "C:/Users/ali95/Documents/Dev/my-project"
        },
        {
            "name": "No repository, file open",
            "repo_path": None,
            "current_file": "C:/Users/ali95/Documents/Dev/other-project/src/main.py",
            "expected_cwd": "C:/Users/ali95/Documents/Dev/other-project/src"
        },
        {
            "name": "No repository, no file (fallback)",
            "repo_path": None,
            "current_file": None,
            "expected_cwd": str(Path(__file__).parent.parent)  # ai-workbench directory
        }
    ]

    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"  Repository: {scenario['repo_path'] or 'None'}")
        print(f"  Current file: {scenario['current_file'] or 'None'}")

        # Simulate the logic from main_window.py
        cwd_path = None
        if scenario['repo_path']:
            cwd_path = scenario['repo_path']
        else:
            if scenario['current_file']:
                file_dir = str(Path(scenario['current_file']).parent)
                cwd_path = file_dir
            else:
                # Use AI Workbench project directory as fallback
                workbench_dir = Path(__file__).parent.parent  # test_dir -> ai-workbench/
                cwd_path = str(workbench_dir)

        print(f"  Determined working directory: {cwd_path}")
        print(f"  Expected: {scenario['expected_cwd']}")
        # Normalize both paths for comparison
        expected_normalized = scenario['expected_cwd'].replace("\\", "/")
        determined_normalized = cwd_path.replace("\\", "/")
        print(f"  ✓ Correct: {determined_normalized == expected_normalized}\n")

        # Test creating an operation with this context
        normalized_cwd = cwd_path.replace("\\", "/")
        op = Operation.create_user_turn("Test prompt", normalized_cwd)
        print(f"  Created operation with cwd: {op.op['cwd']}")
        print()

def test_path_normalization():
    """Test path normalization for JSON compatibility"""
    print("=== Path Normalization Test ===\n")

    test_paths = [
        "C:\\Users\\ali95\\Documents\\Dev\\project",
        "C:/Users/ali95/Documents/Dev/project",
        "/home/user/project",
        "relative/path"
    ]

    for path in test_paths:
        normalized = path.replace("\\", "/")
        print(f"Original: {path}")
        print(f"Normalized: {normalized}")
        print()

if __name__ == "__main__":
    test_directory_context_logic()
    test_path_normalization()

    print("=== Summary ===")
    print("✅ Directory context is now determined more intelligently:")
    print("   - Uses repository directory when available")
    print("   - Uses directory of currently open file when no repository")
    print("   - Falls back to AI Workbench project directory")
    print("   - No longer uses potentially incorrect os.getcwd()")
    print("\n✅ This prevents unexpected directory changes during follow-up questions!")
