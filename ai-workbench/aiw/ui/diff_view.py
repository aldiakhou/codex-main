"""
Diff viewer widget for AI Development Workbench with modern design
"""
import difflib
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QSplitter, QScrollArea, QFrame, QCheckBox
)

from .design_tokens import get_tokens


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

    def __init__(self, header: str, lines: List[DiffLine], file_path: Optional[str] = None):
        self.header = header
        self.lines = lines
        self.selected = False
        self.file_path = file_path

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
    """Text widget for displaying diff content with modern syntax highlighting"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = "dark"  # Default theme
        self.tokens = get_tokens(self.theme)
        
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._setup_theme_colors()
        self._apply_styling()

    def _setup_theme_colors(self):
        """Setup theme-aware colors for diff highlighting"""
        if self.theme == "dark":
            # Dark theme colors
            self.addition_color = QColor("#1a472a")  # Dark green background
            self.removal_color = QColor("#5c1e2a")   # Dark red background
            self.context_color = QColor("#0d1117")   # Dark background
            self.header_color = QColor("#21262d")    # Header background
            
            self.addition_text_color = QColor("#56d364")  # Bright green text
            self.removal_text_color = QColor("#f85149")   # Bright red text
            self.context_text_color = QColor("#e6edf3")   # Light gray text
            self.header_text_color = QColor("#7d8590")    # Muted text
        else:
            # Light theme colors
            self.addition_color = QColor("#dafbe1")  # Light green background
            self.removal_color = QColor("#ffebe9")   # Light red background
            self.context_color = QColor("#ffffff")   # White background
            self.header_color = QColor("#f6f8fa")    # Light gray background
            
            self.addition_text_color = QColor("#116329")  # Dark green text
            self.removal_text_color = QColor("#d1242f")   # Dark red text
            self.context_text_color = QColor("#24292f")   # Dark text
            self.header_text_color = QColor("#656d76")    # Muted text

    def _apply_styling(self):
        """Apply professional styling using design tokens"""
        code_font = QFont(
            self.tokens.typography.code_family.split(',')[0].strip().strip("'\""),
            self.tokens.typography.sizes["sm"]
        )
        self.setFont(code_font)
        
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {self.tokens.colors.semantic["surface"]};
                color: {self.tokens.colors.palette["text"]};
                border: 1px solid {self.tokens.colors.palette["border"]};
                border-radius: {self.tokens.radii.values["md"]}px;
                padding: {self.tokens.spacing.gutters["component"]}px;
                font-family: {self.tokens.typography.code_family};
                font-size: {self.tokens.typography.sizes["sm"]}pt;
                line-height: {int(self.tokens.typography.sizes["sm"] * self.tokens.typography.line_height)}px;
            }}
        """)

    def update_theme(self, theme: str):
        """Update the theme (legacy method name)"""
        self.set_theme(theme)
        
    def set_theme(self, theme: str):
        """Set the theme for the diff viewer"""
        self.theme = theme
        self.tokens = get_tokens(theme)
        self._setup_theme_colors()
        self._apply_styling()
        self.set_diff_content(self.toPlainText())  # Re-apply highlighting

    def set_diff_content(self, content: str):
        """Set the diff content and apply highlighting"""
        self.setPlainText(content)
        self._apply_diff_highlighting()

    def _apply_diff_highlighting(self):
        """Apply modern syntax highlighting to diff content"""
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)

        # Clear existing formatting
        cursor.select(cursor.SelectionType.Document)
        format = QTextCharFormat()
        format.setBackground(QColor(self.tokens.colors.semantic["surface"]))
        format.setForeground(QColor(self.tokens.colors.palette["text"]))
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
                self._highlight_line(block, self.header_color, self.header_text_color)
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
    """Main diff widget with controls and modern design"""

    hunk_selected = Signal(int, bool)  # hunk_index, selected
    apply_requested = Signal()
    discard_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = "dark"  # Default theme
        self.tokens = get_tokens(self.theme)
        self.hunks: List[DiffHunk] = []
        self.current_file = ""

        self._setup_ui()

    def set_theme(self, theme: str):
        """Set the theme for the diff widget (public method)"""
        self.theme = theme
        self.tokens = get_tokens(theme)
        if hasattr(self, 'diff_viewer'):
            self.diff_viewer.set_theme(theme)

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

        # Hunk controls (wrapped in scroll area to cap height)
        self.hunk_controls_widget = QWidget()
        self.hunk_controls_layout = QVBoxLayout(self.hunk_controls_widget)
        from PySide6.QtWidgets import QScrollArea
        self.hunk_controls_scroll = QScrollArea()
        self.hunk_controls_scroll.setWidgetResizable(True)
        self.hunk_controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hunk_controls_scroll.setWidget(self.hunk_controls_widget)
        self.hunk_controls_scroll.setMaximumHeight(180)
        layout.addWidget(self.hunk_controls_scroll)

    def set_diff_content(self, diff_text: str, file_path: str = ""):
        """Set the diff content to display"""
        self.current_file = file_path
        self.file_label.setText(f"Diff: {Path(file_path).name}" if file_path else "Diff")

        # Parse the diff into hunks
        self.hunks = self._parse_diff(diff_text)
        # Auto-select hunks by default for convenience
        for h in self.hunks:
            if h.has_changes:
                h.selected = True

        # Display the diff
        self.diff_viewer.set_diff_content(diff_text)

        # Create hunk controls
        self._create_hunk_controls()

        # Update button states
        self._update_button_states()

    def _parse_diff(self, diff_text: str) -> List[DiffHunk]:
        """Parse diff text into hunks and track file for each hunk."""
        hunks: List[DiffHunk] = []
        lines = diff_text.split('\n')

        current_hunk_lines: List[DiffLine] = []
        current_header = ""
        current_file: Optional[str] = None

        def flush_hunk():
            nonlocal current_hunk_lines, current_header, current_file
            if current_hunk_lines:
                hunks.append(DiffHunk(current_header, current_hunk_lines, file_path=current_file))
                current_hunk_lines = []
                current_header = ""

        for line in lines:
            if line.startswith('diff --git '):
                flush_hunk()
                continue
            if line.startswith('+++ '):
                plus_path = line[4:].strip()
                if plus_path.startswith('b/'):
                    current_file = plus_path[2:]
                elif plus_path != '/dev/null':
                    current_file = plus_path
                continue
            if line.startswith('--- '):
                # old-file header; ignore
                continue
            if line.startswith('@@'):
                flush_hunk()
                current_header = line
                current_hunk_lines = []
                continue

            if line.startswith('+') and not line.startswith('+++'):
                diff_line = DiffLine('add', line[1:], None, None)
            elif line.startswith('-') and not line.startswith('---'):
                diff_line = DiffLine('remove', line[1:], None, None)
            elif line.startswith(' '):
                diff_line = DiffLine('context', line[1:], None, None)
            else:
                diff_line = DiffLine('header', line, None, None)
            current_hunk_lines.append(diff_line)

        flush_hunk()
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

        # Add hunk selection controls (compact)
        for i, hunk in enumerate(self.hunks):
            if hunk.has_changes:
                hunk_layout = QHBoxLayout()
                label = f"Hunk {i+1} (+{hunk.additions}/-{hunk.removals})"
                if getattr(hunk, 'file_path', None):
                    try:
                        label += f" — {Path(hunk.file_path).name}"
                    except Exception:
                        pass
                checkbox = QCheckBox(label)
                checkbox.setChecked(hunk.selected)
                checkbox.stateChanged.connect(lambda state, idx=i: self._on_hunk_toggled(idx, state))
                hunk_layout.addWidget(checkbox)

                hunk_layout.addStretch()
                self.hunk_controls_layout.addLayout(hunk_layout)
        try:
            self.hunk_controls_widget.update()
        except Exception:
            pass

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
        """Construct a diff text from selected hunks only (may contain multiple files)."""
        files = self.get_selected_diffs_by_file()
        if not files:
            return None
        return "\n".join(files.values())

    def get_selected_diffs_by_file(self) -> Dict[str, str]:
        """Return mapping: repo-relative file path -> unified diff text for selected hunks."""
        result: Dict[str, List[str]] = {}
        for hunk in self.hunks:
            if not hunk.selected or not hunk.has_changes or not getattr(hunk, 'file_path', None):
                continue
            fp = hunk.file_path
            if fp not in result:
                result[fp] = [f"--- a/{fp}", f"+++ b/{fp}"]
            result[fp].append(hunk.header)
            for line in hunk.lines:
                if line.is_addition:
                    result[fp].append(f"+{line.content}")
                elif line.is_removal:
                    result[fp].append(f"-{line.content}")
                elif line.is_context:
                    result[fp].append(f" {line.content}")
        return {fp: "\n".join(parts) for fp, parts in result.items()}

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
    """Complete diff view widget with modern design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = "dark"  # Default theme
        self.tokens = get_tokens(self.theme)

        self.diff_widget = DiffWidget()
        self._setup_ui()
        self._apply_styling()

    def set_theme(self, theme: str):
        """Set the theme for the entire diff view (public method)"""
        self.theme = theme
        self.tokens = get_tokens(theme)
        self.diff_widget.set_theme(theme)
        self._apply_styling()

    def _setup_ui(self):
        """Setup the UI with modern design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.tokens.spacing.gutters["panel"],
            self.tokens.spacing.gutters["panel"],
            self.tokens.spacing.gutters["panel"],
            self.tokens.spacing.gutters["panel"]
        )
        layout.setSpacing(self.tokens.spacing.gutters["component"])

        # Modern toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(self.tokens.spacing.gutters["component"])

        # Title with modern styling
        self.title_label = QLabel("📊 Diff Viewer")
        self.title_label.setObjectName("titleLabel")
        toolbar_layout.addWidget(self.title_label)

        toolbar_layout.addStretch()

        # Action buttons with semantic styling
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.setProperty("class", "subtle")
        self.select_all_button.clicked.connect(self.diff_widget.select_all_hunks)
        toolbar_layout.addWidget(self.select_all_button)

        self.select_none_button = QPushButton("Clear Selection")
        self.select_none_button.setProperty("class", "subtle")
        self.select_none_button.clicked.connect(self.diff_widget.select_no_hunks)
        toolbar_layout.addWidget(self.select_none_button)

        layout.addLayout(toolbar_layout)

        # Diff widget with professional spacing
        layout.addWidget(self.diff_widget)

    def _apply_styling(self):
        """Apply professional styling using design tokens"""
        self.title_label.setStyleSheet(f"""
            QLabel#titleLabel {{
                color: {self.tokens.colors.palette["text"]};
                font-size: {self.tokens.typography.sizes["heading"]}pt;
                font-weight: 600;
                padding: {self.tokens.spacing.gutters["component"]}px {self.tokens.spacing.gutters["panel"]}px;
                background: {self.tokens.colors.semantic["surface-alt"]};
                border: 1px solid {self.tokens.colors.palette["border"]};
                border-radius: {self.tokens.radii.values["sm"]}px;
            }}
        """)

    def update_theme(self, theme: str):
        """Update the theme for the entire diff view (legacy method name)"""
        self.set_theme(theme)

    def set_diff_content(self, diff_text: str, file_path: str = ""):
        """Set diff content"""
        self.diff_widget.set_diff_content(diff_text, file_path)
        if file_path:
            self.title_label.setText(f"📊 Diff: {Path(file_path).name}")
        else:
            self.title_label.setText("📊 Diff Viewer")

    def get_selected_hunks(self) -> List[int]:
        """Get selected hunk indices"""
        return self.diff_widget.get_selected_hunks()

    def clear(self):
        """Clear the diff"""
        self.diff_widget.clear()
        self.title_label.setText("📊 Diff Viewer")
