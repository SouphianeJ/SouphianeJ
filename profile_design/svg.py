"""Shared palette and small, escaped SVG building blocks."""

import re
import textwrap
from html import escape

PAPER = "#f1efe7"
SURFACE = "#fffdf5"
INK = "#0a0a0a"
CYAN = "#00e5ff"
LIME = "#c6ff00"
PINK = "#ff4fc8"
RED = "#ff3b1f"
MUTED = "#5c5750"


def text(x, y, value, size=22, bold=False, mono=False, color=INK):
    font = "monospace" if mono else "Arial,Helvetica,sans-serif"
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="{font}" font-weight="{800 if bold else 400}">{escape(str(value))}</text>'
    )


def box(x, y, width, height, fill, stroke=None, shadow=0):
    offset = (
        f'<rect x="{x + shadow}" y="{y + shadow}" width="{width}" height="{height}" fill="{INK}"/>'
        if shadow
        else ""
    )
    border = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
    return offset + (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}"{border}/>'
    )


def line(x, y, x2, y2, color=INK, dash=""):
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="M{x} {y}L{x2} {y2}" stroke="{color}" stroke-width="2" fill="none"{dashed}/>'


def plain(value):
    return value.replace("**", "").replace("`", "")


def paragraph(value, x, y, width=82, size=22, color=INK, bold=False, leading=32):
    result = []
    for row in textwrap.wrap(plain(value), width, break_long_words=False, break_on_hyphens=False):
        result.append(text(x, y, row, size, bold, color=color))
        y += leading
    return "".join(result), y


def document(content, height, title, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" '
        f'viewBox="0 0 1000 {height}" role="img"><title>{escape(title)}</title>'
        f"<style>{css}</style>{box(0, 0, 1000, height, PAPER)}{content}</svg>"
    )


def nested(svg, x, y, width, height, viewbox):
    opening = (
        f'<svg xmlns="http://www.w3.org/2000/svg" x="{x}" y="{y}" '
        f'width="{width}" height="{height}" viewBox="{viewbox}" shape-rendering="crispEdges">'
    )
    return re.sub(r"<svg\b[^>]*>", lambda _: opening, svg, count=1)


def static_version(svg):
    # CSS-less SVG retains complete content, without duplicated mouth frames.
    svg = re.sub(r"<style>.*?</style>", "", svg, flags=re.S)
    return re.sub(r'<g class="game-mouth-closed[^"]*">.*?</g>', "", svg, flags=re.S)
