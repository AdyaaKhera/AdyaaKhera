"""Generate the animated project cards for the AdyaaKhera profile README.

All motion is computed (real 2-link IK, arc-length sampling) and emitted as SMIL
so it animates inside GitHub's <img> rendering without any JavaScript.
"""
import math
import os
import sys

OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, "cards"), exist_ok=True)

# Palette: Purdue black and Boilermaker Gold
BG0 = "#000000"
BG1 = "#111111"
BG2 = "#1C1C1C"
PANEL = "#0A0A0A"
LINE = "#333333"
GOLD = "#CFB991"
STEEL = "#9D9795"
TEXT = "#F2F2F2"
MUTED = "#8E8E8E"
RED = "#E07A6B"

SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".") if abs(x) < 1e6 else str(x)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- kinematics
def ik2(x, y, l1, l2, elbow_up=True):
    """Planar 2-link IK in SVG coordinates (y down). Returns (q1, q2) radians."""
    r2 = x * x + y * y
    c2 = (r2 - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    c2 = max(-1.0, min(1.0, c2))
    best = None
    for s in (1, -1):
        q2 = s * math.acos(c2)
        q1 = math.atan2(y, x) - math.atan2(l2 * math.sin(q2), l1 + l2 * math.cos(q2))
        ey = l1 * math.sin(q1)
        if best is None or (ey < best[2] if elbow_up else ey > best[2]):
            best = (q1, q2, ey)
    return best[0], best[1]


def fk_pts(bx, by, q1, q2, l1, l2):
    ex = bx + l1 * math.cos(q1)
    ey = by + l1 * math.sin(q1)
    gx = ex + l2 * math.cos(q1 + q2)
    gy = ey + l2 * math.sin(q1 + q2)
    return (ex, ey), (gx, gy)



def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return t * t * (3 - 2 * t)


def keyframe_track(keys, t):
    """keys: list of (time, (x, y)). Smoothstep between keys."""
    for i in range(len(keys) - 1):
        t0, p0 = keys[i]
        t1, p1 = keys[i + 1]
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 0
            return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))
    return keys[-1][1]


def anim(attr, values, dur, extra=""):
    return (f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" '
            f'values="{";".join(values)}" {extra}/>')


def discrete_show(i, n, dur):
    """Opacity animation visible only during frame i of n."""
    kt, vals = [], []
    a, b = i / n, (i + 1) / n
    if a > 0:
        kt += ["0"]
        vals += ["0"]
    kt += [f"{a:.4f}"]
    vals += ["1"]
    if b < 1:
        kt += [f"{b:.4f}"]
        vals += ["0"]
    if kt[0] != "0":
        kt[0] = "0"
    return (f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{";".join(kt)}" values="{";".join(vals)}"/>')


def grid_pattern(pid, step=24, color="#FFFFFF", op=0.05):
    return (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<path d="M {step} 0 L 0 0 0 {step}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1"/>'
            f'</pattern>')


def corner_marks(x, y, w, h, s=14, color=GOLD, op=0.7):
    d = (f"M{x},{y+s} L{x},{y} L{x+s},{y} "
         f"M{x+w-s},{y} L{x+w},{y} L{x+w},{y+s} "
         f"M{x+w},{y+h-s} L{x+w},{y+h} L{x+w-s},{y+h} "
         f"M{x+s},{y+h} L{x},{y+h} L{x},{y+h-s}")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1.5"/>'


def write(name, body):
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(body)
    print(name, len(body))




# ================================================================== CARDS
CW, CH = 600, 420
IH = 230  # illustration height


def card(name, idx, cat, title, lines, stats, illus, desc):
    stat_svg = []
    sx = 32
    for val, lab in stats:
        stat_svg.append(f'<text x="{sx}" y="384" class="mono" fill="{TEXT}" font-size="19" font-weight="700">{esc(val)}</text>'
                        f'<text x="{sx}" y="404" class="mono" fill="{MUTED}" font-size="11" letter-spacing="1">{esc(lab)}</text>')
        sx += 184
    body_lines = "".join(
        f'<text x="32" y="{320 + 24*i}" class="sans" fill="{STEEL}" font-size="17">{esc(l)}</text>' for i, l in enumerate(lines))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}" role="img" aria-labelledby="t d">
