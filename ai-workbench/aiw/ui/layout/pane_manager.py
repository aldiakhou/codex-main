"""Pane Manager with split panes and tab stacks.
Provides:
- Recursive splits (horizontal/vertical) with QSplitter
- Per-pane tab stacks (QTabWidget per pane)
- Tab drag & drop reparenting between panes
- Open file opens new/reused tab; single tab per file globally
- Layout serialization/restoration via LayoutSerializer
"""
from __future__ import annotations
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSplitter, QTabBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QMimeData
from PySide6.QtGui import QFont, QDrag
from ..motion.animator import fade_in, fade_out, animate_splitter_open, motion_enabled

from ..code_editor import CodeEditorWidget
from ..components.search_panel import SearchPanel
try:
    from shiboken6 import isValid as _is_qobject_valid
except Exception:  # pragma: no cover
    def _is_qobject_valid(obj):  # type: ignore
        try:
            return obj is not None
        except Exception:
            return False

main_logger = logging.getLogger('MainWindow.PaneManager')


@dataclass
class PaneTab:
    id: str
    title: str
    widget: QWidget
    file_path: Optional[str] = None
    icon: Optional[object] = None
    is_modified: bool = False


class DraggableTabBar(QTabBar):
    """TabBar enabling drag-and-drop of tabs across TabStacks."""

    def __init__(self, stack_ref_getter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self._stack_ref_getter = stack_ref_getter
        self._drag_start_pos: Optional[QPoint] = None

    def mousePressEvent(self, event):
        self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is None:
            return super().mouseMoveEvent(event)
        if (event.buttons() & Qt.MouseButton.LeftButton) and (
            (event.position().toPoint() - self._drag_start_pos).manhattanLength() > 8
        ):
            idx = self.tabAt(self._drag_start_pos)
            if idx >= 0:
                self._start_drag(idx)
                self._drag_start_pos = None
                return
        super().mouseMoveEvent(event)

    def _start_drag(self, index: int):
        mime = QMimeData()
        stack = self._stack_ref_getter()
        mime.setData('application/x-tab-reparent', f"{id(stack)}:{index}".encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-tab-reparent'):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-tab-reparent'):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat('application/x-tab-reparent'):
            return super().dropEvent(event)
        try:
            payload = bytes(event.mimeData().data('application/x-tab-reparent')).decode('utf-8')
            src_id_str, idx_str = payload.split(':', 1)
            src_id = int(src_id_str)
            src_index = int(idx_str)
            target_stack = self._stack_ref_getter()
            target_stack.request_reparent_by_ids(src_id, src_index)
            event.acceptProposedAction()
        except Exception as e:
            main_logger.error(f"Tab drop failed: {e}")
            super().dropEvent(event)


class TabStack(QWidget):
    """A tab stack (pane) wrapping a QTabWidget."""

    def __init__(self, pane_manager: 'PaneManager'):
        super().__init__(pane_manager)
        self.pm = pane_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setMovable(True)
        # Install custom draggable tab bar first
        self._tab_bar = DraggableTabBar(lambda: self)
        self.tab_widget.setTabBar(self._tab_bar)
        # Then enable close buttons and wire both widget and bar signals
        try:
            self.tab_widget.setTabsClosable(True)
            self._tab_bar.setTabsClosable(True)
        except Exception:
            # Some platforms/styles may not support setTabsClosable on bar
            pass
        try:
            self.tab_widget.tabCloseRequested.connect(self._on_close_index)
        except Exception:
            pass
        try:
            self._tab_bar.tabCloseRequested.connect(self._on_close_index)
        except Exception:
            pass
        self.tab_widget.currentChanged.connect(self._on_current_changed)
        self.layout.addWidget(self.tab_widget)

    def request_reparent_by_ids(self, src_obj_id: int, src_index: int):
        self.pm._reparent_from_id_to_stack(src_obj_id, src_index, self)

    def _on_close_index(self, index: int):
        self.pm._close_index_for_stack(self, index)

    def _on_current_changed(self, index: int):
        self.pm._on_tab_changed_global(self, index)


class PaneManager(QWidget):
    """Split-pane, tabbed Pane Manager.

    - Splits via QSplitter
    - Each pane is a TabStack
    - Single global mapping for file tabs (reuse if open)
    - Serialize/restore via LayoutSerializer
    """

    # Signals
    tab_changed = Signal(int)
    file_opened = Signal(str)
    file_closed = Signal(str)
    content_changed = Signal(str)
    before_close_unsaved = Signal(str)  # Emitted when attempting to close a dirty file

    def __init__(self, parent=None, create_default: bool = True):
        super().__init__(parent)
        self.main_window = parent
        self._tabs: Dict[str, PaneTab] = {}
        self._file_tabs: Dict[str, str] = {}  # file_path -> tab_id
        self._stacks: list[TabStack] = []
        self._active_stack: Optional[TabStack] = None
        self._root_container: QWidget
        self._status_area: QWidget | None = None

        self._setup_ui()
        if create_default:
            self._create_default_tab()

    # --- UI wiring ---------------------------------------------------------
    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # Ensure pane manager expands to fill central area
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Start with a single stack
        first_stack = self._create_stack()
        self._root_container = first_stack
        self._active_stack = first_stack
        outer.addWidget(self._root_container, 1)
        outer.setStretchFactor(self._root_container, 1)
        # Status
        self._setup_status_area(outer)

    def _setup_status_area(self, layout):
        status_frame = QFrame()
        status_frame.setMaximumHeight(25)
        status_frame.setStyleSheet("background: #f5f5f5; border-top: 1px solid #ddd;")

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 2, 10, 2)

        self.file_info_label = QLabel("Ready")
        self.file_info_label.setFont(QFont("Cascadia Code", 9))
        status_layout.addWidget(self.file_info_label)

        status_layout.addStretch()

        self.cursor_info_label = QLabel("Ln 1, Col 1")
        self.cursor_info_label.setFont(QFont("Cascadia Code", 9))
        status_layout.addWidget(self.cursor_info_label)

        self.language_label = QLabel("Python")
        self.language_label.setFont(QFont("Cascadia Code", 9))
        status_layout.addWidget(self.language_label)

        layout.addWidget(status_frame)
        self._status_area = status_frame

    def _create_stack(self) -> TabStack:
        stack = TabStack(self)
        # Ensure each stack expands to occupy available space
        stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stack.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Ensure close buttons visible
        try:
            stack.tab_widget.setTabsClosable(True)
        except Exception:
            pass
        self._stacks.append(stack)
        return stack

    def _replace_root(self, new_root: QWidget):
        layout = self.layout()
        if isinstance(layout, QVBoxLayout):
            try:
                layout.removeWidget(self._root_container)
            except Exception:
                pass
            self._root_container.setParent(None)
            layout.insertWidget(0, new_root, 1)
            layout.setStretchFactor(new_root, 1)
        self._root_container = new_root

    # --- Public API --------------------------------------------------------
    def ensure_tab(self, tab_id: str, title: str, factory) -> QWidget:
        if tab_id in self._tabs:
            idx = self._index_of(tab_id)
            if idx >= 0 and self._active_stack:
                self._active_stack.tab_widget.setCurrentIndex(idx)
            return self._tabs[tab_id].widget

        widget = factory()
        pane_tab = PaneTab(id=tab_id, title=title, widget=widget)
        self._tabs[tab_id] = pane_tab
        index = self._active_stack.tab_widget.addTab(widget, title)
        self._active_stack.tab_widget.setCurrentIndex(index)
        try:
            if motion_enabled():
                fade_in(widget, duration_ms=180)
        except Exception:
            pass
        return widget

    # Convenience to open search panel
    def ensure_search(self, root: str) -> QWidget:
        def _factory():
            sp = SearchPanel(root)
            if hasattr(sp, 'open_requested'):
                sp.open_requested.connect(lambda p, _ln: self.main_window._load_file_into_editor(p))
            return sp
        return self.ensure_tab('search', 'Search', _factory)

    def open_file_tab(self, file_path: str, content: str = "") -> Optional[QWidget]:
        try:
            if file_path in self._file_tabs:
                tab_id = self._file_tabs[file_path]
                if tab_id in self._tabs:
                    self._focus_tab_by_id(tab_id)
                    return self._tabs[tab_id].widget

            editor = CodeEditorWidget()
            # Wire unsaved-change signal to set tab modified state
            try:
                editor.file_changed.connect(lambda changed, _fp=file_path: self._mark_tab_modified(_fp, changed))
            except Exception:
                pass
            if content:
                editor.setPlainText(content)
            else:
                try:
                    editor.load_file(file_path)
                except Exception as e:
                    main_logger.warning(f"open_file_tab: failed to load {file_path}: {e}")

            tab_id = f"file_{len(self._tabs)}"
            filename = Path(file_path).name
            pane_tab = PaneTab(id=tab_id, title=filename, widget=editor, file_path=file_path)
            self._tabs[tab_id] = pane_tab
            self._file_tabs[file_path] = tab_id

            index = self._active_stack.tab_widget.addTab(editor, filename)
            self._active_stack.tab_widget.setCurrentIndex(index)
            try:
                editor.setFocus()
            except Exception:
                pass
            try:
                if motion_enabled():
                    fade_in(editor, duration_ms=180)
            except Exception:
                pass

            if hasattr(editor, 'cursorPositionChanged'):
                editor.cursorPositionChanged.connect(self._update_cursor_info)
            if hasattr(editor, 'textChanged'):
                editor.textChanged.connect(self._on_content_changed)
            # Track modified state for confirm-on-close and star title
            try:
                editor.file_changed.connect(lambda changed, _fp=file_path: self._mark_tab_modified(_fp, changed))
            except Exception:
                pass

            self.file_opened.emit(file_path)
            self._update_file_info()
            main_logger.info(f"Opened file: {file_path}")
            return editor
        except Exception as e:
            main_logger.error(f"Failed to open file {file_path}: {e}")
            return None

    def save_current_tab(self, file_path: str = None) -> bool:
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            if not current_widget:
                return False

            tab_id = self._get_tab_id_for_widget(current_widget)
            if not tab_id or tab_id not in self._tabs:
                return False

            tab = self._tabs[tab_id]
            # If widget has a save_file method (CodeEditorWidget), delegate
            if hasattr(current_widget, 'save_file'):
                ok = current_widget.save_file()
                if ok:
                    tab.is_modified = False
                    filename = Path(tab.file_path or 'Untitled').name
                    current_index = self._active_stack.tab_widget.currentIndex()
                    self._active_stack.tab_widget.setTabText(current_index, filename)
                return ok

            if not file_path:
                file_path = tab.file_path
                if not file_path:
                    return False

            content = current_widget.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            tab.file_path = file_path
            tab.is_modified = False
            filename = Path(file_path).name
            tab.title = filename

            current_index = self._active_stack.tab_widget.currentIndex()
            self._active_stack.tab_widget.setTabText(current_index, filename)

            self._file_tabs[file_path] = tab_id
            self._update_file_info()
            main_logger.info(f"Saved file: {file_path}")
            return True
        except Exception as e:
            main_logger.error(f"Failed to save file: {e}")
            return False

    def close_tab(self, tab_id: str):
        try:
            if tab_id not in self._tabs:
                return

            if len(self._tabs) <= 1:
                self._clear_current_tab()
                return

            tab = self._tabs[tab_id]

            # Confirm close if unsaved
            try:
                if tab.is_modified:
                    # Let MainWindow decide (connect to before_close_unsaved)
                    self.before_close_unsaved.emit(tab.file_path or "")
                    # If MainWindow clears modified state (user saved/discarded), refresh local flag
                    # Re-read title star as a heuristic
                    for stack in self._stacks:
                        idx = stack.tab_widget.indexOf(tab.widget)
                        if idx >= 0:
                            t = stack.tab_widget.tabText(idx)
                            if t.endswith("*"):
                                # User cancelled; do not close
                                return
                            break
            except Exception:
                pass

            if tab.file_path and tab.file_path in self._file_tabs:
                del self._file_tabs[tab.file_path]
                self.file_closed.emit(tab.file_path)

            # Remove from whichever stack contains it
            for stack in self._stacks:
                idx = stack.tab_widget.indexOf(tab.widget)
                if idx >= 0:
                    stack.tab_widget.removeTab(idx)
                    break

            self._tabs.pop(tab_id, None)
            if self.main_window and getattr(self.main_window, 'code_editor', None) is tab.widget:
                self.main_window.code_editor = None

            if _is_qobject_valid(tab.widget):
                tab.widget.deleteLater()

            main_logger.info(f"Closed tab: {tab_id}")
        except Exception as e:
            main_logger.error(f"Failed to close tab {tab_id}: {e}")

    def _mark_tab_modified(self, file_path: str, modified: bool):
        try:
            tab_id = self._file_tabs.get(file_path)
            if not tab_id or tab_id not in self._tabs:
                return
            tab = self._tabs[tab_id]
            tab.is_modified = modified
            # Update star in title
            for stack in self._stacks:
                idx = stack.tab_widget.indexOf(tab.widget)
                if idx >= 0:
                    title = Path(file_path).name
                    if modified and not title.endswith("*"):
                        title += "*"
                    stack.tab_widget.setTabText(idx, title)
                    break
        except Exception as e:
            main_logger.error(f"Failed to mark tab modified: {e}")

    def split_current(self, orientation: Qt.Orientation):
        try:
            if self._active_stack is None:
                return
            new_stack = self._create_stack()
            if self._root_container is self._active_stack:
                splitter = QSplitter(orientation, self)
                self._replace_root(splitter)
                splitter.addWidget(self._active_stack)
                splitter.addWidget(new_stack)
                try:
                    animate_splitter_open(splitter)
                except Exception:
                    pass
                # Equal sizes (50/50)
                splitter.setSizes([1, 1])
            else:
                parent = self._active_stack.parent()
                if isinstance(parent, QSplitter):
                    idx = parent.indexOf(self._active_stack)
                    nested = QSplitter(orientation, self)
                    parent.insertWidget(idx, nested)
                    # Remove the old widget at idx+1 (the original active stack moved)
                    parent.widget(idx + 1).setParent(None)
                    nested.addWidget(self._active_stack)
                    nested.addWidget(new_stack)
                    try:
                        animate_splitter_open(nested)
                    except Exception:
                        pass
                    # Equal sizes (50/50)
                    nested.setSizes([1, 1])
                else:
                    splitter = QSplitter(orientation, self)
                    self._replace_root(splitter)
                    splitter.addWidget(self._active_stack)
                    splitter.addWidget(new_stack)
                    try:
                        animate_splitter_open(splitter)
                    except Exception:
                        pass
                    splitter.setSizes([1, 1])
        except Exception as e:
            main_logger.error(f"Failed to split pane: {e}")

    # --- Helpers -----------------------------------------------------------
    def _clear_current_tab(self):
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            if hasattr(current_widget, 'clear'):
                current_widget.clear()
            tab_id = self._get_tab_id_for_widget(current_widget)
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                tab.title = "untitled.py"
                tab.file_path = None
                tab.is_modified = False
                current_index = self._active_stack.tab_widget.currentIndex()
                self._active_stack.tab_widget.setTabText(current_index, "untitled.py")
            self._update_file_info()
        except Exception as e:
            main_logger.error(f"Failed to clear current tab: {e}")

    def get_current_content(self) -> str:
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            if hasattr(current_widget, 'toPlainText'):
                return current_widget.toPlainText()
            return ""
        except Exception as e:
            main_logger.error(f"Failed to get current content: {e}")
            return ""

    def set_current_content(self, content: str):
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            if hasattr(current_widget, 'setPlainText'):
                current_widget.setPlainText(content)
        except Exception as e:
            main_logger.error(f"Failed to set current content: {e}")

    def list_tabs(self) -> List[str]:
        return list(self._tabs.keys())

    def get_open_files(self) -> List[str]:
        return list(self._file_tabs.keys())

    # --- Event Handlers ----------------------------------------------------
    def _on_tab_changed_global(self, stack: TabStack, index: int):
        try:
            if stack is not None:
                self._active_stack = stack
            if index >= 0:
                widget = stack.tab_widget.widget(index)
                if self.main_window and hasattr(widget, 'toPlainText'):
                    self.main_window.code_editor = widget
                self._update_file_info()
                self._update_cursor_info()
                self.tab_changed.emit(index)
        except Exception as e:
            main_logger.error(f"Failed to handle tab change: {e}")

    def _on_content_changed(self):
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            tab_id = self._get_tab_id_for_widget(current_widget)
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                if not tab.is_modified:
                    tab.is_modified = True
                    current_index = self._active_stack.tab_widget.currentIndex()
                    title = self._active_stack.tab_widget.tabText(current_index)
                    if not title.endswith("*"):
                        self._active_stack.tab_widget.setTabText(current_index, title + "*")
            if tab and tab.file_path:
                self.content_changed.emit(tab.file_path)
        except Exception as e:
            main_logger.error(f"Failed to handle content change: {e}")

    def _update_cursor_info(self):
        try:
            current_widget = self._active_stack.tab_widget.currentWidget()
            if hasattr(current_widget, 'textCursor'):
                cursor = current_widget.textCursor()
                line = cursor.blockNumber() + 1
                col = cursor.columnNumber() + 1
                self.cursor_info_label.setText(f"Ln {line}, Col {col}")
        except Exception as e:
            main_logger.error(f"Failed to update cursor info: {e}")

    def _update_file_info(self):
        try:
            if not hasattr(self, 'file_info_label'):
                return
            current_widget = self._active_stack.tab_widget.currentWidget()
            tab_id = self._get_tab_id_for_widget(current_widget)
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                if tab.file_path:
                    self.file_info_label.setText(f"File: {tab.file_path}")
                else:
                    self.file_info_label.setText("Untitled file")
            else:
                self.file_info_label.setText("Ready")
        except Exception as e:
            main_logger.error(f"Failed to update file info: {e}")

    # --- Utility -----------------------------------------------------------
    def _get_tab_id_for_widget(self, widget) -> Optional[str]:
        for tab_id, tab in self._tabs.items():
            if tab.widget == widget:
                return tab_id
        return None

    def _index_of(self, tab_id: str) -> int:
        if tab_id not in self._tabs:
            return -1
        widget = self._tabs[tab_id].widget
        # Active stack first
        if self._active_stack:
            idx = self._active_stack.tab_widget.indexOf(widget)
            if idx >= 0:
                return idx
        for stack in self._stacks:
            idx = stack.tab_widget.indexOf(widget)
            if idx >= 0:
                self._active_stack = stack
                return idx
        return -1

    def _close_index_for_stack(self, stack: TabStack, index: int):
        try:
            widget = stack.tab_widget.widget(index)
            tab_id = self._get_tab_id_for_widget(widget)
            if tab_id:
                try:
                    if motion_enabled() and widget is not None:
                        fade_out(widget, duration_ms=160, on_finished=lambda: self.close_tab(tab_id))
                        return
                except Exception:
                    pass
                self.close_tab(tab_id)
        except Exception as e:
            main_logger.error(f"Failed to close tab at index {index}: {e}")

    def _widget_belongs_to_stack(self, widget: QWidget, stack: TabStack) -> bool:
        return stack.tab_widget.indexOf(widget) >= 0

    def _focus_tab_by_id(self, tab_id: str):
        widget = self._tabs[tab_id].widget
        for stack in self._stacks:
            idx = stack.tab_widget.indexOf(widget)
            if idx >= 0:
                self._active_stack = stack
                stack.tab_widget.setCurrentIndex(idx)
                return

    def _reparent_from_id_to_stack(self, src_obj_id: int, src_index: int, target_stack: TabStack):
        try:
            source_stack = None
            for st in self._stacks:
                if id(st) == src_obj_id:
                    source_stack = st
                    break
            if source_stack is None:
                return
            widget = source_stack.tab_widget.widget(src_index)
            if widget is None:
                return
            title = source_stack.tab_widget.tabText(src_index)
            icon = source_stack.tab_widget.tabIcon(src_index)
            source_stack.tab_widget.removeTab(src_index)
            new_index = target_stack.tab_widget.addTab(widget, icon, title)
            target_stack.tab_widget.setCurrentIndex(new_index)
            self._active_stack = target_stack
        except Exception as e:
            main_logger.error(f"Failed to reparent tab: {e}")

    # --- Persistence --------------------------------------------------------
    def serialize(self) -> Dict[str, Any]:
        try:
            from .layout_serializer import LayoutSerializer
            return LayoutSerializer.serialize(self)
        except Exception as e:
            main_logger.error(f"Failed to serialize pane state: {e}")
            return {'type': 'stack', 'tabs': []}

    def restore(self, state: Dict[str, Any], factory_registry: Dict[str, Any]):
        try:
            from .layout_serializer import LayoutSerializer
            LayoutSerializer.restore(self, state, factory_registry)
        except Exception as e:
            main_logger.error(f"Failed to restore pane state: {e}")


__all__ = ["PaneManager", "PaneTab"]
