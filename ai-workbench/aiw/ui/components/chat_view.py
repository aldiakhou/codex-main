"""Enhanced Chat View skeleton (partial Phase 4).
Implements markdown rendering (basic) & message model structure.
"""
from __future__ import annotations
from typing import List, Literal
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtCore import Qt

@dataclass
class ChatMessage:
    role: Literal['user','assistant','system']
    content: str

class ChatView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: List[ChatMessage] = []
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setObjectName("ChatBrowser")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self._browser)

    def add_message(self, role: str, content: str, rich: bool = False):
        """Add a message.
        If rich=True content is treated as HTML (unsafe - only internal sources should set rich).
        """
        cm = ChatMessage(role=role if role in ('user','assistant','system') else 'assistant', content=content)
        self._messages.append(cm)
        self._render_last(cm, rich=rich)

    def _render_last(self, msg: ChatMessage, rich: bool):
        html = self._browser.toHtml() or ""
        role_label = {
            'user': '<span style="color:#4f8cff">User</span>',
            'assistant': '<span style="color:#44c27a">Assistant</span>',
            'system': '<span style="color:#e0a941">System</span>'
        }[msg.role]
        if rich:
            safe = msg.content  # already HTML
        else:
            safe = (msg.content
                    .replace('&','&amp;')
                    .replace('<','&lt;')
                    .replace('>','&gt;'))
            # simple code fence detection
            if '```' in safe:
                parts = safe.split('```')
                rebuilt = []
                for i,p in enumerate(parts):
                    if i % 2 == 1:
                        rebuilt.append(f"<pre style='background:#181b1f;padding:6px;border-radius:4px;'>{p}</pre>")
                    else:
                        rebuilt.append(p)
                safe = ''.join(rebuilt)
            # inline code
            import re
            safe = re.sub(r'`([^`]+)`', r"<code style='background:#181b1f;padding:2px 4px;border-radius:3px;'>\1</code>", safe)
        html += ("<div class='chat-msg' style='margin:6px 4px 10px 4px;font-size:12px;line-height:1.4;'>"
                 f"<div style='font-weight:600;margin-bottom:2px;'>{role_label}</div>{safe}</div>")
        self._browser.setHtml(html)
        self._browser.verticalScrollBar().setValue(self._browser.verticalScrollBar().maximum())

__all__ = ["ChatView", "ChatMessage"]
