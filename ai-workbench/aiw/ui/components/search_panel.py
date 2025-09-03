"""Global search panel using ripgrep if available, otherwise Python fallback.

Groups results by file and emits open requests when clicking.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QLabel
)


@dataclass
class SearchResult:
    file: Path
    line: int
    text: str


class SearchPanel(QWidget):
    open_requested = Signal(str, int)

    def __init__(self, root: str, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search in workspace…")
        self.btn = QPushButton("Search")
        self.btn.clicked.connect(self._do_search)
        bar.addWidget(QLabel("Find:"))
        bar.addWidget(self.input, 1)
        bar.addWidget(self.btn)
        layout.addLayout(bar)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File/Match", "Line"])
        self.tree.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.tree, 1)

    def _on_item_activated(self, item: QTreeWidgetItem, _col: int):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        line = item.data(1, Qt.ItemDataRole.UserRole) or 1
        if path:
            self.open_requested.emit(path, int(line))

    def _rg_available(self) -> bool:
        return shutil.which('rg') is not None

    def _do_search(self):
        query = self.input.text().strip()
        if not query:
            return
        results: Dict[Path, List[Tuple[int, str]]] = {}
        if self._rg_available():
            try:
                cmd = ['rg', '--vimgrep', '--no-heading', '--hidden', '-g', '!.git', '-g', '!.aiw_trash', query, str(self.root)]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
                for line in proc.stdout.splitlines():
                    # format: file:line:col:text
                    try:
                        file_str, line_str, _col, text = line.split(':', 3)
                        p = Path(file_str)
                        if any(seg in ('.git', 'node_modules', '__pycache__', '.aiw_trash') for seg in p.parts):
                            continue
                        results.setdefault(p, []).append((int(line_str), text.strip()))
                    except Exception:
                        continue
            except Exception:
                pass
        else:
            # Python fallback: naive scan
            for p in self.root.rglob('*'):
                try:
                    if p.is_file() and not any(seg in ('.git', 'node_modules', '__pycache__', '.aiw_trash') for seg in p.parts):
                        with p.open('r', encoding='utf-8', errors='ignore') as f:
                            for idx, t in enumerate(f, start=1):
                                if query.lower() in t.lower():
                                    results.setdefault(p, []).append((idx, t.strip()))
                except Exception:
                    continue

        # Populate tree grouped by file
        self.tree.clear()
        for file_path, matches in sorted(results.items(), key=lambda x: str(x[0]).lower()):
            file_item = QTreeWidgetItem([str(file_path.relative_to(self.root)), ""])
            file_item.setData(0, Qt.ItemDataRole.UserRole, str(file_path))
            self.tree.addTopLevelItem(file_item)
            for line_no, text in matches[:200]:
                child = QTreeWidgetItem([text, str(line_no)])
                child.setData(0, Qt.ItemDataRole.UserRole, str(file_path))
                child.setData(1, Qt.ItemDataRole.UserRole, line_no)
                file_item.addChild(child)


__all__ = ["SearchPanel"]

