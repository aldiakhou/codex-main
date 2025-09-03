"""Quick Switcher (Ctrl+P) listing recent + fuzzy file matches.

Performance target: under ~150ms for <= 5k files.
Uses a lightweight fuzzy scorer and caches directory walk.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem


def _fuzzy_score(pattern: str, text: str) -> int:
    """Subsequence-based fuzzy score. O(len(pattern)+logits) using find().
    Returns -1 if pattern is not a subsequence of text.
    """
    if not pattern:
        return 0
    p = pattern.lower()
    t = text.lower()
    last = -1
    score = 0
    for ch in p:
        idx = t.find(ch, last + 1)
        if idx == -1:
            return -1
        score += 5
        if last >= 0 and idx == last + 1:
            score += 3
        last = idx
    score += max(0, 20 - len(text))
    return score


@dataclass
class FSCache:
    root: Path
    files: List[Path]
    last_scan: float


class QuickSwitcher(QDialog):
    open_requested = Signal(str)

    def __init__(self, root: str, recent: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Switcher")
        self.setModal(True)
        self.resize(600, 400)
        self.root = Path(root)
        self.recent = recent or []
        self.cache: Optional[FSCache] = None
        self._setup_ui()
        self._ensure_cache()
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Type to search files…")
        self.input.textChanged.connect(self._refresh_list)
        self.input.returnPressed.connect(self._accept_current)
        layout.addWidget(self.input)
        self.list = QListWidget(self)
        layout.addWidget(self.list, 1)

    def _ensure_cache(self):
        now = time.time()
        if self.cache and now - self.cache.last_scan < 10:
            return
        files: List[Path] = []
        for p in self.root.rglob('*'):
            try:
                if p.is_file() and not any(seg in ('.git', '.aiw_trash', 'node_modules', '__pycache__') for seg in p.parts):
                    files.append(p)
            except Exception:
                continue
        self.cache = FSCache(root=self.root, files=files, last_scan=now)

    def _refresh_list(self):
        text = self.input.text().strip()
        self.list.clear()
        if not self.cache:
            self._ensure_cache()
        items: List[Tuple[int, Path]] = []
        if not text:
            # show recents first
            for rp in self.recent[:20]:
                p = Path(rp)
                if p.exists():
                    it = QListWidgetItem(p.name)
                    it.setData(Qt.ItemDataRole.UserRole, str(p))
                    self.list.addItem(it)
            return
        # score cache
        pt = time.perf_counter()
        pat = text
        for p in self.cache.files:
            s = _fuzzy_score(pat, str(p.relative_to(self.root)))
            if s >= 0:
                items.append((s, p))
        items.sort(key=lambda x: x[0], reverse=True)
        for _, p in items[:200]:
            it = QListWidgetItem(str(p.relative_to(self.root)))
            it.setData(Qt.ItemDataRole.UserRole, str(p))
            self.list.addItem(it)
        # simple perf guard for visibility
        _ = time.perf_counter() - pt

    def _accept_current(self):
        it = self.list.currentItem()
        if not it and self.list.count() > 0:
            it = self.list.item(0)
        if it:
            path = it.data(Qt.ItemDataRole.UserRole)
            self.open_requested.emit(path)
            self.accept()

    def open(self):  # type: ignore[override]
        super().open()
        self.input.setFocus()


__all__ = ["QuickSwitcher"]
