#!/usr/bin/env python3
"""Generator for connection-streams.svg.

One iroh connection between two devices, zoomed in on the connection itself:
the two phones are small at the left and right edges, the middle shows the
connection as a bubble carrying three independent QUIC streams (pipes).
Stream 1 flows smoothly the whole loop. The two incidents are staggered so
they never overlap:

  ~2.6-7.4s  stream 2, backpressure: the receiver stops reading (amber plug
             at the receiving end), arriving packets queue up behind it,
             then the plug clears and the queue drains.
  ~11.4-15s  stream 3, packet loss: a packet makes it all the way to the
             receiving end, turns hollow (lost); in-order delivery queues
             the packets behind the hole until the retransmit fills it.

Outside its incident each stream flows smoothly. The neighbors never notice
either incident: no head-of-line blocking across streams.

20s loop, SMIL, single clock for the story beats; the smooth dots on stream 1
ride an independent 3s sub-loop.

To change it, edit this script and run:  python3 connection-streams.gen.py
It writes ../public/animations/connection-streams.svg.
The page embeds this via <object>/<img src=... style='width:100%'/>; the
intrinsic aspect ratio comes from the SVG viewBox (VB_W x VB_H).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "connection-streams.svg"))

MONO = "'Space Mono', monospace"
INDIGO, AMBER, GRAY, BLUE = "#6366f1", "#d97706", "#888", "#2563eb"
CYCLE = 20   # seconds
TRANSIT = 3  # seconds for a dot to cross a pipe at smooth speed
VB_W, VB_H = 1000, 300


def fmt_kt(t):
    """Time in seconds -> SMIL keyTimes fraction of CYCLE."""
    f = t / CYCLE
    if f <= 0:
        return "0"
    if f >= 1:
        return "1"
    return f"{f:.4f}".rstrip("0").rstrip(".")


def attr_anim(attr, stops):
    """SMIL <animate> on `attr`; `stops` is a list of (seconds, value)."""
    keytimes = ";".join(fmt_kt(t) for t, _ in stops)
    values = ";".join(str(v) for _, v in stops)
    return (f'<animate attributeName="{attr}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{keytimes}" values="{values}"/>')


def opacity_anim(stops):
    return attr_anim("opacity", stops)


def motion_anim(path_id, points):
    """SMIL <animateMotion> along #path_id; `points` is (seconds, keyPoint).
    Duplicate timestamps express jumps (teleport while faded out)."""
    keytimes = ";".join(fmt_kt(t) for t, _ in points)
    keypoints = ";".join(f"{k:.4f}".rstrip("0").rstrip(".") if k else "0"
                         for _, k in points)
    return (f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" '
            f'calcMode="linear" keyPoints="{keypoints}" keyTimes="{keytimes}">'
            f'<mpath href="#{path_id}"/></animateMotion>')


def iroh_box(cx, cy):
    """The amber iroh box, centered on (cx, cy)."""
    return (
        f'  <rect x="{cx - 25}" y="{cy - 16}" width="50" height="32" rx="4" '
        f'fill="#eee" stroke="{AMBER}" stroke-width="1.5"/>\n'
        f'  <text x="{cx}" y="{cy + 5}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{AMBER}">iroh</text>'
    )


def phone_left():
    """Small iPhone on the left: inner frame with the notch cut out of the top
    edge, a scaled-down copy of the big alice_iphone() path."""
    x, y, w, h = 45, 75, 90, 150
    cx = x + w / 2
    x0, x1, y0, y1, r = x + 4, x + w - 4, y + 4, y + h - 4, 12
    nl, nr, nd = cx - 15, cx + 15, y + 12   # notch left/right/depth
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" '
        f'fill="#eee" stroke="{GRAY}" stroke-width="1.5"/>\n'
        f'  <path d="M {x0 + r} {y0}\n'
        f'           L {nl - 3} {y0}\n'
        f'           Q {nl} {y0} {nl} {y0 + 3}\n'
        f'           L {nl} {nd - 4}\n'
        f'           Q {nl} {nd} {nl + 4} {nd}\n'
        f'           L {nr - 4} {nd}\n'
        f'           Q {nr} {nd} {nr} {nd - 4}\n'
        f'           L {nr} {y0 + 3}\n'
        f'           Q {nr} {y0} {nr + 3} {y0}\n'
        f'           L {x1 - r} {y0}\n'
        f'           A {r} {r} 0 0 1 {x1} {y0 + r}\n'
        f'           L {x1} {y1 - r}\n'
        f'           A {r} {r} 0 0 1 {x1 - r} {y1}\n'
        f'           L {x0 + r} {y1}\n'
        f'           A {r} {r} 0 0 1 {x0} {y1 - r}\n'
        f'           L {x0} {y0 + r}\n'
        f'           A {r} {r} 0 0 1 {x0 + r} {y0} Z"\n'
        f'        fill="#eee" stroke="{INDIGO}" stroke-width="1.5"/>\n'
        + iroh_box(cx, y + h / 2)
    )


def phone_right():
    """Small Android on the right (camera dot)."""
    x, y, w, h = 865, 75, 90, 150
    cx = x + w / 2
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" '
        f'fill="#eee" stroke="{GRAY}" stroke-width="1.5"/>\n'
        f'  <rect x="{x + 4}" y="{y + 4}" width="{w - 8}" height="{h - 8}" rx="12" '
        f'fill="#eee" stroke="{INDIGO}" stroke-width="1.5"/>\n'
        f'  <circle cx="{cx}" cy="{y + 13}" r="2.5" fill="{GRAY}"/>\n'
        + iroh_box(cx, y + h / 2)
    )


# ---- the connection: plain blue line, opened up in the middle into 3 streams ----
LINE_Y = 150                  # the connection line between the two phones
LINE_X0, LINE_X1 = 115, 885   # meets the iroh boxes (per endpoint, not per device)
TUBE_X0, TUBE_X1 = 160, 840   # zoomed-in detail, narrow gap to the phones
TUBE_Y0, TUBE_Y1 = 85, 215
PIPE_X0, PIPE_X1 = 182, 818
PIPE_H = 26
PIPE_CYS = (113, 150, 187)    # vertical centers of the three streams
PAD = 13                      # dot travel inset from the pipe ends

FADE = 0.15
Q_FRONT, Q_STEP = 0.94, 0.07  # queue head keyPoint and per-dot spacing

# backpressure story on stream 2 (all in seconds on the single clock)
T_BLOCK, T_UNBLOCK = 2.6, 7.4   # receiver stops reading / reads again
JAM_N = 5                        # dots that pile up

# packet loss story on stream 3 — staggered to the second half of the loop
LOSS_Q = Q_FRONT                 # the packet makes it all the way to the
                                 # receiving end before it turns out lost,
                                 # mirroring the stream-2 jam location
LOST_ENTER = 8.6                 # the doomed packet enters here
T_LOST = LOST_ENTER + TRANSIT * LOSS_Q   # ...and turns hollow here (~11.4s)
T_REPAIR = 15.0                  # retransmit arrives, circle fills again
LOSS_N = 3                       # packets that queue up behind the hole


def smooth_dots(path_id, n=4):
    """Continuously flowing dots: a TRANSIT-second sub-loop, staggered starts."""
    out = []
    for k in range(n):
        begin = -TRANSIT * k / n
        out.append(
            f'  <circle r="4" fill="{BLUE}" opacity="0">'
            f'<animateMotion dur="{TRANSIT}s" begin="{begin}s" repeatCount="indefinite">'
            f'<mpath href="#{path_id}"/></animateMotion>'
            f'<animate attributeName="opacity" dur="{TRANSIT}s" begin="{begin}s" '
            f'repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="0;0.08;0.92;1" values="0;1;1;0"/></circle>')
    return "\n".join(out)


def build_dot(path_id, trips, attrs="", extra_anim=""):
    """A dot that makes several trips through the pipe during one CYCLE.

    `trips` is a list of (start, q, resume), sorted by start time:
      q is None    — a plain smooth crossing (TRANSIT seconds);
      q is a float — flow in, park at keyPoint q, hold until `resume`,
                     then exit quickly.
    Only the last trip may run over the loop boundary (plain trips only);
    it then continues and exits at the start of the next loop."""
    wrap = None
    ls, lq, _ = trips[-1]
    if lq is None and ls + TRANSIT > CYCLE:
        p_end = (CYCLE - ls) / TRANSIT
        wrap = (p_end, TRANSIT * (1 - p_end))

    pts, opa = [], []
    if wrap:
        p_end, cont = wrap
        pts += [(0, p_end), (cont, 1.0), (cont, 0.0)]
        opa += [(0, 1), (max(0.0, cont - FADE), 1), (cont, 0)]
        prev_end = cont
    else:
        pts += [(0, 0.0)]
        opa += [(0, 0)]
        prev_end = 0.0

    for start, q, resume in (trips[:-1] if wrap else trips):
        if start < prev_end:
            raise ValueError(
                f"overlapping trips on {path_id}: {start} < {prev_end}")
        pts += [(start, 0.0)]
        opa += [(start, 0), (start + FADE, 1)]
        if q is None:
            end = start + TRANSIT
            pts += [(end, 1.0), (end, 0.0)]
        else:
            end = resume + 0.35   # quick exit once unblocked
            pts += [(start + TRANSIT * q, q), (resume, q), (end, 1.0), (end, 0.0)]
        opa += [(end - FADE, 1), (end, 0)]
        prev_end = end

    if wrap:
        pts += [(ls, 0.0), (CYCLE, wrap[0])]
        opa += [(ls, 0), (ls + FADE, 1), (CYCLE, 1)]
    else:
        pts += [(CYCLE, 0.0)]
        opa += [(CYCLE, 0)]

    return (f'  <circle r="4" fill="{BLUE}" opacity="0"{attrs}>'
            f'{motion_anim(path_id, pts)}{opacity_anim(opa)}{extra_anim}</circle>')


def refill_passes(first, enter, count=8):
    """Plain crossings every 3.5s from `first` until the loop runs out,
    dropping a final wrapping pass whose spill-over into the next loop
    would collide with this dot's re-entry at `enter`."""
    passes = []
    p = first
    while p < CYCLE - 0.3 and len(passes) < count:
        if p + TRANSIT > CYCLE and (p + TRANSIT - CYCLE) > enter - 0.2:
            break
        passes.append((p, None, None))
        p += 3.5
    return passes


