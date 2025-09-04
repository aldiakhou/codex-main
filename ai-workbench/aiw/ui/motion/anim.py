"""Small animation helpers for UI motion layer.

Guarded by a UI config flag `animations_enabled` (checked by callers).
These helpers are lightweight and safe to no-op on errors.
"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import QObject, QEasingCurve, QPropertyAnimation, QVariantAnimation
from PySide6.QtWidgets import QWidget, QDockWidget, QGraphicsOpacityEffect


def _attach_anim(host: QWidget, anim: QObject, key: str = "_aiw_anim"):
    """Attach animation object to host to avoid GC during playback."""
    try:
        bucket = getattr(host, key, None)
        if bucket is None:
            setattr(host, key, [])
            bucket = getattr(host, key)
        bucket.append(anim)

        # Auto-clean after finished where possible
        if isinstance(anim, QPropertyAnimation):
            anim.finished.connect(lambda: bucket.remove(anim) if anim in bucket else None)
        elif isinstance(anim, QVariantAnimation):
            anim.finished.connect(lambda: bucket.remove(anim) if anim in bucket else None)
    except Exception:
        pass


def fade_in_widget(w: QWidget, duration_ms: int = 180, start: float = 0.0, end: float = 1.0):
    """Fade a widget in using a QGraphicsOpacityEffect.

    Works for both QWidget and QDockWidget instances.
    """
    try:
        # For QDockWidget, apply effect to its content widget, not the frame
        target: QWidget = w
        if isinstance(w, QDockWidget):
            try:
                cw = w.widget()
                if isinstance(cw, QWidget):
                    target = cw
            except Exception:
                target = w
        # Ensure visible before fading
        target.show()
        eff: Optional[QGraphicsOpacityEffect] = getattr(target, "_aiw_opacity_effect", None)
        if eff is None:
            eff = QGraphicsOpacityEffect(target)
            target.setGraphicsEffect(eff)
            setattr(target, "_aiw_opacity_effect", eff)
        eff.setOpacity(start)
        anim = QPropertyAnimation(eff, b"opacity", target)
        anim.setDuration(duration_ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        _attach_anim(target, anim)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        # Best-effort; fall back to instant show
        try:
            w.show()
        except Exception:
            pass


def animate_height_toggle(w: QWidget, make_visible: bool, duration_ms: int = 180):
    """Smoothly expand/collapse a widget's height.

    - When expanding: setVisible(True) then animate maximumHeight from 0 -> sizeHint().height()
    - When collapsing: animate from current height -> 0, then hide and clear max height limit
    """
    try:
        if make_visible:
            try:
                w.setVisible(True)
            except Exception:
                pass
            target_h = max(1, w.sizeHint().height() or w.height() or 120)
            w.setMaximumHeight(0)
            anim = QPropertyAnimation(w, b"maximumHeight", w)
            anim.setDuration(duration_ms)
            anim.setStartValue(0)
            anim.setEndValue(target_h)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            _attach_anim(w, anim)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        else:
            start_h = w.height() or w.maximumHeight() or w.sizeHint().height() or 120
            anim = QPropertyAnimation(w, b"maximumHeight", w)
            anim.setDuration(duration_ms)
            anim.setStartValue(start_h)
            anim.setEndValue(0)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            def _after():
                try:
                    w.setVisible(False)
                    w.setMaximumHeight(16777215)  # remove max cap
                except Exception:
                    pass
            try:
                anim.finished.connect(_after)
            except Exception:
                _after()
            _attach_anim(w, anim)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        # Fallback: immediate toggle
        try:
            w.setVisible(make_visible)
        except Exception:
            pass


__all__ = ["fade_in_widget", "animate_height_toggle"]
