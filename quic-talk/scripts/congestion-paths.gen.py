#!/usr/bin/env python3
"""Generator for congestion-paths.svg.

Companion piece to connection-streams.svg: same two small phones, same
bubble — but the three pipes are now *paths* (transports): ipv6, ipv4 and
the relay. Each path has its own congestion controller, drawn as an amber
valve ("cc") at the sending end of its pipe. Send rate is visible as dot
density; the relay path is slower (longer transit) and thriftier.

Story: the ipv4 path ramps up (dots get denser — additive increase), then a
packet is dropped mid-path (turns hollow, fades out). The controller reacts:
the valve narrows sharply (multiplicative decrease), the rate drops, then
the valve slowly reopens for the rest of the loop. The other two paths never
change rhythm: their controllers are their own.

20s loop, SMIL, single clock.

To change it, edit this script and run:  python3 congestion-paths.gen.py
It writes ../public/animations/congestion-paths.svg.
The page embeds this via <object>/<img src=... style='width:100%'/>; the
intrinsic aspect ratio comes from the SVG viewBox (VB_W x VB_H).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.normpath(os.path.join(
    HERE, "..", "public", "animations", "congestion-paths.svg"))

MONO = "'Space Mono', monospace"
INDIGO, AMBER, GRAY, BLUE = "#6366f1", "#d97706", "#888", "#2563eb"
CYCLE = 20   # seconds
VB_W, VB_H = 1000, 300
FADE = 0.15


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
    """SMIL <animateMotion> along #path_id; `points` is (seconds, keyPoint)."""
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


# ---- layout: bubble + 3 path pipes, cc valve at each sending end ----
LINE_Y = 150
LINE_X0, LINE_X1 = 115, 885   # meets the iroh boxes (per endpoint, not per device)
TUBE_X0, TUBE_X1 = 160, 840
TUBE_Y0, TUBE_Y1 = 85, 215
PIPE_X0, PIPE_X1 = 182, 818
PIPE_H = 26
PIPE_CYS = (113, 150, 187)
CC_W = 30                     # cc chamber at the sending end of each pipe
VALVE_X = PIPE_X0 + CC_W + 2  # valve bars sit right of the chamber
DOT_X0 = PIPE_X0 + CC_W + 14  # dots emerge right of the valve
DOT_X1 = PIPE_X1 - 13

# the ipv4 path's congestion story
T_DROP_SENT = 7.6             # the doomed packet leaves the sender
DROP_Q = 0.5                  # ...and dies at mid-path
T_DETECT = 9.2                # controller notices (timeout/dupack), backs off


def crossing(path_id, start, transit, lose_at=None):
    """One packet crossing the path: a single-use dot. `lose_at` (fraction)
    makes it a congestion drop: hollow + gone mid-path. A crossing that runs
    over the loop boundary continues and exits at the start of the next loop."""
    if lose_at is not None:
        t_lost = start + transit * lose_at
        pts = [(0, 0.0), (start, 0.0), (t_lost, lose_at),
               (t_lost + 0.6, lose_at), (t_lost + 0.6, 0.0), (CYCLE, 0.0)]
        opa = [(0, 0), (start, 0), (start + FADE, 1),
               (t_lost + 0.3, 1), (t_lost + 0.6, 0), (CYCLE, 0)]
        fill = attr_anim("fill-opacity", [
            (0, 1), (t_lost, 1), (t_lost + 0.2, 0), (CYCLE, 0)])
        return (f'  <circle r="4" fill="{BLUE}" stroke="{BLUE}" '
                f'stroke-width="1.5" opacity="0">'
                f'{motion_anim(path_id, pts)}{opacity_anim(opa)}{fill}</circle>')
    if start + transit > CYCLE:
        p_end = (CYCLE - start) / transit
        cont = transit * (1 - p_end)
        pts = [(0, p_end), (cont, 1.0), (cont, 0.0), (start, 0.0), (CYCLE, p_end)]
        opa = [(0, 1), (max(0.0, cont - FADE), 1), (cont, 0),
               (start, 0), (start + FADE, 1), (CYCLE, 1)]
    else:
        end = start + transit
        pts = [(0, 0.0), (start, 0.0), (end, 1.0), (end, 0.0), (CYCLE, 0.0)]
        opa = [(0, 0), (start, 0), (start + FADE, 1),
               (end - FADE, 1), (end, 0), (CYCLE, 0)]
    return (f'  <circle r="4" fill="{BLUE}" opacity="0">'
            f'{motion_anim(path_id, pts)}{opacity_anim(opa)}</circle>')


def ramp_emissions(t0, t_end, sp0, factor, floor):
    """Emission times with spacing shrinking from sp0 by `factor` per packet
    (additive increase seen from the wire) down to `floor`."""
    times, t, sp = [], t0, sp0
    while t < t_end:
        times.append(t)
        sp = max(floor, sp * factor)
        t += sp
    return times


