#!/usr/bin/env python3
"""
Hand-authored neofetch-style info card (info-card.svg) that sits beside the
ASCII portrait. It tells the story (role, study, stack, projects) while the
contribution heatmap carries the numbers.

Animation: the `$ neofetch` prompt types itself, then each key/value row fades
and slides in on a short stagger (CSS keyframes inside the SVG -- GitHub plays
those for <img>-embedded SVGs, it just never runs JS). Plays once, then holds.

Edit the ROWS / PROJECTS lists below and re-run:

    python scripts/make_info_card.py [output.svg]
    STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

USER = "subhajit"
HOST = "github"

# (key, value) -- keep values under ~44 characters so they fit the card
ROWS = [
    ("Name", "Subhajit Mahapatra"),
    ("Role", "AI & Full-Stack Developer"),
    ("Now", "MCA @ VIT Vellore (class of 2027)"),
    ("Prev", "Frontend Intern @ Techplement"),
    ("Edu", "BCA @ IEM Kolkata (2024)"),
    ("Location", "India"),
    ("Focus", "AI reasoning · system design"),
    (None, None),  # spacer
    ("Languages", "Python · Java · JavaScript · TS · C"),
    ("Web", "React · Node.js · Express · REST · JWT"),
    ("Data", "PostgreSQL · MySQL · MongoDB · Redis"),
    ("ML / AI", "PyTorch · Hugging Face · LoRA · NLP"),
    ("Tools", "Git · Docker · AWS · Kafka · CI/CD"),
]

# (name, one-liner)
PROJECTS = [
    ("JustAdvisor AI", "Mistral-7B + LoRA as an AI judge"),
    ("FamilyWellcare", "microservices · BullMQ · Socket.IO"),
    ("Meeting Summarizer", "Whisper + Gemini meeting notes"),
    ("Car Lifecycle", "Java backend for car lifecycle mgmt"),
]

# ---- look ----------------------------------------------------------------
W, H = 840, 880                      # same canvas as subhajit-ascii.svg
PAD = 34
TITLEBAR_H = 30
FONT = 23                            # shown at ~half size in the README
LINE = 34
CHAR_W = FONT * 0.6
KEY_COL = PAD + CHAR_W * 11

BG, BG2 = "#0d1117", "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
KEY = "#22d3ee"                       # cyan keys, like neofetch
GREEN = "#39d353"
GOLD = "#f2cc60"
PINK = "#ff7b72"

STAGGER = 0.11
FADE = 0.45
TYPE_DUR = 0.7


def esc(s):
    return html.escape(s, quote=True)


p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">')
if not STATIC:
    p.append('<style>'
             '.r{opacity:0;animation:in ' + f'{FADE}' + 's cubic-bezier(.2,.8,.2,1) both}'
             '@keyframes in{0%{opacity:0;transform:translateX(-14px)}100%{opacity:1;transform:translateX(0)}}'
             '@media (prefers-reduced-motion: reduce){.r{opacity:1!important;animation:none!important;transform:none!important}}'
             '</style>')
p.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{20 + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">{USER}@{HOST}: ~$ neofetch</text>')

y = TITLEBAR_H + 52

# typed prompt
cmd = f'<text x="{PAD}" y="{y}" font-size="{FONT}" fill="{GREEN}">$ <tspan fill="{INK}">neofetch --profile</tspan></text>'
if STATIC:
    p.append(cmd)
else:
    cmd_w = CHAR_W * len("$ neofetch --profile") + 4
    p.append(f'<clipPath id="cmd"><rect x="{PAD}" y="{y-FONT}" height="{FONT+8}" width="0">'
             f'<animate attributeName="width" from="0" to="{cmd_w:.1f}" begin="0.2s" dur="{TYPE_DUR}s" '
             f'calcMode="discrete" values="' + ";".join(f"{CHAR_W*k:.1f}" for k in range(2, 21)) + f';{cmd_w:.1f}" '
             f'fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#cmd)">{cmd}</g>')

t = 0.2 + TYPE_DUR + 0.15


def row(content, delay):
    if STATIC:
        p.append(f'<g>{content}</g>')
    else:
        p.append(f'<g class="r" style="animation-delay:{delay:.2f}s">{content}</g>')


# user@host header + underline
y += LINE + 6
head = f"{USER}@{HOST}"
row(f'<text x="{PAD}" y="{y}" font-size="{FONT}" font-weight="700">'
    f'<tspan fill="{KEY}">{USER}</tspan><tspan fill="{INK}">@</tspan><tspan fill="{KEY}">{HOST}</tspan></text>'
    f'<text x="{PAD}" y="{y + LINE*0.62:.1f}" font-size="{FONT}" fill="{MUTED}">{"-" * len(head)}</text>', t)
t += STAGGER
y += LINE + 8

for key, val in ROWS:
    if key is None:
        y += LINE * 0.45
        continue
    row(f'<text x="{PAD}" y="{y}" font-size="{FONT}" fill="{KEY}" font-weight="700">{esc(key)}</text>'
        f'<text x="{KEY_COL:.1f}" y="{y}" font-size="{FONT}" fill="{INK}">{esc(val)}</text>', t)
    t += STAGGER
    y += LINE

# projects block
y += LINE * 0.45
row(f'<text x="{PAD}" y="{y}" font-size="{FONT}" fill="{GOLD}" font-weight="700">Projects</text>', t)
t += STAGGER
y += LINE
for name, desc in PROJECTS:
    row(f'<text x="{PAD}" y="{y}" font-size="{FONT-2}" fill="{MUTED}">›</text>'
        f'<text x="{PAD + CHAR_W*1.6:.1f}" y="{y}" font-size="{FONT-2}" fill="{INK}" font-weight="700">{esc(name)}</text>'
        f'<text x="{PAD + CHAR_W*1.6:.1f}" y="{y + LINE*0.72:.1f}" font-size="{FONT-4}" fill="{MUTED}">{esc(desc)}</text>', t)
    t += STAGGER
    y += LINE * 1.45

# neofetch colour blocks
y = H - 46
blocks = ["#30363d", PINK, GREEN, GOLD, "#58a6ff", "#bc8cff", KEY, INK]
bw = 40
bx = PAD
cells = "".join(f'<rect x="{bx + i*bw}" y="{y}" width="{bw}" height="20" fill="{c}"/>' for i, c in enumerate(blocks))
row(cells, t)
t += STAGGER

# blinking cursor after everything has landed
cur_x = PAD + len(blocks) * bw + 18
if STATIC:
    p.append(f'<rect x="{cur_x}" y="{y}" width="11" height="20" fill="{GREEN}"/>')
else:
    p.append(f'<rect x="{cur_x}" y="{y}" width="11" height="20" fill="{GREEN}" opacity="0">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" begin="{t:.2f}s" repeatCount="indefinite"/></rect>')

p.append("</svg>")
svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {W}x{H}, {len(svg)//1024} KB, last row lands at {t:.1f}s, content bottom y={y}")
