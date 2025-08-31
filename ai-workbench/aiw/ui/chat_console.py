from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QSize
import html as _html
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QLabel,
    QSizePolicy,
    QTextBrowser,
    QToolButton,
    QLineEdit,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QPropertyAnimation, QEasingCurve


class MessageBubble(QFrame):
    """A rounded message bubble supporting rich text and role-based styling."""

    def __init__(self, role: str, text: str, rich: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Identify for QSS styling
        self.setObjectName("MessageBubble")
        self.setProperty("msgRole", role)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setFrameShape(QFrame.Shape.NoFrame)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)

        # Align user messages to the right, others to the left
        align_right = role in ("user",)
        if align_right:
            outer.addStretch(1)

        container = QFrame()
        container.setObjectName("BubbleContainer")
        container.setProperty("msgRole", role)
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        v = QVBoxLayout(container)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(6)

        header = QLabel("You" if role == "user" else ("System" if role == "system" else "AI"))
        header.setObjectName("BubbleHeader")
        header.setProperty("msgRole", role)
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        v.addWidget(header)

        # Action row (copy/collapse)
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(6)
        actions.addStretch(1)

        copy_btn = QToolButton()
        copy_btn.setText("Copy")
        actions.addWidget(copy_btn)

        self.collapse_btn = QToolButton()
        self.collapse_btn.setText("Collapse")
        actions.addWidget(self.collapse_btn)
        # Compact action buttons styling (QSS hooks)
        try:
            copy_btn.setObjectName("BubbleAction")
            self.collapse_btn.setObjectName("BubbleAction")
        except Exception:
            pass
        v.addLayout(actions)

        # Use QTextBrowser to allow rich content like <pre>, code, etc.
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setObjectName("BubbleBody")
        body.setProperty("msgRole", role)
        body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        body.setMinimumWidth(300)
        # Make it look like a label, not an editor
        body.setReadOnly(True)
        body.setFrameStyle(QFrame.Shape.NoFrame)

        self._rich = rich
        if rich:
            body.setHtml(text)
        else:
            safe = _html.escape(text).replace("\n", "<br>")
            body.setHtml(f"<span>{safe}</span>")

        v.addWidget(body)
        # Tighter bubble margins and width for right-dock layout
        try:
            v.setContentsMargins(10, 6, 10, 6)
            container.setMaximumWidth(560)
        except Exception:
            pass

        # Restrict max width so long lines wrap nicely
        container.setMaximumWidth(720)

        outer.addWidget(container)
        if not align_right:
            outer.addStretch(1)

        # Hook up actions
        def _copy():
            QGuiApplication.clipboard().setText(body.toPlainText())
        copy_btn.clicked.connect(_copy)

        # Collapse for long content
        self._collapsed = False
        self._body = body
        long_content = len(body.toPlainText()) > 1200 or (rich and "<pre" in text)
        if long_content:
            self._set_collapsed(True)
        self.collapse_btn.clicked.connect(lambda: self._set_collapsed(not self._collapsed))

    @property
    def has_code(self) -> bool:
        if not hasattr(self, "_body"):
            return False
        text = self._body.toHtml()
        return "<pre" in text or "<code" in text

    def _set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        if collapsed:
            self._body.setMaximumHeight(140)
            self.collapse_btn.setText("Expand")
        else:
            self._body.setMaximumHeight(16777215)  # no limit
            self.collapse_btn.setText("Collapse")


class ChatConsole(QWidget):
    """Scrollable list of message bubbles with a simple API."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("ChatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(12, 12, 12, 12)
        self.vbox.setSpacing(8)
        self.vbox.addStretch(1)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll)

        # Mini action bar
        tools = QHBoxLayout()
        tools.setContentsMargins(8, 0, 8, 4)
        tools.setSpacing(6)
        tools.addStretch(1)
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Search chat…")
        self.search_line.setVisible(False)
        tools.addWidget(self.search_line)
        self.next_code_btn = QToolButton()
        self.next_code_btn.setText("Next code ⤵")
        tools.addWidget(self.next_code_btn)
        root.addLayout(tools)
        # Ensure plain-text labels to avoid emoji rendering issues
        try:
            self.search_line.setPlaceholderText("Search chat...")
            self.next_code_btn.setText("Next code")
        except Exception:
            pass

        self.next_code_btn.clicked.connect(self.jump_to_next_code)
        self.search_line.returnPressed.connect(lambda: self.search(self.search_line.text()))

    def add_message(self, role: str, content: str, rich: bool = True):
        # Insert above the stretch so messages stack top->bottom
        index = self.vbox.count() - 1
        bubble = MessageBubble(role, content, rich, self.container)
        self.vbox.insertWidget(index, bubble, 0, Qt.AlignmentFlag.AlignTop)
        self._animate_in(bubble)
        self._scroll_to_bottom()

    def clear(self):
        # Remove all message widgets (keep the stretch at end)
        for i in reversed(range(self.vbox.count() - 1)):
            item = self.vbox.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _scroll_to_bottom(self):
        # Post a scroll to bottom to allow layout to recompute
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _animate_in(self, w: QWidget):
        try:
            eff = w.graphicsEffect()
            if eff is None:
                from PySide6.QtWidgets import QGraphicsOpacityEffect
                eff = QGraphicsOpacityEffect(w)
                w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", w)
            anim.setDuration(180)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        except Exception:
            pass

    def jump_to_next_code(self):
        # Find the next bubble after current scroll position that has code
        y = self.scroll.verticalScrollBar().value()
        found = None
        for i in range(self.vbox.count() - 1):
            w = self.vbox.itemAt(i).widget()
            if not isinstance(w, MessageBubble):
                continue
            top = w.mapTo(self.container, w.rect().topLeft()).y()
            if top > y and w.has_code:
                found = w
                break
        if found:
            self.scroll.ensureWidgetVisible(found)

    def search(self, text: str):
        if not text:
            return
        for i in range(self.vbox.count() - 1):
            w = self.vbox.itemAt(i).widget()
            if not isinstance(w, MessageBubble):
                continue
            if text.lower() in w._body.toPlainText().lower():
                self.scroll.ensureWidgetVisible(w)
                # Highlight inside the bubble if possible
                w._body.find(text, QTextBrowser.FindFlag.FindCaseSensitively)
                break
