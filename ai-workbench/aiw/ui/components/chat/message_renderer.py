"""Lightweight Markdown-to-HTML renderer for ChatView.

Features:
- Code fences with optional language and per-block copy/collapse/inline actions
- Diff blocks with basic line coloring
- Simple tables (pipe syntax)
- Basic inline formatting and links

Dependency-free by design.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import html
import re
import uuid


@dataclass
class RenderResult:
    html: str
    blocks: Dict[str, str]  # block_id -> raw code payload


class MessageRenderer:
    def __init__(self, *, theme: str = "dark") -> None:
        self.theme = theme if theme in ("dark", "light") else "dark"

    def set_theme(self, theme: str) -> None:
        self.theme = theme if theme in ("dark", "light") else "dark"

    # --- Markdown parsing helpers -----------------------------------------
    _fence_re = re.compile(r"```([A-Za-z0-9_+-]*)\n([\s\S]*?)```", re.MULTILINE)
    _link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    _bold_re = re.compile(r"\*\*([^*]+)\*\*")
    _italic_re = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
    _inline_code_re = re.compile(r"`([^`]+)`")

    def _render_diff_html(self, raw: str) -> str:
        lines = raw.splitlines()
        out = ["<pre class='code diff'>"]
        for ln in lines:
            if ln.startswith("+++") or ln.startswith("---") or ln.startswith("@@"):
                out.append(f"<span class='meta'>{html.escape(ln)}</span>")
            elif ln.startswith("+"):
                out.append(f"<span class='add'>{html.escape(ln)}</span>")
            elif ln.startswith("-"):
                out.append(f"<span class='del'>{html.escape(ln)}</span>")
            else:
                out.append(html.escape(ln))
        out.append("</pre>")
        return "\n".join(out)

    def _render_table(self, text: str) -> Optional[str]:
        lines = [ln.rstrip() for ln in text.strip().splitlines() if ln.strip()]
        if len(lines) < 2 or "|" not in lines[0]:
            return None
        # Look for header separator consisting of dashes and pipes
        if not re.match(r"^\|?\s*-+[\s\|-]*-+\s*\|?$", lines[1]):
            return None
        def split_row(ln: str):
            parts = [c.strip() for c in ln.strip("|").split("|")]
            return parts
        header = split_row(lines[0])
        body = [split_row(ln) for ln in lines[2:]]
        html_rows = [
            "<table class='md-table'>",
            "<thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in header) + "</tr></thead>",
            "<tbody>",
        ]
        for row in body:
            html_rows.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>")
        html_rows.append("</tbody></table>")
        return "\n".join(html_rows)

    def md_to_html(self, text: str, *, collapsed_blocks: Optional[Dict[str, bool]] = None) -> RenderResult:
        collapsed_blocks = collapsed_blocks or {}
        code_blocks: Dict[str, str] = {}

        # Code fences: operate on original text to capture raw blocks
        pos = 0
        parts: list[str] = []
        for m in self._fence_re.finditer(text):
            before = text[pos:m.start()]
            parts.append(html.escape(before))
            lang = (m.group(1) or "").lower()
            raw = m.group(2)
            block_id = str(uuid.uuid4())
            code_blocks[block_id] = raw
            is_long = len(raw.splitlines()) > 30
            is_collapsed = collapsed_blocks.get(block_id, False) or is_long
            toolbar = [
                f"<a class='btn copy' href='copy://{block_id}'>Copy</a>",
                f"<a class='btn toggle' href='toggle://{block_id}'>" + ("Expand" if is_collapsed else "Collapse") + "</a>",
                f"<a class='btn action' href='action://explain/{block_id}'>Explain</a>",
                f"<a class='btn action' href='action://refine/{block_id}'>Refine</a>",
            ]
            if lang == 'diff':
                toolbar.append(f"<a class='btn action' href='action://apply_patch/{block_id}'>Apply Patch</a>")
            toolbar_html = "<div class='toolbar'>" + " ".join(toolbar) + "</div>"
            if lang == 'diff':
                body_html = self._render_diff_html(raw)
            else:
                body_html = f"<pre class='code {lang}'><code>{html.escape(raw)}</code></pre>"
            if is_collapsed:
                preview = html.escape("\n".join(raw.splitlines()[:8]))
                body = f"<div class='collapsed'><pre class='code preview'>{preview}\n…</pre></div>"
            else:
                body = body_html
            parts.append(f"<div class='code-block'>{toolbar_html}{body}</div>")
            pos = m.end()
        parts.append(html.escape(text[pos:]))

        # Inline formatting and links (best-effort) on the composed string
        safe = "".join(parts)
        safe = self._link_re.sub(lambda m: f"<a href='{html.escape(m.group(2))}'>{m.group(1)}</a>", safe)
        safe = self._bold_re.sub(r"<b>\1</b>", safe)
        safe = self._italic_re.sub(r"<i>\1</i>", safe)
        safe = self._inline_code_re.sub(r"<code>\1</code>", safe)

        # Simple table transform for non-code islands separated by blank lines
        def table_transform(fragment: str) -> str:
            unescaped = html.unescape(fragment)
            tbl = self._render_table(unescaped)
            return tbl if tbl else fragment
        final_html = "\n\n".join(table_transform(p) for p in safe.split("\n\n"))

        return RenderResult(html=final_html, blocks=code_blocks)

    # --- Message wrapper ---------------------------------------------------
    def wrap_message(self, *, role: str, content_html: str, timestamp: Optional[str] = None) -> str:
        role_class = {
            'user': 'user-msg',
            'assistant': 'assistant-msg',
            'system': 'system-msg',
        }.get(role, 'assistant-msg')
        avatar = {
            'user': '🧑',
            'assistant': '🤖',
            'system': '⚙️',
        }.get(role, '🤖')
        stamp = f"<span class='timestamp'>{html.escape(timestamp or '')}</span>" if timestamp else ""
        return (
            f"<div class='chat-msg {role_class}'>"
            f"<div class='avatar'>{avatar}</div>"
            f"<div class='bubble'><div class='meta'><span class='role'>{role.title()}</span>{stamp}</div>"
            f"<div class='content'>{content_html}</div></div>"
            f"</div>"
        )

    def base_css(self) -> str:
        """Return base CSS for chat content, tuned for readability.

        Dark theme targets a Tailwind-like palette for better contrast.
        """
        if self.theme == 'dark':
            # Tailwind-inspired slate/blue accents for dark mode
            text = '#e5e7eb'      # slate-200
            subtle = '#a1a1aa'    # zinc-400
            usr_bg = '#0f172a'    # slate-900
            usr_border = '#3b82f6'  # blue-500
            ai_bg = '#111827'     # gray-900
            ai_border = '#22c55e' # green-500
            sys_bg = '#1f2937'    # gray-800
            sys_border = '#818cf8' # indigo-400
            code_bg = '#0b1220'   # very dark blue-gray
            code = '#e2e8f0'      # slate-200
            meta = '#94a3b8'      # slate-400
        else:
            text = '#1f2937'      # gray-800
            subtle = '#6b7280'    # gray-500
            usr_bg = '#eaf2ff'
            usr_border = '#3b82f6'
            ai_bg = '#f8fafc'
            ai_border = '#16a34a'
            sys_bg = '#eef2ff'
            sys_border = '#6366f1'
            code_bg = '#f1f5f9'   # slate-100
            code = '#0f172a'      # slate-900
            meta = '#6b7280'

        return "\n".join([
            # Cascadia everywhere for consistency with the app
            f"body {{ margin:0; padding:10px; font-family:'Cascadia Code','Cascadia Mono','Segoe UI',Arial,sans-serif; color:{text}; }}",
            ".chat-msg { display:flex; gap:10px; margin:12px 8px; }",
            ".chat-msg .avatar { width:24px; height:24px; display:flex; align-items:center; justify-content:center; font-size:16px; }",
            ".chat-msg .bubble { flex:1; }",
            f".user-msg .bubble {{ background:{usr_bg}; border-left:3px solid {usr_border}; border-radius:10px; padding:10px; }}",
            f".assistant-msg .bubble {{ background:{ai_bg}; border-left:3px solid {ai_border}; border-radius:10px; padding:10px; }}",
            f".system-msg .bubble {{ background:{sys_bg}; border-left:3px solid {sys_border}; border-radius:10px; padding:10px; }}",
            f".meta {{ font-size:11px; color:{subtle}; margin-bottom:6px; display:flex; justify-content:space-between; }}",
            f".content {{ font-size:13px; line-height:1.5; color:{text}; }}",
            f"code {{ background:{code_bg}; color:{code}; padding:2px 4px; border-radius:4px; font-family:'Cascadia Code','Consolas',monospace; }}",
            f"pre.code {{ background:{code_bg}; color:{code}; padding:10px; border-radius:8px; overflow-x:auto; font-family:'Cascadia Code','Consolas',monospace; }}",
            ".code-block .toolbar { display:flex; gap:8px; margin:6px 0; }",
            ".code-block .btn { font-size:11px; text-decoration:none; padding:2px 6px; border:1px solid rgba(127,127,127,.25); border-radius:6px; }",
            ".diff .add { color:#22c55e; }",
            ".diff .del { color:#ef4444; }",
            f".diff .meta {{ color:{meta}; }}",
            ".md-table { border-collapse: collapse; font-size:12px; }",
            ".md-table th, .md-table td { border:1px solid rgba(127,127,127,.25); padding:6px 8px; }",
        ])