def jam_dot(path_id, j):
    """Backpressure dot j on stream 2: park in the queue early in the loop,
    drain front-first, then keep the stream flowing for the rest of it."""
    enter = 2.0 + 0.8 * j
    trips = [(enter, Q_FRONT - Q_STEP * j, T_UNBLOCK + 0.2 * j)]
    trips += refill_passes(9.4 + 0.7 * j, enter)
    return build_dot(path_id, trips)


def lost_dot(path_id):
    """The doomed packet on stream 3: two smooth passes, then it travels to
    the receiving end, turns hollow (lost), holds the line until the
    retransmit fills it again, drains, and makes one more pass."""
    fill = attr_anim("fill-opacity", [
        (0, 1), (T_LOST, 1), (T_LOST + 0.25, 0),
        (T_REPAIR, 0), (T_REPAIR + 0.25, 1), (CYCLE, 1)])
    trips = [(1.4, None, None), (4.9, None, None),
             (LOST_ENTER, LOSS_Q, T_REPAIR + 0.3),
             (16.6, None, None)]
    return build_dot(path_id, trips, extra_anim=fill,
                     attrs=f' stroke="{BLUE}" stroke-width="1.5"')


def loss_followers(path_id):
    """In-order delivery: the packets behind the hole queue up against it,
    flowing smoothly before and after the incident."""
    out = []
    for j in range(LOSS_N):
        enter = 9.4 + 0.8 * j
        trips = [(2.2 + 0.8 * j, None, None), (5.9 + 0.8 * j, None, None),
                 (enter, LOSS_Q - Q_STEP * (j + 1), T_REPAIR + 0.5 + 0.2 * j)]
        trips += refill_passes(16.8 + 0.7 * j, 2.2 + 0.8 * j)
        out.append(build_dot(path_id, trips))
    return "\n".join(out)


