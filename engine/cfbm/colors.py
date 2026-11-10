"""Team colors that stay readable: WCAG contrast checks with alt-color and lighten/darken fallbacks."""

from __future__ import annotations

import colorsys
import re

INK = "#0b1220"
_HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _parse(h: str | None) -> tuple[float, float, float] | None:
    m = _HEX.match((h or "").strip())
    if not m:
        return None
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb)


def _lum(rgb: tuple[float, float, float]) -> float:
    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a_hex: str, b_hex: str) -> float:
    a, b = _parse(a_hex), _parse(b_hex)
    if a is None or b is None:
        return 1.0
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _shift(rgb: tuple[float, float, float], toward_dark: bool, bg: str, need: float) -> str:
    h, l, s = colorsys.rgb_to_hls(*rgb)
    for _ in range(40):
        cand = _hex(colorsys.hls_to_rgb(h, l, s))
        if contrast(cand, bg) >= need:
            return cand
        l = max(0.0, l - 0.05) if toward_dark else min(1.0, l + 0.05)
    return INK if toward_dark else "#ffffff"


def _pick(bg: str, primary: str | None, alt: str | None, need: float) -> str:
    p = _parse(primary)
    if p is None:
        return INK if _lum(_parse(bg) or (1, 1, 1)) > 0.5 else "#f3f5f7"
    if contrast(_hex(p), bg) >= need:
        return _hex(p)
    a = _parse(alt)
    if a is not None and contrast(_hex(a), bg) >= need:
        return _hex(a)
    bg_light = _lum(_parse(bg) or (1, 1, 1)) > 0.5
    return _shift(p, toward_dark=bg_light, bg=bg, need=need)


def fill_for_white_text(primary: str | None, alt: str | None) -> str:
    """A team fill that white text can sit on (4.5:1)."""
    return _pick("#ffffff", primary, alt, 4.5)


def text_on(bg_hex: str, primary: str | None, alt: str | None) -> str:
    """A team color usable as text on the given card background (4.5:1)."""
    return _pick(bg_hex, primary, alt, 4.5)


def bar_on(bg_hex: str, primary: str | None) -> str:
    """The team's own color, shifted only in lightness until it shows on the card (3:1 for graphics)."""
    p = _parse(primary)
    if p is None:
        return "#8e9aab"
    if contrast(_hex(p), bg_hex) >= 3:
        return _hex(p)
    return _shift(p, toward_dark=_lum(_parse(bg_hex) or (1, 1, 1)) > 0.5, bg=bg_hex, need=3)
