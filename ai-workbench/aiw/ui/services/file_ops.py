"""File operations service with safe wrappers and undo queue.

Provides basic file operations without relying on any backend:
- new_file, new_folder, rename, duplicate, delete (to trash), reveal_in_explorer
- simple undo stack for last N operations (delete/move/rename/duplicate)

All operations are best-effort and raise exceptions on unrecoverable errors.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Union
import shutil
import os
import sys
import subprocess


@dataclass
class UndoOp:
    kind: str  # 'delete', 'move', 'rename', 'duplicate'
    src: Path
    dst: Optional[Path] = None


class FileOpsService:
    def __init__(self, root: Union[str, Path], undo_size: int = 50):
        self.root = Path(root).resolve()
        self.undo_stack: List[UndoOp] = []
        self.undo_size = undo_size
        self.trash_dir = self.root / ".aiw_trash"
        try:
            self.trash_dir.mkdir(exist_ok=True)
        except Exception:
            pass

    # --- Helpers ---------------------------------------------------------
    def _push_undo(self, op: UndoOp):
        self.undo_stack.append(op)
        if len(self.undo_stack) > self.undo_size:
            self.undo_stack.pop(0)

    def _ensure_parent(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_within_root(self, path: Path):
        p = path.resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("Path outside workspace root")

    # --- Operations ------------------------------------------------------
    def new_file(self, rel_path: Union[str, Path]) -> Path:
        path = (self.root / Path(rel_path)).resolve()
        self._ensure_within_root(path)
        if path.exists():
            raise FileExistsError(f"File already exists: {path}")
        self._ensure_parent(path)
        path.write_text("")
        # undo of new_file: delete created file
        self._push_undo(UndoOp(kind='delete', src=path, dst=None))
        return path

    def new_folder(self, rel_path: Union[str, Path]) -> Path:
        path = (self.root / Path(rel_path)).resolve()
        self._ensure_within_root(path)
        path.mkdir(parents=True, exist_ok=False)
        # undo of new_folder: delete folder (if empty)
        self._push_undo(UndoOp(kind='delete', src=path, dst=None))
        return path

    def rename(self, rel_src: Union[str, Path], new_name: str) -> Path:
        src = (self.root / Path(rel_src)).resolve()
        self._ensure_within_root(src)
        if not src.exists():
            raise FileNotFoundError(src)
        dst = src.with_name(new_name)
        self._ensure_within_root(dst)
        src.rename(dst)
        self._push_undo(UndoOp(kind='rename', src=dst, dst=src))
        return dst

    def move(self, rel_src: Union[str, Path], rel_dst_dir: Union[str, Path]) -> Path:
        src = (self.root / Path(rel_src)).resolve()
        dst_dir = (self.root / Path(rel_dst_dir)).resolve()
        self._ensure_within_root(src)
        self._ensure_within_root(dst_dir)
        if not src.exists():
            raise FileNotFoundError(src)
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        shutil.move(str(src), str(dst))
        self._push_undo(UndoOp(kind='move', src=dst, dst=src))
        return dst

    def duplicate(self, rel_src: Union[str, Path], rel_dst: Optional[Union[str, Path]] = None) -> Path:
        src = (self.root / Path(rel_src)).resolve()
        self._ensure_within_root(src)
        if not src.exists():
            raise FileNotFoundError(src)
        if rel_dst is None:
            base = src.with_suffix('')
            ext = src.suffix
            i = 1
            while True:
                candidate = Path(f"{base.name} copy {i}{ext}")
                candidate_path = src.parent / candidate
                if not candidate_path.exists():
                    rel_dst = candidate_path.relative_to(self.root)
                    break
                i += 1
        dst = (self.root / Path(rel_dst)).resolve()
        self._ensure_within_root(dst)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            self._ensure_parent(dst)
            shutil.copy2(src, dst)
        # undo duplicate = delete the duplicate
        self._push_undo(UndoOp(kind='delete', src=dst))
        return dst

    def delete(self, rel_path: Union[str, Path]) -> Path:
        path = (self.root / Path(rel_path)).resolve()
        self._ensure_within_root(path)
        if not path.exists():
            raise FileNotFoundError(path)
        # Move to workspace trash
        i = 0
        trash_candidate = self.trash_dir / path.name
        while trash_candidate.exists():
            i += 1
            trash_candidate = self.trash_dir / f"{path.stem} ({i}){path.suffix}"
        shutil.move(str(path), str(trash_candidate))
        # undo delete = move back
        self._push_undo(UndoOp(kind='move', src=trash_candidate, dst=path))
        return trash_candidate

    def reveal_in_explorer(self, rel_path: Union[str, Path]):
        path = (self.root / Path(rel_path)).resolve()
        self._ensure_within_root(path)
        try:
            if sys.platform.startswith('win'):
                os.startfile(path if path.is_dir() else path.parent)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path if path.is_dir() else path.parent])
            else:
                subprocess.run(['xdg-open', path if path.is_dir() else path.parent])
        except Exception:
            # non-fatal
            pass

    # --- Undo ------------------------------------------------------------
    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        op = self.undo_stack.pop()
        try:
            if op.kind == 'delete':
                # delete src
                if op.src.is_dir():
                    shutil.rmtree(op.src)
                else:
                    try:
                        op.src.unlink(missing_ok=False)
                    except TypeError:
                        if op.src.exists():
                            op.src.unlink()
            elif op.kind in ('move', 'rename'):
                if op.dst is None:
                    return False
                self._ensure_parent(op.dst)
                shutil.move(str(op.src), str(op.dst))
            elif op.kind == 'duplicate':
                # same as delete of duplicate
                if op.src.is_dir():
                    shutil.rmtree(op.src)
                else:
                    try:
                        op.src.unlink(missing_ok=False)
                    except TypeError:
                        if op.src.exists():
                            op.src.unlink()
            else:
                return False
            return True
        except Exception:
            return False

__all__ = ["FileOpsService"]