<title id="t">{esc(title)}</title>
<desc id="d">{esc(desc)}</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>
{grid_pattern("g", 20)}
<clipPath id="ic"><rect x="12" y="12" width="{CW-24}" height="{IH}" rx="10"/></clipPath>
<style>.sans{{font-family:{SANS};}} .mono{{font-family:{MONO};}}</style>
</defs>
<rect x="0.5" y="0.5" width="{CW-1}" height="{CH-1}" rx="14" fill="url(#bg)" stroke="{LINE}"/>
<rect x="12" y="12" width="{CW-24}" height="{IH}" rx="10" fill="{PANEL}"/>
<g clip-path="url(#ic)"><rect x="12" y="12" width="{CW-24}" height="{IH}" fill="url(#g)"/>{illus}</g>
{corner_marks(12, 12, CW-24, IH, 12, GOLD, 0.5)}
<text x="32" y="268" class="mono" fill="{GOLD}" font-size="12" letter-spacing="2.5">{idx}  /  {esc(cat)}</text>
<text x="31" y="298" class="sans" fill="{TEXT}" font-size="25" font-weight="700">{esc(title)}</text>
{body_lines}
<line x1="32" y1="360" x2="{CW-32}" y2="360" stroke="{LINE}"/>
{"".join(stat_svg)}
</svg>'''
    write(f"cards/{name}.svg", svg)


def path_anim(frames, dur, style):
    return f'<path {style} d="{frames[0]}">{anim("d", frames + [frames[0]], dur)}</path>'


def arm_d(bx, by, gx, gy, l1, l2, elbow_up=True, jaw=None):
    q1, q2 = ik2(gx - bx, gy - by, l1, l2, elbow_up)
    (ex, ey), (tx, ty) = fk_pts(bx, by, q1, q2, l1, l2)
    return f"M{f(bx)},{f(by)} L{f(ex)},{f(ey)} L{f(tx)},{f(ty)}", (ex, ey), (tx, ty)


# ---- 01 peg transfer
def illus_peg():
    dur, N = 9, 90
    floor = 200
    lpegs = [(110, floor), (160, floor), (210, floor)]
    rpegs = [(390, floor), (440, floor), (490, floor)]
    mid = (300, 92)
    src, dst = lpegs[1], rpegs[1]
    lift = 30
    # triangle keyframes (center of triangle)
    tri_keys = [(0.00, (src[0], floor - 16)), (0.10, (src[0], floor - 16)), (0.25, (src[0], floor - 80)),
                (0.42, mid), (0.55, mid), (0.70, (dst[0], floor - 80)), (0.85, (dst[0], floor - 16)),
                (1.00, (dst[0], floor - 16))]
    # left gripper: goes to src, carries to mid, returns home
    lhome, rhome = (140, 80), (460, 80)
    lg_keys = [(0.0, lhome), (0.10, (src[0], floor - 26)), (0.25, (src[0], floor - 90)), (0.42, (mid[0] - 2, mid[1] - 10)),
               (0.52, (mid[0] - 2, mid[1] - 10)), (0.66, lhome), (1.0, lhome)]
    rg_keys = [(0.0, rhome), (0.30, rhome), (0.44, (mid[0] + 2, mid[1] - 10)), (0.55, (mid[0] + 2, mid[1] - 10)),
               (0.70, (dst[0], floor - 90)), (0.85, (dst[0], floor - 26)), (0.92, (dst[0], floor - 60)), (1.0, rhome)]
    lb, rb = (60, 30), (540, 30)
    l1, l2 = 120, 120
    la, ra, tri = [], [], []
    for k in range(N):
        t = k / N
        gx, gy = keyframe_track(lg_keys, t)
        la.append(arm_d(lb[0], lb[1], gx, gy, l1, l2, elbow_up=False)[0])
        gx, gy = keyframe_track(rg_keys, t)
        ra.append(arm_d(rb[0], rb[1], gx, gy, l1, l2, elbow_up=False)[0])
        cx, cy = keyframe_track(tri_keys, t)
        tri.append(f"M{f(cx)},{f(cy-14)} L{f(cx+14)},{f(cy+10)} L{f(cx-14)},{f(cy+10)} Z")
    pegs = "".join(f'<rect x="{x-3}" y="{floor-40}" width="6" height="40" rx="2" fill="{MUTED}"/>' for x, _ in lpegs + rpegs)
    return f'''
