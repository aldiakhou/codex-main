from __future__ import annotations
from typing import List, Tuple, Callable
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

Command = Tuple[str, Callable, str]

class CommandPalette(QDialog):
    """Simple modal command palette (filter + execute)."""
    def __init__(self, actions: List[Command], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.resize(520, 420)
        self._actions = actions
        layout = QVBoxLayout(self)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Type to filter commands…")
        self.list = QListWidget(self)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        self.search.textChanged.connect(self._refilter)
        self.list.itemActivated.connect(self._activate)
        self._refilter()

    def _refilter(self):
        term = self.search.text().lower().strip()
        self.list.clear()
        for label, cb, sc in self._actions:
            if term and term not in label.lower():
                continue
            item = QListWidgetItem(label + (f"  [{sc}]" if sc else ""))
            item.setData(Qt.ItemDataRole.UserRole, cb)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _activate(self, item: QListWidgetItem):
        cb = item.data(Qt.ItemDataRole.UserRole)
        if callable(cb):
            cb()
        self.accept()
