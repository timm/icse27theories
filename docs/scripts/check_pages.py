#!/usr/bin/env python3
"""Page contract checker for MYTHS model pages.

Fails non-zero if any page violates the per-page contract. Wire as a
pre-commit hook (or run manually before push).

Contract per docs/models/*.html:
  - >= MIN_WORDS plain-text words
  - >= 1 <pre><code> block
  - References table present
  - 6 tab panels, each non-empty
  - manual=True pages: must contain at least one diagram (mermaid
    block, ASCII <pre> diagram, or <svg>)

Anti-regression: also checks page length vs the last committed copy.
If a page shrinks by > SHRINK_FRAC, fail.

Usage:
  python scripts/check_pages.py             # check all pages
  python scripts/check_pages.py --bless     # update length floor
  python scripts/check_pages.py path.html   # check a single page
"""
import json, re, sys, html as htmllib
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[2]
DOCS     = ROOT / "docs" / "models"
FLOOR_JS = ROOT / "docs" / "scripts" / "_page_floor.json"

MIN_WORDS    = 600
SHRINK_FRAC  = 0.20   # > 20% smaller than last bless => fail
TAB_COUNT    = 6
MANUAL_PAGES = {"brooks.html", "diapers.html"}


def strip_html(src: str) -> str:
    src = re.sub(r"<script.*?</script>", " ", src, flags=re.S | re.I)
    src = re.sub(r"<style.*?</style>",   " ", src, flags=re.S | re.I)
    src = re.sub(r"<[^>]+>",             " ", src)
    return htmllib.unescape(src)


def violations(path: Path) -> list[str]:
    src   = path.read_text(encoding="utf-8")
    txt   = strip_html(src)
    words = len(txt.split())
    errs  = []

    if words < MIN_WORDS:
        errs.append(f"word-count {words} < {MIN_WORDS}")

    if len(re.findall(r"<pre[^>]*>\s*<code", src, flags=re.I)) < 1:
        errs.append("no <pre><code> block found")

    if "References" not in src or "<table" not in src:
        errs.append("no References table found")

    panels = re.findall(r'id="panel-\d+"', src)
    if len(panels) != TAB_COUNT:
        errs.append(f"found {len(panels)} tab panels, want {TAB_COUNT}")
    else:
        for p in panels:
            block = re.search(
                rf'{p}[^>]*>(.*?)(?:<div id="panel|</div>\s*</div>)',
                src, flags=re.S)
            if block and len(strip_html(block.group(1)).split()) < 20:
                errs.append(f"{p} too short (<20 words)")

    if path.name in MANUAL_PAGES:
        has_diag = ("mermaid" in src) or ("<svg" in src) or (
            re.search(r"<pre[^>]*>\s*[^<]*[+|\-]{3,}", src) is not None)
        if not has_diag:
            errs.append("manual page missing diagram (mermaid/ascii/svg)")

    return errs


def floors():
    if FLOOR_JS.exists():
        return json.loads(FLOOR_JS.read_text())
    return {}


def regression(path: Path, floor: dict) -> str | None:
    cur = path.stat().st_size
    prev = floor.get(path.name)
    if prev and cur < prev * (1 - SHRINK_FRAC):
        return f"size {cur}b is {100*(1-cur/prev):.0f}% < bless ({prev}b)"
    return None


def bless():
    sizes = {p.name: p.stat().st_size for p in sorted(DOCS.glob("*.html"))}
    FLOOR_JS.write_text(json.dumps(sizes, indent=2, sort_keys=True))
    print(f"Blessed {len(sizes)} pages -> {FLOOR_JS.relative_to(ROOT)}")


def main():
    args = sys.argv[1:]
    if "--bless" in args:
        bless()
        return 0

    pages = ([ROOT / a for a in args]
             if args else sorted(DOCS.glob("*.html")))
    floor = floors()
    bad   = 0
    for p in pages:
        errs = violations(p)
        reg  = regression(p, floor)
        if reg:
            errs.append(reg)
        if errs:
            bad += 1
            print(f"FAIL {p.relative_to(ROOT)}")
            for e in errs:
                print(f"   - {e}")
    if bad == 0:
        print(f"OK  {len(pages)} pages")
        return 0
    print(f"\n{bad}/{len(pages)} pages failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
