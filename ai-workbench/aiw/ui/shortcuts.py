from __future__ import annotations
"""Central shortcut registry for UI actions."""

SHORTCUTS = {
    'theme.toggle': {
        'text': 'Toggle Theme',
        'shortcut': 'Ctrl+Shift+T',
        'description': 'Switch between dark and light theme'
    },
    'chat.focus': {
        'text': 'Focus Chat Input',
        'shortcut': 'Ctrl+L',
        'description': 'Focus the chat prompt input'
    },
    'command.palette': {
        'text': 'Open Command Palette',
        'shortcut': 'Ctrl+Shift+P',
        'description': 'Search all commands'
    },
}

def get_shortcut(key: str) -> str:
    return SHORTCUTS.get(key, {}).get('shortcut', '')

def all_shortcuts():
    return SHORTCUTS
