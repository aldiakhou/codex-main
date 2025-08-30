"""
AI Development Workbench - Main Application Entry Point
"""
import sys
from PySide6.QtWidgets import QApplication
from aiw.ui.main_window import MainWindow
from qt_material import apply_stylesheet


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply the material theme
    apply_stylesheet(app, theme='dark_blue.xml')

    # Set application properties
    app.setApplicationName("AI Development Workbench")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("AI Workbench")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
