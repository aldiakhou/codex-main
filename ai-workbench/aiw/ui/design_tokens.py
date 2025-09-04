"""Design tokens and theme registry for AI Workbench.

Phase 0/1: Provide a structured, extensible source of truth for spacing, radii,
font sizes, palette, elevations, and derived QSS variable generation.

The goal: allow future themes to override just subsets while we compose
complete token sets.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any


# ---- Core Token Dataclasses -------------------------------------------------
@dataclass(frozen=True)
class ColorScheme:
    name: str
    palette: Dict[str, str]
    semantic: Dict[str, str]
    
    # Button and component semantic colors
    buttons: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "accent": {
            "bg": "#0066cc",
            "bg_hover": "#0052a3",
            "bg_pressed": "#003d7a",
            "border": "#0066cc",
            "text": "#ffffff",
        },
        "danger": {
            "bg": "#dc3545",
            "bg_hover": "#c82333",
            "bg_pressed": "#bd2130",
            "border": "#dc3545", 
            "text": "#ffffff",
        },
        "subtle": {
            "bg": "transparent",
            "bg_hover": "rgba(255,255,255,0.1)",
            "bg_pressed": "rgba(255,255,255,0.2)",
            "border": "rgba(255,255,255,0.2)",
            "text": "#ffffff",
        },
        "toolbar": {
            "bg": "transparent",
            "bg_hover": "rgba(255,255,255,0.08)",
            "bg_pressed": "rgba(255,255,255,0.15)",
            "border": "transparent",
            "text": "#ffffff",
        },
    })

    def merged(self, other: "ColorScheme") -> "ColorScheme":
        return ColorScheme(
            name=other.name or self.name,
            palette={**self.palette, **other.palette},
            semantic={**self.semantic, **other.semantic},
            buttons={**self.buttons, **other.buttons},
        )


@dataclass(frozen=True)
class Spacing:
    scale: Dict[str, int] = field(default_factory=lambda: {
        "0": 0,
        "1": 2,
        "2": 4,
        "3": 6,
        "4": 8,
        "5": 12,
        "6": 16,
        "7": 20,
        "8": 24,
        "9": 32,
        "10": 40,
        "12": 48,
    })
    
    # Semantic spacing aliases
    gutters: Dict[str, int] = field(default_factory=lambda: {
        "panel": 12,      # Standard panel padding
        "content": 16,    # Content area padding
        "section": 24,    # Section spacing
        "component": 8,   # Between components
        "inline": 4,      # Inline element spacing
    })


@dataclass(frozen=True)
class Elevation:
    shadows: Dict[str, str] = field(default_factory=lambda: {
        "0": "none",
        "1": "0 1px 2px rgba(0,0,0,0.08)",
        "2": "0 2px 4px rgba(0,0,0,0.12)",
        "3": "0 4px 8px rgba(0,0,0,0.16)",
        "4": "0 8px 16px rgba(0,0,0,0.20)",
    })
    
    # Semantic elevations
    semantic: Dict[str, str] = field(default_factory=lambda: {
        "panel": "0 1px 3px rgba(0,0,0,0.1)",
        "floating": "0 4px 12px rgba(0,0,0,0.15)",
        "overlay": "0 8px 24px rgba(0,0,0,0.2)",
        "tooltip": "0 2px 8px rgba(0,0,0,0.12)",
    })


@dataclass(frozen=True)
class Typography:
    # Use Cascadia across the app for a cohesive, editor-like feel.
    # Falls back gracefully if the font isn't installed.
    font_family: str = "'Cascadia Code', 'Cascadia Mono', 'Segoe UI', system-ui, -apple-system, sans-serif"
    code_family: str = "'Cascadia Code', 'Cascadia Mono', Consolas, 'Fira Code', 'Courier New', monospace"
    
    sizes: Dict[str, int] = field(default_factory=lambda: {
        "xs": 10,
        "sm": 11,
        "base": 12,
        "md": 13,
        "lg": 15,
        "xl": 18,
        "xxl": 22,
        "code": 12,
        "heading": 16,
        "subheading": 14,
    })
    
    weights: Dict[str, str] = field(default_factory=lambda: {
        "normal": "400",
        "medium": "500", 
        "semibold": "600",
        "bold": "700",
    })
    
    line_height: float = 1.4


@dataclass(frozen=True)
class Radii:
    values: Dict[str, int] = field(default_factory=lambda: {
        "none": 0,
        "sm": 2,
        "md": 4,
        "lg": 8,
        "xl": 12,
        "pill": 999,
    })


@dataclass(frozen=True)
class DesignTokens:
    colors: ColorScheme
    typography: Typography = Typography()
    spacing: Spacing = Spacing()
    radii: Radii = Radii()
    elevation: Elevation = Elevation()

    def to_qss_vars(self) -> Dict[str, str]:
        """Translate core tokens into a dict of QSS variable names -> values."""
        vars: Dict[str, str] = {}
        for key, val in self.colors.palette.items():
            vars[f"@color-{key}"] = val
        for key, val in self.colors.semantic.items():
            vars[f"@semantic-{key}"] = val
        
        # Button semantic colors
        for btn_type, states in self.colors.buttons.items():
            for state, color in states.items():
                vars[f"@btn-{btn_type}-{state}"] = color
        
        for key, val in self.spacing.scale.items():
            vars[f"@space-{key}"] = f"{val}px"
        for key, val in self.spacing.gutters.items():
            vars[f"@gutter-{key}"] = f"{val}px"
        for key, val in self.radii.values.items():
            vars[f"@radius-{key}"] = f"{val}px"
        for key, val in self.typography.sizes.items():
            vars[f"@font-size-{key}"] = f"{val}pt"
        for key, val in self.elevation.shadows.items():
            vars[f"@shadow-{key}"] = val
        for key, val in self.elevation.semantic.items():
            vars[f"@elevation-{key}"] = val
        vars["@font-family-base"] = self.typography.font_family
        vars["@font-family-code"] = self.typography.code_family
        return vars


# ---- Default Themes ---------------------------------------------------------
_dark_base = ColorScheme(
    name="dark",
    palette={
        "bg0": "#101215",
        "bg1": "#1a1d21",
        "bg2": "#23272d",
        "bg3": "#2e333a",
        "border": "#3c424b",
        "accent": "#4f8cff",
        "accent-alt": "#7aa5ff",
        "danger": "#ff4d4f",
        "warn": "#e0a941",
        "ok": "#44c27a",
        "info": "#369bd1",
        "text": "#e6e8eb",
        "text-dim": "#9aa1ab",
        "code-bg": "#181b1f",
    },
    semantic={
        "surface": "#1a1d21",
        "surface-alt": "#23272d",
        "panel": "#1f2227",
        "panel-header": "#24282f",
        "selection": "#28406b",
        "focus": "#4f8cff",
        "link": "#7aa5ff",
        "outline": "#4f8cff",
    },
    buttons={
        "accent": {
            "bg": "#4f8cff",
            "bg_hover": "#6ca1ff",
            "bg_pressed": "#3970db",
            "border": "#4f8cff",
            "text": "#ffffff",
        },
        "danger": {
            "bg": "#ff4d4f",
            "bg_hover": "#ff7875",
            "bg_pressed": "#d73027",
            "border": "#ff4d4f", 
            "text": "#ffffff",
        },
        "subtle": {
            "bg": "transparent",
            "bg_hover": "rgba(255,255,255,0.08)",
            "bg_pressed": "rgba(255,255,255,0.15)",
            "border": "rgba(255,255,255,0.2)",
            "text": "#e6e8eb",
        },
        "toolbar": {
            "bg": "transparent",
            "bg_hover": "rgba(255,255,255,0.05)",
            "bg_pressed": "rgba(255,255,255,0.1)",
            "border": "transparent",
            "text": "#9aa1ab",
        },
    },
)

_light_base = ColorScheme(
    name="light",
    palette={
        "bg0": "#f8f9fb",
        "bg1": "#eef0f3",
        "bg2": "#e2e6ea",
        "bg3": "#d5dbe1",
        "border": "#c2c9d1",
        "accent": "#2f6fe8",
        "accent-alt": "#4d84f0",
        "danger": "#d93033",
        "warn": "#c47d18",
        "ok": "#1f9a57",
        "info": "#2a7db1",
        "text": "#1f2428",
        "text-dim": "#4f5a63",
        "code-bg": "#f1f3f5",
    },
    semantic={
        "surface": "#ffffff",
        "surface-alt": "#f3f5f7",
        "panel": "#ffffff",
        "panel-header": "#f0f2f4",
        "selection": "#d0e2ff",
        "focus": "#2f6fe8",
        "link": "#2f6fe8",
        "outline": "#2f6fe8",
    },
    buttons={
        "accent": {
            "bg": "#2f6fe8",
            "bg_hover": "#4d84f0",
            "bg_pressed": "#1f5bdb",
            "border": "#2f6fe8",
            "text": "#ffffff",
        },
        "danger": {
            "bg": "#d93033",
            "bg_hover": "#f05659",
            "bg_pressed": "#b02529",
            "border": "#d93033", 
            "text": "#ffffff",
        },
        "subtle": {
            "bg": "transparent",
            "bg_hover": "rgba(0,0,0,0.05)",
            "bg_pressed": "rgba(0,0,0,0.1)",
            "border": "rgba(0,0,0,0.1)",
            "text": "#1f2428",
        },
        "toolbar": {
            "bg": "transparent",
            "bg_hover": "rgba(0,0,0,0.03)",
            "bg_pressed": "rgba(0,0,0,0.08)",
            "border": "transparent",
            "text": "#4f5a63",
        },
    },
)

# Register token sets
THEME_REGISTRY: Dict[str, DesignTokens] = {
    "dark": DesignTokens(colors=_dark_base),
    "light": DesignTokens(colors=_light_base),
}


def get_tokens(theme: str) -> DesignTokens:
    return THEME_REGISTRY.get(theme, THEME_REGISTRY["dark"])


def generate_qss(theme: str) -> str:
    """Generate comprehensive QSS with beautiful modern styling."""
    tokens = get_tokens(theme)
    vars = tokens.to_qss_vars()
    
    # Beautiful Button Styles
    button_styles = f"""