def loss_label(cy):
    """Amber caption above the hole while the packet is lost."""
    x = PIPE_X0 + PAD + (PIPE_X1 - PIPE_X0 - 2 * PAD) * LOSS_Q
    return (
        f'  <text x="{x:.0f}" y="{cy - 17}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="10" fill="{AMBER}" opacity="0">'
        + 'packet lost'
        + opacity_anim([(0, 0), (T_LOST, 0), (T_LOST + 0.3, 1),
                        (T_REPAIR, 1), (T_REPAIR + 0.3, 0), (CYCLE, 0)])
        + '</text>')


def backpressure_extras(cy):
    """The amber plug at the receiving end of the blocked pipe + caption."""
    plug = (
        f'  <rect x="{PIPE_X1 - 8}" y="{cy - 9}" width="4" height="18" rx="2" '
        f'fill="{AMBER}" opacity="0">'
        + opacity_anim([(0, 0), (T_BLOCK, 0), (T_BLOCK + 0.3, 1),
                        (T_UNBLOCK, 1), (T_UNBLOCK + 0.3, 0), (CYCLE, 0)])
        + '</rect>')
    label = (
        f'  <text x="{PIPE_X1}" y="{cy - 17}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{AMBER}" opacity="0">'
        + 'receiver not reading'
        + opacity_anim([(0, 0), (T_BLOCK, 0), (T_BLOCK + 0.3, 1),
                        (T_UNBLOCK, 1), (T_UNBLOCK + 0.3, 0), (CYCLE, 0)])
        + '</text>')
    return plug + "\n" + label


