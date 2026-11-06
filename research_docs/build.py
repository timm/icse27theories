#!/usr/bin/env python3 -B
"""build.py: assemble the research docs site.

  python research_docs/build.py          # -> research_docs/site/
  python -m http.server 8765 -d research_docs/site

Pages are hand-written HTML fragments in research_docs/pages/; charts
come from figs.py (generated from outputs/); evidence cards and the
synthesis are rendered from their markdown sources so they never drift."""

import re, shutil
from pathlib import Path
import markdown
import figs

HERE = Path(__file__).resolve().parent
ROOT, SITE = HERE.parent, HERE / "site"

NAV = [("index.html", "Overview"),
       ("before.html", "A. The project as received"),
       ("brooks.html", "B1. Your Brooks work"),
       ("review.html", "B2. Review of the Brooks work"),
       ("lawkit.html", "C1. lawkit framework"),
       ("results.html", "C2. Results per law"),
       ("evidence.html", "C3. Real-world evidence"),
       ("strategy.html", "D. Strategy, Cartwright, next steps"),
       ("reproduce.html", "Files & reproduce"),
       ("cards/index.html", "Evidence cards")]

CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:980px;
 margin:0 auto;padding:0 16px 60px;line-height:1.55;color:#111;
 background:#fff}
nav{border-bottom:1px solid #ccc;padding:10px 0;font-size:14px}
nav a{margin-right:12px;white-space:nowrap}
nav a.on{font-weight:bold;color:#000;text-decoration:none}
h1{font-size:26px;margin-top:24px}h2{font-size:20px;margin-top:34px;
 border-bottom:1px solid #eee;padding-bottom:4px}h3{font-size:16px}
table{border-collapse:collapse;margin:12px 0;font-size:14px;width:100%}
th,td{border:1px solid #ccc;padding:5px 8px;text-align:left;
 vertical-align:top}th{background:#f3f3f3}
code{background:#f3f3f3;padding:1px 4px;font-size:90%}
pre{background:#f6f6f6;padding:10px;overflow-x:auto;font-size:13px}
img{max-width:100%;border:1px solid #eee}figure{margin:16px 0}
figcaption{font-size:13px;color:#444;margin-top:4px}
.note{border-left:4px solid #888;background:#f7f7f7;padding:8px 12px}
.warn{border-left:4px solid #c05621;background:#fff7f0;padding:8px 12px}
.mermaid{margin:16px 0;text-align:center}
.tag{font-size:12px;border:1px solid #999;padding:0 5px;border-radius:3px}
"""

MERMAID = ('<script src="{up}vendor/mermaid.min.js"></script><script>'
           'mermaid.initialize({{startOnLoad:true,theme:"neutral",'
           'flowchart:{{htmlLabels:true}}}});</script>')   # mermaid 10.9.1

def page(href, title, body, depth=0):
  up = "../" * depth
  nav = " ".join(f'<a href="{up}{h}"{" class=on" if h == href else ""}>'
                 f'{t}</a>' for h, t in NAV)
  return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
          f"<meta name=viewport content='width=device-width,initial-scale=1'>"
          f"<title>{title}</title><style>{CSS}</style></head><body>"
          f"<nav>{nav}</nav>{body}{MERMAID.format(up=up)}</body></html>")

def md(path, depth):
  txt = Path(path).read_text(encoding="utf-8")
  txt = re.sub(r"\]\((\w+?)_card\.md\)", r"](\1.html)", txt)
  txt = txt.replace("](sensitivity.md)", "](sensitivity.html)")
  return markdown.markdown(txt, extensions=["tables", "fenced_code"])

def main():
  if SITE.exists(): shutil.rmtree(SITE)
  (SITE / "cards").mkdir(parents=True)
  figs.build(SITE / "img")
  shutil.copytree(HERE / "vendor", SITE / "vendor")
  prior = SITE / "img/prior"; prior.mkdir()
  for p in (ROOT / "outputs").glob("*.png"): shutil.copy(p, prior / p.name)
  for f in sorted((HERE / "pages").glob("*.html")):
    body = f.read_text(encoding="utf-8")
    body = re.sub(r"<!--SVG:(.*?)-->",      # inline: the SVG uses HTML entities
                  lambda m: (ROOT / m[1]).read_text(encoding="utf-8"), body)
    title = re.search(r"<h1>(.*?)</h1>", body)[1]
    (SITE / f.name).write_text(page(f.name, re.sub("<.*?>", "", title),
                                    body), encoding="utf-8")
  cards = sorted((ROOT / "outputs/laws").glob("*_card.md"))
  links = []
  for c in cards:
    law = c.stem[:-5]
    (SITE / "cards" / f"{law}.html").write_text(
      page("cards/index.html", f"card: {law}", md(c, 1), 1), encoding="utf-8")
    links.append(f'<li><a href="{law}.html">{law}</a></li>')
  for name in ("SYNTHESIS", "sensitivity"):
    (SITE / "cards" / f"{name.lower()}.html").write_text(
      page("cards/index.html", name, md(ROOT / f"outputs/laws/{name}.md", 1),
           1), encoding="utf-8")
  (SITE / "cards/forrester_all.html").write_text(
    page("cards/index.html", "Forrester tests",
         md(ROOT / "outputs/forrester_all.md", 1), 1), encoding="utf-8")
  (SITE / "cards/index.html").write_text(page("cards/index.html",
    "Evidence cards", "<h1>Evidence cards (generated)</h1><p>Rendered "
    "verbatim from <code>outputs/laws/*_card.md</code>, the files "
    "<code>run_laws.py</code> writes. Each card has the same six "
    "sections: machine battery, robustness, deciding factors, "
    "scenarios, variants, real-project placement.</p><ul>" +
    "".join(links) + '</ul><p>Also: <a href="synthesis.html">SYNTHESIS.md'
    '</a> (the written synthesis) and <a href="sensitivity.html">'
    'sensitivity.md</a>, and <a href="forrester_all.html">every no-data '
    'Forrester test on every Brooks scenario</a>.</p>', 1), encoding="utf-8")
  print(f"built {SITE}")

if __name__ == "__main__":
  main()
