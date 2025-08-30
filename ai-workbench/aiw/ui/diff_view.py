"""
Diff viewer widget for AI Development Workbench
"""
import difflib
from pathlib import Path
from typing import List, Tuple, Optional
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QSplitter, QScrollArea, QFrame, QCheckBox
)


class DiffLine:
    """Represents a line in a diff"""

    def __init__(self, line_type: str, content: str, old_line_no: Optional[int] = None,
                 new_line_no: Optional[int] = None):
        self.line_type = line_type  # 'context', 'add', 'remove', 'header'
        self.content = content
        self.old_line_no = old_line_no
        self.new_line_no = new_line_no
        self.selected = False

    @property
    def is_addition(self) -> bool:
        return self.line_type == 'add'

    @property
    def is_removal(self) -> bool:
        return self.line_type == 'remove'

    @property
    def is_context(self) -> bool:
        return self.line_type == 'context'

    @property
    def is_header(self) -> bool:
        return self.line_type == 'header'


class DiffHunk:
    """Represents a hunk (section) of a diff"""

    def __init__(self, header: str, lines: List[DiffLine]):
        self.header = header
        self.lines = lines
        self.selected = False

    @property
    def has_changes(self) -> bool:
        """Check if this hunk contains any changes"""
        return any(line.is_addition or line.is_removal for line in self.lines)

    @property
    def additions(self) -> int:
        """Count of added lines"""
        return sum(1 for line in self.lines if line.is_addition)

    @property
    def removals(self) -> int:
        """Count of removed lines"""
        return sum(1 for line in self.lines if line.is_removal)


