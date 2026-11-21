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
GAP = 250.0                   # px between layers

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


L1 = L2 = L3 = L4 = 0.0   # every layer drawn flat at 0; CSS moves them apart
LIFTS = [3 * GAP, 2 * GAP, GAP, 0.45 * GAP]   # top panel, frame, electronics, bottom panel
el = []
groups = {}

# ---- 4. bottom panel
el += slab(L4, CREAM_D, "#D3C7AF", "#C7BBA2")

groups['bottom'] = el; el = []
# ---- 3. electronics
mid = B / 2
# wires first (under the parts)
wire = 'stroke="%s" stroke-width="3" fill="none" stroke-linecap="round" class="wire"' % GREEN
readers = [(mid, 70), (B - 70, mid), (mid, B - 70), (70, mid)]
screens_at = []    # screens left out of the drawing for now (were at the ends of one diagonal)
for rx, ry in readers + screens_at:
    a, b = p(mid, mid, 0, L3), p(rx, ry, 0, L3)
    el.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" {wire}/>')
# readers: cream pad with red waves
for rx, ry in readers:
    h = 34
    el.append(poly(rect(rx - h, ry - h, rx + h, ry + h, L3), CREAM, NAVY, 1.5))
    cx, cy = p(rx, ry, 0, L3)
    for i_r, r in enumerate((6, 11, 16)):
        el.append(f'<ellipse class="ring r{i_r + 1}"'
                  f'  cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * C30 * S * 1.4:.1f}" ry="{r * S30 * S * 1.4:.1f}" '
                  f'fill="none" stroke="{RED}" stroke-width="1.8"/>')
    el.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="2.6" ry="1.5" fill="{RED}"/>')
# chip: navy square with cream legs, like the logo
ch = 56
for i in range(5):
    t = -ch + (i + 1) * 2 * ch / 6
    for (x0, y0, x1, y1) in [(-ch - 10, t - 3, -ch, t + 3), (ch, t - 3, ch + 10, t + 3),
                             (t - 3, -ch - 10, t + 3, -ch), (t - 3, ch, t + 3, ch + 10)]:
        el.append(poly(rect(mid + x0, mid + y0, mid + x1, mid + y1, L3), CREAM, NAVY, 0.8))
el.append(poly(rect(mid - ch, mid - ch, mid + ch, mid + ch, L3), NAVY))
el.append(poly(rect(mid - 24, mid - 24, mid + 24, mid + 24, L3), "none", CREAM, 2))
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

groups['elec'] = el; el = []
# ---- 2. frame: a solid border all round, and a honeycomb filling the whole inside
wb = 16.0          # border width (mm)
HEX = 68.0         # honeycomb cell size (centre to corner, mm)
HW = 5.5           # honeycomb wall thickness (mm)
f = []
inner = [p(wb, wb, 0, L2), p(B - wb, wb, 0, L2), p(B - wb, B - wb, 0, L2), p(wb, B - wb, 0, L2)]
f.append('<clipPath id="hc"><polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in inner) + '"/></clipPath>')
cells = []
dx, dy = 1.5 * HEX, math.sqrt(3) * HEX
col = 0
x = -HEX
while x < B + 2 * HEX:
    y = (-dy / 2 if col % 2 else 0.0) - dy
    while y < B + 2 * dy:
        pts = [p(x + HEX * math.cos(math.radians(60 * i)), y + HEX * math.sin(math.radians(60 * i)), 0, L2) for i in range(6)]
        cells.append("M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z")
        y += dy
    x += dx
    col += 1
hw_px = HW * S * 1.0
f.append(f'<path d="{" ".join(cells)}" fill="none" stroke="{FRAME}" stroke-width="{hw_px:.1f}" '
         f'stroke-linejoin="round" clip-path="url(#hc)"/>')
# border: outer square minus inner square
outer = [p(0, 0, 0, L2), p(B, 0, 0, L2), p(B, B, 0, L2), p(0, B, 0, L2)]
ring = ("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in outer) + " Z M"
        + " L".join(f"{x:.1f},{y:.1f}" for x, y in reversed(inner)) + " Z")
t = 8.0
bq, cq, dq = outer[1], outer[2], outer[3]
f.insert(0, poly([bq, cq, (cq[0], cq[1] + t), (bq[0], bq[1] + t)], "#B5A47C"))
f.insert(0, poly([cq, dq, (dq[0], dq[1] + t), (cq[0], cq[1] + t)], "#BFAF88"))
f.append(f'<path d="{ring}" fill="{FRAME}" fill-rule="evenodd"/>')
el += f

groups['frame'] = el; el = []
# ---- 1. top panel (green, like the logo), with the card cross faintly marked
el += slab(L1, GREEN, GREEN_D, "#145039")
for (x0, y0, x1, y1) in [(mid - 45, 40, mid + 45, 170), (mid - 45, B - 170, mid + 45, B - 40),
                         (40, mid - 45, 170, mid + 45), (B - 170, mid - 45, B - 40, mid + 45)]:
    el.append(poly(rect(x0, y0, x1, y1, L1), "none", CREAM, 1.5, ' stroke-dasharray="5 5" opacity="0.6"'))

groups['top'] = el

# ---- labels, alternating right / left so the board itself sits in the middle of the drawing;
# they travel with their layer. Long names are split over two lines.
NAMES = {"top": ("Top panel",), "frame": ("Frame",), "elec": ("Circuit",), "bottom": ("Bottom panel",)}
SIDE = {"top": "r", "frame": "l", "elec": "r", "bottom": "l"}
LABEL_SPACE = 270            # room for labels on each side of the board (drawing units)
rx, _ = p(B, 0)
lx, _ = p(0, B)
labels = {}
for key, lines in NAMES.items():
    if key == "elec":                  # no outline on this layer: point at the right-hand card reader
        ax, ay = p(B - 70 + 34, mid)
        tx, anchor, lx2 = rx + 40, "start", rx + 30
    elif SIDE[key] == "r":
        ax, ay = p(B, B * 0.22)
        tx, anchor, lx2 = rx + 40, "start", rx + 30
    else:
        ax, ay = p(B * 0.22, B)
        tx, anchor, lx2 = lx - 40, "end", lx - 30
    n = len(lines)
    tsp = "".join(f'<tspan x="{tx:.1f}" dy="{0 if i == 0 else 1.15:.2f}em">{t}</tspan>' for i, t in enumerate(lines))
    labels[key] = (f'<g class="lab"><circle cx="{ax:.1f}" cy="{ay:.1f}" r="4" fill="{NAVY}"/>'
                   f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx2:.1f}" y2="{ay:.1f}" stroke="{NAVY}" stroke-width="1.5" opacity="0.4"/>'
                   f'<text y="{ay:.1f}" dy="{0.35 - (n - 1) * 0.575:.2f}em" text-anchor="{anchor}" font-size="24" font-weight="600" fill="{NAVY}">{tsp}</text></g>')

