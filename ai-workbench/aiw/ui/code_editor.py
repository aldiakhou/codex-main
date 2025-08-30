"""
Enhanced code editor with syntax highlighting for AI Development Workbench
"""
import re
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRegularExpression, QSize, QPoint
from PySide6.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, QColor,
    QFontMetrics, QPainter, QTextBlock
)
from PySide6.QtWidgets import (
    QTextEdit, QVBoxLayout, QWidget, QLabel,
    QPushButton, QMessageBox, QHBoxLayout
)


class SyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for various programming languages"""

    def __init__(self, parent=None, language="python"):
        super().__init__(parent)
        self.language = language
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self):
        """Setup text formats for different syntax elements"""
        # Keywords
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#0000FF"))  # Blue
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        # Strings
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#008000"))  # Green

        # Comments
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#808080"))  # Gray
        self.comment_format.setFontItalic(True)

        # Numbers
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#FF6600"))  # Orange

        # Functions
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#800080"))  # Purple
        self.function_format.setFontWeight(QFont.Weight.Bold)

        # Classes
        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor("#000080"))  # Dark Blue
        self.class_format.setFontWeight(QFont.Weight.Bold)

    def _setup_rules(self):
        """Setup highlighting rules based on language"""
        self.highlighting_rules = []

        if self.language.lower() in ["python", "py"]:
            self._setup_python_rules()
        elif self.language.lower() in ["javascript", "js", "typescript", "ts"]:
            self._setup_javascript_rules()
        elif self.language.lower() in ["java"]:
            self._setup_java_rules()
        elif self.language.lower() in ["cpp", "c++", "cxx"]:
            self._setup_cpp_rules()
        else:
            self._setup_generic_rules()

    def _setup_python_rules(self):
        """Python-specific highlighting rules"""
        # Keywords
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "not", "or",
            "pass", "raise", "return", "try", "while", "with", "yield",
            "True", "False", "None", "self", "super"
        ]
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Strings
        self.highlighting_rules.append((QRegularExpression(r'".*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), self.string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r'\b\d+\b'), self.number_format))

        # Functions
        self.highlighting_rules.append((QRegularExpression(r'\bdef\s+(\w+)'), self.function_format))

        # Classes
        self.highlighting_rules.append((QRegularExpression(r'\bclass\s+(\w+)'), self.class_format))

    def _setup_javascript_rules(self):
        """JavaScript/TypeScript highlighting rules"""
        keywords = [
            "var", "let", "const", "function", "if", "else", "for", "while",
            "do", "switch", "case", "default", "break", "continue", "return",
            "try", "catch", "finally", "throw", "typeof", "instanceof", "in",
            "new", "this", "super", "class", "extends", "import", "export",
            "from", "async", "await", "true", "false", "null", "undefined"
        ]
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Strings
        self.highlighting_rules.append((QRegularExpression(r'".*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), self.string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), self.number_format))

        # Functions
        self.highlighting_rules.append((QRegularExpression(r'\bfunction\s+(\w+)'), self.function_format))

        # Classes
        self.highlighting_rules.append((QRegularExpression(r'\bclass\s+(\w+)'), self.class_format))

    def _setup_java_rules(self):
        """Java highlighting rules"""
        keywords = [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int", "interface",
            "long", "native", "new", "package", "private", "protected", "public",
            "return", "short", "static", "strictfp", "super", "switch", "synchronized",
            "this", "throw", "throws", "transient", "try", "void", "volatile", "while"
        ]
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Strings
        self.highlighting_rules.append((QRegularExpression(r'".*"'), self.string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), self.number_format))

        # Classes
        self.highlighting_rules.append((QRegularExpression(r'\bclass\s+(\w+)'), self.class_format))

    def _setup_cpp_rules(self):
        """C/C++ highlighting rules"""
        keywords = [
            "auto", "break", "case", "char", "const", "continue", "default", "do",
            "double", "else", "enum", "extern", "float", "for", "goto", "if",
            "int", "long", "register", "return", "short", "signed", "sizeof",
            "static", "struct", "switch", "typedef", "union", "unsigned", "void",
            "volatile", "while", "class", "public", "private", "protected",
            "virtual", "friend", "inline", "template", "namespace", "using",
            "new", "delete", "this", "true", "false", "nullptr"
        ]
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Strings
        self.highlighting_rules.append((QRegularExpression(r'".*"'), self.string_format))

        # Comments
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'/\*.*?\*/', QRegularExpression.DotMatchesEverythingOption), self.comment_format))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), self.number_format))

        # Classes
        self.highlighting_rules.append((QRegularExpression(r'\bclass\s+(\w+)'), self.class_format))

    def _setup_generic_rules(self):
        """Generic highlighting for unknown languages"""
        # Basic strings
        self.highlighting_rules.append((QRegularExpression(r'".*"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), self.string_format))

        # Basic comments
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'//.*'), self.comment_format))

        # Numbers
        self.highlighting_rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), self.number_format))

    def highlightBlock(self, text):
        """Apply highlighting to a block of text"""
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class LineNumberArea(QWidget):
    """Widget for displaying line numbers"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QTextEdit):
    """Enhanced code editor with syntax highlighting and line numbers"""

    file_changed = Signal(bool)  # True if file has unsaved changes
    file_saved = Signal(str)     # Emitted when file is saved

    def __init__(self, parent=None):
        super().__init__(parent)

        # Editor state
        self.current_file_path = None
        self.original_content = ""
        self.has_unsaved_changes = False
        self.language = "python"

        # Setup UI
        self.setFont(QFont("Consolas", 10))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)

        # Line numbers
        self.line_number_area = LineNumberArea(self)
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(
            lambda value: self.update_line_number_area()
        )
        self.update_line_number_area_width()

        # Syntax highlighting
        self.highlighter = SyntaxHighlighter(self.document(), self.language)

        # Connect signals
        self.textChanged.connect(self._on_text_changed)

    def set_language(self, language: str):
        """Set the programming language for syntax highlighting"""
        self.language = language.lower()
        if hasattr(self, 'highlighter'):
            self.highlighter.language = self.language
            self.highlighter.rehighlight()

    def detect_language_from_file(self, file_path: str):
        """Detect programming language from file extension"""
        if not file_path:
            return "text"

        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown'
        }
        return language_map.get(ext, 'text')

    def load_file(self, file_path: str) -> bool:
        """Load a file into the editor"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.setPlainText(content)
            self.current_file_path = file_path
            self.original_content = content
            self.has_unsaved_changes = False

            # Detect and set language
            self.language = self.detect_language_from_file(file_path)
            self.highlighter.language = self.language
            self.highlighter.rehighlight()

            self.file_changed.emit(False)
            return True

        except Exception as e:
            QMessageBox.warning(
                self, "Error Loading File",
                f"Failed to load file:\n{str(e)}"
            )
            return False

    def save_file(self) -> bool:
        """Save the current file"""
        if not self.current_file_path:
            return False

        try:
            content = self.toPlainText()
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.original_content = content
            self.has_unsaved_changes = False
            self.file_changed.emit(False)
            self.file_saved.emit(self.current_file_path)
            return True

        except Exception as e:
            QMessageBox.warning(
                self, "Error Saving File",
                f"Failed to save file:\n{str(e)}"
            )
            return False

    def save_file_as(self, file_path: str) -> bool:
        """Save the current content to a new file"""
        try:
            content = self.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.current_file_path = file_path
            self.original_content = content
            self.has_unsaved_changes = False

            # Detect and set language
            self.language = self.detect_language_from_file(file_path)
            self.highlighter.language = self.language
            self.highlighter.rehighlight()

            self.file_changed.emit(False)
            self.file_saved.emit(file_path)
            return True

        except Exception as e:
            QMessageBox.warning(
                self, "Error Saving File",
                f"Failed to save file:\n{str(e)}"
            )
            return False

    def has_changes(self) -> bool:
        """Check if the file has unsaved changes"""
        return self.has_unsaved_changes

    def get_current_file_path(self) -> str:
        """Get the current file path"""
        return self.current_file_path or ""

    def get_current_file_name(self) -> str:
        """Get the current file name"""
        if self.current_file_path:
            return Path(self.current_file_path).name
        return "Untitled"

    def _on_text_changed(self):
        """Handle text changes"""
        current_content = self.toPlainText()
        has_changes = current_content != self.original_content

        if has_changes != self.has_unsaved_changes:
            self.has_unsaved_changes = has_changes
            self.file_changed.emit(has_changes)

    def line_number_area_width(self):
        """Calculate width needed for line number area"""
        digits = len(str(max(1, self.document().blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self):
        """Update line number area width"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self):
        """Update line number area when scrolling"""
        self.line_number_area.update()

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(),
            self.line_number_area_width(), cr.height()
        )

    def line_number_area_paint_event(self, event):
        """Paint line numbers"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.GlobalColor.lightGray)

        # Get the first visible block
        block = self.document().findBlock(self.cursorForPosition(QPoint(0, 0)).position())
        if not block.isValid():
            block = self.document().firstBlock()

        block_number = block.blockNumber()

        # Calculate the top position of the first visible block
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        rect = self.cursorRect(cursor)
        top = rect.top()

        # Get the height of each block
        font_metrics = self.fontMetrics()
        block_height = font_metrics.height()

        while block.isValid() and top <= event.rect().bottom():
            if top >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(
                    0, int(top), self.line_number_area.width() - 2,
                    block_height,
                    Qt.AlignmentFlag.AlignRight, number
                )

            block = block.next()
            top += block_height
            block_number += 1

        painter.end()


class CodeEditorWidget(QWidget):
    """Widget containing the code editor with toolbar"""

    file_changed = Signal(bool)
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = CodeEditor()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.file_label = QLabel("No file selected")
        toolbar_layout.addWidget(self.file_label)

        toolbar_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_file)
        self.save_button.setEnabled(False)
        toolbar_layout.addWidget(self.save_button)

        layout.addLayout(toolbar_layout)

        # Editor
        layout.addWidget(self.editor)

    def _connect_signals(self):
        """Connect signals"""
        self.editor.file_changed.connect(self._on_file_changed)
        self.editor.file_saved.connect(self._on_file_saved)

    def load_file(self, file_path: str) -> bool:
        """Load a file"""
        success = self.editor.load_file(file_path)
        if success:
            self.file_label.setText(f"File: {self.editor.get_current_file_name()}")
        return success

    def save_file(self) -> bool:
        """Save the current file"""
        return self.editor.save_file()

    def has_changes(self) -> bool:
        """Check if file has changes"""
        return self.editor.has_changes()

    def get_current_file_path(self) -> str:
        """Get current file path"""
        return self.editor.get_current_file_path()

    def set_text(self, text: str):
        """Set the editor's text content programmatically."""
        self.editor.setPlainText(text)
        # We consider this a new "original" state, so unsaved changes are reset
        self.editor.original_content = text
        self.editor._on_text_changed()

    def _save_file(self):
        """Save file button clicked"""
        self.save_file()

    def _on_file_changed(self, has_changes: bool):
        """Handle file changed"""
        self.save_button.setEnabled(has_changes)
        self.file_changed.emit(has_changes)

    def _on_file_saved(self, file_path: str):
        """Handle file saved"""
        self.save_button.setEnabled(False)
        self.file_saved.emit(file_path)
