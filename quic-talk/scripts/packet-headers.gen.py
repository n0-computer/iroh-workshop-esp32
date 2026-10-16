#!/usr/bin/env python3
"""Generator for packet-headers.svg.

What a middlebox sees in one UDP datagram, for three protocols, one row each:

  WireGuard transport data: type + reserved bytes, receiver index, counter,
                            then ciphertext and tag.
  Tailscale disco:          magic "TS💬", sender disco key, nonce, sealed box
                            (layout from tailscale's disco/disco.go).
  QUIC short header:        header-form bit, destination connection ID, then
                            header-protected packet number and ciphertext
                            (fixed bit greased, RFC 9287).

Each field is colored by what an observer learns from it: the same in every
packet (red), the same or predictable within a flow (amber), or random-looking
(gray). Field widths are not to scale; the byte counts are under each field.

Static, no animation. To change it, edit this script and run:
python3 packet-headers.gen.py
It writes ../public/animations/packet-headers.svg.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "packet-headers.svg"))

MONO = "'Space Mono', monospace"
VB_W, VB_H = 1060, 400
X0 = 220          # left edge of the packets; row labels sit left of it
BOX_H = 46

# fill, stroke, text color per category
STYLE = {
    "fixed": ("#fee2e2", "#dc2626", "#991b1b"),
    "flow": ("#fef3c7", "#d97706", "#92400e"),
    "random": ("#f3f4f6", "#9ca3af", "#6b7280"),
}

# (label, [(width, category, text, bytes)])
ROWS = [
    ("WireGuard", [
        (130, "fixed", "04 00 00 00", "4"),
        (130, "flow", "receiver", "4"),
        (150, "flow", "counter +1", "8"),
        (300, "random", "encrypted IP packet", "n"),
        (110, "random", "tag", "16"),
    ]),
    ("disco", [
        (200, "fixed", "54 53 F0 9F 92 AC", "6"),
        (230, "flow", "sender disco key", "32"),
        (150, "random", "nonce", "24"),
        (240, "random", "sealed box", "n"),
    ]),
    ("QUIC", [
        (90, "random", "flags", "1"),
        (180, "flow", "connection id", "0-20"),
        (140, "random", "packet nr", "1-4"),
        (410, "random", "encrypted frames + tag", "n"),
    ]),
]

SUBTITLE = {
    "WireGuard": "transport data",
    "disco": "Tailscale hole punching",
    "QUIC": "short header, greased",
}


def box(x, y, w, cat, text, nbytes, text_x=None):
    fill, stroke, ink = STYLE[cat]
    if text_x is None:
        text_x = x + w / 2
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{BOX_H}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
        f'  <text x="{text_x}" y="{y + BOX_H / 2 + 6}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="16" fill="{ink}">{text}</text>\n'
        f'  <text x="{x + w / 2}" y="{y + BOX_H + 18}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="12" fill="#888">{nbytes}</text>\n'
    )


parts = []
for i, (label, fields) in enumerate(ROWS):
    y = 20 + i * 105
    parts.append(
        f'  <text x="{X0 - 16}" y="{y + 22}" text-anchor="end" '
        f'font-family="{MONO}" font-size="18" font-weight="bold" '
        f'fill="#222">{label}</text>\n'
        f'  <text x="{X0 - 16}" y="{y + 40}" text-anchor="end" '
        f'font-family="{MONO}" font-size="11" fill="#888">'
        f'{SUBTITLE[label]}</text>\n')
    x = X0
    for w, cat, text, nbytes in fields:
        # QUIC's first byte: center the text right of the header-form bit.
        text_x = x + 14 + (w - 14) / 2 if text == "flags" else None
        parts.append(box(x, y, w, cat, text, nbytes, text_x))
        x += w
    if label == "QUIC":
        # The header-form bit: the only bit that is the same in every packet.
        fill, stroke, ink = STYLE["fixed"]
        parts.append(
            f'  <rect x="{X0}" y="{y}" width="14" height="{BOX_H}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
            f'  <text x="{X0 + 7}" y="{y + BOX_H / 2 + 5}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="13" fill="{ink}">0</text>\n')

# legend
LEGEND = [
    ("fixed", "same in every packet"),
    ("flow", "same or predictable within a flow"),
    ("random", "looks random"),
]
lx, ly = X0, 350
for cat, text in LEGEND:
    fill, stroke, _ = STYLE[cat]
    parts.append(
        f'  <rect x="{lx}" y="{ly}" width="22" height="22" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="1.5"/>\n'
        f'  <text x="{lx + 32}" y="{ly + 16}" font-family="{MONO}" '
        f'font-size="14" fill="#444">{text}</text>\n')
    lx += 32 + len(text) * 8.6 + 36

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
    + "".join(parts)
    + "</svg>\n"
)
open(OUT_PATH, "w").write(svg)
