"""Animator helpers for concise, consistent micro-interactions.

Goals:
- Centralize motion enable/disable via UI config (prefers reduced motion)
- Provide small wrappers around QPropertyAnimation and animation groups
- Offer convenience functions used across the UI (fade, slide+fade, splitter)
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QTimer,
    QVariantAnimation,
    QAbstractAnimation,
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QSplitter


def _get_cfg_ui():
    """Internal: get the UI config safely without creating hard imports."""
    try:
        from ...core.config import get_config_manager  # lazy import to avoid cycles
        return get_config_manager().config.ui
    except Exception:
        class _D:  # fallback defaults
            animations_enabled = True
            prefers_reduced_motion = False
        return _D()


def motion_enabled() -> bool:
    """Return True if animations are allowed given the current settings."""
    ui = _get_cfg_ui()
    # Support both legacy flag and explicit reduced-motion preference
    enabled = getattr(ui, "animations_enabled", True)
    reduced = getattr(ui, "prefers_reduced_motion", False)
    return bool(enabled and not reduced)


def _ensure_opacity_effect(w: QWidget) -> QGraphicsOpacityEffect:
    eff = getattr(w, "_aiw_opacity_effect", None)
    if eff is None:
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        setattr(w, "_aiw_opacity_effect", eff)
    return eff


def fade_in(widget: QWidget, duration_ms: int = 180, start: float = 0.0, end: float = 1.0):
    """Fade widget from `start` to `end` opacity.

    Uses InOutCubic and auto no-ops in reduced-motion mode.
    """
    try:
        if not motion_enabled():
            widget.setVisible(True)
            return
        widget.show()
        eff = _ensure_opacity_effect(widget)
        eff.setOpacity(start)
        from PySide6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(eff, b"opacity", widget)
        anim.setDuration(min(duration_ms, 300))
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        # Keep anim alive on the widget
        _attach_anim(widget, anim)
        anim.start(anim.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        try:
            widget.show()
        except Exception:
            pass


def fade_out(widget: QWidget, duration_ms: int = 180, start: float = 1.0, end: float = 0.0, on_finished: Optional[Callable[[], None]] = None):
    """Fade widget out; optionally call `on_finished` after.

    If reduced motion, instantly calls on_finished.
    """
    try:
        if not motion_enabled():
            if on_finished:
                on_finished()
            return
        eff = _ensure_opacity_effect(widget)
        from PySide6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(eff, b"opacity", widget)
        anim.setDuration(min(duration_ms, 300))
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        if on_finished:
            try:
                anim.finished.connect(on_finished)  # type: ignore[attr-defined]
            except Exception:
                pass
        _attach_anim(widget, anim)
        anim.start(anim.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        if on_finished:
            try:
                on_finished()
            except Exception:
                pass


def pulse_opacity(widget: QWidget, from_opacity: float = 0.6, to_opacity: float = 1.0, duration_ms: int = 200):
    """Subtle one-shot opacity pulse (useful to hint at new content)."""
    try:
        if not motion_enabled():
            return
        eff = _ensure_opacity_effect(widget)
        eff.setOpacity(from_opacity)
        from PySide6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(eff, b"opacity", widget)
        anim.setDuration(min(duration_ms, 300))
        anim.setStartValue(from_opacity)
        anim.setEndValue(to_opacity)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        _attach_anim(widget, anim)
        anim.start(anim.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        pass


def slide_and_fade_in(widget: QWidget, offset: QPoint = QPoint(0, 8), duration_ms: int = 200):
    """Attempt a tiny slide upward and fade in in parallel.

    Note: Layouts manage geometry; this is best-effort and small offset
    (~8px) to avoid fighting layouts.
    """
    try:
        if not motion_enabled():
            widget.show()
            return
        widget.show()
        start_pos = widget.pos() + offset
        end_pos = widget.pos()
        # Position animation
        from PySide6.QtCore import QPropertyAnimation, QParallelAnimationGroup
        pos_anim = QPropertyAnimation(widget, b"pos", widget)
        pos_anim.setDuration(min(duration_ms, 300))
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(end_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        # Opacity animation
        eff = _ensure_opacity_effect(widget)
        eff.setOpacity(0.0)
        op_anim = QPropertyAnimation(eff, b"opacity", widget)
        op_anim.setDuration(min(duration_ms, 300))
        op_anim.setStartValue(0.0)
        op_anim.setEndValue(1.0)
        op_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        group = QParallelAnimationGroup(widget)
        group.addAnimation(pos_anim)
        group.addAnimation(op_anim)
        _attach_anim(widget, group)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        try:
            widget.show()
        except Exception:
            pass


def animate_splitter_open(splitter: QSplitter, duration_ms: int = 220):
    """Animate a newly created two-widget splitter from [total-1, 1] to half/half.

    Call after both children are added. Uses InOutCubic. No-ops if disabled.
    """
    try:
        if not motion_enabled():
            return

        def _do_anim():
            try:
                is_vertical = splitter.orientation() == splitter.Orientation.Vertical
                total = splitter.height() if is_vertical else splitter.width()
                total = max(total, 2)
                start = [total - 1, 1]
                end = [total // 2, total - (total // 2)]
                splitter.setSizes(start)

                anim = QVariantAnimation(splitter)
                anim.setDuration(min(duration_ms, 300))
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

                def _step(v: float):
                    a = int(start[0] + (end[0] - start[0]) * v)
                    b = max(total - a, 1)
                    splitter.setSizes([a, b])

                anim.valueChanged.connect(lambda v: _step(float(v)))  # type: ignore[arg-type]
                _attach_anim(splitter, anim)
                anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            except Exception:
                pass

        # Wait a tick so splitter has geometry
        QTimer.singleShot(0, _do_anim)
    except Exception:
        pass


def pulse_item_background(item_like, set_color: Callable, duration_ms: int = 3000):
    """Animate a background color alpha from 1 -> 0 to create a pulse fade.

    - `item_like` is any object used as animation parent to keep GC away.
    - `set_color(alpha: float)` is called with alpha in [0..1].
    """
    try:
        if not motion_enabled():
            set_color(0.0)
            return
        anim = QVariantAnimation()
        anim.setDuration(min(duration_ms, 3000))
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.valueChanged.connect(lambda v: set_color(float(v)))  # type: ignore[arg-type]
        _attach_anim(item_like, anim)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    except Exception:
        pass


# --- Minimal attach bucket to avoid premature GC ---------------------------
def _attach_anim(host: QWidget, anim_obj):
    try:
        bucket = getattr(host, "_aiw_anim", None)
        if bucket is None:
            setattr(host, "_aiw_anim", [])
            bucket = getattr(host, "_aiw_anim")
        bucket.append(anim_obj)
        try:
            anim_obj.finished.connect(lambda: bucket.remove(anim_obj) if anim_obj in bucket else None)
        except Exception:
            pass
    except Exception:
        pass


__all__ = [
    "motion_enabled",
    "fade_in",
    "fade_out",
    "pulse_opacity",
    "slide_and_fade_in",
    "animate_splitter_open",
    "pulse_item_background",
]