/* ========== BUTTON SYSTEM ========== */

/* Base Button */
QPushButton {{
    background: {vars['@color-bg2']};
    border: 1px solid {vars['@color-border']};
    padding: {vars['@gutter-component']} {vars['@gutter-panel']};
    border-radius: {vars['@radius-md']};
    font-family: {vars['@font-family-base']};
    font-size: {vars['@font-size-base']};
    font-weight: 500;
    color: {vars['@color-text']};
    min-height: 20px;
}}
QPushButton:hover {{
    background: {vars['@color-bg3']};
    border-color: {vars['@semantic-focus']};
}}
QPushButton:pressed {{
    background: {vars['@color-accent']};
    color: white;
}}
QPushButton:disabled {{
    background: {vars['@color-bg1']};
    color: {vars['@color-text-dim']};
    border-color: {vars['@color-border']};
}}

/* Accent Button (Primary) */
QPushButton[class~='accent'] {{
    background: {vars['@btn-accent-bg']};
    color: {vars['@btn-accent-text']};
    border: 1px solid {vars['@btn-accent-border']};
    font-weight: 600;
}}
QPushButton[class~='accent']:hover {{
    background: {vars['@btn-accent-bg_hover']};
}}
QPushButton[class~='accent']:pressed {{
    background: {vars['@btn-accent-bg_pressed']};
}}

