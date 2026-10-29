#!/usr/bin/env python3
"""Generator for wire-headers.svg.

What an on-path observer can read, field by field, for three packets:

  TCP:        the TCP header (RFC 9293) followed by a TLS record header
              and the encrypted record. Every header field is readable,
              including the acknowledgment number.
  QUIC long:  an Initial packet (RFC 9000, 17.2.2), used during the
              handshake: version and both connection IDs are readable.
  QUIC short: a 1-RTT packet (RFC 9000, 17.3.1), used after the
              handshake: only the header form bit and the destination
              connection ID are readable. ACKs are frames inside the
              encrypted payload.

Readable fields are amber, encrypted or header-protected ones gray. Field
widths are not to scale; byte counts are under each field. The IP header
(and UDP header for QUIC) in front is left out, ports included.

Static, no animation. To change it, edit this script and run:
python3 wire-headers.gen.py
It writes ../public/animations/wire-headers.svg.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "wire-headers.svg"))

MONO = "'Space Mono', monospace"
VB_W, VB_H = 1100, 390
X0 = 150          # left edge of the packets; row labels sit left of it
BOX_H = 46
FORM_W = 14       # the header form bit, drawn as its own box

# fill, stroke, text color per category
STYLE = {
    "visible": ("#fef3c7", "#d97706", "#92400e"),
    "hidden": ("#f3f4f6", "#9ca3af", "#6b7280"),
}
# (label, subtitle, form bit or None, [(width, category, text, bytes)])
ROWS = [
    ("TCP + TLS", "every packet", None, [
        (96, "visible", "seq nr", "4"),
        (96, "visible", "ACK nr", "4"),
        (74, "visible", "flags", "2"),
        (80, "visible", "window", "2"),
        (84, "visible", "checksum", "2"),
        (70, "visible", "urgent", "2"),
        (80, "visible", "options", "0-40"),
        (90, "visible", "TLS hdr", "5"),
        (270, "hidden", "encrypted", "n"),
    ]),
    ("QUIC long", "handshake", "1", [
        (56, "hidden", "flags", "1"),
        (90, "visible", "version", "4"),
        (170, "visible", "dest conn id", "1+0-20"),
        (170, "visible", "src conn id", "1+0-20"),
        (90, "visible", "token", "n"),
        (90, "hidden", "pkt nr", "1-4"),
        (260, "hidden", "encrypted frames", "n"),
    ]),
    ("QUIC short", "all other packets", "0", [
        (56, "hidden", "flags", "1"),
        (150, "visible", "dest conn id", "0-20"),
        (100, "hidden", "pkt nr", "1-4"),
        (620, "hidden", "encrypted frames: ACK, STREAM, … + tag", "n"),
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
    y = 20 + i * 110
    parts.append(
        f'  <text x="{X0 - 14}" y="{y + 22}" text-anchor="end" '
        f'font-family="{MONO}" font-size="17" font-weight="bold" '
        f'fill="#222">{label}</text>\n'
        f'  <text x="{X0 - 14}" y="{y + 40}" text-anchor="end" '
        f'font-family="{MONO}" font-size="11" fill="#888">{subtitle}</text>\n')
    x = X0
    if form_bit is not None:
        # The header form bit: readable, says long (1) or short (0) header.
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
lx, ly = X0, 360
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
