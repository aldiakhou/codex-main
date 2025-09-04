from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath, QPolygonF

from .design_tokens import get_tokens


def _mk_canvas(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def _pen(color: QColor, size: int) -> QPen:
    p = QPen(color)
    p.setWidthF(max(1.2, size * 0.10))
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def make_icon(name: str, theme: str = "dark", size: int = 18) -> QIcon:
    """Return a small, theme-aware vector-style icon drawn with QPainter.

    Avoids external assets; shapes are intentionally simple and crisp at 18–20px.
    Names: 'folder-open', 'save', 'send', 'diff', 'stop', 'bulb'
    """
    tokens = get_tokens(theme)
    fg = QColor(tokens.colors.palette.get("text", "#e6e8eb"))
    accent = QColor(tokens.colors.palette.get("accent", "#4f8cff"))

    pm = _mk_canvas(size)
    p = QPainter(pm)
    try:
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        p.setPen(_pen(fg, size))

        s = float(size)
        inset = s * 0.18
        mid = s * 0.5

        if name == 'folder-open':
            # folder body
            rect = pm.rect().adjusted(int(s*0.12), int(s*0.42), -int(s*0.12), -int(s*0.14))
            path = QPainterPath()
            path.addRoundedRect(rect, s*0.12, s*0.12)
            p.drawPath(path)
            # tab flap (polyline)
            p.setPen(_pen(accent, size))
            poly = QPolygonF([
                QPointF(s*0.14, s*0.36), QPointF(s*0.44, s*0.36), QPointF(s*0.54, s*0.46), QPointF(s*0.86, s*0.46)
            ])
            p.drawPolyline(poly)

        elif name == 'save':
            # tray
            p.drawRoundedRect(int(s*0.18), int(s*0.60), int(s*0.64), int(s*0.22), s*0.08, s*0.08)
            # arrow
            p.setPen(_pen(accent, size))
            p.drawLine(int(mid), int(s*0.20), int(mid), int(s*0.56))
            poly = QPolygonF([
                QPointF(mid, s*0.56), QPointF(mid - s*0.12, s*0.44), QPointF(mid + s*0.12, s*0.44), QPointF(mid, s*0.56)
            ])
            p.drawPolyline(poly)

        elif name == 'send':
            path = QPainterPath()
            path.moveTo(s*0.16, s*0.18)
            path.lineTo(s*0.84, s*0.50)
            path.lineTo(s*0.16, s*0.82)
            path.closeSubpath()
            p.setPen(_pen(accent, size))
            p.drawPath(path)

        elif name == 'diff':
            # minus
            p.drawLine(int(s*0.16), int(s*0.34), int(s*0.46), int(s*0.34))
            # plus
            p.setPen(_pen(accent, size))
            p.drawLine(int(s*0.60), int(s*0.30), int(s*0.88), int(s*0.30))
            p.drawLine(int(s*0.74), int(s*0.16), int(s*0.74), int(s*0.44))
            # divider
            p.setPen(_pen(fg, size))
            p.drawLine(int(s*0.50), int(s*0.16), int(s*0.50), int(s*0.84))

        elif name == 'stop':
            p.setPen(_pen(accent, size))
            p.drawRoundedRect(int(s*0.26), int(s*0.26), int(s*0.48), int(s*0.48), s*0.10, s*0.10)

        elif name == 'bulb':
            # bulb outline
            path = QPainterPath()
            path.addEllipse(QPointF(mid, s*0.42), s*0.22, s*0.22)
            p.drawPath(path)
            # base
            p.setPen(_pen(accent, size))
            p.drawRoundedRect(int(s*0.40), int(s*0.62), int(s*0.20), int(s*0.16), s*0.06, s*0.06)
        else:
            # fallback: a simple dot
            p.setPen(_pen(accent, size))
            p.drawEllipse(QPointF(mid, mid), s*0.12, s*0.12)
    finally:
        p.end()
    return QIcon(pm)


__all__ = ["make_icon"]
