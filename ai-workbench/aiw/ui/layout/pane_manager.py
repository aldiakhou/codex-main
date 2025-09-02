"""Enhanced Pane Manager with full IDE functionality.
Supports multiple tabs, file management, and IDE-like features.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, 
                               QLabel, QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..code_editor import CodeEditorWidget

main_logger = logging.getLogger('MainWindow.PaneManager')

@dataclass
class PaneTab:
    id: str
    title: str
    widget: QWidget
    file_path: Optional[str] = None
    icon: Optional[object] = None
    is_modified: bool = False

class PaneManager(QWidget):
    """Enhanced pane manager with file management and IDE features"""
    
    # Signals
    tab_changed = Signal(int)
    file_opened = Signal(str)
    file_closed = Signal(str)
    content_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._tabs: Dict[str, PaneTab] = {}
        self._file_tabs: Dict[str, str] = {}  # file_path -> tab_id mapping
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the pane manager UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_index)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tab_widget)
        
        # Create default editor tab
        self._create_default_tab()
        
        # Status area
        self._setup_status_area(layout)
        
    def _setup_status_area(self, layout):
        """Set up the status area at the bottom"""
        status_frame = QFrame()
        status_frame.setMaximumHeight(25)
        status_frame.setStyleSheet("background: #f5f5f5; border-top: 1px solid #ddd;")
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 2, 10, 2)
        
        # File info
        self.file_info_label = QLabel("Ready")
        self.file_info_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(self.file_info_label)
        
        status_layout.addStretch()
        
        # Cursor position
        self.cursor_info_label = QLabel("Ln 1, Col 1")
        self.cursor_info_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(self.cursor_info_label)
        
        # Language mode
        self.language_label = QLabel("Python")
        self.language_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(self.language_label)
        
        layout.addWidget(status_frame)
        
    def _create_default_tab(self):
        """Create the default editor tab"""
        editor = CodeEditorWidget()
        self.ensure_tab("default", "untitled.py", lambda: editor)
        
        # Make available to main window
        if self.main_window:
            self.main_window.code_editor = editor
            
        # Connect editor signals
        if hasattr(editor, 'cursorPositionChanged'):
            editor.cursorPositionChanged.connect(self._update_cursor_info)
        if hasattr(editor, 'textChanged'):
            editor.textChanged.connect(self._on_content_changed)

    # --- Enhanced Public API ------------------------------------------------
    def ensure_tab(self, tab_id: str, title: str, factory) -> QWidget:
        """Ensure a tab exists, creating it if necessary"""
        if tab_id in self._tabs:
            idx = self._index_of(tab_id)
            if idx >= 0:
                self._tab_widget.setCurrentIndex(idx)
            return self._tabs[tab_id].widget
            
        widget = factory()
        pane_tab = PaneTab(id=tab_id, title=title, widget=widget)
        self._tabs[tab_id] = pane_tab
        
        index = self._tab_widget.addTab(widget, title)
        self._tab_widget.setCurrentIndex(index)
        
        return widget
        
    def open_file_tab(self, file_path: str, content: str = "") -> QWidget:
        """Open a file in a tab, or switch to existing tab"""
        try:
            # Check if already open
            if file_path in self._file_tabs:
                tab_id = self._file_tabs[file_path]
                if tab_id in self._tabs:
                    idx = self._index_of(tab_id)
                    if idx >= 0:
                        self._tab_widget.setCurrentIndex(idx)
                        return self._tabs[tab_id].widget
            
            # Create new tab
            editor = CodeEditorWidget()
            if content:
                editor.setPlainText(content)
            
            # Generate unique tab ID
            tab_id = f"file_{len(self._tabs)}"
            filename = Path(file_path).name
            
            # Create tab
            pane_tab = PaneTab(
                id=tab_id, 
                title=filename, 
                widget=editor, 
                file_path=file_path
            )
            self._tabs[tab_id] = pane_tab
            self._file_tabs[file_path] = tab_id
            
            index = self._tab_widget.addTab(editor, filename)
            self._tab_widget.setCurrentIndex(index)
            
            # Connect signals
            if hasattr(editor, 'cursorPositionChanged'):
                editor.cursorPositionChanged.connect(self._update_cursor_info)
            if hasattr(editor, 'textChanged'):
                editor.textChanged.connect(self._on_content_changed)
            
            self.file_opened.emit(file_path)
            self._update_file_info()
            
            main_logger.info(f"Opened file: {file_path}")
            return editor
            
        except Exception as e:
            main_logger.error(f"Failed to open file {file_path}: {e}")
            return None

    def save_current_tab(self, file_path: str = None) -> bool:
        """Save the current tab's content"""
        try:
            current_widget = self._tab_widget.currentWidget()
            if not current_widget or not hasattr(current_widget, 'toPlainText'):
                return False
                
            # Get tab info
            tab_id = self._get_tab_id_for_widget(current_widget)
            if not tab_id or tab_id not in self._tabs:
                return False
                
            tab = self._tabs[tab_id]
            
            # Determine file path
            if not file_path:
                file_path = tab.file_path
                if not file_path:
                    return False  # Need file path for new files
            
            # Save content
            content = current_widget.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update tab info
            tab.file_path = file_path
            tab.is_modified = False
            filename = Path(file_path).name
            tab.title = filename
            
            # Update UI
            current_index = self._tab_widget.currentIndex()
            self._tab_widget.setTabText(current_index, filename)
            
            # Update file mapping
            self._file_tabs[file_path] = tab_id
            
            self._update_file_info()
            main_logger.info(f"Saved file: {file_path}")
            return True
            
        except Exception as e:
            main_logger.error(f"Failed to save file: {e}")
            return False

    def close_tab(self, tab_id: str):
        """Close a specific tab"""
        try:
            if tab_id not in self._tabs:
                return
                
            # Don't close the last tab
            if len(self._tabs) <= 1:
                self._clear_current_tab()
                return
                
            tab = self._tabs[tab_id]
            
            # Remove from file mapping
            if tab.file_path and tab.file_path in self._file_tabs:
                del self._file_tabs[tab.file_path]
                self.file_closed.emit(tab.file_path)
            
            # Remove from UI
            idx = self._index_of(tab_id)
            if idx >= 0:
                self._tab_widget.removeTab(idx)
                
            # Clean up
            self._tabs.pop(tab_id, None)
            tab.widget.deleteLater()
            
            main_logger.info(f"Closed tab: {tab_id}")
            
        except Exception as e:
            main_logger.error(f"Failed to close tab {tab_id}: {e}")
            
    def _clear_current_tab(self):
        """Clear the current tab but don't close it"""
        try:
            current_widget = self._tab_widget.currentWidget()
            if hasattr(current_widget, 'clear'):
                current_widget.clear()
                
            # Reset tab info
            tab_id = self._get_tab_id_for_widget(current_widget)
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                tab.title = "untitled.py"
                tab.file_path = None
                tab.is_modified = False
                
                current_index = self._tab_widget.currentIndex()
                self._tab_widget.setTabText(current_index, "untitled.py")
                
            self._update_file_info()
            
        except Exception as e:
            main_logger.error(f"Failed to clear current tab: {e}")

    def get_current_content(self) -> str:
        """Get content of current tab"""
        try:
            current_widget = self._tab_widget.currentWidget()
            if hasattr(current_widget, 'toPlainText'):
                return current_widget.toPlainText()
            return ""
        except Exception as e:
            main_logger.error(f"Failed to get current content: {e}")
            return ""
            
    def set_current_content(self, content: str):
        """Set content of current tab"""
        try:
            current_widget = self._tab_widget.currentWidget()
            if hasattr(current_widget, 'setPlainText'):
                current_widget.setPlainText(content)
        except Exception as e:
            main_logger.error(f"Failed to set current content: {e}")

    def list_tabs(self) -> List[str]:
        """List all tab IDs"""
        return list(self._tabs.keys())
        
    def get_open_files(self) -> List[str]:
        """Get list of open file paths"""
        return list(self._file_tabs.keys())

    # --- Event Handlers -----------------------------------------------------
    def _on_tab_changed(self, index):
        """Handle tab change"""
        try:
            if index >= 0:
                widget = self._tab_widget.widget(index)
                
                # Update main window code editor reference
                if self.main_window and hasattr(widget, 'toPlainText'):
                    self.main_window.code_editor = widget
                
                self._update_file_info()
                self._update_cursor_info()
                self.tab_changed.emit(index)
                
        except Exception as e:
            main_logger.error(f"Failed to handle tab change: {e}")
            
    def _on_content_changed(self):
        """Handle content change in current tab"""
        try:
            current_widget = self._tab_widget.currentWidget()
            tab_id = self._get_tab_id_for_widget(current_widget)
            
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                if not tab.is_modified:
                    tab.is_modified = True
                    current_index = self._tab_widget.currentIndex()
                    title = self._tab_widget.tabText(current_index)
                    if not title.endswith("*"):
                        self._tab_widget.setTabText(current_index, title + "*")
                        
            if tab and tab.file_path:
                self.content_changed.emit(tab.file_path)
                
        except Exception as e:
            main_logger.error(f"Failed to handle content change: {e}")
            
    def _update_cursor_info(self):
        """Update cursor position display"""
        try:
            current_widget = self._tab_widget.currentWidget()
            if hasattr(current_widget, 'textCursor'):
                cursor = current_widget.textCursor()
                line = cursor.blockNumber() + 1
                col = cursor.columnNumber() + 1
                self.cursor_info_label.setText(f"Ln {line}, Col {col}")
        except Exception as e:
            main_logger.error(f"Failed to update cursor info: {e}")
            
    def _update_file_info(self):
        """Update file information display"""
        try:
            # Safety check to ensure UI is initialized
            if not hasattr(self, 'file_info_label'):
                main_logger.debug("file_info_label not yet initialized, skipping update")
                return
                
            current_widget = self._tab_widget.currentWidget()
            tab_id = self._get_tab_id_for_widget(current_widget)
            
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                if tab.file_path:
                    self.file_info_label.setText(f"File: {tab.file_path}")
                else:
                    self.file_info_label.setText("Untitled file")
            else:
                self.file_info_label.setText("Ready")
                
        except Exception as e:
            main_logger.error(f"Failed to update file info: {e}")

    # --- Utility Methods ----------------------------------------------------
    def _get_tab_id_for_widget(self, widget) -> Optional[str]:
        """Get tab ID for a widget"""
        for tab_id, tab in self._tabs.items():
            if tab.widget == widget:
                return tab_id
        return None

    def _index_of(self, tab_id: str) -> int:
        """Get tab widget index for tab ID"""
        if tab_id not in self._tabs:
            return -1
            
        widget = self._tabs[tab_id].widget
        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) == widget:
                return i
        return -1

    def _close_index(self, index: int):
        """Close tab by index"""
        try:
            widget = self._tab_widget.widget(index)
            tab_id = self._get_tab_id_for_widget(widget)
            if tab_id:
                self.close_tab(tab_id)
        except Exception as e:
            main_logger.error(f"Failed to close tab at index {index}: {e}")

    # --- Persistence --------------------------------------------------------
    def serialize(self) -> Dict[str, Any]:
        """Serialize pane state for saving"""
        try:
            current_widget = self._tab_widget.currentWidget()
            current_tab_id = self._get_tab_id_for_widget(current_widget)
            
            return {
                'tabs': [
                    {
                        'id': tab.id,
                        'title': tab.title,
                        'file_path': tab.file_path,
                        'is_modified': tab.is_modified,
                        'active': (tab.id == current_tab_id)
                    }
                    for tab in self._tabs.values()
                ]
            }
        except Exception as e:
            main_logger.error(f"Failed to serialize pane state: {e}")
            return {'tabs': []}

    def restore(self, state: Dict[str, Any], factory_registry: Dict[str, Any]):
        """Restore pane state from serialized data"""
        try:
            if not state or 'tabs' not in state:
                return
                
            # Clear existing tabs except default
            for tab_id in list(self._tabs.keys()):
                if tab_id != "default":
                    self.close_tab(tab_id)
            
            # Restore tabs
            active_tab_id = None
            for tab_info in state['tabs']:
                tab_id = tab_info.get('id')
                title = tab_info.get('title', 'untitled')
                file_path = tab_info.get('file_path')
                
                if tab_info.get('active'):
                    active_tab_id = tab_id
                    
                if file_path and Path(file_path).exists():
                    # Restore file tab
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.open_file_tab(file_path, content)
                    except Exception as e:
                        main_logger.warning(f"Could not restore file {file_path}: {e}")
                        
            # Set active tab
            if active_tab_id and active_tab_id in self._tabs:
                idx = self._index_of(active_tab_id)
                if idx >= 0:
                    self._tab_widget.setCurrentIndex(idx)
                    
        except Exception as e:
            main_logger.error(f"Failed to restore pane state: {e}")

__all__ = ["PaneManager", "PaneTab"]