/* Danger Button */
QPushButton[class~='danger'] {{
    background: {vars['@btn-danger-bg']};
    color: {vars['@btn-danger-text']};
    border: 1px solid {vars['@btn-danger-border']};
    font-weight: 600;
}}
QPushButton[class~='danger']:hover {{
    background: {vars['@btn-danger-bg_hover']};
}}
QPushButton[class~='danger']:pressed {{
    background: {vars['@btn-danger-bg_pressed']};
}}

/* Subtle Button */
QPushButton[class~='subtle'] {{
    background: {vars['@btn-subtle-bg']};
    color: {vars['@btn-subtle-text']};
    border: 1px solid {vars['@btn-subtle-border']};
}}
QPushButton[class~='subtle']:hover {{
    background: {vars['@btn-subtle-bg_hover']};
}}
QPushButton[class~='subtle']:pressed {{
    background: {vars['@btn-subtle-bg_pressed']};
}}

/* Toolbar Button */
QPushButton[class~='toolbar'] {{
    background: {vars['@btn-toolbar-bg']};
    color: {vars['@btn-toolbar-text']};
    border: 1px solid {vars['@btn-toolbar-border']};
    padding: {vars['@space-2']} {vars['@space-3']};
    border-radius: {vars['@radius-sm']};
    min-height: 16px;
}}
QPushButton[class~='toolbar']:hover {{
    background: {vars['@btn-toolbar-bg_hover']};
}}
QPushButton[class~='toolbar']:pressed {{
    background: {vars['@btn-toolbar-bg_pressed']};
}}
"""

    # Beautiful Tab Widget Styling
    tab_styles = f"""