<rect x="70" y="{floor}" width="190" height="12" rx="3" fill="{BG2}" stroke="{LINE}"/>
<rect x="340" y="{floor}" width="190" height="12" rx="3" fill="{BG2}" stroke="{LINE}"/>
{pegs}
<line x1="300" y1="40" x2="300" y2="{floor+10}" stroke="{STEEL}" stroke-opacity="0.2" stroke-dasharray="4 6"/>
<text x="300" y="34" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle" letter-spacing="1.5">MID-AIR HANDOVER</text>
{path_anim(la, dur, f'fill="none" stroke="{STEEL}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"')}
{path_anim(ra, dur, f'fill="none" stroke="{STEEL}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"')}
{path_anim(tri, dur, f'fill="{GOLD}" fill-opacity="0.9" stroke="{GOLD}" stroke-width="2" stroke-linejoin="round"')}
<circle cx="60" cy="30" r="9" fill="{BG0}" stroke="{STEEL}" stroke-width="2"/><circle cx="540" cy="30" r="9" fill="{BG0}" stroke="{STEEL}" stroke-width="2"/>
<text x="28" y="230" class="mono" fill="{MUTED}" font-size="10" letter-spacing="1.5">YAM ARM L</text>
<text x="572" y="230" class="mono" fill="{MUTED}" font-size="10" letter-spacing="1.5" text-anchor="end">YAM ARM R</text>'''



# ---- 03 NEXUS rover
def illus_rover():
    dur = 8
    states = ["BOOT", "CAL", "SCAN", "HAZ", "SAMP", "DARK"]
    chips = []
    n = len(states)
    for i, s in enumerate(states):
        x = 40 + i * 88
        chips.append(f'<rect x="{x}" y="28" width="76" height="24" rx="4" fill="none" stroke="{LINE}"/>'
                     f'<rect x="{x}" y="28" width="76" height="24" rx="4" fill="{RED if s=="HAZ" else GOLD}" fill-opacity="0.22" stroke="{RED if s=="HAZ" else GOLD}" opacity="0">{discrete_show(i, n, dur)}</rect>'
                     f'<text x="{x+38}" y="45" class="mono" fill="{TEXT}" font-size="12" text-anchor="middle" letter-spacing="1.5">{s}</text>')
    # terrain profile (scrolling, 2 tiles of 600)
    def terrain(off):
        pts = []
        for k in range(0, 601, 20):
            x = k
            y = 196 + 6 * math.sin(2 * math.pi * 2 * k / 600) + 4 * math.sin(2 * math.pi * 7 * k / 600 + 1)
            pts.append(f"{f(x+off)},{f(y)}")
        return "M" + " L".join(pts) + f" L{600+off},240 L{off},240 Z"
    rocks = "".join(f'<path d="M{x},{198} l10,-14 l12,4 l8,10 Z" fill="{BG2}" stroke="{MUTED}" stroke-width="1"/>' for x in (120, 430, 720, 1030))
    wheel = lambda cx: (f'<g transform="translate({cx},172)"><circle r="15" fill="{BG0}" stroke="{STEEL}" stroke-width="2.5"/>'
                        f'<g><animateTransform attributeName="transform" type="rotate" values="0;360" dur="1.6s" repeatCount="indefinite"/>'
                        f'<path d="M-15,0 H15 M0,-15 V15" stroke="{STEEL}" stroke-width="1.5"/></g></g>')
    return f'''
{"".join(chips)}
<g><animateTransform attributeName="transform" type="translate" values="0,0;-600,0" dur="6s" repeatCount="indefinite"/>
<path d="{terrain(0)}" fill="{BG2}"/><path d="{terrain(600)}" fill="{BG2}"/><path d="{terrain(0).split(" L600")[0]}" fill="none" stroke="{STEEL}" stroke-opacity="0.35"/><path d="{terrain(600).split(" L1200,240")[0]}" fill="none" stroke="{STEEL}" stroke-opacity="0.35"/>{rocks}</g>
<g>
<animateTransform attributeName="transform" type="translate" values="0,0;0,-2;0,1;0,0" dur="0.9s" repeatCount="indefinite"/>
<rect x="210" y="128" width="150" height="34" rx="6" fill="{BG1}" stroke="{STEEL}" stroke-width="2"/>
<rect x="226" y="112" width="58" height="16" rx="3" fill="{BG0}" stroke="{LINE}"/>
<line x1="320" y1="128" x2="320" y2="96" stroke="{STEEL}" stroke-width="2"/>
<rect x="308" y="86" width="26" height="12" rx="2" fill="{BG0}" stroke="{GOLD}"/>
<circle cx="334" cy="92" r="2.5" fill="{GOLD}"/>
<rect x="360" y="138" width="10" height="14" rx="2" fill="{GOLD}"/>
{wheel(230)}{wheel(285)}{wheel(340)}
</g>
<g fill="none" stroke="{GOLD}" stroke-width="2">
{"".join(f'<path d="M378,{132+0} a{r},{r} 0 0 1 0,{14}" opacity="0"><animate attributeName="opacity" values="0;0.9;0" dur="1.2s" begin="{i*0.3}s" repeatCount="indefinite"/><animateTransform attributeName="transform" type="translate" values="0,0;60,0" dur="1.2s" begin="{i*0.3}s" repeatCount="indefinite"/></path>' for i, r in enumerate((8, 8, 8, 8)))}
</g>
<g class="mono" font-size="10" fill="{MUTED}" letter-spacing="1.2">
  <text x="440" y="96">US RANGE</text><text x="440" y="110" fill="{GOLD}">HAZ OVERRIDE</text>
  <text x="40" y="96">WATCHDOG</text><text x="40" y="110" fill="{STEEL}">900 ms auto-stop</text>
