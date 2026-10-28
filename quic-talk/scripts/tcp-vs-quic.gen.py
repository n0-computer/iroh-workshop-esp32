#!/usr/bin/env python3
"""Generator for tcp-works.svg and quic-works.svg.

Two slides with the same layout: a sender on the left, a receiver on the
right, the network between them, and a dashed line between user space and
the kernel across both sides.

  TCP:  the application writes bytes to a file descriptor; send buffer,
        segmentation, loss recovery, congestion control, reassembly, ACKs
        and flow control all live in the kernel. TLS, if any, is a library
        in user space on top.
  QUIC: the same jobs, plus encryption and per-stream buffers, live in a
        library in user space. The kernel only moves UDP datagrams.

Boxes are colored by what they do: encryption (amber), the transport itself
(indigo), everything else (gray). Rows line up between the two diagrams, so
flipping slides shows the boxes moving above the line.

Static, no animation. To change it, edit this script and run:
python3 tcp-vs-quic.gen.py
It writes ../public/animations/tcp-works.svg and quic-works.svg.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "public", "animations"))

MONO = "'Space Mono', monospace"
VB_W, VB_H = 1100, 560
SIDE_W = 400
SIDES = {"sender": 40, "receiver": VB_W - 40 - SIDE_W}
MID_X = VB_W / 2
TOP = 56
ROW_H, GAP = 46, 10
BOUNDARY_GAP = 34

# fill, stroke, text color per category
STYLE = {
    "crypto": ("#fef3c7", "#d97706", "#92400e"),
    "transport": ("#e0e7ff", "#6366f1", "#3730a3"),
    "plain": ("#f3f4f6", "#9ca3af", "#374151"),
}

LINE = "---"  # the user space / kernel boundary

# per diagram, per side: rows of (category, title, subtitle), top to bottom
DIAGRAMS = {
    "tcp-works": {
        "wire": "TCP segments · headers in plaintext",
        "sender": [
            ("plain", "application", "write(fd, bytes)"),
            ("crypto", "TLS library", "encrypt · optional"),
            LINE,
            ("transport", "send buffer", "bytes not yet acked"),
            ("transport", "segmentation", "bytes → packets"),
            ("transport", "loss recovery", "ACKs · retransmit timers"),
            ("transport", "congestion control", "how fast to send"),
            ("plain", "IP · NIC", None),
        ],
        "receiver": [
            ("plain", "application", "read(fd) → bytes"),
            ("crypto", "TLS library", "decrypt · optional"),
            LINE,
            ("transport", "receive buffer", "in-order bytes for read()"),
            ("transport", "reassembly", "reorder · loss stalls all"),
            ("transport", "ACK generation", "what arrived"),
            ("transport", "flow control", "receive window"),
            ("plain", "IP · NIC", None),
        ],
    },
    "quic-works": {
        "wire": "UDP datagrams · almost all encrypted",
        "sender": [
            ("plain", "application", "write to streams"),
            ("transport", "stream send buffers", "one per stream"),
            ("transport", "packetization", "frames from many streams"),
            ("crypto", "encryption", "TLS 1.3 keys · every packet"),
            ("transport", "loss recovery", "ACK frames · retransmit"),
            ("transport", "congestion control", "per path"),
            LINE,
            ("plain", "UDP socket", "datagrams only"),
            ("plain", "IP · NIC", None),
        ],
        "receiver": [
            ("plain", "application", "read from streams"),
            ("transport", "stream receive buffers", "one per stream"),
            ("transport", "reassembly", "loss stalls one stream"),
            ("crypto", "decryption", "TLS 1.3 keys · every packet"),
            ("transport", "ACK generation", "ACK frames · encrypted"),
            ("transport", "flow control", "per stream + connection"),
            LINE,
            ("plain", "UDP socket", "datagrams only"),
            ("plain", "IP · NIC", None),
        ],
    },
}


def box(x, y, cat, title, subtitle):
    fill, stroke, ink = STYLE[cat]
    cx = x + SIDE_W / 2
    out = (
        f'  <rect x="{x}" y="{y}" width="{SIDE_W}" height="{ROW_H}" rx="6" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
    )
    if subtitle is None:
        out += (
            f'  <text x="{cx}" y="{y + ROW_H / 2 + 6}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="17" font-weight="bold" '
            f'fill="{ink}">{title}</text>\n')
    else:
        out += (
            f'  <text x="{cx}" y="{y + 20}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="17" font-weight="bold" '
            f'fill="{ink}">{title}</text>\n'
            f'  <text x="{cx}" y="{y + 38}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="12" fill="{ink}">{subtitle}</text>\n')
    return out


def arrow(x1, x2, y, color):
    """Horizontal arrow from x1 to x2 with a head at x2."""
    d = 1 if x2 > x1 else -1
    return (
        f'  <line x1="{x1}" y1="{y}" x2="{x2 - d * 10}" y2="{y}" '
        f'stroke="{color}" stroke-width="2.5"/>\n'
        f'  <path d="M{x2},{y} l{-d * 12},-7 v14 z" fill="{color}"/>\n')


def render(diagram):
    parts = []
    boundary_y = None
    last_y = None
    for side, x in SIDES.items():
        parts.append(
            f'  <text x="{x + SIDE_W / 2}" y="32" text-anchor="middle" '
            f'font-family="{MONO}" font-size="20" font-weight="bold" '
            f'fill="#222">{side}</text>\n')
        y = TOP
        for row in diagram[side]:
            if row == LINE:
                boundary_y = y - GAP + BOUNDARY_GAP / 2
                y += BOUNDARY_GAP - GAP
                continue
            parts.append(box(x, y, *row))
            last_y = y
            y += ROW_H + GAP

    # user space / kernel boundary, labels in the gap between the sides
    parts.append(
        f'  <line x1="10" y1="{boundary_y}" x2="{VB_W - 10}" y2="{boundary_y}" '
        f'stroke="#dc2626" stroke-width="2" stroke-dasharray="8 6"/>\n')
    for label, y in [("user space", boundary_y - 10), ("kernel", boundary_y + 22)]:
        parts.append(
            f'  <text x="{MID_X}" y="{y}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="15" font-weight="bold" '
            f'fill="#dc2626">{label}</text>\n')

    # the network: packets one way, ACKs back, between the IP rows
    left = SIDES["sender"] + SIDE_W + 6
    right = SIDES["receiver"] - 6
    cy = last_y + ROW_H / 2
    parts.append(arrow(left, right, cy - 9, "#6366f1"))
    parts.append(arrow(right, left, cy + 9, "#9ca3af"))
    for text, y, color in [("data", cy - 18, "#6366f1"), ("ACKs", cy + 31, "#888")]:
        parts.append(
            f'  <text x="{MID_X}" y="{y}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="12" fill="{color}">{text}</text>\n')
    parts.append(
        f'  <text x="{MID_X}" y="{last_y + ROW_H + 30}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="14" fill="#444">{diagram["wire"]}</text>\n')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
        + "".join(parts)
        + "</svg>\n"
    )


for name, diagram in DIAGRAMS.items():
    with open(os.path.join(OUT_DIR, f"{name}.svg"), "w") as f:
        f.write(render(diagram))
