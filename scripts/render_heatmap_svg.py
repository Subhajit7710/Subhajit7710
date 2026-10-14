#!/usr/bin/env python3
"""
Render data/contributions.json as contrib-heatmap.svg: a GitHub-style
53-week x 7-day grid of rounded boxes inside a terminal window, with month
and weekday labels, a Less -> More legend and a stats footer.

Animation (CSS keyframes inside the SVG, plays once then freezes): the boxes
drop in along a diagonal -- left-to-right across weeks, top-to-bottom within a
week -- then the stat numbers fade up. Colours use GitHub's own intensity
level for each day (data-level 0..4), so the shading matches your real graph.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.

    python scripts/render_heatmap_svg.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "contrib-heatmap.svg")
STATIC = bool(os.environ.get("STATIC"))
USER = "subhajit"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]   # level 0..4

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 22
LABEL_W = 32
TITLEBAR_H = 30
MONTH_H = 22
STATS_H = 92

BG, BG2 = "#0a0e14", "#0d1420"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
GREEN = "#39d353"
CYAN = "#22d3ee"
GOLD = "#f2cc60"

COL_T, ROW_T, CELL_DUR = 0.022, 0.05, 0.4


def grid_of(days):
    """53-ish columns of 7 (Sun..Sat); None pads the first/last week."""
    first = datetime.date.fromisoformat(days[0]["date"])
    col = [None] * ((first.weekday() + 1) % 7)
    grid = []
    for d in days:
        col.append(d)
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        grid.append(col + [None] * (7 - len(col)))
    return grid


def pretty(iso):
    return datetime.date.fromisoformat(iso).strftime("%b %-d") if iso else "—"


def render(data):
    grid = grid_of(data["days"])
    gw = len(grid) * STEP - GAP
    W = PAD + LABEL_W + gw + PAD
    top = TITLEBAR_H + MONTH_H + 8
    gh = 7 * STEP - GAP
    H = top + gh + 30 + STATS_H

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    if not STATIC:
        p.append('<style>'
                 '@keyframes drop{0%{opacity:0;transform:translateY(-7px)}100%{opacity:1;transform:translateY(0)}}'
                 f'.c{{opacity:0;animation:drop {CELL_DUR}s cubic-bezier(.2,.8,.2,1) both}}'
                 '@keyframes up{0%{opacity:0;transform:translateY(8px)}100%{opacity:1;transform:translateY(0)}}'
                 '.s{opacity:0;animation:up .5s ease-out both}'
                 '@media (prefers-reduced-motion: reduce){.c,.s{opacity:1!important;animation:none!important;transform:none!important}}'
                 '</style>')
    p.append(f'<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>')
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#hbg)"/>')
    p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>')
    p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{20 + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'{USER}@github: ~/contributions --graph --last-year</text>')

    left = PAD + LABEL_W

    # month labels: first column whose first real day is in days 1..7 of a month
    last_x = -99
    for ci, col in enumerate(grid):
        d = next((c for c in col if c), None)
        if not d:
            continue
        date = datetime.date.fromisoformat(d["date"])
        x = left + ci * STEP
        if date.day <= 7 and x - last_x > 28:
            p.append(f'<text x="{x}" y="{TITLEBAR_H + 18}" fill="{MUTED}" font-size="10">{date:%b}</text>')
            last_x = x

    for ri, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p.append(f'<text x="{PAD}" y="{top + ri*STEP + 9.5}" fill="{MUTED}" font-size="9">{name}</text>')

    # the boxes
    last_delay = 0
    for ci, col in enumerate(grid):
        for ri, d in enumerate(col):
            if d is None:
                continue
            lvl = max(0, min(4, int(d.get("level", 0))))
            n = d["count"]
            delay = ci * COL_T + ri * ROW_T
            last_delay = max(last_delay, delay)
            anim = "" if STATIC else f' class="c" style="animation-delay:{delay:.3f}s"'
            outline = ' stroke="#1b232e" stroke-width="0.6"' if lvl == 0 else ""
            p.append(f'<rect{anim} x="{left + ci*STEP}" y="{top + ri*STEP}" width="{CELL}" height="{CELL}" '
                     f'rx="2.5" fill="{PALETTE[lvl]}"{outline}>'
                     f'<title>{d["date"]}: {n} contribution{"" if n == 1 else "s"}</title></rect>')

    # legend
    ly = top + gh + 10
    lx = W - PAD - 5 * (CELL + 2) - 34
    p.append(f'<text x="{lx - 6}" y="{ly + 10}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        p.append(f'<rect x="{lx + i*(CELL+2)}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>')
    p.append(f'<text x="{lx + 5*(CELL+2) + 4}" y="{ly + 10}" fill="{MUTED}" font-size="10">More</text>')
    rng = data["range"]
    p.append(f'<text x="{left}" y="{ly + 10}" fill="{MUTED}" font-size="10">'
             f'{pretty(rng["start"])}, {rng["start"][:4]} → {pretty(rng["end"])}, {rng["end"][:4]}'
             f'  ·  refreshed daily by GitHub Actions</text>')

    # stats footer: four chips
    sy = ly + 30
    p.append(f'<line x1="0" y1="{sy - 8}" x2="{W}" y2="{sy - 8}" stroke="{FRAME}"/>')
    cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
    chips = [
        ("contributions", f'{data["total_contributions"]:,}', f'{data["active_days"]} active days', GREEN),
        ("current streak", f'{cur["length"]}d',
         f'{pretty(cur["start"])} → {pretty(cur["end"])}' if cur["length"] else "start one today", CYAN),
        ("longest streak", f'{lng["length"]}d',
         f'{pretty(lng["start"])} → {pretty(lng["end"])}' if lng["length"] else "—", CYAN),
        ("best day", f'{best["count"]}', pretty(best["date"]) if best["count"] else "—", GOLD),
    ]
    cw = (W - PAD * 2 - 3 * 12) / 4
    start = last_delay + CELL_DUR
    for i, (label, value, sub, col) in enumerate(chips):
        x = PAD + i * (cw + 12)
        cls = "" if STATIC else f' class="s" style="animation-delay:{start + i*0.12:.2f}s"'
        p.append(f'<g{cls}>'
                 f'<rect x="{x:.1f}" y="{sy}" width="{cw:.1f}" height="{STATS_H - 22}" rx="8" fill="#161b22" stroke="{FRAME}"/>'
                 f'<text x="{x+14:.1f}" y="{sy+20}" fill="{MUTED}" font-size="11">$ {label}</text>'
                 f'<text x="{x+14:.1f}" y="{sy+46}" fill="{col}" font-size="22" font-weight="700">{value}</text>'
                 f'<text x="{x+14:.1f}" y="{sy+62}" fill="{MUTED}" font-size="10">{sub}</text>'
                 f'</g>')

    p.append("</svg>")
    return "".join(p), W, H


if __name__ == "__main__":
    with open(SRC) as f:
        data = json.load(f)
    svg, W, H = render(data)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)}: {W}x{H}, {len(svg)//1024} KB")
