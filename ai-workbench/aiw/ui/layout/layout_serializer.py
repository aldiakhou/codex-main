"""LayoutSerializer: Save/restore PaneManager split tree and tab stacks.

Schema examples:
- Stack with tabs
  {"type":"stack","tabs":[{"id":"editor","title":"Editor","file_path":null,"active":true}]}

- Split of two stacks
  {"type":"split","orientation":"horizontal","sizes":[1,1],"children":[stack1, stack2]}
"""
from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter


class LayoutSerializer:
    @staticmethod
    def serialize(pm) -> Dict[str, Any]:
        def serialize_widget(widget):
            if isinstance(widget, QSplitter):
                orient = 'horizontal' if widget.orientation() == Qt.Orientation.Horizontal else 'vertical'
                children = [serialize_widget(widget.widget(i)) for i in range(widget.count())]
                sizes = widget.sizes()
                return {
                    'type': 'split',
                    'orientation': orient,
                    'sizes': sizes,
                    'children': children,
                }
            # TabStack
            stack = widget
            tabs = []
            current = stack.tab_widget.currentIndex()
            for i in range(stack.tab_widget.count()):
                w = stack.tab_widget.widget(i)
                tab_id = pm._get_tab_id_for_widget(w)
                tab = pm._tabs.get(tab_id) if tab_id else None
                tabs.append({
                    'id': tab_id or f"anon_{i}",
                    'title': stack.tab_widget.tabText(i),
                    'file_path': getattr(tab, 'file_path', None) if tab else None,
                    'is_modified': getattr(tab, 'is_modified', False) if tab else False,
                    'active': i == current,
                })
            return {'type': 'stack', 'tabs': tabs}

        root = pm._root_container
        data = serialize_widget(root)
        return data

    @staticmethod
    def restore(pm, state: Dict[str, Any], registry: Dict[str, Any]):
        # Clear to a single stack root
        from PySide6.QtWidgets import QVBoxLayout
        # Remove existing root
        layout = pm.layout()
        if isinstance(layout, QVBoxLayout) and pm._root_container is not None:
            pm._root_container.setParent(None)
            pm._stacks.clear()

        def make_stack():
            stack = pm._create_stack()
            return stack

        def restore_node(node):
            ntype = node.get('type')
            if ntype == 'split':
                orientation = Qt.Orientation.Horizontal if node.get('orientation') == 'horizontal' else Qt.Orientation.Vertical
                splitter = QSplitter(orientation, pm)
                for child in node.get('children', []):
                    w = restore_node(child)
                    splitter.addWidget(w)
                sizes = node.get('sizes') or []
                if sizes and len(sizes) == splitter.count():
                    splitter.setSizes(sizes)
                return splitter
            else:
                stack = make_stack()
                # Populate tabs
                active_idx = 0
                for i, t in enumerate(node.get('tabs', [])):
                    tab_id = t.get('id')
                    title = t.get('title', 'untitled')
                    file_path = t.get('file_path')
                    # Try to restore file tabs
                    if file_path and Path(file_path).exists():
                        pm._active_stack = stack
                        pm.open_file_tab(file_path)
                    else:
                        # Non-file tab: use factory if available
                        factory = registry.get(tab_id)
                        if callable(factory):
                            pm._active_stack = stack
                            widget = factory()
                            # Register under tab_id for future reuse
                            pm._tabs[tab_id] = LayoutSerializer._create_panetab(pm, tab_id, title, widget)
                            stack.tab_widget.addTab(widget, title)
                    if t.get('active'):
                        active_idx = i
                if stack.tab_widget.count() > 0:
                    stack.tab_widget.setCurrentIndex(min(active_idx, stack.tab_widget.count() - 1))
                return stack

        new_root = restore_node(state or {'type': 'stack', 'tabs': []})
        pm._replace_root(new_root)
        pm._active_stack = pm._stacks[0] if pm._stacks else None

    # Helper to create PaneTab for non-file restoration
    @staticmethod
    def _create_panetab(pm, tab_id, title, widget):
        from .pane_manager import PaneTab
        return PaneTab(id=tab_id, title=title, widget=widget)
