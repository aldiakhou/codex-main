from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class ThemeTokens:
    # Core Colors
    bg: str              # Main background
    bg_offset: str       # Slightly offset background (toolbars, etc.)
    fg: str              # Primary foreground (main text)
    fg_muted: str        # Muted foreground (secondary text, icons)
    border: str          # Borders for elements
    border_subtle: str   # Softer borders, dividers
    
    # Interactive Elements
    accent: str          # Primary accent color (buttons, selections)
    accent_fg: str       # Foreground color for on top of accent
    accent_hover: str    # Accent color for hover states
    
    # Special UI Elements
    selection_bg: str    # Background for selected text or items
    danger: str          # Color for destructive actions or errors
    
    # Message Bubbles
    bubble_user_bg: str
    bubble_user_fg: str
    bubble_ai_bg: str
    bubble_ai_fg: str
    bubble_sys_bg: str
    bubble_sys_fg: str

# Inspired by modern editor themes like VS Code's default dark theme
THEMES: Dict[str, ThemeTokens] = {
    "dark": ThemeTokens(
        bg="#1e1e1e",
        bg_offset="#252526",
        fg="#d4d4d4",
        fg_muted="#8c8c8c",
        border="#3c3c3c",
        border_subtle="#2a2a2a",
        accent="#007acc",
        accent_fg="#ffffff",
        accent_hover="#009aff",
        selection_bg="#264f78",
        danger="#f44747",
        bubble_user_bg="#264f78",
        bubble_user_fg="#d4d4d4",
        bubble_ai_bg="#252526",
        bubble_ai_fg="#d4d4d4",
        bubble_sys_bg="#3c3c3c",
        bubble_sys_fg="#a0a0a0",
    ),
    "light": ThemeTokens(
        bg="#ffffff",
        bg_offset="#f3f3f3",
        fg="#333333",
        fg_muted="#6e6e6e",
        border="#e0e0e0",
        border_subtle="#f0f0f0",
        accent="#007acc",
        accent_fg="#ffffff",
        accent_hover="#0062a3",
        selection_bg="#add6ff",
        danger="#d1242f",
        bubble_user_bg="#e7f3ff",
        bubble_user_fg="#333333",
        bubble_ai_bg="#f3f3f3",
        bubble_ai_fg="#333333",
        bubble_sys_bg="#e0e0e0",
        bubble_sys_fg="#555555",
    ),
}

