"""UI motion package: small animation helpers and wrappers."""
from .anim import fade_in_widget, animate_height_toggle
from .animator import (
    motion_enabled,
    fade_in,
    fade_out,
    pulse_opacity,
    slide_and_fade_in,
    animate_splitter_open,
    pulse_item_background,
)

__all__ = [
    "fade_in_widget",
    "animate_height_toggle",
    "motion_enabled",
    "fade_in",
    "fade_out",
    "pulse_opacity",
    "slide_and_fade_in",
    "animate_splitter_open",
    "pulse_item_background",
]

