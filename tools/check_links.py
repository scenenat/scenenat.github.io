#!/usr/bin/env python3
"""Check that every local asset the page references actually exists.

The previous version of this site shipped with index.html pointing at a
static/images/ directory that was never committed, so the live page rendered as
text with two broken images. This catches exactly that, over both the HTML and
the generated data.js.

    python3 tools/check_links.py     # exits 1 if anything is missing
"""

import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent

HTML_REF = re.compile(r'(?:src|href)="([^"]+)"')
DATA_PATH = re.compile(r'"(static/[^"]+)"')


def local(ref):
    return not ref.startswith(("http://", "https://", "//", "#", "data:", "mailto:"))


def main():
    missing, checked = [], 0

    html = (SITE / "index.html").read_text()
    for ref in HTML_REF.findall(html):
        if not local(ref):
            continue
        checked += 1
        if not (SITE / ref.lstrip("./")).exists():
            missing.append(f"index.html -> {ref}")

    data = SITE / "static" / "js" / "data.js"
    if not data.exists():
        missing.append("static/js/data.js is missing -- run tools/build_assets.py")
    else:
        for ref in sorted(set(DATA_PATH.findall(data.read_text()))):
            checked += 1
            if not (SITE / ref).exists():
                missing.append(f"data.js -> {ref}")

    if missing:
        print(f"{len(missing)} missing reference(s):")
        for m in missing:
            print("  " + m)
        return 1
    print(f"all {checked} local references resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
