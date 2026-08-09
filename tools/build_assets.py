#!/usr/bin/env python3
"""Build the SceneNAT project page assets from the TMLR paper sources.

Copies the rendered scenes out of ../appen_fig, pulls each instruction out of its
vector PDF as real text, rasterizes the main figures from ../figure, and writes
static/js/data.js.

Everything under static/images and static/js/data.js is generated -- rerun this
script after the paper figures change. Requires pdftotext and pdftocairo (poppler)
and Pillow.

    python3 tools/build_assets.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parent.parent
PAPER = SITE.parent
APPEN = PAPER / "appen_fig"
FIGURE = PAPER / "figure"
IMAGES = SITE / "static" / "images"

ROOMS = {"bed": "Bedroom", "living": "Living room", "dining": "Dining room"}
METHODS = ["atiss", "diff", "inst", "ours"]

# Every *.png under appen_fig/ is really JPEG data (see the paper README), so the
# copies get a .jpg name. Anything we resize is re-encoded as JPEG anyway.
JPEG_QUALITY = 90


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def reset(d):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def instruction_text(pdf):
    """The instruction panels are vector text, so poppler gives us the sentence."""
    if not pdf.exists():
        return None
    return " ".join(sh("pdftotext", str(pdf), "-").split()) or None


def copy_render(src, dst):
    """Renders are already web-sized (418-705px), so copy the bytes untouched."""
    shutil.copyfile(src, dst)


def resize_render(src, dst, width):
    """Downscale the oversized mask grids.

    These are hard-edged cell grids at ~1200-2300px. Pillow's BOX filter averages
    over the source pixels without the ringing LANCZOS puts on sharp boundaries,
    which is what smears cell edges here.
    """
    with Image.open(src) as im:
        if im.width > width:
            h = round(im.height * width / im.width)
            im = im.resize((width, h), Image.BOX)
        im.convert("RGB").save(dst, "JPEG", quality=JPEG_QUALITY)


def rasterize(pdf, dst, width, page=1, crop=None):
    """Render one PDF page to JPEG.

    crop is (left, bottom, right, top) in PostScript points, matching the trim=
    argument the paper's \\includegraphics calls use.
    """
    tmp = dst.with_suffix(".tmp")
    sh("pdftocairo", "-jpeg", "-r", "300", "-f", str(page), "-l", str(page),
       "-singlefile", str(pdf), str(tmp))
    tmp = tmp.with_suffix(".tmp.jpg")
    with Image.open(tmp) as im:
        if crop:
            l, b, r, t = crop
            scale = im.width / _page_width(pdf, page)
            im = im.crop((round(l * scale), round(t * scale),
                          im.width - round(r * scale), im.height - round(b * scale)))
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.convert("RGB").save(dst, "JPEG", quality=JPEG_QUALITY)
    tmp.unlink()


def _page_width(pdf, page):
    out = sh("pdfinfo", "-f", str(page), "-l", str(page), str(pdf))
    m = re.search(r"Page +%d size: +([\d.]+) x" % page, out) or \
        re.search(r"Page size: +([\d.]+) x", out)
    return float(m.group(1))


# --------------------------------------------------------------------------- #
# 1. Qualitative comparison sets (F1 + F2)
# --------------------------------------------------------------------------- #

SET_RE = re.compile(r"^n_(\d)_(bed|living|dining)_(\d+)_(\d+)_ours\.(png|jpg)$")


def build_gallery():
    out = reset(IMAGES / "qual")
    entries = []
    for src_dir, tag in ((APPEN / "F1", "f1"), (APPEN / "F2", "f2")):
        for p in sorted(src_dir.iterdir()):
            m = SET_RE.match(p.name)
            if not m:
                continue
            nrel, room, scene, seed, ext = m.groups()
            stem = f"n_{nrel}_{room}_{scene}"
            text = instruction_text(src_dir / f"{stem}.pdf")
            if text is None:
                print(f"  skipped {tag}/{stem}: instruction is a raster, no text to extract")
                continue
            img = {}
            for meth in METHODS:
                src = src_dir / f"{stem}_{seed}_{meth}.{ext}"
                dst = out / f"{tag}_{stem}_{seed}_{meth}.jpg"
                copy_render(src, dst)
                img[meth] = f"static/images/qual/{dst.name}"
            entries.append({
                "id": f"{tag}_{stem}_{seed}",
                "room": ROOMS[room],
                "nrel": int(nrel),
                "text": text,
                "img": img,
            })
    entries.sort(key=lambda e: (e["nrel"], e["room"], e["id"]))
    print(f"  gallery: {len(entries)} sets, {len(entries) * 4} renders")
    return entries


# --------------------------------------------------------------------------- #
# 2. Sampling process (appen_fig/B)
# --------------------------------------------------------------------------- #

STEPS = [10, 20, 30, 40, 50]


def build_sampling():
    out = reset(IMAGES / "sampling")
    resize_render(APPEN / "B" / "mask0.png", out / "mask0.jpg", 1000)
    scenes = []
    dirs = sorted(p for p in (APPEN / "B").iterdir() if p.is_dir())
    for i, d in enumerate(dirs, 1):
        mask, render = {"0": "static/images/sampling/mask0.jpg"}, {}
        for step in STEPS:
            mp = out / f"{d.name}_mask_{step}.jpg"
            rp = out / f"{d.name}_render_{step}.jpg"
            resize_render(d / "masks" / f"step_{step}.png", mp, 1000)
            copy_render(d / f"topdown_step{step}.png", rp)
            mask[str(step)] = f"static/images/sampling/{mp.name}"
            render[str(step)] = f"static/images/sampling/{rp.name}"
        scenes.append({"id": d.name, "label": f"Scene {i}",
                       "steps": [0] + STEPS, "mask": mask, "render": render})
    print(f"  sampling: {len(scenes)} scenes x {len(STEPS)} steps")
    return scenes


# --------------------------------------------------------------------------- #
# 3. In-the-wild / open-vocabulary / arbitration
# --------------------------------------------------------------------------- #

# (group key, group label, [(render stem, instruction stem)]).  The instruction
# PDF for negative_1 is misspelled "nagative_1.pdf" in the paper sources.
WILD_GROUPS = [
    ("openvocab", "Open vocabulary", "etc", [
        ("open_rel_1", "open_rel_1"), ("open_rel_2", "open_rel_2"), ("open_rel_3", "open_rel_3"),
        ("open_obj_1", "open_obj_1"), ("open_obj_2", "open_obj_2"), ("open_obj_3", "open_obj_3"),
    ]),
    ("function", "Role and functionality", "wild", [
        ("function_1", "function_1"), ("function_2", "function_2"),
    ]),
    ("abstract", "Aesthetic and abstract descriptions", "wild", [
        ("abstract_1", "abstract_1"), ("abstract_2", "abstract_2"),
    ]),
    ("llm", "High-level reasoning via LLM rewriting", "wild", [
        ("highlevel_1", "highlevel_1"), ("reviewers", "reviewers"),
    ]),
    ("arbitration", "Physically implausible instructions", "etc", [
        ("arb_1", "arb_1"), ("arb_2", "arb_2"), ("arb_3", "arb_3"),
    ]),
    ("negative", "Negative constraints (inconsistent)", "wild", [
        ("negative_1", "nagative_1"), ("negative_2", "negative_2"),
    ]),
]


def build_wild():
    out = reset(IMAGES / "wild")
    groups = []
    for key, label, subdir, items in WILD_GROUPS:
        src_dir = APPEN / subdir
        examples = []
        for render_stem, text_stem in items:
            text = instruction_text(src_dir / f"{text_stem}.pdf")
            if text is None:
                print(f"  skipped wild/{render_stem}: no instruction PDF")
                continue
            dst = out / f"{render_stem}.jpg"
            copy_render(src_dir / f"{render_stem}.png", dst)
            examples.append({"text": text, "img": f"static/images/wild/{dst.name}"})
        groups.append({"key": key, "label": label, "examples": examples})
    print(f"  wild: {len(groups)} groups, {sum(len(g['examples']) for g in groups)} examples")
    return groups


# --------------------------------------------------------------------------- #
# 4. Main figures
# --------------------------------------------------------------------------- #

def build_figures():
    out = IMAGES
    out.mkdir(parents=True, exist_ok=True)
    # The teaser is three stacked bands on a 1212x688pt page, and each one lands in
    # a different section of the page: the pipeline up top, the two comparison
    # plots in the middle, the four application cards at the bottom.
    rasterize(FIGURE / "new_title_fig.pdf", out / "teaser.jpg", 2000, crop=(0, 508, 0, 0))
    rasterize(FIGURE / "new_title_fig.pdf", out / "teaser_plots.jpg", 1600, crop=(0, 220, 0, 182))
    rasterize(FIGURE / "new_title_fig.pdf", out / "applications.jpg", 1800, crop=(0, 0, 0, 478))
    rasterize(FIGURE / "fig2_final.pdf", out / "arch.jpg", 2000)
    # trim= values copied from sec/4_experiment.tex
    rasterize(FIGURE / "fig_last_new_2.pdf", out / "fig6_unseen.jpg", 1800, page=2,
              crop=(76.75, 320.83, 72.86, 35.86))
    rasterize(FIGURE / "fig_last_new_2.pdf", out / "fig6_wild.jpg", 1600, page=3,
              crop=(131.75, 166.61, 280.50, 179.14))
    print("  figures: teaser, teaser_plots, applications, arch, fig6_unseen, fig6_wild")


# --------------------------------------------------------------------------- #

def write_data(gallery, sampling, wild):
    import json
    dst = SITE / "static" / "js" / "data.js"
    dst.write_text(
        "// Generated by tools/build_assets.py -- do not edit by hand.\n"
        f"const QUALITATIVE = {json.dumps(gallery, indent=2, ensure_ascii=False)};\n\n"
        f"const SAMPLING = {json.dumps(sampling, indent=2, ensure_ascii=False)};\n\n"
        f"const WILD = {json.dumps(wild, indent=2, ensure_ascii=False)};\n"
    )
    print(f"  wrote {dst.relative_to(SITE)} ({dst.stat().st_size // 1024} KB)")


def main():
    for tool in ("pdftotext", "pdftocairo", "pdfinfo"):
        if shutil.which(tool) is None:
            sys.exit(f"{tool} not found -- install poppler-utils")
    print("building assets from", PAPER)
    gallery = build_gallery()
    sampling = build_sampling()
    wild = build_wild()
    build_figures()
    write_data(gallery, sampling, wild)
    total = sum(f.stat().st_size for f in IMAGES.rglob("*") if f.is_file())
    print(f"  static/images total: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