def generate_qss(theme: str = "dark", base_font_pt: float = 10.5) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    code_pt = max(9.0, base_font_pt - 1.0)
    
    return f"""
/* AI Workbench - Generated Theme: {theme} */

/* --- Global --- */
QWidget {{
  background-color: {t.bg};
  color: {t.fg};
  font-family: "Segoe UI", "Inter", system-ui, -apple-system, sans-serif;
  font-size: {base_font_pt}pt;
  border: none;
}}

/* --- Main Window & Docks --- */
QMainWindow::separator {{
  background-color: {t.bg_offset};
  width: 6px; /* vertical */
  height: 6px; /* horizontal */
}}
QDockWidget {{
  titlebar-close-icon: url(none);
  titlebar-normal-icon: url(none);
}}
QDockWidget::title {{
  background: {t.bg_offset};
  color: {t.fg_muted};
  padding: 8px 12px;
  font-weight: 600;
  border-bottom: 1px solid {t.border};
}}

/* --- Text & Input --- */
QTextEdit, QLineEdit, QTextBrowser {{
  background-color: {t.bg_offset};
  color: {t.fg};
  border: 1px solid {t.border};
  border-radius: 6px;
  padding: 8px;
  selection-background-color: {t.selection_bg};
}}
QTextEdit:focus, QLineEdit:focus {{
  border: 1px solid {t.accent};
}}
QTextBrowser {{
  font-size: {code_pt}pt;
  font-family: "Consolas", "Fira Code", "Courier New", monospace;
}}

/* --- Buttons --- */
QPushButton {{
  background-color: {t.accent};
  color: {t.accent_fg};
  border: 1px solid {t.accent};
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
}}
QPushButton:hover {{
  background-color: {t.accent_hover};
  border-color: {t.accent_hover};
}}
QPushButton:pressed {{
  background-color: {t.accent};
}}
QToolButton {{
  background-color: {t.bg_offset};
  color: {t.fg_muted};
  border: 1px solid {t.border};
  padding: 6px;
  border-radius: 6px;
}}
QToolButton:hover {{
  background-color: {t.bg};
  border-color: {t.border};
  color: {t.fg};
}}
QToolButton#BubbleAction {{
  background: transparent;
  border: 1px solid transparent;
  color: {t.fg_muted};
  padding: 2px;
}}
QToolButton#BubbleAction:hover {{
  background: {t.bg_offset};
  border: 1px solid {t.border};
  color: {t.fg};
}}

/* --- Tree View (Repo Explorer) --- */
QTreeView, QTreeWidget {{
  background-color: {t.bg};
  border: 1px solid {t.border};
  padding: 4px;
}}
QTreeView::item, QTreeWidget::item {{
  padding: 6px;
  border-radius: 4px;
}}
QTreeView::item:hover, QTreeWidget::item:hover {{
  background-color: {t.bg_offset};
}}
QTreeView::item:selected, QTreeWidget::item:selected {{
  background-color: {t.selection_bg};
  color: {t.fg};
}}

/* --- Tabs --- */
QTabWidget::pane {{
  border-top: 1px solid {t.border};
}}
QTabBar::tab {{
  background: {t.bg};
  color: {t.fg_muted};
  padding: 8px 16px;
  border: 1px solid transparent;
  border-bottom: none;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}}
QTabBar::tab:hover {{
  color: {t.fg};
}}
QTabBar::tab:selected {{
  background: {t.bg_offset};
  color: {t.fg};
  border: 1px solid {t.border};
  border-bottom: 1px solid {t.bg_offset};
}}

/* --- Status & Tool Bars --- */
QStatusBar {{
  background: {t.bg_offset};
  border-top: 1px solid {t.border};
}}
QStatusBar::item {{
  border: none;
  padding: 0 8px;
}}
QToolBar {{
  background: {t.bg};
  border-bottom: 1px solid {t.border};
  spacing: 8px;
  padding: 8px;
}}

/* --- Scroll & Splitter --- */
QSplitter::handle {{
  background: {t.bg_offset};
}}
QSplitter::handle:horizontal {{ width: 4px; }}
QSplitter::handle:vertical {{ height: 4px; }}

QScrollBar:vertical {{
  background: {t.bg};
  width: 10px;
  margin: 0;
}}
QScrollBar::handle:vertical {{
  background: {t.bg_offset};
  min-height: 20px;
  border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0px;
}}
QScrollBar:horizontal {{
  background: {t.bg};
  height: 10px;
  margin: 0;
}}
QScrollBar::handle:horizontal {{
  background: {t.bg_offset};
  min-width: 20px;
  border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
  width: 0px;
}}

/* --- Chat Console --- */
QScrollArea#ChatScroll {
  border: none;
}
QFrame#BubbleContainer {
  border-radius: 12px;
}
QFrame#BubbleContainer[msgRole="user"] {
  background: {t.bubble_user_bg};
}
QFrame#BubbleContainer[msgRole="assistant"] {
  background: {t.bubble_ai_bg};
  border: 1px solid {t.border};
}
QFrame#BubbleContainer[msgRole="system"] {
  background: {t.bubble_sys_bg};
}
QTextBrowser#BubbleBody {
  background: transparent;
  border: none;
  color: {t.fg};
}
"""

def apply_theme(widget, theme: str = "dark", base_font_pt: float = 10.5):
    qss = generate_qss(theme, base_font_pt)
    widget.setStyleSheet(qss)