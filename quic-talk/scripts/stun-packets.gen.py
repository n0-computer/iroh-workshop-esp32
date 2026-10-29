#!/usr/bin/env python3
"""Generator for stun-packets.svg.

What an on-path observer can read when an endpoint asks "what is my public
address?", once with STUN and once with QUIC address discovery (QAD):

  STUN request:  a Binding request (RFC 8489): message type, length, the
                 fixed magic cookie 0x2112A442 and a transaction ID. One UDP
                 datagram, all of it readable.
  STUN response: the same header plus an XOR-MAPPED-ADDRESS attribute. The
                 address is XORed with the magic cookie so that NATs don't
                 rewrite it; anyone can undo that.
  QAD:           an OBSERVED_ADDRESS frame inside an ordinary QUIC short
                 header packet, encrypted like every other frame.

Same look as wire-headers.svg: readable fields amber, encrypted or
header-protected ones gray. Field widths are not to scale; byte counts are
under each field. IP and UDP headers are left out.

Static, no animation. To change it, edit this script and run:
python3 stun-packets.gen.py
It writes ../public/animations/stun-packets.svg.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "stun-packets.svg"))

MONO = "'Space Mono', monospace"
VB_W, VB_H = 1100, 330
X0 = 150          # left edge of the packets; row labels sit left of it
BOX_H = 46
ROW_STEP = 88
FORM_W = 14       # the QUIC header form bit, drawn as its own box

# fill, stroke, text color per category
STYLE = {
    "visible": ("#fef3c7", "#d97706", "#92400e"),
    "hidden": ("#f3f4f6", "#9ca3af", "#6b7280"),
}

STUN_HEADER = [
    (90, "visible", "type", "2"),
    (70, "visible", "length", "2"),
    (130, "visible", "2112A442", "4"),
    (200, "visible", "transaction id", "12"),
]

# (label, subtitle, form bit or None, [(width, category, text, bytes)])
ROWS = [
    ("STUN", "request", None, STUN_HEADER),
    ("STUN", "response", None, STUN_HEADER + [
        (80, "visible", "attr hdr", "4"),
        (70, "visible", "family", "2"),
        (130, "visible", "port ⊕ cookie", "2"),
        (160, "visible", "IP ⊕ cookie", "4"),
    ]),
    ("QAD", "inside QUIC", "0", [
        (56, "hidden", "flags", "1"),
        (150, "visible", "dest conn id", "0-20"),
        (100, "hidden", "pkt nr", "1-4"),
        (620, "hidden", "encrypted frames: OBSERVED_ADDRESS, …", "n"),
    ]),
]


def box(x, y, w, cat, text, nbytes):
    fill, stroke, ink = STYLE[cat]
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{BOX_H}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
        f'  <text x="{x + w / 2}" y="{y + BOX_H / 2 + 5}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="13" fill="{ink}">{text}</text>\n'
        f'  <text x="{x + w / 2}" y="{y + BOX_H + 17}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="#888">{nbytes}</text>\n'
    )


parts = []
for i, (label, subtitle, form_bit, fields) in enumerate(ROWS):
    y = 12 + i * ROW_STEP
    parts.append(
        f'  <text x="{X0 - 14}" y="{y + 22}" text-anchor="end" '
        f'font-family="{MONO}" font-size="17" font-weight="bold" '
        f'fill="#222">{label}</text>\n'
        f'  <text x="{X0 - 14}" y="{y + 40}" text-anchor="end" '
        f'font-family="{MONO}" font-size="11" fill="#888">{subtitle}</text>\n')
    x = X0
    if form_bit is not None:
        fill, stroke, ink = STYLE["visible"]
        parts.append(
            f'  <rect x="{x}" y="{y}" width="{FORM_W}" height="{BOX_H}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
            f'  <text x="{x + FORM_W / 2}" y="{y + BOX_H / 2 + 5}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="13" '
            f'fill="{ink}">{form_bit}</text>\n')
        x += FORM_W
    for w, cat, text, nbytes in fields:
        parts.append(box(x, y, w, cat, text, nbytes))
        x += w

# legend
LEGEND = [
    ("visible", "readable on the wire"),
    ("hidden", "encrypted or header-protected"),
]
lx, ly = X0, 272
for cat, text in LEGEND:
    fill, stroke, _ = STYLE[cat]
    parts.append(
        f'  <rect x="{lx}" y="{ly}" width="22" height="22" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="1.5"/>\n'
        f'  <text x="{lx + 32}" y="{ly + 16}" font-family="{MONO}" '
        f'font-size="14" fill="#444">{text}</text>\n')
    lx += 32 + len(text) * 8.6 + 36
parts.append(
    f'  <text x="{X0}" y="{ly + 50}" font-family="{MONO}" font-size="12" '
    f'fill="#888">2112A442: the STUN magic cookie, same in every packet · '
    f'⊕ cookie: so NATs don\'t rewrite it, not encryption</text>\n')

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
    + "".join(parts)
    + "</svg>\n"
)
open(OUT_PATH, "w").write(svg)