def cc_valve(cy, aperture_anim=None, aperture=4):
    """The congestion controller: 'cc' chamber + valve bars at the pipe inlet.
    `aperture_anim` is a list of (seconds, bar-height) stops; bars grow from
    the pipe walls, so a taller bar means a narrower opening."""
    top = f'{VALVE_X},{cy - PIPE_H / 2 + 1.5}'
    parts = [
        f'  <text x="{PIPE_X0 + 2 + CC_W / 2}" y="{cy + 3.5}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="9" fill="{AMBER}">cc</text>'
    ]
    for anchor_top in (True, False):
        y_expr = (cy - PIPE_H / 2 + 1.5) if anchor_top else None
        if aperture_anim:
            h_anim = attr_anim("height", aperture_anim)
            if anchor_top:
                y_anim = ""
                y0 = cy - PIPE_H / 2 + 1.5
            else:
                # bottom bar is anchored at the pipe floor: y moves with height
                y_anim = attr_anim(
                    "y", [(t, cy + PIPE_H / 2 - 1.5 - h) for t, h in aperture_anim])
                y0 = cy + PIPE_H / 2 - 1.5 - aperture_anim[0][1]
            h0 = aperture_anim[0][1]
            parts.append(
                f'  <rect x="{VALVE_X}" y="{y0}" width="5.5" height="{h0}" rx="1.5" '
                f'fill="{AMBER}">{h_anim}{y_anim}</rect>')
        else:
            y0 = (cy - PIPE_H / 2 + 1.5) if anchor_top \
                else (cy + PIPE_H / 2 - 1.5 - aperture)
            parts.append(
                f'  <rect x="{VALVE_X}" y="{y0}" width="5.5" height="{aperture}" '
                f'rx="1.5" fill="{AMBER}"/>')
    return "\n".join(parts)


def connection():
    labels = ("ipv6", "ipv4", "relay")
    parts = [
        f'  <rect x="{TUBE_X0}" y="{TUBE_Y0}" width="{TUBE_X1 - TUBE_X0}" '
        f'height="{TUBE_Y1 - TUBE_Y0}" rx="20" fill="none" '
        f'stroke="{INDIGO}" stroke-width="1.5"/>\n'
        f'  <text x="{VB_W / 2}" y="{TUBE_Y0 - 12}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="13" fill="{INDIGO}">one iroh connection</text>\n'
        f'  <text x="{VB_W / 2}" y="{TUBE_Y1 + 20}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{GRAY}">'
        'each path has its own congestion controller</text>'
    ]
    for i, cy in enumerate(PIPE_CYS, start=1):
        parts.append(
            f'  <path id="path{i}" d="M {DOT_X0} {cy} L {DOT_X1} {cy}" '
            f'fill="none" stroke="none"/>\n'
            f'  <rect x="{PIPE_X0}" y="{cy - PIPE_H / 2}" width="{PIPE_X1 - PIPE_X0}" '
            f'height="{PIPE_H}" rx="{PIPE_H / 2}" fill="#eee" '
            f'stroke="{BLUE}" stroke-width="1.5"/>\n'
            f'  <text x="{PIPE_X0 + 4}" y="{cy - 17}" text-anchor="start" '
            f'font-family="{MONO}" font-size="10" fill="{GRAY}">{labels[i - 1]}</text>'
        )

    # path 1, ipv6: steady mid rate, its controller is content
    parts.append(cc_valve(PIPE_CYS[0], aperture=4))
    parts.append("\n".join(
        crossing("path1", t, 3.0) for t in ramp_emissions(0.1, 19.95, 0.9, 1.0, 0.9)))

    # path 2, ipv4: ramp up, drop, back off, recover
    valve = [(0, 4), (T_DETECT, 4), (T_DETECT + 0.4, 10),
             (T_DETECT + 2.0, 10), (19.5, 4.5), (CYCLE, 4.5)]
    parts.append(cc_valve(PIPE_CYS[1], aperture_anim=valve))
    pre = ramp_emissions(0.4, T_DROP_SENT - 0.05, 1.4, 0.86, 0.5)
    in_flight = [T_DROP_SENT + 0.5, T_DROP_SENT + 1.0]   # sent before detection
    post = ramp_emissions(T_DETECT + 0.6, 19.4, 1.7, 0.93, 0.9)
    parts.append("\n".join(crossing("path2", t, 3.0) for t in pre + in_flight + post))
    parts.append(crossing("path2", T_DROP_SENT, 3.0, lose_at=DROP_Q))

    # path 3, relay: slow but steady (longer transit, thriftier controller)
    parts.append(cc_valve(PIPE_CYS[2], aperture=8))
    parts.append("\n".join(
        crossing("path3", t, 4.5) for t in ramp_emissions(0.6, 19.5, 2.4, 1.0, 2.4)))

    # caption at the drop site
    drop_x = DOT_X0 + (DOT_X1 - DOT_X0) * DROP_Q
    t_lost = T_DROP_SENT + 3.0 * DROP_Q
    parts.append(
        f'  <text x="{drop_x:.0f}" y="{PIPE_CYS[1] - 17}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="10" fill="{AMBER}" opacity="0">'
        + 'packet dropped'
        + opacity_anim([(0, 0), (t_lost, 0), (t_lost + 0.3, 1),
                        (T_DETECT + 1.8, 1), (T_DETECT + 2.1, 0), (CYCLE, 0)])
        + '</text>')
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
       path 1 (ipv6):  steady flow, valve steady
       path 2 (ipv4):  rate ramps up (dots densify), a packet is dropped
                       mid-path at ~{T_DROP_SENT + 3.0 * DROP_Q:.1f}s (hollow, fades),
                       controller detects at {T_DETECT}s: valve narrows sharply,
                       rate drops, valve reopens slowly for the rest of the loop
       path 3 (relay): slow transit, low steady rate, half-closed valve -->

  <!-- ========== connection (bubble + 3 paths with cc valves) ========== -->
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
