#!/usr/bin/env python3
"""Generator for middleboxes.svg.

Alice (a phone) and Bob (a server) on the same level, with the boxes a
packet typically passes in between arranged on an arc above them: home
router, carrier-grade NAT, firewall, traffic shaper, load balancer. Next to
each: what it does, and what it reads to do it.

No keys and no iroh here: this comes before iroh is introduced. Phone,
router and rack icons follow hole-punching.gen.py so the figures look alike.

Static, no animation. Edit this script and run:  python3 middleboxes.gen.py
Writes ../public/animations/middleboxes.svg.
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "middleboxes.svg"))

MONO = "'Space Mono', monospace"
INDIGO, AMBER, GRAY, INK, BLUE = "#6366f1", "#d97706", "#888", "#111", "#2563eb"
VB_W, VB_H = 1100, 450

# the arc: half an ellipse from Alice to Bob
CX, BASE_Y = 550, 330
RX, RY = 420, 230
ALICE_X, BOB_X = CX - RX, CX + RX

# (angle in degrees on the arc, icon, title, what it does, what it reads,
#  caption placement)
BOXES = [
    (150, "router", "home router", "rewrites addresses", "IPs · ports", "left"),
    (120, "rack", "carrier NAT", "rewrites addresses", "IPs · ports", "above"),
    (90, "rack", "firewall", "drops what looks odd", "ports · flags", "above"),
    (60, "rack", "traffic shaper", "slows some apps", "ports · sizes", "above"),
    (30, "rack", "load balancer", "picks a server", "IPs · ports", "right"),
]


def phone(cx, top):
    pw, ph = 50, 92
    px0 = cx - pw / 2
    return f'''  <rect x="{px0}" y="{top}" width="{pw}" height="{ph}" rx="9" fill="#eee" stroke="{INDIGO}" stroke-width="1.5"/>
  <rect x="{px0+3}" y="{top+3}" width="{pw-6}" height="{ph-6}" rx="6" fill="#eee" stroke="{INDIGO}" stroke-width="1"/>
  <circle cx="{cx}" cy="{top+8}" r="1.6" fill="{GRAY}"/>'''


def router(cx, cy):
    bx, by, bw, bh = cx - 30, cy - 20, 60, 40
    return f'''  <polyline points="{bx},{by+bh-5} {bx-10},{by+bh-5} {bx-10},{by-8}" fill="none" stroke="{GRAY}" stroke-width="1.5"/>
  <circle cx="{bx-10}" cy="{by-10}" r="1.5" fill="{GRAY}"/>
  <polyline points="{bx+bw},{by+bh-5} {bx+bw+10},{by+bh-5} {bx+bw+10},{by-8}" fill="none" stroke="{GRAY}" stroke-width="1.5"/>
  <circle cx="{bx+bw+10}" cy="{by-10}" r="1.5" fill="{GRAY}"/>
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3" fill="#eee" stroke="{GRAY}" stroke-width="1.5"/>
  <circle cx="{cx+20}" cy="{by+bh-6}" r="1.5" fill="{AMBER}"/>'''


def rack(cx, cy):
    """A 1U rack unit, like the relay icon in the other figures."""
    bx, by, bw, bh = cx - 32, cy - 9, 64, 18
    s = [f'  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="2" fill="#eee" stroke="{GRAY}" stroke-width="1.5"/>',
         f'  <line x1="{bx+16}" y1="{by+3}" x2="{bx+16}" y2="{by+bh-3}" stroke="{GRAY}" stroke-width="1"/>',
         f'  <circle cx="{bx+6}" cy="{by+6}" r="1.5" fill="{AMBER}"/>',
         f'  <circle cx="{bx+6}" cy="{by+12}" r="1.5" fill="{GRAY}"/>']
    for i in range(6):
        vx = bx + 24 + i * 5
        s.append(f'  <line x1="{vx}" y1="{by+4}" x2="{vx}" y2="{by+bh-4}" stroke="{GRAY}" stroke-width="1"/>')
    return "\n".join(s)


def caption(x, y, anchor, title, does, reads):
    return (
        f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="14" font-weight="bold" fill="{INK}">{title}</text>\n'
        f'  <text x="{x}" y="{y + 19}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="12" fill="#444">{does}</text>\n'
        f'  <text x="{x}" y="{y + 36}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="12" fill="{GRAY}">reads: {reads}</text>')


def name(cx, y, text):
    return (f'  <text x="{cx}" y="{y}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="16" fill="{INDIGO}">{text}</text>')


parts = [
    f'  <path d="M {ALICE_X} {BASE_Y} A {RX} {RY} 0 0 1 {BOB_X} {BASE_Y}" '
    f'fill="none" stroke="{BLUE}" stroke-width="1.5"/>',
    phone(ALICE_X, BASE_Y),
    name(ALICE_X, BASE_Y + 116, "Alice"),
]

# Bob: a server, three rack units stacked
for i in range(3):
    parts.append(rack(BOB_X, BASE_Y + 10 + i * 21))
parts.append(name(BOB_X, BASE_Y + 116, "Bob"))

for angle, icon, title, does, reads, place in BOXES:
    a = math.radians(angle)
    x = CX + RX * math.cos(a)
    y = BASE_Y - RY * math.sin(a)
    parts.append(router(x, y) if icon == "router" else rack(x, y))
    if place == "above":
        top = y - 34 if icon == "rack" else y - 54
        parts.append(caption(x, top - 36, "middle", title, does, reads))
    elif place == "left":
        parts.append(caption(x - 52, y - 10, "end", title, does, reads))
    else:
        parts.append(caption(x + 46, y - 10, "start", title, does, reads))

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
    + "\n".join(parts)
    + "\n</svg>\n"
)
open(OUT_PATH, "w").write(svg)
