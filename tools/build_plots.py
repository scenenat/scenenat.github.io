#!/usr/bin/env python3
"""Generate the three comparison plots as standalone SVG.

Every number here is copied from the pgfplots coordinates in the paper sources --
figure/main_fig3_fig4.tex, sec/4_experiment.tex and sec/appendix.tex -- so the
plots stay in sync with the PDF. Emitting SVG instead of cropping the compiled
PDF keeps them sharp at any zoom and lets them use the page's own type.

    python3 tools/build_plots.py
"""

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "images" / "plots"

# Colour follows the model, not its rank: the same hue means the same method in
# every plot on the page. Slot order is the validated categorical order
# (blue, orange, aqua, yellow) -- see the dataviz palette reference.
COLOR = {
    "SceneNAT": "#2a78d6",
    "SceneNAT-B": "#2a78d6",
    "SceneNAT-S": "#86b6ef",
    "InstructScene": "#eb6834",
    "DiffuScene": "#1baf7a",
    "ATISS": "#eda100",
}

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


# --------------------------------------------------------------------------- #
# tiny svg helpers
# --------------------------------------------------------------------------- #

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=11, fill=MUTED, anchor="middle", weight=400, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{extra}>{esc(s)}</text>')


def linear(domain, rng):
    d0, d1 = domain
    r0, r1 = rng
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def log(domain, rng):
    d0, d1 = math.log10(domain[0]), math.log10(domain[1])
    r0, r1 = rng
    return lambda v: r0 + (math.log10(v) - d0) / (d1 - d0) * (r1 - r0)


def nudge(labels, gap=13):
    """Push overlapping direct labels apart, keeping their original order."""
    labels = sorted(labels, key=lambda l: l["y"])
    for i in range(1, len(labels)):
        if labels[i]["y"] - labels[i - 1]["y"] < gap:
            labels[i]["y"] = labels[i - 1]["y"] + gap
    return labels


