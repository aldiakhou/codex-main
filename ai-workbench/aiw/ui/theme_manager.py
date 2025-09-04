"""Theme Manager: applies generated QSS built from design tokens.
Phase 1 deliverable.
"""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QApplication
from .design_tokens import generate_qss
from pathlib import Path
import logging

_current_theme: str = "dark"


def apply_theme(theme: str = "dark"):
    global _current_theme
    _current_theme = theme
    qss = generate_qss(theme)

    # Optional: append repository QSS override if present
    try:
        base_dir = Path(__file__).parent
        override = base_dir / ("styles_light.qss" if theme == "light" else "styles.qss")
        if override.exists():
            extra = override.read_text(encoding="utf-8")
            if extra.strip():
                qss = qss + "\n\n/* --- Repo override appended --- */\n" + extra
                logging.getLogger('ThemeManager').info("Appended repo override QSS: %s (%d bytes)", override.name, len(extra))
    except Exception as e:
        logging.getLogger('ThemeManager').warning("Failed to append repo override QSS: %s", e)

    # Optional: append external developer override from config
    try:
        from ..core.config import get_config_manager
        cfg = get_config_manager().config
        custom_path = getattr(cfg.ui, 'custom_qss_path', None)
        if custom_path:
            p = Path(custom_path).expanduser()
            if p.exists():
                extra = p.read_text(encoding='utf-8')
                if extra.strip():
                    qss = qss + f"\n\n/* --- External override appended ({p}) --- */\n" + extra
                    logging.getLogger('ThemeManager').info("Appended external override QSS: %s (%d bytes)", str(p), len(extra))
    except Exception as e:
        logging.getLogger('ThemeManager').warning("Failed to append external override QSS: %s", e)
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)


def get_current_theme() -> str:
    return _current_theme

__all__ = ["apply_theme", "get_current_theme"]