/* ========== TAB SYSTEM ========== */

QTabWidget::pane {{
    border: 1px solid {vars['@color-border']};
    background: {vars['@semantic-panel']};
    border-radius: {vars['@radius-md']};
    padding: {vars['@gutter-content']};
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background: transparent;
    border: none;
    padding: {vars['@gutter-component']} {vars['@gutter-panel']};
    margin-right: {vars['@space-1']};
    border-radius: {vars['@radius-sm']} {vars['@radius-sm']} 0 0;
    color: {vars['@color-text-dim']};
    font-size: {vars['@font-size-base']};
    font-weight: 500;
    min-width: 80px;
}}

QTabBar::tab:hover {{
    background: {vars['@color-bg2']};
    color: {vars['@color-text']};
}}

QTabBar::tab:selected {{
    background: {vars['@semantic-panel']};
    color: {vars['@color-text']};
    border-bottom: 2px solid {vars['@semantic-focus']};
    font-weight: 600;
}}

QTabBar::tab:!selected {{
    margin-top: 2px;
}}

/* Active indicator bar */
QTabBar::tab:selected {{
    border-bottom: 2px solid {vars['@color-accent']};
}}
"""

    # Core Application Styling
    core_styles = f"""
/* ========== CORE APPLICATION ========== */

QWidget {{
    font-family: {vars['@font-family-base']};
    color: {vars['@color-text']};
    background: {vars['@color-bg0']};
    selection-background-color: {vars['@semantic-selection']};
    font-size: {vars['@font-size-base']};
}}

QMainWindow {{
    background: {vars['@color-bg0']};
}}

QMainWindow::separator {{
    background: {vars['@color-border']};
    width: 2px; 
    height: 2px;
}}

QMainWindow::separator:hover {{
    background: {vars['@semantic-focus']};
}}

/* ========== DOCK WIDGETS ========== */

QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    background: {vars['@semantic-panel']};
    border: 1px solid {vars['@color-border']};
    border-radius: {vars['@radius-md']};
}}

QDockWidget::title {{
    text-align: left;
    padding: {vars['@gutter-component']} {vars['@gutter-panel']};
    background: {vars['@semantic-panel-header']};
    font-size: {vars['@font-size-sm']};
    font-weight: 600;
    color: {vars['@color-text']};
    border-bottom: 1px solid {vars['@color-border']};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    padding: 0px;
    icon-size: 12px;
    background: transparent;
    border: none;
    margin: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {vars['@color-bg3']};
    border-radius: 2px;
}}
"""

    # Tree and List Views
    tree_styles = f"""
/* ========== TREE/LIST VIEWS ========== */

QTreeView, QTreeWidget, QListView, QListWidget {{
    background: {vars['@semantic-surface']};
    border: 1px solid {vars['@color-border']};
    border-radius: {vars['@radius-md']};
    font-size: {vars['@font-size-sm']};
    outline: none;
    padding: {vars['@space-2']};
}}

