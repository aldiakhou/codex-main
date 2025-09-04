"""AnimatedContainer: lightweight wrapper to animate show/hide of content.

Provides smooth expand/collapse via maximumHeight and optional fade.
Respects reduced-motion preference via animator.motion_enabled().
"""
from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QEasingCurve

from .animator import motion_enabled, fade_in, fade_out


class AnimatedContainer(QWidget):
    def __init__(self, parent=None, fade_on_show: bool = True):
        super().__init__(parent)
        self._content: Optional[QWidget] = None
        self._fade_on_show = fade_on_show
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def set_content(self, w: QWidget):
        if self._content is not None:
            try:
                self._layout.removeWidget(self._content)
            except Exception:
                pass
            self._content.setParent(None)
        self._content = w
        self._layout.addWidget(w)

    def content(self) -> Optional[QWidget]:
        return self._content

    # --- Expand/Collapse -------------------------------------------------
    def expand(self, duration_ms: int = 200):
        if not self._content:
            return
        if not motion_enabled():
            self._content.setVisible(True)
            self.setMaximumHeight(16777215)
            return
        # Height animation via maximumHeight
        target_h = max(1, self._content.sizeHint().height() or self._content.height() or 120)
        self.setMaximumHeight(0)
        self._content.setVisible(True)
        from PySide6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(self, b"maximumHeight", self)
        anim.setDuration(min(duration_ms, 300))
        anim.setStartValue(0)
        anim.setEndValue(target_h)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        try:
            from .animator import _attach_anim  # type: ignore
            _attach_anim(self, anim)
        except Exception:
            pass
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        if self._fade_on_show:
            fade_in(self._content, duration_ms=min(duration_ms, 300))

    def collapse(self, duration_ms: int = 200):
        if not self._content:
            return
        if not motion_enabled():
            self._content.setVisible(False)
            return
        from PySide6.QtCore import QPropertyAnimation
        start_h = self.height() or self.maximumHeight() or self.sizeHint().height() or 120
        anim = QPropertyAnimation(self, b"maximumHeight", self)
        anim.setDuration(min(duration_ms, 300))
        anim.setStartValue(start_h)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        def _after():
            try:
                self._content.setVisible(False)
                self.setMaximumHeight(16777215)
            except Exception:
                pass
        try:
            anim.finished.connect(_after)
        except Exception:
            _after()
        try:
            from .animator import _attach_anim  # type: ignore
            _attach_anim(self, anim)
        except Exception:
            pass
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        if self._fade_on_show:
            fade_out(self._content, duration_ms=min(duration_ms, 300))


__all__ = ["AnimatedContainer"]