class DiffViewer(QTextEdit):
    """Text widget for displaying diff content with syntax highlighting"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Setup colors for diff display
        self.addition_color = QColor("#e6ffed")  # Light green
        self.removal_color = QColor("#ffeef0")  # Light red
        self.context_color = QColor("#f6f8fa")  # Light gray
        self.header_color = QColor("#fafbfc")   # Very light gray

        self.addition_text_color = QColor("#22863a")  # Dark green
        self.removal_text_color = QColor("#cb2431")  # Dark red
        self.context_text_color = QColor("#24292e")  # Dark gray

    def set_diff_content(self, content: str):
        """Set the diff content and apply highlighting"""
        self.setPlainText(content)
        self._apply_diff_highlighting()

    def _apply_diff_highlighting(self):
        """Apply syntax highlighting to diff content"""
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)

        # Clear existing formatting
        cursor.select(cursor.SelectionType.Document)
        format = QTextCharFormat()
        format.setBackground(QColor("white"))
        cursor.setCharFormat(format)
        cursor.clearSelection()

        # Apply highlighting line by line
        block = self.document().firstBlock()
        while block.isValid():
            text = block.text()

            if text.startswith('+') and not text.startswith('+++'):
                # Addition line
                self._highlight_line(block, self.addition_color, self.addition_text_color)
            elif text.startswith('-') and not text.startswith('---'):
                # Removal line
                self._highlight_line(block, self.removal_color, self.removal_text_color)
            elif text.startswith('@@'):
                # Hunk header
                self._highlight_line(block, self.header_color, self.context_text_color)
            elif text.startswith(' '):
                # Context line
                self._highlight_line(block, self.context_color, self.context_text_color)

            block = block.next()

    def _highlight_line(self, block, bg_color: QColor, text_color: QColor):
        """Highlight a specific line"""
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, block.length())

        format = QTextCharFormat()
        format.setBackground(bg_color)
        format.setForeground(text_color)
        cursor.setCharFormat(format)


class DiffWidget(QWidget):
    """Main diff widget with controls"""

    hunk_selected = Signal(int, bool)  # hunk_index, selected
    apply_requested = Signal()
    discard_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hunks: List[DiffHunk] = []
        self.current_file = ""

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # Header with file info
        header_layout = QHBoxLayout()
        self.file_label = QLabel("No diff loaded")
        header_layout.addWidget(self.file_label)

        header_layout.addStretch()

        # Control buttons
        self.apply_button = QPushButton("Apply Selected")
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.apply_button.setEnabled(False)
        header_layout.addWidget(self.apply_button)

        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(self._on_discard_clicked)
        header_layout.addWidget(self.discard_button)

        layout.addLayout(header_layout)

        # Diff viewer
        self.diff_viewer = DiffViewer()
        layout.addWidget(self.diff_viewer)

        # Hunk controls
        self.hunk_controls_widget = QWidget()
        self.hunk_controls_layout = QVBoxLayout(self.hunk_controls_widget)
        layout.addWidget(self.hunk_controls_widget)

    def set_diff_content(self, diff_text: str, file_path: str = ""):
        """Set the diff content to display"""
        self.current_file = file_path
        self.file_label.setText(f"Diff: {Path(file_path).name}" if file_path else "Diff")

        # Parse the diff into hunks
        self.hunks = self._parse_diff(diff_text)

        # Display the diff
        self.diff_viewer.set_diff_content(diff_text)

        # Create hunk controls
        self._create_hunk_controls()

        # Update button states
        self._update_button_states()

    def _parse_diff(self, diff_text: str) -> List[DiffHunk]:
        """Parse diff text into hunks"""
        hunks = []
        lines = diff_text.split('\n')

        current_hunk_lines = []
        current_header = ""

        for line in lines:
            if line.startswith('@@'):
                # New hunk header
                if current_hunk_lines:
                    hunks.append(DiffHunk(current_header, current_hunk_lines))

                current_header = line
                current_hunk_lines = []
            elif line.startswith('+++') or line.startswith('---'):
                # File header, skip
                continue
            else:
                # Diff line
                if line.startswith('+'):
                    diff_line = DiffLine('add', line[1:], None, None)
                elif line.startswith('-'):
                    diff_line = DiffLine('remove', line[1:], None, None)
                elif line.startswith(' '):
                    diff_line = DiffLine('context', line[1:], None, None)
                else:
                    diff_line = DiffLine('header', line, None, None)

                current_hunk_lines.append(diff_line)

        # Add the last hunk
        if current_hunk_lines:
            hunks.append(DiffHunk(current_header, current_hunk_lines))

        return hunks

    def _create_hunk_controls(self):
        """Create checkboxes for hunk selection"""
        # Clear existing controls
        for i in reversed(range(self.hunk_controls_layout.count())):
            widget = self.hunk_controls_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.hunks:
            return

        # Add hunk selection controls
        for i, hunk in enumerate(self.hunks):
            if hunk.has_changes:
                hunk_layout = QHBoxLayout()

                checkbox = QCheckBox(f"Hunk {i+1}: +{hunk.additions} -{hunk.removals}")
                checkbox.setChecked(hunk.selected)
                checkbox.stateChanged.connect(lambda state, idx=i: self._on_hunk_toggled(idx, state))
                hunk_layout.addWidget(checkbox)

                hunk_layout.addStretch()
                self.hunk_controls_layout.addLayout(hunk_layout)

    def _on_hunk_toggled(self, hunk_index: int, state: int):
        """Handle hunk selection toggle"""
        if 0 <= hunk_index < len(self.hunks):
            self.hunks[hunk_index].selected = (state == Qt.CheckState.Checked)
            self.hunk_selected.emit(hunk_index, self.hunks[hunk_index].selected)
            self._update_button_states()

    def _on_apply_clicked(self):
        """Handle apply button clicked"""
        self.apply_requested.emit()

    def _on_discard_clicked(self):
        """Handle discard button clicked"""
        self.discard_requested.emit()

    def _update_button_states(self):
        """Update button enabled states"""
        has_selection = any(hunk.selected for hunk in self.hunks)
        self.apply_button.setEnabled(has_selection)

    def get_selected_hunks(self) -> List[int]:
        """Get indices of selected hunks"""
        return [i for i, hunk in enumerate(self.hunks) if hunk.selected]

    def get_selected_diff_text(self) -> Optional[str]:
        """Construct a diff text from selected hunks only."""
        if not any(hunk.selected for hunk in self.hunks):
            return None

        full_diff_lines = self.diff_viewer.toPlainText().split('\n')
        header_lines = [line for line in full_diff_lines if line.startswith('---') or line.startswith('+++')]
        
        new_diff_parts = header_lines
        
        selected_hunk_indices = self.get_selected_hunks()
        
        for i in selected_hunk_indices:
            hunk = self.hunks[i]
            new_diff_parts.append(hunk.header)
            for line in hunk.lines:
                if line.is_addition:
                    new_diff_parts.append(f'+{line.content}')
                elif line.is_removal:
                    new_diff_parts.append(f'-{line.content}')
                elif line.is_context:
                    new_diff_parts.append(f' {line.content}')

        return "\n".join(new_diff_parts)

    def select_all_hunks(self):
        """Select all hunks"""
        for hunk in self.hunks:
            hunk.selected = True
        self._create_hunk_controls()
        self._update_button_states()

    def select_no_hunks(self):
        """Deselect all hunks"""
        for hunk in self.hunks:
            hunk.selected = False
        self._create_hunk_controls()
        self._update_button_states()

    def get_diff_text(self) -> str:
        """Get the current diff text"""
        return self.diff_viewer.toPlainText()

    def clear(self):
        """Clear the diff display"""
        self.hunks.clear()
        self.diff_viewer.clear()
        self.file_label.setText("No diff loaded")
        self._create_hunk_controls()
        self._update_button_states()


class DiffViewWidget(QWidget):
    """Complete diff view widget for the main window"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.diff_widget = DiffWidget()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.title_label = QLabel("Diff Viewer")
        toolbar_layout.addWidget(self.title_label)

        toolbar_layout.addStretch()

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.diff_widget.select_all_hunks)
        toolbar_layout.addWidget(self.select_all_button)

        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self.diff_widget.select_no_hunks)
        toolbar_layout.addWidget(self.select_none_button)

        layout.addLayout(toolbar_layout)

        # Diff widget
        layout.addWidget(self.diff_widget)

    def set_diff_content(self, diff_text: str, file_path: str = ""):
        """Set diff content"""
        self.diff_widget.set_diff_content(diff_text, file_path)
        if file_path:
            self.title_label.setText(f"Diff: {Path(file_path).name}")
        else:
            self.title_label.setText("Diff Viewer")

    def get_selected_hunks(self) -> List[int]:
        """Get selected hunk indices"""
        return self.diff_widget.get_selected_hunks()

    def clear(self):
        """Clear the diff"""
        self.diff_widget.clear()
        self.title_label.setText("Diff Viewer")
