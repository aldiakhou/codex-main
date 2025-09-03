"""File Tree component with context menu and inline rename.

Features:
- Multi-select QTreeWidget-based file browser
- Context menu: New File / New Folder / Rename / Duplicate / Delete / Reveal in Explorer
- Inline rename (F2), keyboard navigation
- Emits file_open_requested when user activates an item
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QMenu,
    QFileDialog, QMessageBox
)

from ..services.file_ops import FileOpsService


class FileTree(QWidget):
    file_open_requested = Signal(str)
    root_changed = Signal(str)

    def __init__(self, root: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.root = Path(root or Path.cwd()).resolve()
        self.ops = FileOpsService(self.root)
        self._setup_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(250)
        self._refresh_timer.timeout.connect(self.refresh)
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Filter files…")
        self.filter_box.textChanged.connect(lambda _: self._refresh_timer.start())
        layout.addWidget(self.filter_box)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.itemActivated.connect(self._on_item_activated)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

    # --- Data -------------------------------------------------------------
    def set_root(self, root: str):
        self.root = Path(root).resolve()
        self.ops = FileOpsService(self.root)
        self.root_changed.emit(str(self.root))
        self.refresh()

    def refresh(self):
        filter_text = self.filter_box.text().lower().strip()
        self.tree.blockSignals(True)
        self.tree.clear()
        try:
            self._populate_dir(self.root, None, filter_text)
            self.tree.expandToDepth(1)
        finally:
            self.tree.blockSignals(False)

    def _populate_dir(self, directory: Path, parent_item: Optional[QTreeWidgetItem], filter_text: str):
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            entries = []
        for entry in entries:
            if entry.name.startswith('.') and entry.name not in ('.git',):
                continue
            if entry.is_dir() and entry.name in ('node_modules', '.git', '.aiw_trash', '__pycache__'):
                continue
            # filter
            if filter_text and filter_text not in entry.name.lower():
                # if folder may contain filtered items, still include folder
                if entry.is_dir():
                    # Peek into folder names
                    try:
                        if not any(filter_text in p.name.lower() for p in entry.iterdir()):
                            continue
                    except Exception:
                        continue
                else:
                    continue

            item = QTreeWidgetItem()
            item.setText(0, entry.name)
            item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            if parent_item is None:
                self.tree.addTopLevelItem(item)
            else:
                parent_item.addChild(item)

            if entry.is_dir():
                self._populate_dir(entry, item, filter_text)

    # --- Actions ----------------------------------------------------------
    def _on_item_activated(self, item: QTreeWidgetItem, _col: int):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and Path(path).is_file():
            self.file_open_requested.emit(path)

    def _on_item_changed(self, item: QTreeWidgetItem, _col: int):
        # Inline rename handling
        old_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        new_name = item.text(0)
        if old_path.name != new_name:
            try:
                new_path = self.ops.rename(old_path.relative_to(self.root), new_name)
                item.setData(0, Qt.ItemDataRole.UserRole, str(new_path))
            except Exception as e:
                QMessageBox.warning(self, "Rename Failed", str(e))
                # revert
                item.setText(0, old_path.name)

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        act_new_file = menu.addAction("New File")
        act_new_folder = menu.addAction("New Folder")
        act_rename = menu.addAction("Rename")
        act_duplicate = menu.addAction("Duplicate")
        act_delete = menu.addAction("Delete")
        menu.addSeparator()
        act_reveal = menu.addAction("Reveal in Explorer")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if not action:
            return

        target_dir = self.root
        target_path = None
        if item:
            target_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            target_dir = target_path if target_path.is_dir() else target_path.parent

        try:
            if action == act_new_file:
                name, _ = QFileDialog.getSaveFileName(self, "Create File", str(target_dir))
                if name:
                    self.ops.new_file(Path(name).relative_to(self.root))
                    self.refresh()
            elif action == act_new_folder:
                name = QFileDialog.getExistingDirectory(self, "Create Folder", str(target_dir))
                if name:
                    # If user selected an existing folder, create inside
                    base = Path(name)
                    if base.exists():
                        base = base / "New Folder"
                    rel = base.relative_to(self.root)
                    self.ops.new_folder(rel)
                    self.refresh()
            elif action == act_rename and item and target_path:
                self.tree.editItem(item, 0)
            elif action == act_duplicate and target_path:
                self.ops.duplicate(target_path.relative_to(self.root))
                self.refresh()
            elif action == act_delete and target_path:
                # Multi-select delete
                items = self.tree.selectedItems() or [item]
                for it in items:
                    p = Path(it.data(0, Qt.ItemDataRole.UserRole))
                    self.ops.delete(p.relative_to(self.root))
                self.refresh()
            elif action == act_reveal and target_path:
                rel = target_path.relative_to(self.root)
                self.ops.reveal_in_explorer(rel)
        except Exception as e:
            QMessageBox.warning(self, "Operation Failed", str(e))

    # --- Shortcuts --------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            items = self.tree.selectedItems()
            if items:
                self.tree.editItem(items[0], 0)
                return
        super().keyPressEvent(event)


__all__ = ["FileTree"]

