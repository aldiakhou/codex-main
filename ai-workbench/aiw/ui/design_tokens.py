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

    def merged(self, other: "ColorScheme") -> "ColorScheme":
        return ColorScheme(
            name=other.name or self.name,
            palette={**self.palette, **other.palette},
            semantic={**self.semantic, **other.semantic},
        )


@dataclass(frozen=True)
class Typography:
    font_family: str = "Cascadia Code, Consolas, 'Courier New', monospace"
    sizes: Dict[str, int] = field(default_factory=lambda: {
        "xs": 10,
        "sm": 11,
        "base": 12,
        "md": 13,
        "lg": 15,
        "xl": 18,
        "code": 12,
    })
    line_height: float = 1.35


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
    })


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
class Elevation:
    shadows: Dict[str, str] = field(default_factory=lambda: {
        "0": "none",
        "1": "0 1px 2px rgba(0,0,0,0.32)",
        "2": "0 2px 4px rgba(0,0,0,0.35)",
        "3": "0 4px 8px rgba(0,0,0,0.4)",
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
        for key, val in self.spacing.scale.items():
            vars[f"@space-{key}"] = f"{val}px"
        for key, val in self.radii.values.items():
            vars[f"@radius-{key}"] = f"{val}px"
        for key, val in self.typography.sizes.items():
            vars[f"@font-size-{key}"] = f"{val}pt"
        for key, val in self.elevation.shadows.items():
            vars[f"@shadow-{key}"] = val
        vars["@font-family-base"] = self.typography.font_family
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
)

# Register token sets
THEME_REGISTRY: Dict[str, DesignTokens] = {
    "dark": DesignTokens(colors=_dark_base),
    "light": DesignTokens(colors=_light_base),
}


def get_tokens(theme: str) -> DesignTokens:
    return THEME_REGISTRY.get(theme, THEME_REGISTRY["dark"])


def generate_qss(theme: str) -> str:
    tokens = get_tokens(theme)
    vars = tokens.to_qss_vars()
    # Simple variable injection: we generate a :root-like comment block for reference
    header = ["/* Generated QSS vars */"] + [f"/* {k} = {v} */" for k, v in vars.items()]
    base = f"""\
QWidget {{\n    font-family: {vars['@font-family-base']};\n    color: {vars['@color-text']};\n    background: {vars['@color-bg0']};\n    selection-background-color: {vars['@semantic-selection']};\n}}\n\nQMainWindow::separator {{\n    background: {vars['@color-bg2']};\n    width: 4px; height: 4px;\n}}\n\nQDockWidget {{\n    titlebar-close-icon: none;\n    titlebar-normal-icon: none;\n    background: {vars['@semantic-panel']};\n    border: 1px solid {vars['@color-border']};\n}}\n\nQDockWidget::title {{\n    text-align: left;\n    padding: 4px 8px;\n    background: {vars['@semantic-panel-header']};\n    font-size: {vars['@font-size-sm']};\n}}\n\nQTreeView, QTreeWidget {{\n    background: {vars['@color-bg1']};\n    border: 1px solid {vars['@color-border']};\n    font-size: {vars['@font-size-sm']};\n}}\n\nQTreeView::item:selected, QTreeWidget::item:selected {{\n    background: {vars['@semantic-selection']};\n}}\n\nQPushButton {{\n    background: {vars['@color-bg2']};\n    border: 1px solid {vars['@color-border']};\n    padding: 4px 10px;\n    border-radius: {vars['@radius-md']};\n}}\nQPushButton:hover {{\n    background: {vars['@color-bg3']};\n}}\nQPushButton:pressed {{\n    background: {vars['@color-accent']};\n    color: #fff;\n}}\n\nQPushButton[class~='accent'] {{\n    background: {vars['@color-accent']};\n    color: #fff;\n    border: 1px solid {vars['@color-accent-alt']};\n}}\nQPushButton[class~='accent']:hover {{\n    background: {vars['@color-accent-alt']};\n}}\n\nQStatusBar {{\n    background: {vars['@color-bg1']};\n    border-top: 1px solid {vars['@color-border']};\n    font-size: {vars['@font-size-xs']};\n}}\n\nQToolBar {{\n    background: {vars['@semantic-panel-header']};\n    border-bottom: 1px solid {vars['@color-border']};\n    spacing: 6px;\n}}\nQToolButton {{ background: transparent; }}\nQToolButton:hover {{ background: {vars['@color-bg2']}; border-radius: {vars['@radius-sm']}; }}\nQToolButton:checked {{ background: {vars['@color-accent']}; color: #fff; }}\n\nQTextEdit, QTextBrowser {{\n    background: {vars['@color-bg1']};\n    border: 1px solid {vars['@color-border']};\n    font-size: {vars['@font-size-code']};\n}}\n\nQScrollBar:vertical {{ width:10px; background: {vars['@color-bg1']}; }}\nQScrollBar::handle:vertical {{ background:{vars['@color-bg3']}; min-height:20px; border-radius:4px; }}\nQScrollBar::handle:vertical:hover {{ background:{vars['@color-accent']}; }}\n"""
    return "\n".join(header) + "\n" + base


__all__ = [
    "DesignTokens",
    "get_tokens",
    "generate_qss",
]
