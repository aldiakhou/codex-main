"""Theme Manager: applies generated QSS built from design tokens.
Phase 1 deliverable.
"""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QApplication
from .design_tokens import generate_qss

_current_theme: str = "dark"


def apply_theme(theme: str = "dark"):
    global _current_theme
    _current_theme = theme
    qss = generate_qss(theme)
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)


def get_current_theme() -> str:
    return _current_theme

__all__ = ["apply_theme", "get_current_theme"]