def connection():
    parts = [
        f'  <rect x="{TUBE_X0}" y="{TUBE_Y0}" width="{TUBE_X1 - TUBE_X0}" '
        f'height="{TUBE_Y1 - TUBE_Y0}" rx="20" fill="none" '
        f'stroke="{INDIGO}" stroke-width="1.5"/>\n'
        f'  <text x="{VB_W / 2}" y="{TUBE_Y0 - 12}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="13" fill="{INDIGO}">one QUIC connection</text>'
    ]
    for i, cy in enumerate(PIPE_CYS, start=1):
        parts.append(
            f'  <path id="pipe{i}" d="M {PIPE_X0 + PAD} {cy} L {PIPE_X1 - PAD} {cy}" '
            f'fill="none" stroke="none"/>\n'
            f'  <rect x="{PIPE_X0}" y="{cy - PIPE_H / 2}" width="{PIPE_X1 - PIPE_X0}" '
            f'height="{PIPE_H}" rx="{PIPE_H / 2}" fill="#eee" '
            f'stroke="{BLUE}" stroke-width="1.5"/>\n'
            f'  <text x="{PIPE_X0 + 4}" y="{cy - 17}" text-anchor="start" '
            f'font-family="{MONO}" font-size="10" fill="{GRAY}">stream {i}</text>'
        )
    # stream 1: smooth flow all loop long
    parts.append(smooth_dots("pipe1"))
    # stream 2: backpressure story (first half of the loop)
    parts.append("\n".join(jam_dot("pipe2", j) for j in range(JAM_N)))
    parts.append(backpressure_extras(PIPE_CYS[1]))
    # stream 3: packet loss story (second half of the loop)
    parts.append(lost_dot("pipe3"))
    parts.append(loss_followers("pipe3"))
    parts.append(loss_label(PIPE_CYS[2]))
    return "\n".join(parts)


def conn_lines():
    """The familiar blue connection line, iroh box to detail tube on each side.
    Drawn last so it stays on top of the phone bodies."""
    return (
        f'  <line x1="{LINE_X0}" y1="{LINE_Y}" x2="{TUBE_X0}" y2="{LINE_Y}" '
        f'stroke="{BLUE}" stroke-width="2"/>\n'
        f'  <line x1="{TUBE_X1}" y1="{LINE_Y}" x2="{LINE_X1}" y2="{LINE_Y}" '
        f'stroke="{BLUE}" stroke-width="2"/>'
    )


svg = f'''<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg">
  <style>/* transparent-canvas */ :root {{ background-color: transparent; color-scheme: light dark; }}</style>
  <!-- {CYCLE}s loop (SMIL):
       stream 1: smooth dot flow throughout ({TRANSIT}s per crossing)
       stream 2: flows, receiver stops reading at {T_BLOCK}s (amber plug),
                 dots queue at the receiving end, reads again at {T_UNBLOCK}s,
                 queue drains, smooth flow for the rest of the loop
       stream 3: flows smoothly, a packet reaches the receiving end and turns
                 hollow (lost) at {T_LOST:.1f}s, followers queue behind the
                 hole, retransmit fills it at {T_REPAIR}s, drain, flow -->

  <!-- ========== connection (bubble + 3 streams) ========== -->
{connection()}

  <!-- ========== left device ========== -->
{phone_left()}

  <!-- ========== right device ========== -->
{phone_right()}

  <!-- ========== connection lines (on top of the phone bodies) ========== -->
{conn_lines()}

  <!-- Timer bar (position in loop) -->
  <rect x="0" y="{VB_H - 4}" width="0" height="3" fill="#9ca3af">
    <animate attributeName="width" from="0" to="{VB_W}" dur="{CYCLE}s" repeatCount="indefinite"/>
  </rect>
</svg>
'''

with open(OUT_PATH, "w") as f:
    f.write(svg)
print(f"wrote {len(svg)} bytes -> {OUT_PATH}")
