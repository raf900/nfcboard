"""Draws assets/board-exploded.svg: the NFCBOARD board as an exploded view in 4 layers.

Sizes follow the 3D design (version 3): board 800 x 800 mm, 60 mm seat lanes from the middle of
each side, centre box 150 x 70 mm. Screens are 3.5" (about 71 x 53 mm), two back to back at each
end of one diagonal. Electronics are drawn simplified: one chip in the centre, one reader per seat.

Run: python3 tools/exploded.py
"""
import math
import os

B = 800.0
S = 0.52                      # px per mm
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
OX, OY = 470.0, 70.0          # where board corner (0,0) lands on the page
GAP = 285.0                   # px between layers

GREEN, CREAM, NAVY, RED = "#1F6E54", "#F6F1E7", "#12283F", "#D9473E"
GREEN_D, CREAM_D, FRAME = "#17563F", "#E6DCC8", "#C9B994"


def p(x, y, z=0.0, lift=0.0):
    """board mm (x right-down, y left-down, z up mm) + layer lift (px) -> page px."""
    X = OX + (x - y) * C30 * S
    Y = OY + (x + y) * S30 * S - z * S - lift
    return X, Y


def poly(pts, fill, stroke="none", sw=0, extra=""):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke != "none" else ""
    return f'<polygon points="{d}" fill="{fill}"{st}{extra}/>'


def rect(x0, y0, x1, y1, lift, z=0.0):
    return [p(x0, y0, z, lift), p(x1, y0, z, lift), p(x1, y1, z, lift), p(x0, y1, z, lift)]


def slab(lift, top, side_l, side_r, t=8.0, extra=""):
    """a flat panel: top face plus the two visible edges (front-left and front-right)."""
    out = []
    a, b, c_, d = p(0, 0, 0, lift), p(B, 0, 0, lift), p(B, B, 0, lift), p(0, B, 0, lift)
    # visible edges: x = B side (b->c) and y = B side (c->d)
    out.append(poly([b, c_, (c_[0], c_[1] + t), (b[0], b[1] + t)], side_r))
    out.append(poly([c_, d, (d[0], d[1] + t), (c_[0], c_[1] + t)], side_l))
    out.append(poly([a, b, c_, d], top, extra=extra))
    return out


def bar(x0, y0, x1, y1, w, lift, fill):
    """a flat strip of width w (mm) from (x0,y0) to (x1,y1)."""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * w / 2, dx / n * w / 2
    return poly([p(x0 + nx, y0 + ny, 0, lift), p(x1 + nx, y1 + ny, 0, lift),
                 p(x1 - nx, y1 - ny, 0, lift), p(x0 - nx, y0 - ny, 0, lift)], fill)


L1, L2, L3, L4 = 3 * GAP, 2 * GAP, 1 * GAP, 0.0   # top panel, frame, electronics, bottom panel
el = []

# ---- 4. bottom panel
el += slab(L4, CREAM_D, "#D3C7AF", "#C7BBA2")

# ---- 3. electronics
mid = B / 2
el.append(poly([p(0, 0, 0, L3), p(B, 0, 0, L3), p(B, B, 0, L3), p(0, B, 0, L3)], "none", NAVY, 1.2,
              ' stroke-dasharray="6 6" opacity="0.3"'))
# wires first (under the parts)
wire = 'stroke="%s" stroke-width="2" fill="none" stroke-dasharray="1 0"' % GREEN
readers = [(mid, 70), (B - 70, mid), (mid, B - 70), (70, mid)]
screens_at = [(B - 110, 110), (110, B - 110)]    # ends of the diagonal (800,0)-(0,800)
for rx, ry in readers + screens_at:
    a, b = p(mid, mid, 0, L3), p(rx, ry, 0, L3)
    el.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" {wire} opacity="0.55"/>')
# readers: cream pad with red waves
for rx, ry in readers:
    h = 26
    el.append(poly(rect(rx - h, ry - h, rx + h, ry + h, L3), CREAM, NAVY, 1.5))
    cx, cy = p(rx, ry, 0, L3)
    for r in (6, 11, 16):
        el.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * C30 * S * 1.4:.1f}" ry="{r * S30 * S * 1.4:.1f}" '
                  f'fill="none" stroke="{RED}" stroke-width="1.6"/>')
    el.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="2.6" ry="1.5" fill="{RED}"/>')
# chip: navy square with cream legs, like the logo
ch = 45
for i in range(5):
    t = -ch + 15 + i * 15
    for (x0, y0, x1, y1) in [(-ch - 10, t - 3, -ch, t + 3), (ch, t - 3, ch + 10, t + 3),
                             (t - 3, -ch - 10, t + 3, -ch), (t - 3, ch, t + 3, ch + 10)]:
        el.append(poly(rect(mid + x0, mid + y0, mid + x1, mid + y1, L3), CREAM, NAVY, 0.8))
