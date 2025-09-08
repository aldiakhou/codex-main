"""
TurnDiffTracker: detect file changes (added/modified/deleted/renamed) between two snapshots.

Snapshot format: { rel_path: { size: float, mtime: float, sha1?: str } }
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
import fnmatch


def build_snapshot(
    root: str,
    ignore: Optional[Iterable[str]] = None,
    hash_limit_bytes: Optional[int] = 128 * 1024,
    max_files: Optional[int] = None,
    file_size_limit_bytes: Optional[int] = None,
) -> Dict[str, Dict[str, float]]:
    base = Path(root)
    snap: Dict[str, Dict[str, float]] = {}
    ignore = list(ignore or [])
    count = 0
    for p in base.rglob('*'):
        if not p.is_file():
            continue
        rel = str(p.relative_to(base).as_posix())
        if _ignored(rel, ignore):
            continue
        try:
            st = p.stat()
            if file_size_limit_bytes is not None and st.st_size > file_size_limit_bytes:
                # Skip very large files entirely
                continue
            entry = {"size": float(st.st_size), "mtime": float(st.st_mtime)}
            if hash_limit_bytes is not None and st.st_size <= hash_limit_bytes:
                entry["sha1"] = _sha1(p)
            snap[rel] = entry
            count += 1
            if max_files is not None and count >= max_files:
                break
        except Exception:
            continue
    return snap


def diff_snapshots(before: Dict[str, Dict[str, float]], after: Dict[str, Dict[str, float]]) -> List[dict]:
    out: List[dict] = []
    before_keys = set(before.keys())
    after_keys = set(after.keys())
    added = after_keys - before_keys
    removed = before_keys - after_keys
    common = before_keys & after_keys

    # direct changes
    for k in sorted(common):
        b = before[k]
        a = after[k]
        if b.get("size") != a.get("size") or b.get("mtime") != a.get("mtime"):
            out.append({"path": k, "status": "modified", "before": b, "after": a})

    # rename detection: match removed->added pairs by sha1 or size
    added_meta = {k: after[k] for k in added}
    removed_meta = {k: before[k] for k in removed}
    matched_added: Set[str] = set()
    matched_removed: Set[str] = set()

    # sha1 match first
    index_by_sha = {}
    for k, m in removed_meta.items():
        h = m.get("sha1")
        if h:
            index_by_sha.setdefault(h, []).append(k)
    for k, m in added_meta.items():
        h = m.get("sha1")
        if h and h in index_by_sha and index_by_sha[h]:
            src = index_by_sha[h].pop(0)
            out.append({"path": k, "status": "renamed", "from": src, "to": k})
            matched_added.add(k)
            matched_removed.add(src)

    # size match fallback
    index_by_size = {}
    for k, m in removed_meta.items():
        if k in matched_removed:
            continue
        s = m.get("size")
        index_by_size.setdefault(s, []).append(k)
    for k, m in added_meta.items():
        if k in matched_added:
            continue
        s = m.get("size")
        if s in index_by_size and index_by_size[s]:
            src = index_by_size[s].pop(0)
            out.append({"path": k, "status": "renamed", "from": src, "to": k})
            matched_added.add(k)
            matched_removed.add(src)

    # remaining added/removed as new/deleted
    for k in sorted(added - matched_added):
        out.append({"path": k, "status": "added", "size": after[k].get("size")})
    for k in sorted(removed - matched_removed):
        out.append({"path": k, "status": "deleted"})

    return out


def _sha1(p: Path) -> str:
    h = hashlib.sha1()
    with p.open('rb') as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _ignored(rel: str, patterns: Iterable[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat):
            return True
    return False
