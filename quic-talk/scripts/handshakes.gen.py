#!/usr/bin/env python3
"""Generator for handshake-https.svg and handshake-iroh.svg.

Two sequence diagrams with the same layout: client on the left, server on
the right, three handshake flights between them, the checks each side
does, and what each side knows at the end.

  HTTPS: the server proves its name through a certificate chain that ends
         in a root CA from the client's trust store. The client stays
         anonymous; the app authenticates it later.
  iroh:  raw public keys, no SNI. The client checks that the server holds
         the key it dialed; the server asks for the client's key too, so
         both sides end up knowing who they talk to. Nobody vouches;
         whether a key is welcome is up to the app.

Simplified to the parts that differ: TLS 1.3 flights, no extensions,
no 0-RTT. Static, no animation. To change it, edit this script and run:
python3 handshakes.gen.py
It writes ../public/animations/handshake-https.svg and handshake-iroh.svg.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "public", "animations"))

MONO = "'Space Mono', monospace"
VB_W, VB_H = 1100, 540
CLIENT_X, SERVER_X = 200, 900
MID_X = (CLIENT_X + SERVER_X) / 2
NOTE_W = 330

INK = "#222"
MUTED = "#888"
RED = "#dc2626"
# fill, stroke, text color per note category
STYLE = {
    "check": ("#e0e7ff", "#6366f1", "#3730a3"),
    "crypto": ("#fef3c7", "#d97706", "#92400e"),
    "plain": ("#f3f4f6", "#9ca3af", "#374151"),
}

# Steps, top to bottom:
#   ("msg", y, direction, label, sublabel, sublabel_color)
#   ("note", y, side, category, [lines])
DIAGRAMS = {
    "handshake-https": {
        "client": ("client", "browser"),
        "server": ("server", "example.com"),
        "steps": [
            ("msg", 118, "->", "ClientHello",
             "SNI: example.com · readable on the wire", RED),
            ("msg", 196, "<-", "certificate chain + signature",
             "example.com ← intermediate CA ← root CA", MUTED),
            ("note", 232, "client", "check", [
                "chain ends in a root CA",
                "from my trust store?",
                "name is example.com?",
            ]),
            ("msg", 350, "->", "Finished", "no client certificate", MUTED),
            ("note", 382, "server", "plain", ["client: anonymous"]),
        ],
        "summary": [
            ("client knows:", "a CA vouches that this is example.com"),
            ("server knows:", "nothing; the app might ask for a password later"),
        ],
    },
    "handshake-iroh": {
        "client": ("client", "dials 8e2b…"),
        "server": ("server", "holds 8e2b…"),
        "steps": [
            ("msg", 118, "->", "ClientHello",
             "no SNI · raw public keys only", MUTED),
            ("msg", 196, "<-", "public key 8e2b… + signature",
             "and: show me your key", MUTED),
            ("note", 232, "client", "check", [
                "is this the key",
                "I dialed?",
                "8e2b… = 8e2b… ✓",
            ]),
            ("msg", 350, "->", "public key a41f… + signature",
             "Finished", MUTED),
            ("note", 382, "server", "check", [
                "client is a41f… ✓",
                "welcome? the app decides",
            ]),
        ],
        "summary": [
            ("client knows:", "this is 8e2b…, no third party involved"),
            ("server knows:", "this is a41f…; trust is up to the app"),
        ],
    },
}


def arrow(x1, x2, y):
    d = 1 if x2 > x1 else -1
    return (
        f'  <line x1="{x1}" y1="{y}" x2="{x2 - d * 10}" y2="{y}" '
        f'stroke="{INK}" stroke-width="2"/>\n'
        f'  <path d="M{x2},{y} l{-d * 12},-7 v14 z" fill="{INK}"/>\n')


def text(x, y, s, size, color, bold=False, anchor="middle"):
    weight = ' font-weight="bold"' if bold else ""
    return (
        f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{MONO}" '
        f'font-size="{size}"{weight} fill="{color}">{s}</text>\n')


def render(diagram):
    parts = []
    # participants and lifelines
    for x, (name, sub) in [(CLIENT_X, diagram["client"]),
                           (SERVER_X, diagram["server"])]:
        parts.append(text(x, 32, name, 20, INK, bold=True))
        parts.append(text(x, 54, sub, 14, "#6366f1"))
        parts.append(
            f'  <line x1="{x}" y1="70" x2="{x}" y2="440" stroke="#cbd0d8" '
            f'stroke-width="2"/>\n')

    for step in diagram["steps"]:
        if step[0] == "msg":
            _, y, direction, label, sub, sub_color = step
            gap = 8
            if direction == "->":
                parts.append(arrow(CLIENT_X + gap, SERVER_X - gap, y))
            else:
                parts.append(arrow(SERVER_X - gap, CLIENT_X + gap, y))
            parts.append(text(MID_X, y - 12, label, 17, INK, bold=True))
            parts.append(text(MID_X, y + 24, sub, 13, sub_color))
        else:
            _, y, side, cat, lines = step
            fill, stroke, ink = STYLE[cat]
            cx = CLIENT_X if side == "client" else SERVER_X
            h = 16 + 22 * len(lines)
            parts.append(
                f'  <rect x="{cx - NOTE_W / 2}" y="{y}" width="{NOTE_W}" '
                f'height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="1.5"/>\n')
            for i, line in enumerate(lines):
                parts.append(text(cx, y + 28 + 22 * i, line, 15, ink))

    # what each side knows afterwards
    for i, (who, what) in enumerate(diagram["summary"]):
        y = 482 + 30 * i
        parts.append(text(MID_X - 250, y, who, 16, INK, bold=True, anchor="end"))
        parts.append(text(MID_X - 236, y, what, 16, "#444", anchor="start"))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
        + "".join(parts)
        + "</svg>\n"
    )


for name, diagram in DIAGRAMS.items():
    with open(os.path.join(OUT_DIR, f"{name}.svg"), "w") as f:
        f.write(render(diagram))