QTreeView::item, QTreeWidget::item, QListView::item, QListWidget::item {{
    padding: {vars['@space-2']} {vars['@space-3']};
    border: none;
    border-radius: {vars['@radius-sm']};
    margin: 1px 0;
}}

QTreeView::item:hover, QTreeWidget::item:hover, 
QListView::item:hover, QListWidget::item:hover {{
    background: {vars['@color-bg2']};
}}

QTreeView::item:selected, QTreeWidget::item:selected,
QListView::item:selected, QListWidget::item:selected {{
    background: {vars['@semantic-selection']};
    color: {vars['@color-text']};
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    border-image: none;
    image: url(:/icons/branch-closed.png);
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    border-image: none;
    image: url(:/icons/branch-open.png);
}}
"""

    # Text Editors and Browsers
    text_styles = f"""
/* ========== TEXT EDITORS ========== */

QTextEdit, QTextBrowser, QPlainTextEdit {{
    background: {vars['@semantic-surface']};
    border: 1px solid {vars['@color-border']};
    border-radius: {vars['@radius-md']};
    font-family: {vars['@font-family-code']};
    font-size: {vars['@font-size-code']};
    color: {vars['@color-text']};
    padding: {vars['@gutter-component']};
    selection-background-color: {vars['@semantic-selection']};
    line-height: {int(tokens.typography.sizes["code"] * tokens.typography.line_height)}px;
}}

QTextEdit:focus, QTextBrowser:focus, QPlainTextEdit:focus {{
    border-color: {vars['@semantic-focus']};
}}

/* Line number area for code editor */
QTextEdit .line-number-area {{
    background: {vars['@color-bg1']};
    color: {vars['@color-text-dim']};
    border-right: 1px solid {vars['@color-border']};
}}
"""

    # Toolbar and Status Bar
    toolbar_styles = f"""
/* ========== TOOLBARS & STATUS ========== */

QToolBar {{
    background: {vars['@semantic-panel-header']};
    border: none;
    border-bottom: 1px solid {vars['@color-border']};
    spacing: {vars['@space-2']};
    padding: {vars['@space-2']} {vars['@gutter-component']};
}}

QToolButton {{
    background: transparent;
    border: none;
    padding: {vars['@space-2']} {vars['@space-3']};
    border-radius: {vars['@radius-sm']};
    color: {vars['@color-text-dim']};
    font-size: {vars['@font-size-sm']};
}}

QToolButton:hover {{
    background: {vars['@color-bg2']};
    color: {vars['@color-text']};
}}

QToolButton:pressed {{
    background: {vars['@color-bg3']};
}}

QToolButton:checked {{
    background: {vars['@semantic-focus']};
    color: white;
}}

QStatusBar {{
    background: {vars['@semantic-panel-header']};
    border-top: 1px solid {vars['@color-border']};
    font-size: {vars['@font-size-xs']};
    color: {vars['@color-text-dim']};
    padding: {vars['@space-2']} {vars['@gutter-component']};
}}

QStatusBar::item {{
    border: none;
}}
"""

    # Scrollbars
    scrollbar_styles = f"""
/* ========== SCROLLBARS ========== */

QScrollBar:vertical {{
    width: 12px;
    background: {vars['@color-bg1']};
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {vars['@color-bg3']};
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {vars['@color-accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    subcontrol-position: none;
}}

QScrollBar:horizontal {{
    height: 12px;
    background: {vars['@color-bg1']};
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {vars['@color-bg3']};
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {vars['@color-accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    subcontrol-position: none;
}}
"""

    # Header comment with all variable references
    header = ["/* ========== GENERATED QSS DESIGN SYSTEM ========== */"] + [f"/* {k} = {v} */" for k, v in vars.items()]
    
    return "\n".join(header) + "\n\n" + core_styles + button_styles + tab_styles + tree_styles + text_styles + toolbar_styles + scrollbar_styles


__all__ = [
    "DesignTokens",
    "get_tokens",
    "generate_qss",
]