</g>'''


# ---- 04 Neural IK
def illus_ik():
    dur, N = 10, 100
    layers = [2, 5, 5, 2]
    lx = [48, 108, 168, 228]
    nodes = []
    for li, n in enumerate(layers):
        ys = [121 + (k - (n - 1) / 2) * 30 for k in range(n)]
        nodes.append([(lx[li], y) for y in ys])
    edges, pulses = [], []
    for li in range(len(layers) - 1):
        for a in nodes[li]:
            for b in nodes[li + 1]:
                edges.append(f'<line x1="{a[0]}" y1="{f(a[1])}" x2="{b[0]}" y2="{f(b[1])}" stroke="{STEEL}" stroke-opacity="0.18"/>')
    for li in range(len(layers) - 1):
        for k, a in enumerate(nodes[li]):
            b = nodes[li + 1][(k * 2 + li) % len(nodes[li + 1])]
            pulses.append(f'<circle r="2.5" fill="{GOLD}"><animateMotion path="M{a[0]},{f(a[1])} L{b[0]},{f(b[1])}" dur="1.4s" begin="{li*0.45 + k*0.1:.2f}s" repeatCount="indefinite"/></circle>')
    nd = "".join(f'<circle cx="{x}" cy="{f(y)}" r="7" fill="{BG0}" stroke="{GOLD if li in (0,3) else STEEL}" stroke-width="1.8"/>'
                 for li, layer in enumerate(nodes) for (x, y) in layer)
    labels = (f'<text x="48" y="58" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle">x, y</text>'
              f'<text x="228" y="58" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle">θ1, θ2</text>'
              f'<text x="138" y="216" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle" letter-spacing="1.5">MLP · PYTORCH</text>')
    # arm on the right reaching click targets
    bx, by, l1, l2 = 420, 205, 90, 75
    targets = [(500, 90), (360, 80), (470, 150), (400, 120), (520, 130)]
    keys = []
    T = len(targets)
    for i, p in enumerate(targets):
        keys.append((i / T, p))
        keys.append((i / T + 0.6 / T, p))
    keys = [(t, p) for (t, p) in keys]
    keys.append((1.0, targets[0]))
    # rotate so motion starts with move: hold then move
    arm, ef = [], []
    for k in range(N):
        t = k / N
        gx, gy = keyframe_track(keys, t)
        d, e, g = arm_d(bx, by, gx, gy, l1, l2)
        arm.append(d)
    tgt = []
    for i, (x, y) in enumerate(targets):
        tgt.append(f'<g opacity="0">{discrete_show(i, T, dur)}<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{GOLD}" stroke-width="1.5"/>'
                   f'<path d="M{x-14},{y} h8 M{x+6},{y} h8 M{x},{y-14} v8 M{x},{y+6} v8" stroke="{GOLD}" stroke-width="1.5"/></g>')
    return f'''
{"".join(edges)}{"".join(pulses)}{nd}{labels}
<line x1="270" y1="30" x2="270" y2="225" stroke="{LINE}"/>
<circle cx="{bx}" cy="{by}" r="{l1+l2}" fill="none" stroke="{STEEL}" stroke-opacity="0.18" stroke-dasharray="3 6"/>
{"".join(tgt)}
{path_anim(arm, dur, f'fill="none" stroke="{STEEL}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"')}
<circle cx="{bx}" cy="{by}" r="8" fill="{BG0}" stroke="{STEEL}" stroke-width="2"/>
<text x="560" y="222" class="mono" fill="{MUTED}" font-size="10" text-anchor="end" letter-spacing="1.5">CLICK-TO-REACH</text>'''



# ---- 06 SCARA chip placement
def illus_scara():
    dur = 15
    bx, by, l1, l2 = 300, 222, 110, 95
    gx0, gy0 = 236, 52  # grid origin (3 rows x 5 cols)
    sp = 32
    stacks = [(140, 160), (460, 160)]
    slots = [(gx0 + c * sp, gy0 + r * sp) for r in range(3) for c in range(5)]
    n = len(slots)
    keys = []
    seg = 1.0 / n
    for i, slot in enumerate(slots):
        src = stacks[0] if i < 10 else stacks[1]
        t0 = i * seg
        keys += [(t0, src), (t0 + seg * 0.15, src), (t0 + seg * 0.75, slot), (t0 + seg * 0.9, slot)]
    keys.append((1.0, stacks[0]))
    N = 300
    arm = []
    chip = []
    for k in range(N):
        t = k / N
        gx, gy = keyframe_track(keys, t)
        d, _, _ = arm_d(bx, by, gx, gy, l1, l2, elbow_up=True)
        arm.append(d)
    placed = []
    for i, (x, y) in enumerate(slots):
        appear = (i * seg + seg * 0.8)
        placed.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{GOLD}" fill-opacity="0.85" stroke="{GOLD}" opacity="0">'
                      f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;{appear:.4f};0.985;1" calcMode="discrete" dur="{dur}s" repeatCount="indefinite"/></circle>')
    slot_outline = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="none" stroke="{LINE}" stroke-dasharray="3 3"/>' for x, y in slots)
    stack_svg = "".join(f'<circle cx="{x}" cy="{y}" r="13" fill="{BG2}" stroke="{STEEL}"/><circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{STEEL}" stroke-opacity="0.5"/>' for x, y in stacks)
    # carried chip follows end effector during transport only: approximate via same keys
    carry = []
    for k in range(N):
        t = k / N
        gx, gy = keyframe_track(keys, t)
        carry.append(f"M{f(gx-11)},{f(gy)} a11,11 0 1 0 22,0 a11,11 0 1 0 -22,0")
    car_op = []
    for i in range(n):
        t0 = i * seg
        car_op.append((t0 + seg * 0.15, 1))
        car_op.append((t0 + seg * 0.8, 0))
    kt = ["0"] + [f"{t:.4f}" for t, _ in car_op]
    vals = ["0"] + [str(v) for _, v in car_op]
    return f'''
{slot_outline}{stack_svg}{"".join(placed)}
<text x="140" y="196" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle">STACK A · 10</text>
<text x="460" y="196" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle">STACK B · 5</text>
<text x="300" y="28" class="mono" fill="{MUTED}" font-size="10" text-anchor="middle" letter-spacing="1.5">3 x 5 TARGET PATTERN</text>
<path fill="{GOLD}" fill-opacity="0.9" d="{carry[0]}" opacity="0">{anim("d", carry + [carry[0]], dur)}<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{";".join(kt)}" values="{";".join(vals)}"/></path>
{path_anim(arm, dur, f'fill="none" stroke="{STEEL}" stroke-width="12" stroke-opacity="0.85" stroke-linecap="round" stroke-linejoin="round"')}
<circle cx="{bx}" cy="{by}" r="12" fill="{BG0}" stroke="{STEEL}" stroke-width="2"/>
<text x="560" y="222" class="mono" fill="{MUTED}" font-size="10" text-anchor="end" letter-spacing="1.5">SCARA · TOP VIEW</text>
<text x="40" y="222" class="mono" fill="{MUTED}" font-size="10" letter-spacing="1.5">SUCTION + INDUCTIVE SENSE</text>'''


def build_cards():
    card("peg-transfer", "01", "BIMANUAL MANIPULATION · SIMULATION",
         "FLS Peg Transfer Benchmark",
         ["Two YAM arms in Isaac Sim 6.0.1 perform a surgical", "skills exam, driven by frontier vision-language models."],
         [("12 / 12", "TRANSFERS"), ("0", "DROPS"), ("2", "MODELS VS BASELINE")], illus_peg(),
         "Animation of two robot arms passing a triangular object mid-air between pegboards.")
    card("nexus", "02", "FIELD ROBOTICS · EMBEDDED",
         "NEXUS Exploration Rover",
         ["Rover, firmware, telemetry and mission-control dashboard", "built from scratch in 36 hours, with layered motor safety."],
         [("36 h", "BUILD TIME"), ("900 ms", "WATCHDOG"), ("6", "MISSION STATES")], illus_rover(),
         "Animation of a rover crossing terrain with an ultrasonic sensor and a cycling mission state machine.")
    card("neural-ik", "03", "LEARNING-BASED CONTROL",
         "Neural Inverse Kinematics",
         ["An MLP trained from scratch maps end-effector targets", "to joint angles, validated against forward kinematics."],
         [("2-DOF", "PLANAR ARM"), ("MLP", "PYTORCH"), ("FK", "VALIDATION")], illus_ik(),
         "Animation of a neural network and a robot arm reaching successive target points.")
    card("scara-chip-placement", "04", "INDUSTRIAL ROBOTICS",
         "Yamaha SCARA Chip Placement",
         ["A Yamaha SCARA picks 15 poker chips from two stacks", "and places them in a 3 x 5 grid using suction."],
         [("15", "CHIPS PLACED"), ("3 x 5", "TARGET GRID"), ("RCX 340", "CONTROLLER")], illus_scara(),
         "Animation of a SCARA robot, seen from above, placing chips from two stacks into a three by five grid.")


build_cards()
