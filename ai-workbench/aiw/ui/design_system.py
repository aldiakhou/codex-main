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
        bg="#1c1c1c",
        bg_offset="#2a2a2a",
        fg="#e0e0e0",
        fg_muted="#9a9a9a",
        border="#4a4a4a",
        border_subtle="#333333",
        accent="#0a84ff",
        accent_fg="#ffffff",
        accent_hover="#3b9dff",
        selection_bg="#2a5c8e",
        danger="#ff4d4d",
        bubble_user_bg="#2a5c8e",
        bubble_user_fg="#e0e0e0",
        bubble_ai_bg="#2a2a2a",
        bubble_ai_fg="#e0e0e0",
        bubble_sys_bg="#3c3c3c",
        bubble_sys_fg="#b0b0b0",
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
  """Generate a Qt Style Sheet string for the given theme.

  NOTE: Avoid f-string curly-brace escaping issues by building line-by-line.
  """
  t = THEMES.get(theme, THEMES["dark"])
  code_pt = max(9.0, base_font_pt - 1.0)

  lines: list[str] = []
  ap = lines.append
  ap(f"/* AI Workbench - Generated Theme: {theme} */")
  ap("")
  # Global
  ap("QWidget {")
  ap(f"  background-color: {t.bg};")
  ap(f"  color: {t.fg};")
  ap(f"  font-family: 'Cascadia Code', 'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif;")
  ap(f"  font-size: {base_font_pt}pt;")
  ap("  border: none;")
  ap("}")

  # Main window & docks
  ap("QMainWindow::separator {")
  ap(f"  background-color: {t.bg_offset};")
  ap("  width: 6px;")
  ap("  height: 6px;")
  ap("}")
  ap("QDockWidget {")
  ap("  titlebar-close-icon: url(none);")
  ap("  titlebar-normal-icon: url(none);")
  ap("}")
  ap("QDockWidget::title {")
  ap(f"  background: {t.bg_offset};")
  ap(f"  color: {t.fg_muted};")
  ap("  padding: 8px 12px;")
  ap("  font-weight: 600;")
  ap(f"  border-bottom: 1px solid {t.border};")
  ap("}")

  # Text inputs
  ap("QTextEdit, QLineEdit, QTextBrowser {")
  ap(f"  background-color: {t.bg_offset};")
  ap(f"  color: {t.fg};")
  ap(f"  border: 1px solid {t.border};")
  ap("  border-radius: 6px;")
  ap("  padding: 8px;")
  ap(f"  selection-background-color: {t.selection_bg};")
  ap("}")
  ap("QTextEdit:focus, QLineEdit:focus {")
  ap(f"  border: 1px solid {t.accent};")
  ap("}")
  ap("QTextBrowser {")
  ap(f"  font-size: {code_pt}pt;")
  ap("  font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;")
  ap("}")

  # Buttons
  ap("QPushButton {")
  ap(f"  background-color: {t.accent};")
  ap(f"  color: {t.accent_fg};")
  ap(f"  border: 1px solid {t.accent};")
  ap("  padding: 8px 16px;")
  ap("  border-radius: 6px;")
  ap("  font-weight: 600;")
  ap("}")
  ap("QPushButton:hover {")
  ap(f"  background-color: {t.accent_hover};")
  ap(f"  border-color: {t.accent_hover};")
  ap("}")
  ap("QPushButton:pressed {")
  ap(f"  background-color: {t.accent};")
  ap("}")
  ap("QToolButton {")
  ap(f"  background-color: {t.bg_offset};")
  ap(f"  color: {t.fg_muted};")
  ap(f"  border: 1px solid {t.border};")
  ap("  padding: 6px;")
  ap("  border-radius: 6px;")
  ap("}")
  ap("QToolButton:hover {")
  ap(f"  background-color: {t.bg};")
  ap(f"  border-color: {t.border};")
  ap(f"  color: {t.fg};")
  ap("}")
  ap("QToolButton#BubbleAction {")
  ap("  background: transparent;")
  ap("  border: 1px solid transparent;")
  ap(f"  color: {t.fg_muted};")
  ap("  padding: 2px;")
  ap("}")
  ap("QToolButton#BubbleAction:hover {")
  ap(f"  background: {t.bg_offset};")
  ap(f"  border: 1px solid {t.border};")
  ap(f"  color: {t.fg};")
  ap("}")

  # Tree view
  ap("QTreeView, QTreeWidget {")
  ap(f"  background-color: {t.bg};")
  ap(f"  border: 1px solid {t.border};")
  ap("  padding: 4px;")
  ap("}")
  ap("QTreeView::item, QTreeWidget::item {")
  ap("  padding: 6px;")
  ap("  border-radius: 4px;")
  ap("}")
  ap("QTreeView::item:hover, QTreeWidget::item:hover {")
  ap(f"  background-color: {t.bg_offset};")
  ap("}")
  ap("QTreeView::item:selected, QTreeWidget::item:selected {")
  ap(f"  background-color: {t.selection_bg};")
  ap(f"  color: {t.fg};")
  ap("}")

  # Tabs
  ap("QTabWidget::pane {")
  ap(f"  border-top: 1px solid {t.border};")
  ap("}")
  ap("QTabBar::tab {")
  ap(f"  background: {t.bg};")
  ap(f"  color: {t.fg_muted};")
  ap("  padding: 8px 16px;")
  ap("  border: 1px solid transparent;")
  ap("  border-bottom: none;")
  ap("  border-top-left-radius: 6px;")
  ap("  border-top-right-radius: 6px;")
  ap("}")
  ap("QTabBar::tab:hover {")
  ap(f"  color: {t.fg};")
  ap("}")
  ap("QTabBar::tab:selected {")
  ap(f"  background: {t.bg_offset};")
  ap(f"  color: {t.fg};")
  ap(f"  border: 1px solid {t.border};")
  ap(f"  border-bottom: 1px solid {t.bg_offset};")
  ap("}")

  # Status & tool bars
  ap("QStatusBar {")
  ap(f"  background: {t.bg_offset};")
  ap(f"  border-top: 1px solid {t.border};")
  ap("}")
  ap("QStatusBar::item {")
  ap("  border: none;")
  ap("  padding: 0 8px;")
  ap("}")
  ap("QToolBar {")
  ap(f"  background: {t.bg};")
  ap(f"  border-bottom: 1px solid {t.border};")
  ap("  spacing: 8px;")
  ap("  padding: 8px;")
  ap("}")

  # Splitter & scrollbars
  ap("QSplitter::handle {")
  ap(f"  background: {t.bg_offset};")
  ap("}")
  ap("QSplitter::handle:horizontal { width: 4px; }")
  ap("QSplitter::handle:vertical { height: 4px; }")
  ap("QScrollBar:vertical {")
  ap(f"  background: {t.bg};")
  ap("  width: 10px;")
  ap("  margin: 0;")
  ap("}")
  ap("QScrollBar::handle:vertical {")
  ap(f"  background: {t.bg_offset};")
  ap("  min-height: 20px;")
  ap("  border-radius: 5px;")
  ap("}")
  ap("QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }")
  ap("QScrollBar:horizontal {")
  ap(f"  background: {t.bg};")
  ap("  height: 10px;")
  ap("  margin: 0;")
  ap("}")
  ap("QScrollBar::handle:horizontal {")
  ap(f"  background: {t.bg_offset};")
  ap("  min-width: 20px;")
  ap("  border-radius: 5px;")
  ap("}")
  ap("QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }")

  # Chat console
  ap("QScrollArea#ChatScroll { border: none; }")
  ap("QFrame#BubbleContainer { border-radius: 12px; }")
  ap(f"QFrame#BubbleContainer[msgRole='user'] {{ background: {t.bubble_user_bg}; }}")
  ap(f"QFrame#BubbleContainer[msgRole='assistant'] {{ background: {t.bubble_ai_bg}; border: 1px solid {t.border}; }}")
  ap(f"QFrame#BubbleContainer[msgRole='system'] {{ background: {t.bubble_sys_bg}; }}")
  ap(f"QTextBrowser#BubbleBody {{ background: transparent; border: none; color: {t.fg}; }}")

  return "\n".join(lines)

def apply_theme(widget, theme: str = "dark", base_font_pt: float = 10.5):
  """Apply theme to the top-level widget and the QApplication.

  Applying at the app level ensures dialogs created later also inherit styling.
  """
  from PySide6.QtWidgets import QApplication
  qss = generate_qss(theme, base_font_pt)
  app = QApplication.instance()
  if app:
    app.setStyle("Fusion")
    app.setStyleSheet(qss)
    # Debug: log confirmation
    try:
      import logging
      logging.getLogger("DesignSystem").info(
        "Applied theme '%s' (%d chars stylesheet)", theme, len(qss)
      )
    except Exception:
      pass
  # Also set on widget in case app-level fails
  widget.setStyleSheet(qss)