el.append(poly(rect(mid - ch, mid - ch, mid + ch, mid + ch, L3), NAVY))
el.append(poly(rect(mid - 20, mid - 20, mid + 20, mid + 20, L3), "none", CREAM, 1.6))
# screens: two back to back, standing on the diagonal near each end; plane along (-1, 1)
SW, SH = 71.0, 53.0
for sx, sy in screens_at:
    u = (-1 / math.sqrt(2), 1 / math.sqrt(2))
    x0, y0 = sx - u[0] * SW / 2, sy - u[1] * SW / 2
    x1, y1 = sx + u[0] * SW / 2, sy + u[1] * SW / 2
    base = 6
    el.append(poly([p(x0, y0, 0, L3), p(x1, y1, 0, L3), p(x1, y1, base + SH, L3), p(x0, y0, base + SH, L3)], NAVY))
    m = 5
    ix0, iy0 = x0 + u[0] * m, y0 + u[1] * m
    ix1, iy1 = x1 - u[0] * m, y1 - u[1] * m
    el.append(poly([p(ix0, iy0, base + m, L3), p(ix1, iy1, base + m, L3),
                    p(ix1, iy1, base + SH - m, L3), p(ix0, iy0, base + SH - m, L3)], GREEN))
    # tiny suit marks on the screen
    cx, cy = p(sx, sy, base + SH / 2, L3)
    el.append(f'<text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle" font-size="12" fill="{CREAM}" '
              f'font-family="Segoe UI Symbol, DejaVu Sans, sans-serif">&#9824;&#9829;</text>')

# ---- 2. frame (border, seat rails, diagonals, centre box)
lane0, lane1 = 370.0, 430.0
wb, wr, wd = 12.5, 10.0, 6.0
f = []
for a0, a1 in [(0, lane0), (lane1, B)]:
    f.append(bar(a0, wb / 2, a1, wb / 2, wb, L2, FRAME))           # y = 0 side
    f.append(bar(a0, B - wb / 2, a1, B - wb / 2, wb, L2, FRAME))   # y = B side
    f.append(bar(wb / 2, a0, wb / 2, a1, wb, L2, FRAME))           # x = 0 side
    f.append(bar(B - wb / 2, a0, B - wb / 2, a1, wb, L2, FRAME))   # x = B side
rail_end = 320.0
for xr in (lane0 - wr / 2, lane1 + wr / 2):
    f.append(bar(xr, 0, xr, rail_end, wr, L2, FRAME))
    f.append(bar(xr, B, xr, B - rail_end, wr, L2, FRAME))
    f.append(bar(0, xr, rail_end, xr, wr, L2, FRAME))
    f.append(bar(B, xr, B - rail_end, xr, wr, L2, FRAME))
for cx_, cy_ in [(0, 0), (B, 0), (B, B), (0, B)]:
    ex = mid + (25 if cx_ > mid else -25)
    ey = mid + (25 if cy_ > mid else -25)
    sx_ = 20 if cx_ == 0 else B - 20
    sy_ = 20 if cy_ == 0 else B - 20
    f.append(bar(sx_, sy_, ex, ey, wd, L2, FRAME))
    # corner triangles
    dx = 1 if cx_ == 0 else -1
    dy = 1 if cy_ == 0 else -1
    f.append(poly([p(cx_ + dx * wb, cy_ + dy * wb, 0, L2), p(cx_ + dx * 50, cy_ + dy * wb, 0, L2),
                   p(cx_ + dx * wb, cy_ + dy * 50, 0, L2)], FRAME))
f.append(poly(rect(mid - 80, mid - 35, mid + 80, mid + 35, L2), "none", FRAME, 7))
el += f

# ---- 1. top panel (green, like the logo), with the card cross faintly marked
el += slab(L1, GREEN, GREEN_D, "#145039")
for (x0, y0, x1, y1) in [(mid - 45, 40, mid + 45, 170), (mid - 45, B - 170, mid + 45, B - 40),
                         (40, mid - 45, 170, mid + 45), (B - 170, mid - 45, B - 40, mid + 45)]:
    el.append(poly(rect(x0, y0, x1, y1, L1), "none", CREAM, 1.5, ' stroke-dasharray="5 5" opacity="0.6"'))

# ---- labels on the left, with leader lines to each layer's left corner
labels = [(L1, "Top panel"), (L2, "Frame"), (L3, "Chip, card readers, screens"), (L4, "Bottom panel")]
lab = []
for lift, text in labels:
    ax, ay = p(0, B * 0.75, 0, lift)
    tx = 70
    lab.append(f'<line x1="{tx + 4}" y1="{ay:.1f}" x2="{ax - 8:.1f}" y2="{ay:.1f}" stroke="{NAVY}" '
               f'stroke-width="1" opacity="0.35"/>')
    lab.append(f'<circle cx="{ax - 8:.1f}" cy="{ay:.1f}" r="3" fill="{NAVY}" opacity="0.6"/>')
    lab.append(f'<text x="{tx}" y="{ay - 12:.1f}" text-anchor="end" font-size="34" font-weight="600" '
               f'fill="{NAVY}">{text}</text>')

xs, ys = [], []
import re
for s in el:
    for m in re.finditer(r"(-?\d+\.\d),(-?\d+\.\d)", s):
        xs.append(float(m.group(1))); ys.append(float(m.group(2)))
minx = -400
maxx = max(xs) + 20
miny = min(ys) - 20
maxy = max(ys) + 20
vb = f"{minx:.0f} {miny:.0f} {maxx - minx:.0f} {maxy - miny:.0f}"

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
       f'font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">'
       f'<title>NFCBOARD exploded view: top panel, frame, electronics, bottom panel</title>'
       + "".join(el) + "".join(lab) + "</svg>")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "board-exploded.svg")
open(out, "w").write(svg)
print(out, vb, len(svg))
