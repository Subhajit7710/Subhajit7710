#!/usr/bin/env python3
"""
Turn the prepped portrait (source-prepped.png) into a monochrome ASCII-art SVG
that "prints" itself like a terminal, then holds still.

Why an SVG: GitHub READMEs strip <script> and most inline CSS, but an SVG
embedded with <img> keeps its own SMIL / CSS-keyframe animations. So all the
motion lives inside this file and the README only places it.

How it animates: each row of characters sits behind a clipPath whose width
grows 0 -> full (left-to-right wipe), with a small block cursor riding the
wipe edge. Rows start one after another, top to bottom, so a single cursor
appears to raster down the portrait. Everything uses fill="freeze": it plays
once and stays.

    python scripts/make_ascii_svg.py [input.png] [output.svg]
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previews
    COLS=140 python scripts/make_ascii_svg.py   # more/less detail
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "subhajit-ascii.svg")
STATIC = bool(os.environ.get("STATIC"))

USER = "subhajit"
NAME = "Subhajit Mahapatra"

# ---- grid ----------------------------------------------------------------
# A monospace cell is ~8 wide x 15 tall, so a square photo needs
# ROWS = COLS * 8/15 to keep its proportions.
COLS = int(os.environ.get("COLS", 132))
ROWS = round(COLS * 8 / 15)
ART_W = 800.0
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8
ART_H = ROWS * CELL_H

RAMP = " .`:-=+*cs#%@"   # light/sparse -> dark/dense; leading space = blank
GAMMA = 1.0              # >1 pushes mid-tones toward the sparse end
CONTRAST = 1.05
WHITE_FLOOR = 0.93       # anything brighter than this becomes a blank

# ---- frame ---------------------------------------------------------------
PAD = 20
TITLEBAR_H = 30
STATUS_H = 36
W = 840                               # same canvas as info-card.svg so the
H = 880                               # two panels line up side by side
ART_TOP = TITLEBAR_H + (H - TITLEBAR_H - STATUS_H - ART_H) / 2

BG, BG2 = "#0d1117", "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
ACCENT = "#39d353"

# whole portrait prints in ~6 s regardless of resolution
ROW_DUR = 6.0 / ROWS

# ---- 1. sample the image -------------------------------------------------
im = Image.open(SRC).convert("L")
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows = []
for y in range(ROWS):
    line = []
    for x in range(COLS):
        lum = (px[x, y] / 255.0) ** GAMMA
        if lum >= WHITE_FLOOR:
            line.append(" ")
            continue
        i = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        line.append(RAMP[max(0, min(len(RAMP) - 1, i))])
    rows.append("".join(line).rstrip())

# trim fully blank rows at top/bottom so the art is vertically centred
while rows and not rows[0].strip():
    rows.pop(0)
while rows and not rows[-1].strip():
    rows.pop()
ROWS_USED = len(rows)
ART_TOP = TITLEBAR_H + (H - TITLEBAR_H - STATUS_H - ROWS_USED * CELL_H) / 2

# ---- 2. assemble the SVG -------------------------------------------------
p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">')
p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')

# title bar
p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">{USER}@github: ~$ ./portrait.sh</text>')

font_size = CELL_H * 0.86
x0 = (W - ART_W) / 2
for r, line in enumerate(rows):
    row_y = ART_TOP + r * CELL_H
    base = row_y + CELL_H * 0.74
    if not line.strip():
        continue
    # textLength pins each row to its exact width so columns stay aligned
    width = len(line) * CELL_W
    text = (f'<text xml:space="preserve" x="{x0}" y="{base:.1f}" fill="{INK}" font-size="{font_size:.2f}" '
            f'textLength="{width:.1f}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC:
        p.append(text)
        continue
    begin = r * ROW_DUR
    p.append(f'<clipPath id="r{r}"><rect x="{x0}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
             f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#r{r})">{text}</g>')
    # cursor riding the wipe edge, visible only while this row prints
    p.append(f'<rect y="{row_y+0.5:.1f}" width="{CELL_W:.2f}" height="{CELL_H-1:.2f}" fill="{ACCENT}" opacity="0">'
             f'<animate attributeName="x" from="{x0}" to="{x0+width:.1f}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{begin+ROW_DUR:.3f}s"/></rect>')

# status bar with a blinking cursor
sy = H - STATUS_H
p.append(f'<line x1="0" y1="{sy}" x2="{W}" y2="{sy}" stroke="{FRAME}"/>')
ty = sy + 23
prompt = f"{USER}@github:~$ whoami "
p.append(f'<text x="{PAD}" y="{ty}" fill="{MUTED}" font-size="13">{prompt}'
         f'<tspan fill="{INK}">{NAME}</tspan></text>')
cx = PAD + (len(prompt) + len(NAME) + 1) * 13 * 0.6
p.append(f'<rect x="{cx:.1f}" y="{ty-12}" width="8" height="15" fill="{ACCENT}">'
         f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" '
         f'repeatCount="indefinite"/></rect>')

p.append("</svg>")
svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {W}x{H}, {COLS}x{ROWS_USED} chars, {len(svg)//1024} KB")
