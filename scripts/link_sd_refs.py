#!/usr/bin/env python3
"""Post-process docs/models/*.html to hyperlink models/sd.py references.

Run after gen_rich.py. Idempotent — only wraps unwrapped <code> nodes.

Sources every `<code>models/sd.py</code>` and `<code>models/sd.py:<name></code>`
to the canonical GitHub source. Per-function refs deep-link to line.

For double-blind submission, swap GH_BASE for the anonymous mirror URL.
"""
import re, sys
from pathlib import Path

GH_BASE = "https://github.com/timm/icse27theories/blob/main/models/sd.py"
ROOT    = Path(__file__).resolve().parents[1]
SD_PY   = ROOT / "models/sd.py"
DOCS    = ROOT / "docs/models"


def function_lines():
    out = {}
    for i, line in enumerate(SD_PY.read_text().splitlines(), 1):
        m = re.match(r"^def (\w+)\(\):", line)
        if m:
            out[m.group(1)] = i
    return out


FUNCS = function_lines()


def link_for(name=None):
    if name and name in FUNCS:
        return f"{GH_BASE}#L{FUNCS[name]}"
    return GH_BASE


UNWRAP = re.compile(
    r'<a class="src-link"[^>]*>\s*(<code>models/sd\.py(?::\w+)?</code>)\s*</a>')


def linkify(html: str) -> str:
    # Strip any prior wrappers (possibly nested) so the pass is idempotent.
    while True:
        new = UNWRAP.sub(r"\1", html)
        if new == html:
            break
        html = new

    def wrap(m):
        name = m.group(1)
        href = link_for(name)
        if name:
            inner = f"<code>models/sd.py:{name}</code>"
        else:
            inner = "<code>models/sd.py</code>"
        return f'<a class="src-link" href="{href}" target="_blank" rel="noopener">{inner}</a>'

    pat = re.compile(r"<code>models/sd\.py(?::(\w+))?</code>")
    return pat.sub(wrap, html)


def main():
    targets = ([Path(a) for a in sys.argv[1:]]
               if len(sys.argv) > 1 else sorted(DOCS.glob("*.html")))
    n = 0
    for p in targets:
        s   = p.read_text()
        out = linkify(s)
        if out != s:
            p.write_text(out)
            n += 1
    print(f"Linked sd.py refs in {n}/{len(targets)} files (FUNCS known: {len(FUNCS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