def panel(x0, y0, w, h, xs, ys, xticks, yticks, xlabel, ylabel, title=None,
          series=None, direct_labels=False, xtick_fmt=str, shade=None):
    """One plot panel: grid, axes, lines, markers, optional end labels."""
    p = []
    if title:
        p.append(text(x0 + w / 2, y0 - 12, title, 12, INK, weight=600))
    if shade:
        a, b = xs(shade[0]), xs(shade[1])
        p.append(f'<rect x="{a:.1f}" y="{y0:.1f}" width="{b - a:.1f}" height="{h:.1f}" '
                 f'fill="{GRID}" opacity="0.45"/>')
    for t in yticks:
        y = ys(t)
        p.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + w}" y2="{y:.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        p.append(text(x0 - 7, y + 3.5, t, 10, MUTED, "end"))
    for t in xticks:
        x = xs(t)
        p.append(text(x, y0 + h + 15, xtick_fmt(t), 10, MUTED))
    p.append(f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" '
             f'stroke="{AXIS}" stroke-width="1"/>')
    p.append(text(x0 + w / 2, y0 + h + 32, xlabel, 11, INK_2))
    if ylabel:
        p.append(f'<g transform="translate({x0 - 34},{y0 + h / 2}) rotate(-90)">'
                 f'{text(0, 0, ylabel, 11, INK_2)}</g>')

    ends = []
    for name, pts, dash in series:
        c = COLOR[name]
        d = " ".join(f"{xs(px):.1f},{ys(py):.1f}" for px, py in pts)
        p.append(f'<polyline points="{d}" fill="none" stroke="{c}" stroke-width="2" '
                 f'stroke-linejoin="round" stroke-linecap="round"'
                 + (f' stroke-dasharray="5 3"' if dash else "") + "/>")
        for px, py in pts:
            p.append(f'<circle cx="{xs(px):.1f}" cy="{ys(py):.1f}" r="4" fill="{c}" '
                     f'stroke="{SURFACE}" stroke-width="2"><title>{esc(name)}: '
                     f'{esc(py)} at {esc(px)}</title></circle>')
        ends.append({"name": name, "x": xs(pts[-1][0]), "y": ys(pts[-1][1]), "c": c})
    if direct_labels:
        for l in nudge(ends):
            p.append(text(l["x"] + 9, l["y"] + 3.5, l["name"], 10, l["c"], "start", 600))
    return "\n".join(p)


def legend(x, y, names, note=None):
    p, cx = [], x
    for n in names:
        p.append(f'<circle cx="{cx + 5}" cy="{y - 4}" r="5" fill="{COLOR[n]}"/>')
        p.append(text(cx + 15, y, n, 11, INK_2, "start"))
        cx += 15 + len(n) * 6.4 + 20
    if note:
        p.append(text(cx + 4, y, note, 10, MUTED, "start"))
    return "\n".join(p)


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" font-family=\'{FONT}\'>\n'
            f'<title>{esc(title)}</title>\n'
            f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>\n{body}\n</svg>\n')


# --------------------------------------------------------------------------- #
# 1. iRecall vs number of relational constraints  (figure/main_fig3_fig4.tex)
# --------------------------------------------------------------------------- #

RELATIONS = {
    "Bedroom": {
        "ylim": (15, 90), "yticks": [20, 40, 60, 80],
        "ATISS": [36.81, 33.82, 29.22, 29.80, 31.71, 31.78],
        "DiffuScene": [47.45, 47.62, 47.38, 43.17, 43.13, 48.22],
        "InstructScene": [64.58, 68.89, 68.68, 64.19, 64.69, 62.43],
        "SceneNAT": [81.71, 74.21, 68.20, 68.54, 68.08, 69.16],
    },
    "Living room": {
        "ylim": (10, 65), "yticks": [20, 30, 40, 50, 60],
        "ATISS": [21.05, 21.21, 21.36, 19.18, 20.73, 20.12],
        "DiffuScene": [34.62, 26.23, 26.42, 26.77, 27.53, 28.72],
        "InstructScene": [58.70, 48.98, 48.73, 43.85, 43.21, 41.69],
        "SceneNAT": [60.93, 52.97, 47.16, 47.67, 47.56, 50.15],
    },
    "Dining room": {
        "ylim": (20, 70), "yticks": [30, 40, 50, 60],
        "ATISS": [32.89, 30.38, 34.45, 26.92, 27.66, 31.33],
        "DiffuScene": [41.67, 39.47, 36.17, 34.13, 37.01, 33.70],
        "InstructScene": [51.10, 47.01, 48.10, 43.69, 46.17, 44.94],
        "SceneNAT": [63.60, 57.65, 56.52, 53.31, 53.08, 53.64],
    },
}
ORDER = ["SceneNAT", "InstructScene", "DiffuScene", "ATISS"]


def plot_relations():
    pw, ph, gap = 250, 190, 108
    x0, y0 = 62, 46
    w = x0 + 3 * pw + 2 * gap + 24
    h = y0 + ph + 78
    body = [legend(x0, h - 16, ORDER,
                   "shaded: 5-6 constraints, beyond the 4 seen in training")]
    for i, (room, d) in enumerate(RELATIONS.items()):
        px = x0 + i * (pw + gap)
        xs = linear((1, 6), (px, px + pw))
        ys = linear(d["ylim"], (y0 + ph, y0))
        series = [(n, list(zip(range(1, 7), d[n])), False) for n in ORDER]
        # Only the first panel carries the axis label and the end labels -- on the
        # others they would land on top of the neighbouring panel. The three
        # panels have different y ranges, so each keeps its own ticks.
        body.append(panel(px, y0, pw, ph, xs, ys, [1, 2, 3, 4, 5, 6], d["yticks"],
                          "# of relations", "iRecall (%)" if i == 0 else "", room,
                          series, direct_labels=(i == 0), shade=(4.5, 6)))
    return svg(w, h, "\n".join(body),
               "iRecall versus the number of relational constraints, per room type")


# --------------------------------------------------------------------------- #
# 2. Inference latency vs batch size  (sec/appendix.tex)
# --------------------------------------------------------------------------- #

BATCH = [1, 8, 32, 64, 128]
LATENCY = {
    "InstructScene": [2.46, 2.52, 2.66, 3.89, 6.73],
    "SceneNAT-B": [0.64, 0.72, 0.70, 0.79, 1.35],
    "SceneNAT-S": [0.49, 0.51, 0.52, 0.62, 1.02],
}


def plot_latency():
    pw, ph = 420, 220
    x0, y0 = 66, 26
    w, h = x0 + pw + 110, y0 + ph + 76
    xs = log((1, 128), (x0, x0 + pw))
    ys = linear((0, 7.5), (y0 + ph, y0))
    series = [("InstructScene", list(zip(BATCH, LATENCY["InstructScene"])), False),
              ("SceneNAT-B", list(zip(BATCH, LATENCY["SceneNAT-B"])), False),
              ("SceneNAT-S", list(zip(BATCH, LATENCY["SceneNAT-S"])), True)]
    body = [panel(x0, y0, pw, ph, xs, ys, BATCH, [0, 2, 4, 6],
                  "batch size", "latency (s)", None, series, direct_labels=True),
            legend(x0, h - 14, ["SceneNAT-B", "SceneNAT-S", "InstructScene"])]
    return svg(w, h, "\n".join(body), "Inference latency against batch size")


# --------------------------------------------------------------------------- #
# 3. FID and iRecall vs inference steps  (sec/4_experiment.tex)
# --------------------------------------------------------------------------- #

STEPS = {
    "DiffuScene": [(10, 185.95, 11.25), (20, 175.52, 17.85), (30, 167.47, 20.78),
                   (50, 160.70, 20.05), (100, 148.23, 26.16), (500, 120.72, 41.56),
                   (1000, 120.02, 45.48)],
    "InstructScene": [(10, 123.23, 58.44), (20, 114.98, 63.57), (30, 116.78, 64.30),
                      (50, 116.45, 64.55), (100, 113.76, 62.10)],
    "SceneNAT": [(10, 111.51, 68.46), (20, 108.94, 69.93), (30, 110.81, 70.17),
                 (50, 108.21, 71.12), (100, 108.54, 70.42)],
}
STEP_ORDER = ["SceneNAT", "InstructScene", "DiffuScene"]
STEP_TICKS = [10, 30, 100, 300, 1000]


def plot_steps():
    pw, ph, vgap = 430, 150, 70
    x0, y0 = 66, 26
    w, h = x0 + pw + 40, y0 + 2 * ph + vgap + 60
    xs = log((9, 1100), (x0, x0 + pw))
    body = []
    for i, (idx, ylim, yticks, ylabel) in enumerate(
            [(1, (90, 200), [100, 140, 180], "FID"),
             (2, (10, 80), [20, 40, 60, 80], "iRecall (%)")]):
        py = y0 + i * (ph + vgap)
        ys = linear(ylim, (py + ph, py))
        series = [(n, [(s[0], s[idx]) for s in STEPS[n]], False) for n in STEP_ORDER]
        body.append(panel(x0, py, pw, ph, xs, ys, STEP_TICKS, yticks,
                          "inference steps", ylabel, None, series))
    body.append(legend(x0, h - 14, STEP_ORDER))
    return svg(w, h, "\n".join(body),
               "FID and iRecall against the number of inference steps")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("relations", plot_relations),
                     ("latency", plot_latency),
                     ("steps", plot_steps)):
        p = OUT / f"{name}.svg"
        p.write_text(fn())
        print(f"  {p.relative_to(OUT.parent.parent.parent)} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