_, ty = p(0, 0)
_, by = p(B, B)
minx, maxx = lx - LABEL_SPACE, rx + LABEL_SPACE
miny, maxy = ty - LIFTS[0] - 20, by - LIFTS[3] + 30
vb = f"{minx:.0f} {miny:.0f} {maxx - minx:.0f} {maxy - miny:.0f}"

# collapsed: layers start stacked close together, then move apart (exploded)
order = ["bottom", "elec", "frame", "top"]
lift = {"top": LIFTS[0], "frame": LIFTS[1], "elec": LIFTS[2], "bottom": LIFTS[3]}
# How open the board is comes from the CSS variable --open (0 = closed, 1 = fully apart).
# The page's slider sets it; on load the page opens the board once by itself.
css = ["#board-svg{overflow:visible;--open:1}",
       "#board-svg .lab{opacity:clamp(0,calc((var(--open) - .55) * 3),1);transition:opacity .2s}",
       # card readers send rings outwards; dots run along the wires to the chip
       "#board-svg .ring{animation:ring 1.8s ease-out infinite;transform-box:fill-box;transform-origin:center}",
       "#board-svg .r2{animation-delay:.3s}#board-svg .r3{animation-delay:.6s}",
       "@keyframes ring{0%{opacity:0;transform:scale(.6)}30%{opacity:1}100%{opacity:0;transform:scale(1.15)}}",
       "#board-svg .wire{stroke-dasharray:2 14;opacity:.7;animation:wire 1.2s linear infinite}",
       "@keyframes wire{to{stroke-dashoffset:16}}",
       "@media (prefers-reduced-motion:reduce){#board-svg .ring,#board-svg .wire{animation:none}}"]
MIDDLE = 1.5 * GAP   # closed: all layers meet halfway, so the top comes down and the bottom comes up
# closed: each layer sits right on the one below (panels and frame are drawn 8 units thick)
CLOSED = {"bottom": MIDDLE - 8, "elec": MIDDLE - 8, "frame": MIDDLE, "top": MIDDLE + 8}
for i, k in enumerate(order):
    start = CLOSED[k]
    css.append(f"#board-svg .{k}{{transform:translateY(calc(({start:.0f} + {lift[k] - start:.0f} * var(--open)) * -1px))}}")
# "15 mm thickness": a measure beside the closed stack, shown only while the board is closed
cx_r, cy_r = p(B, 0)
y_top = cy_r - CLOSED["top"]
y_bot = cy_r - CLOSED["bottom"] + 8
mx = cx_r + 22
thick = (f'<g class="thick"><line x1="{mx:.1f}" y1="{y_top:.1f}" x2="{mx:.1f}" y2="{y_bot:.1f}" stroke="{NAVY}" stroke-width="1.5" opacity="0.5"/>'
         f'<line x1="{mx - 7:.1f}" y1="{y_top:.1f}" x2="{mx + 7:.1f}" y2="{y_top:.1f}" stroke="{NAVY}" stroke-width="1.5" opacity="0.5"/>'
         f'<line x1="{mx - 7:.1f}" y1="{y_bot:.1f}" x2="{mx + 7:.1f}" y2="{y_bot:.1f}" stroke="{NAVY}" stroke-width="1.5" opacity="0.5"/>'
         f'<text x="{mx + 18:.1f}" y="{(y_top + y_bot) / 2:.1f}" dy="0.35em" font-size="24" font-weight="600" fill="{NAVY}">15 mm thickness</text></g>')
css.append("#board-svg .thick{opacity:clamp(0,calc((.3 - var(--open)) * 5),1);transition:opacity .2s}")
body = thick + "".join(f'<g class="layer {k}">' + "".join(groups[k]) + labels[k] + "</g>" for k in order)
svg = (f'<svg id="board-svg" xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
       f'font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">'
       f'<title>NFCBOARD exploded view: top panel, frame, circuit, bottom panel</title>'
       f'<style>{"".join(css)}</style>' + body + "</svg>")
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# standalone copy (fully open), and the same drawing placed inside index.html between the markers
open(os.path.join(root, "assets", "board-exploded.svg"), "w").write(svg)
page_path = os.path.join(root, "index.html")
page = open(page_path).read()
a, b = "<!-- BOARD START -->", "<!-- BOARD END -->"
if a in page and b in page:
    page = page[:page.index(a) + len(a)] + svg + page[page.index(b):]
    open(page_path, "w").write(page)
print(vb, len(svg))
