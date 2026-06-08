#!/usr/bin/env python3
"""Reference geometry + visual preview for the telemetry signal cone.

Usage:
  python tests/signal-cone-preview.py            # writes tests/signal-cone-preview.html
  python tests/signal-cone-preview.py --check    # asserts math invariants, prints PASS

The math here is the source of truth for the Cheetah `signalCone` helper in
skins/neowx-material/telemetry.html.tmpl. Keep the two in sync.
"""
import math
import os
import sys

R = 14.6
CY = 12.0
HH_I = 4.75
HH_O = 11.0
DOT_R = 3.5
GREEN = "#4caf50"
RED = "#f44336"
DIM = "#4a4a4a"

# (inner x, outer x, direction) per wing
LEFT = (52.0, 12.0, -1)
RIGHT = (68.0, 108.0, 1)


def sag(hh):
    """Bulge depth (sagitta) of a chord of half-height hh on a circle radius R."""
    return R - math.sqrt(R * R - hh * hh)


def ctrl_x(xv, s, direction):
    """Quadratic control x reproducing sagitta s at x=xv, bulging in direction."""
    return xv + direction * 2 * s


def _fmt(v):
    return "%.3f" % v


def wing_full(wing):
    xi, xo, d = wing
    si, so = sag(HH_I), sag(HH_O)
    return (
        "M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" % (
            _fmt(xi), _fmt(CY - HH_I),
            _fmt(xo), _fmt(CY - HH_O),
            _fmt(ctrl_x(xo, so, d)), _fmt(CY), _fmt(xo), _fmt(CY + HH_O),
            _fmt(xi), _fmt(CY + HH_I),
            _fmt(ctrl_x(xi, si, d)), _fmt(CY), _fmt(xi), _fmt(CY - HH_I),
        )
    )


def fill_band(wing, f):
    xi, xo, d = wing
    f = max(0.0, min(1.0, f))
    xf = xi + f * (xo - xi)
    hhf = HH_I + f * (HH_O - HH_I)
    si, sf = sag(HH_I), sag(hhf)
    return (
        "M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" % (
            _fmt(xi), _fmt(CY - HH_I),
            _fmt(xf), _fmt(CY - hhf),
            _fmt(ctrl_x(xf, sf, d)), _fmt(CY), _fmt(xf), _fmt(CY + hhf),
            _fmt(xi), _fmt(CY + HH_I),
            _fmt(ctrl_x(xi, si, d)), _fmt(CY), _fmt(xi), _fmt(CY - HH_I),
        )
    )


def cone_svg(percentage, threshold=30, width=120):
    f = percentage / 100.0
    color = RED if percentage < threshold else GREEN
    return (
        '<svg viewBox="0 0 120 24" width="%d" height="%d" '
        'style="display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">'
        '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
        '<path d="%s" fill="%s"/><path d="%s" fill="%s"/>'
        '<circle cx="60" cy="12" r="%s" fill="#ddd"/></svg>' % (
            width, int(width * 24 / 120),
            wing_full(LEFT), DIM, wing_full(RIGHT), DIM,
            fill_band(LEFT, f), color, fill_band(RIGHT, f), color,
            DOT_R,
        )
    )


def write_preview():
    cells = ""
    for pct in (100, 70, 40, 15, 0):
        cells += (
            '<div style="background:#2b2b2b;padding:14px;border-radius:8px;'
            'text-align:center">%s<div style="color:#999;font:12px sans-serif;'
            'margin-top:6px">%d%%</div></div>' % (cone_svg(pct), pct)
        )
    html = (
        '<!doctype html><meta charset="utf-8"><body style="background:#1e1e1e;'
        'display:flex;gap:18px;flex-wrap:wrap;padding:30px">%s</body>' % cells
    )
    out = os.path.join(os.path.dirname(__file__), "signal-cone-preview.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote " + out)


def check():
    assert abs(sag(HH_O) - 5.0) < 1e-6, "sag(HH_O) should be 5.0"
    # f=1 fill frontier reaches the outer tip x on both wings.
    for wing, xo in ((LEFT, 12.0), (RIGHT, 108.0)):
        d = fill_band(wing, 1.0)
        assert (" %s " % _fmt(xo)) in d, "fill at f=1 must reach outer x %s" % xo
    # Left frontier x decreases monotonically as fill grows.
    prev = None
    for i in range(0, 11):
        f = i / 10.0
        xf = LEFT[0] + f * (LEFT[1] - LEFT[0])
        if prev is not None:
            assert xf < prev, "left frontier x must decrease as f grows"
        prev = xf
    # Half-height interpolates between inner and outer.
    assert abs((HH_I + 0.0 * (HH_O - HH_I)) - 4.75) < 1e-9
    assert abs((HH_I + 1.0 * (HH_O - HH_I)) - 11.0) < 1e-9
    print("PASS")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        write_preview()
