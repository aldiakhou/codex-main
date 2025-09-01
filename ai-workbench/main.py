"""
AI Development Workbench - Main Application Entry Point
"""
import sys
from PySide6.QtWidgets import QApplication
from aiw.ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # App-level palette: window-specific theming is applied in MainWindow

    # Set application properties
    app.setApplicationName("AI Development Workbench")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("AI Workbench")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Apply the theme after the window is shown
    window._apply_theme()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
