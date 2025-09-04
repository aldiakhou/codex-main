"""Advanced Chat View with avatars, markdown rendering and inline actions.

Implements:
- Avatars for user/assistant/system
- Markdown rendering (code fences, diffs, tables) via MessageRenderer
- Copy button for code blocks
- Collapsible long outputs and expandable diffs
- Streaming typing indicator + token pace label
- Toolbar with model selector placeholder, temperature slider, reasoning toggle, clear
- Message hydration API compatible with MainWindow expectations
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional, Dict
from datetime import datetime
import hashlib
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QLabel,
    QApplication, QCheckBox, QSlider, QComboBox
)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont

from ...theme_manager import get_current_theme
from .message_renderer import MessageRenderer, RenderResult


main_logger = logging.getLogger('MainWindow.ChatView')


@dataclass
class ChatMessage:
    role: Literal['user', 'assistant', 'system']
    content: str
    timestamp: Optional[str] = None
    rich: bool = False


class ChatView(QWidget):
    # Signals
    message_sent = Signal(str)
    copy_requested = Signal(str)
    temperature_changed = Signal(float)
    reasoning_toggle = Signal(bool)
    apply_patch_requested = Signal(str)  # Raw patch/diff content
    explain_requested = Signal(str)
    refine_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: List[ChatMessage] = []
        self._renderer = MessageRenderer(theme=get_current_theme() or 'dark')
        self._last_render_blocks: Dict[str, str] = {}
        self._collapsed_by_hash: Dict[str, bool] = {}
        self._streaming = False
        self._typing_timer: Optional[QTimer] = None
        self._typing_phase = 0
        self._setup_ui()

    # --- UI ---------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar: model (placeholder), temp slider, reasoning pill, clear
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 6, 6, 2)
        self.model_combo = QComboBox(); self.model_combo.addItems(["<default>"]); self.model_combo.setEnabled(False)
        toolbar.addWidget(QLabel("Model:")); toolbar.addWidget(self.model_combo)
        toolbar.addSpacing(8)
        toolbar.addWidget(QLabel("Temp:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0); self.temp_slider.setMaximum(100); self.temp_slider.setValue(30); self.temp_slider.setFixedWidth(120)
        self.temp_slider.valueChanged.connect(lambda v: self.temperature_changed.emit(v/100.0))
        toolbar.addWidget(self.temp_slider)
        toolbar.addStretch(1)
        self.reasoning_cb = QCheckBox("Thinking"); self.reasoning_cb.setChecked(True)
        self.reasoning_cb.toggled.connect(lambda b: self.reasoning_toggle.emit(b))
        toolbar.addWidget(self.reasoning_cb)
        layout.addLayout(toolbar)

        # Chat browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setObjectName("ChatBrowser")
        # Use Cascadia everywhere for a cohesive, editor-like feel
        self._browser.setFont(QFont("Cascadia Code", 11))
        self._browser.setAcceptRichText(True)
        self._browser.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._browser.anchorClicked.connect(self._on_anchor_clicked)
        layout.addWidget(self._browser)

        # Streaming indicator + token label
        pace_bar = QHBoxLayout(); pace_bar.setContentsMargins(6, 2, 6, 4)
        # Slightly brighter labels for better readability in dark mode
        self.typing_label = QLabel(""); self.typing_label.setStyleSheet("color:#a1a1aa;font-size:11px;")
        self.token_label = QLabel(""); self.token_label.setStyleSheet("color:#a1a1aa;font-size:11px;")
        pace_bar.addWidget(self.typing_label); pace_bar.addStretch(1); pace_bar.addWidget(self.token_label)
        layout.addLayout(pace_bar)

        # Role filters and actions
        ctrl = QHBoxLayout(); ctrl.setContentsMargins(5, 5, 5, 5)
        self._user_filter = QCheckBox("User"); self._assistant_filter = QCheckBox("Assistant"); self._system_filter = QCheckBox("System")
        for cb in (self._user_filter, self._assistant_filter, self._system_filter):
            cb.setChecked(True)
        self._user_filter.setChecked(True); self._assistant_filter.setChecked(True); self._system_filter.setChecked(True)
        self._user_filter.stateChanged.connect(self._apply_filters)
        self._assistant_filter.stateChanged.connect(self._apply_filters)
        self._system_filter.stateChanged.connect(self._apply_filters)
        ctrl.addWidget(self._user_filter); ctrl.addWidget(self._assistant_filter); ctrl.addWidget(self._system_filter)
        self.clear_button = QPushButton("Clear Chat"); self.clear_button.clicked.connect(self.clear_chat); ctrl.addWidget(self.clear_button)
        self.export_button = QPushButton("Export"); self.export_button.clicked.connect(self._export_chat); ctrl.addWidget(self.export_button)
        ctrl.addStretch(1)
        self.count_label = QLabel("0 messages"); self.count_label.setStyleSheet("color:#666;font-size:10px;"); ctrl.addWidget(self.count_label)
        layout.addLayout(ctrl)

    # --- API used by MainWindow -------------------------------------------
    def add_message(self, role: str, content: str, rich: bool = False, timestamp: Optional[str] = None):
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        cm = ChatMessage(role=role if role in ('user','assistant','system') else 'assistant', content=content, timestamp=timestamp, rich=rich)
        self._messages.append(cm)
        self._render_all()
        self._update_count()

    def add_user_message(self, content: str, timestamp: Optional[str] = None):
        self.add_message('user', content, timestamp=timestamp)

    def add_ai_message(self, content: str, rich: bool = False, timestamp: Optional[str] = None):
        self.add_message('assistant', content, rich=rich, timestamp=timestamp)

    def add_system_message(self, content: str, timestamp: Optional[str] = None):
        self.add_message('system', content, timestamp=timestamp)

    def append_assistant_delta(self, delta: str):
        if not delta:
            return
        for msg in reversed(self._messages):
            if msg.role == 'assistant':
                msg.content += delta
                self._render_all()
                return
        self.add_ai_message(delta)

    def set_messages(self, messages: List[ChatMessage]):
        self._messages = messages
        self._render_all()
        self._update_count()

    def get_messages(self) -> List[ChatMessage]:
        return list(self._messages)

    def get_message_count(self) -> int:
        return len(self._messages)

    def refresh_theme(self):
        try:
            self._renderer.set_theme(get_current_theme() or 'dark')
            self._render_all()
        except Exception as e:
            main_logger.error(f"Failed to refresh chat theme: {e}")

    # Streaming pacing
    def set_streaming(self, streaming: bool):
        self._streaming = streaming
        if streaming:
            self._start_typing_indicator()
        else:
            self._stop_typing_indicator()

    def set_token_counts(self, input_tokens: int, output_tokens: int, total_tokens: int):
        self.token_label.setText(f"Tokens: {total_tokens} (In: {input_tokens}, Out: {output_tokens})")

    # --- Internal rendering ------------------------------------------------
    def _render_all(self, allowed_roles: Optional[set] = None):
        try:
            parts = ['<!DOCTYPE html>','<html><head><meta charset="utf-8">','<style>', self._renderer.base_css(), '</style></head><body>']
            self._last_render_blocks.clear()
            added = 0
            for msg in self._messages:
                if allowed_roles and msg.role not in allowed_roles:
                    continue
                wrapped = self._build_message_html(msg)
                parts.append(wrapped)
                added += 1
            if added == 0:
                parts.append('<div style="color:#777; font-size:12px;">(No messages with current filter)</div>')
            parts.append('</body></html>')
            self._browser.setHtml('\n'.join(parts))
            sb = self._browser.verticalScrollBar(); sb.setValue(sb.maximum())
        except Exception as e:
            main_logger.error(f"Failed to render chat: {e}")

    def _build_message_html(self, msg: ChatMessage) -> str:
        if msg.rich:
            content_html = msg.content
        else:
            res: RenderResult = self._renderer.md_to_html(msg.content, collapsed_blocks=self._collapsed_by_hash)
            content_html = res.html
            self._last_render_blocks.update(res.blocks)
        return self._renderer.wrap_message(role=msg.role, content_html=content_html, timestamp=msg.timestamp)

    def _apply_filters(self):
        roles: set[str] = set()
        if self._user_filter.isChecked(): roles.add('user')
        if self._assistant_filter.isChecked(): roles.add('assistant')
        if self._system_filter.isChecked(): roles.add('system')
        self._render_all(roles)

    def _update_count(self):
        n = len(self._messages)
        self.count_label.setText(f"{n} message{'s' if n != 1 else ''}")

    def clear_chat(self):
        try:
            self._messages.clear()
            self._browser.clear()
            self._update_count()
        except Exception as e:
            main_logger.error(f"Failed to clear chat: {e}")

    def _export_chat(self):
        try:
            lines = []
            for m in self._messages:
                ts = f"[{m.timestamp}] " if m.timestamp else ""
                lines.append(f"{ts}{m.role.title()}: {m.content}")
            QApplication.clipboard().setText("\n\n".join(lines))
            old = self.export_button.text(); self.export_button.setText("Exported!")
            QTimer.singleShot(1500, lambda: self.export_button.setText(old))
        except Exception as e:
            main_logger.error(f"Failed to export chat: {e}")

    # --- Typing indicator --------------------------------------------------
    def _start_typing_indicator(self):
        if self._typing_timer is None:
            self._typing_timer = QTimer(self)
            self._typing_timer.timeout.connect(self._tick_typing)
        self._typing_phase = 0
        self._typing_timer.start(450)

    def _stop_typing_indicator(self):
        if self._typing_timer:
            self._typing_timer.stop()
        self.typing_label.setText("")

    def _tick_typing(self):
        dots = "." * ((self._typing_phase % 3) + 1)
        self.typing_label.setText(f"Assistant is typing{dots}")
        self._typing_phase += 1

    # --- Anchor actions ----------------------------------------------------
    def _on_anchor_clicked(self, url: QUrl):
        try:
            scheme = url.scheme()
            full = url.toString()
            if scheme in ("http", "https"):
                self._browser.setSource(url)
                return
            if scheme in ("copy", "toggle", "action"):
                path = full.split("://", 1)[1]
                if scheme == "copy":
                    raw = self._last_render_blocks.get(path)
                    if raw is not None:
                        QApplication.clipboard().setText(raw)
                        self.copy_requested.emit(raw)
                elif scheme == "toggle":
                    raw = self._last_render_blocks.get(path)
                    if raw is not None:
                        h = hashlib.sha1(raw.encode('utf-8')).hexdigest()
                        self._collapsed_by_hash[h] = not self._collapsed_by_hash.get(h, True)
                        self._render_all()
                elif scheme == "action":
                    parts = path.split("/", 1)
                    if len(parts) == 2:
                        verb, block_id = parts
                        raw = self._last_render_blocks.get(block_id)
                        if raw is None:
                            return
                        if verb == 'apply_patch':
                            self.apply_patch_requested.emit(raw)
                        elif verb == 'explain':
                            self.explain_requested.emit(raw)
                        elif verb == 'refine':
                            self.refine_requested.emit(raw)
                return
        except Exception as e:
            main_logger.error(f"Anchor click error: {e}")


__all__ = ["ChatView", "ChatMessage"]
