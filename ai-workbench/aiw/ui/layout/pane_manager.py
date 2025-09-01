"""Minimal Pane Manager skeleton (partial Phase 2).
Future: support nested splits & tab re-parenting.
Current: single tab bar abstraction placeholder.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

@dataclass
class PaneTab:
    id: str
    title: str
    widget: QWidget
    icon: Optional[object] = None

class PaneManager(QWidget):
    """Initial simple manager: wraps a QTabWidget, API forward-compatible."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: Dict[str, PaneTab] = {}
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_index)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self._tab_widget)

    # --- Public API ---------------------------------------------------------
    def ensure_tab(self, tab_id: str, title: str, factory) -> QWidget:
        if tab_id in self._tabs:
            idx = self._index_of(tab_id)
            if idx >= 0:
                self._tab_widget.setCurrentIndex(idx)
            return self._tabs[tab_id].widget
        widget = factory()
        pane_tab = PaneTab(id=tab_id, title=title, widget=widget)
        self._tabs[tab_id] = pane_tab
        self._tab_widget.addTab(widget, title)
        self._tab_widget.setCurrentWidget(widget)
        return widget

    def close_tab(self, tab_id: str):
        idx = self._index_of(tab_id)
        if idx >= 0:
            w = self._tab_widget.widget(idx)
            self._tab_widget.removeTab(idx)
            self._tabs.pop(tab_id, None)
            w.deleteLater()

    def list_tabs(self) -> List[str]:
        return list(self._tabs.keys())

    # --- Persistence --------------------------------------------------------
    def serialize(self) -> Dict[str, Any]:
        """Return a JSON-serializable snapshot of current tabs.
        Only store id & title; responsibility for restoring widget type
        belongs to caller (MainWindow) via a registry mapping.
        """
        return {
            'tabs': [
                {'id': t.id, 'title': t.title, 'active': (self._tab_widget.currentWidget() is t.widget)}
                for t in self._tabs.values()
            ]
        }

    def restore(self, state: Dict[str, Any], factory_registry: Dict[str, Any]):
        """Recreate tabs from a prior serialize() result.
        factory_registry: mapping of tab_id -> callable returning widget.
        Silently skips unknown ids.
        """
        if not state:
            return
        tabs = state.get('tabs', [])
        for tinfo in tabs:
            tid = tinfo.get('id')
            title = tinfo.get('title', tid)
            if not tid or tid in self._tabs:
                continue
            factory = factory_registry.get(tid)
            if not factory:
                continue
            self.ensure_tab(tid, title, factory)
            if tinfo.get('active'):
                w = self._tabs[tid].widget
                self._tab_widget.setCurrentWidget(w)

    # --- Internals ----------------------------------------------------------
    def _index_of(self, tab_id: str) -> int:
        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) is self._tabs.get(tab_id, None).widget if tab_id in self._tabs else False:
                return i
        return -1

    def _close_index(self, index: int):
        # Map to id
        for tid, t in list(self._tabs.items()):
            if self._tab_widget.widget(index) is t.widget:
                self.close_tab(tid)
                break

__all__ = ["PaneManager"]
