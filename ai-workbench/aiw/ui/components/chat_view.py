"""Enhanced Chat View with full message support and UI features.
Implements markdown rendering, message management, and interactive features.
"""
from __future__ import annotations
from typing import List, Literal, Optional
from dataclasses import dataclass
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextBrowser, QPushButton, 
                               QHBoxLayout, QLabel, QFrame, QApplication, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QPalette
from ..theme_manager import get_current_theme
import logging

main_logger = logging.getLogger('MainWindow.ChatView')

@dataclass
class ChatMessage:
    role: Literal['user','assistant','system']
    content: str
    timestamp: Optional[str] = None
    rich: bool = False

class ChatView(QWidget):
    """Enhanced chat view with message management and features"""
    
    # Signals
    message_sent = Signal(str)  # Emitted when user sends a message
    copy_requested = Signal(str)  # Emitted when user wants to copy text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: List[ChatMessage] = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the chat view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setObjectName("ChatBrowser")
        self._browser.setFont(QFont("Segoe UI", 10))
        
        # Enable proper HTML rendering
        self._browser.setAcceptRichText(True)
        self._browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        
        layout.addWidget(self._browser)
        
        # Control buttons
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)
        # Role filter checkboxes
        self._user_filter = QCheckBox("User")
        self._assistant_filter = QCheckBox("Assistant")
        self._system_filter = QCheckBox("System")
        for cb in (self._user_filter, self._assistant_filter, self._system_filter):
            cb.setChecked(True)
            cb.stateChanged.connect(self._apply_filters)
            control_layout.addWidget(cb)
        
        # Clear chat button
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        control_layout.addWidget(self.clear_button)
        
        # Export chat button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._export_chat)
        control_layout.addWidget(self.export_button)
        
        control_layout.addStretch()
        
        # Message count label
        self.count_label = QLabel("0 messages")
        self.count_label.setStyleSheet("color: #666; font-size: 10px;")
        control_layout.addWidget(self.count_label)
        
        layout.addLayout(control_layout)

    def add_message(self, role: str, content: str, rich: bool = False, timestamp: Optional[str] = None):
        """Add a message to the chat.
        If rich=True content is treated as HTML (unsafe - only internal sources should set rich).
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
        cm = ChatMessage(
            role=role if role in ('user','assistant','system') else 'assistant', 
            content=content,
            timestamp=timestamp,
            rich=rich
        )
        self._messages.append(cm)
        self._render_last(cm)
        self._update_count()

    def add_user_message(self, content: str, timestamp: Optional[str] = None):
        """Add a user message to the chat"""
        self.add_message('user', content, timestamp=timestamp)
        
    def add_ai_message(self, content: str, rich: bool = False, timestamp: Optional[str] = None):
        """Add an AI response to the chat"""
        self.add_message('assistant', content, rich=rich, timestamp=timestamp)
        
    def add_system_message(self, content: str, timestamp: Optional[str] = None):
        """Add a system message to the chat"""
        self.add_message('system', content, timestamp=timestamp)

    def _render_last(self, msg: ChatMessage):
        """Render the last message to the browser"""
        try:
            # Get current messages HTML
            existing_html = ""
            if len(self._messages) > 1:
                # Rebuild all messages to maintain consistency
                all_html = self._build_all_messages_html()
                self._browser.setHtml(all_html)
            else:
                # First message, create fresh HTML
                all_html = self._build_all_messages_html()
                self._browser.setHtml(all_html)
            
            # Auto-scroll to bottom
            scrollbar = self._browser.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            main_logger.error(f"Failed to render message: {e}")
    
    def _build_all_messages_html(self) -> str:
        """Build complete HTML for all messages"""
        colors = self._get_theme_colors()
        
        # HTML document structure
        html_parts = [
            '<!DOCTYPE html>',
            '<html><head>',
            '<meta charset="utf-8">',
            '<style>',
            'body { margin: 0; padding: 8px; font-family: "Segoe UI", Arial, sans-serif; }',
            f'.chat-msg {{ margin: 8px 6px 12px 6px; padding: 8px; border-radius: 6px; font-size: 12px; line-height: 1.4; }}',
            f'.user-msg {{ background: {colors["user_bg"]}; border-left: 3px solid {colors["user_border"]}; }}',
            f'.assistant-msg {{ background: {colors["assistant_bg"]}; border-left: 3px solid {colors["assistant_border"]}; }}',
            f'.system-msg {{ background: {colors["system_bg"]}; border-left: 3px solid {colors["system_border"]}; }}',
            f'.role-label {{ font-weight: bold; margin-bottom: 4px; }}',
            f'.timestamp {{ color: {colors["timestamp_color"]}; font-size: 10px; float: right; }}',
            f'.content {{ clear: both; color: {colors["text_color"]}; }}',
            f'code {{ background: {colors["code_bg"]}; color: {colors["code_color"]}; padding: 2px 4px; border-radius: 3px; font-family: "Consolas", monospace; }}',
            f'pre {{ background: {colors["pre_bg"]}; color: {colors["pre_color"]}; padding: 8px; border-radius: 4px; overflow-x: auto; font-family: "Consolas", monospace; margin: 8px 0; }}',
            '</style>',
            '</head><body>'
        ]
        
        # Add messages
        for msg in self._messages:
            html_parts.append(self._build_message_html(msg, colors))
        
        html_parts.extend(['</body></html>'])
        
        return '\n'.join(html_parts)
    
    def _build_message_html(self, msg: ChatMessage, colors: dict) -> str:
        """Build HTML for a single message"""
        # Role styling
        role_info = {
            'user': ('👤 User', colors['user_color'], 'user-msg'),
            'assistant': ('🤖 Assistant', colors['assistant_color'], 'assistant-msg'),
            'system': ('⚙️ System', colors['system_color'], 'system-msg')
        }
        
        role_text, role_color, css_class = role_info.get(msg.role, role_info['assistant'])
        
        # Process content
        if msg.rich:
            safe_content = msg.content  # already HTML
        else:
            safe_content = self._process_markdown(msg.content, colors)
        
        # Create message HTML
        timestamp_html = f"<span class='timestamp'>{msg.timestamp}</span>" if msg.timestamp else ""
        
        message_html = (
            f"<div class='chat-msg {css_class}'>"
            f"<div class='role-label'>"
            f"<span style='color: {role_color};'>{role_text}</span>"
            f"{timestamp_html}"
            f"</div>"
            f"<div class='content'>{safe_content}</div>"
            f"</div>"
        )
        
        return message_html
            
    def _process_markdown(self, content: str, colors: dict) -> str:
        """Process basic markdown in content with theme-aware colors"""
        # Escape HTML
        safe = (content
                .replace('&','&amp;')
                .replace('<','&lt;')
                .replace('>','&gt;'))
        
        # Code blocks
        if '```' in safe:
            parts = safe.split('```')
            rebuilt = []
            for i, p in enumerate(parts):
                if i % 2 == 1:
                    rebuilt.append(f"<pre>{p}</pre>")
                else:
                    rebuilt.append(p)
            safe = ''.join(rebuilt)
        
        # Inline code - use theme colors from CSS
        import re
        safe = re.sub(r'`([^`]+)`', r"<code>\1</code>", safe)
        
        # Bold text
        safe = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', safe)
        
        # Italic text
        safe = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', safe)
        
        # Line breaks
        safe = safe.replace('\n', '<br>')
        
        return safe

    def refresh_theme(self):
        """Refresh the chat display to match current theme"""
        try:
            if self._messages:
                # Rebuild all messages with new theme
                all_html = self._build_all_messages_html()
                self._browser.setHtml(all_html)
                
                # Auto-scroll to bottom
                scrollbar = self._browser.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            main_logger.error(f"Failed to refresh theme: {e}")
        
    def _get_theme_colors(self) -> dict:
        """Get theme-appropriate colors for chat messages"""
        current_theme = get_current_theme()
        
        if current_theme == "light":
            return {
                'user_bg': '#e3f2fd',
                'user_border': '#2196f3', 
                'user_color': '#1976d2',
                'assistant_bg': '#f1f8e9',
                'assistant_border': '#4caf50',
                'assistant_color': '#388e3c',
                'system_bg': '#fff3e0',
                'system_border': '#ff9800',
                'system_color': '#f57c00',
                'text_color': '#212121',
                'timestamp_color': '#757575',
                'code_bg': '#f5f5f5',
                'code_color': '#d32f2f',
                'pre_bg': '#fafafa',
                'pre_color': '#424242'
            }
        else:  # dark theme
            return {
                'user_bg': '#1a237e',
                'user_border': '#3f51b5',
                'user_color': '#7986cb',
                'assistant_bg': '#1b5e20',
                'assistant_border': '#4caf50',
                'assistant_color': '#81c784',
                'system_bg': '#e65100',
                'system_border': '#ff9800',
                'system_color': '#ffb74d',
                'text_color': '#e0e0e0',
                'timestamp_color': '#9e9e9e',
                'code_bg': '#2d2d2d',
                'code_color': '#f8f8f2',
                'pre_bg': '#1e1e1e',
                'pre_color': '#d4d4d4'
            }

    def clear_chat(self):
        """Clear all messages from the chat"""
        try:
            self._messages.clear()
            self._browser.clear()
            self._update_count()
            main_logger.info("Chat cleared")
        except Exception as e:
            main_logger.error(f"Failed to clear chat: {e}")

    def _export_chat(self):
        """Export chat to clipboard"""
        try:
            chat_text = []
            for msg in self._messages:
                timestamp = f"[{msg.timestamp}] " if msg.timestamp else ""
                role = msg.role.title()
                chat_text.append(f"{timestamp}{role}: {msg.content}")
            
            full_text = "\n\n".join(chat_text)
            clipboard = QApplication.clipboard()
            clipboard.setText(full_text)
            
            # Show temporary status
            old_text = self.export_button.text()
            self.export_button.setText("Exported!")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.export_button.setText(old_text))
            
        except Exception as e:
            main_logger.error(f"Failed to export chat: {e}")
            
    def _update_count(self):
        """Update the message count display"""
        count = len(self._messages)
        self.count_label.setText(f"{count} message{'s' if count != 1 else ''}")
        
    def get_message_count(self) -> int:
        """Get the number of messages in the chat"""
        return len(self._messages)
        
    def get_messages(self) -> List[ChatMessage]:
        """Get all messages"""
        return self._messages.copy()

    def set_messages(self, messages: List[ChatMessage]):
        """Replace all messages (hydration)."""
        self._messages = messages
        self._rebuild_all()
        self._update_count()

    def _apply_filters(self):
        roles = set()
        if self._user_filter.isChecked():
            roles.add('user')
        if self._assistant_filter.isChecked():
            roles.add('assistant')
        if self._system_filter.isChecked():
            roles.add('system')
        self._rebuild_all(roles)

    def _rebuild_all(self, allowed_roles: Optional[set] = None):
        try:
            colors = self._get_theme_colors()
            html_parts = ['<!DOCTYPE html>','<html><head><meta charset="utf-8">','<style>',
                          'body { margin:0; padding:8px; font-family: "Segoe UI", Arial, sans-serif; }',
                          f'.chat-msg {{ margin:8px 6px 12px 6px; padding:8px; border-radius:6px; font-size:12px; line-height:1.4; }}',
                          f'.user-msg {{ background:{colors["user_bg"]}; border-left:3px solid {colors["user_border"]}; }}',
                          f'.assistant-msg {{ background:{colors["assistant_bg"]}; border-left:3px solid {colors["assistant_border"]}; }}',
                          f'.system-msg {{ background:{colors["system_bg"]}; border-left:3px solid {colors["system_border"]}; }}',
                          f'.role-label {{ font-weight:bold; margin-bottom:4px; }}',
                          f'.timestamp {{ color:{colors["timestamp_color"]}; font-size:10px; float:right; }}',
                          f'.content {{ clear:both; color:{colors["text_color"]}; }}',
                          f'code {{ background:{colors["code_bg"]}; color:{colors["code_color"]}; padding:2px 4px; border-radius:3px; font-family:"Consolas", monospace; }}',
                          f'pre {{ background:{colors["pre_bg"]}; color:{colors["pre_color"]}; padding:8px; border-radius:4px; overflow-x:auto; font-family:"Consolas", monospace; margin:8px 0; }}',
                          '</style></head><body>']
            count_added = 0
            for msg in self._messages:
                if allowed_roles and msg.role not in allowed_roles:
                    continue
                html_parts.append(self._build_message_html(msg, colors))
                count_added += 1
            if count_added == 0:
                html_parts.append('<div style="color:#777; font-size:12px;">(No messages with current filter)</div>')
            html_parts.append('</body></html>')
            self._browser.setHtml('\n'.join(html_parts))
            sb = self._browser.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            main_logger.error(f"Failed to rebuild chat: {e}")

    def append_assistant_delta(self, delta: str):
        """Append streaming delta to the last assistant message, creating one if absent."""
        if not delta:
            return
        # Find last assistant message
        for msg in reversed(self._messages):
            if msg.role == 'assistant':
                msg.content += delta
                self._rebuild_all()  # re-render with updated content
                return
        # No assistant message yet, start a new one
        self.add_ai_message(delta)

__all__ = ["ChatView", "ChatMessage"]
