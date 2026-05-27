#!/usr/bin/env python3
"""Sweep the repo for stale numbers vs current paper/outputs/full_audit.csv.
Checks: cell label, inp_cnt, par_cnt, verdict, verdict_n per model."""
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
AUDIT = {row["model"]: row for row in csv.DictReader(
    (ROOT / "paper/outputs/full_audit.csv").open())}

issues = []

def check(label, condition, msg):
    if not condition:
        issues.append(f"  [{label}] {msg}")

# gen_rich.py: stale cell= in M[]
gr = (ROOT / "docs/scripts/gen_rich.py").read_text()
for m in re.finditer(r'^M\["([a-z]+)"\] = dict\((.*?)^\)', gr, re.M | re.S):
    name, body = m.group(1), m.group(2)
    if name not in AUDIT: continue
    cell_match = re.search(r"cell=['\"]([^'\"]+)['\"]", body)
    if cell_match:
        gr_cell = cell_match.group(1)
        au_cell = AUDIT[name]["cell"]
        check("gen_rich", gr_cell == au_cell,
              f"M['{name}'].cell={gr_cell!r} vs audit={au_cell!r}")
    # check for stress count quotes inside cell_para
    cp = re.search(r"cell_para=['\"](.*?)['\"]", body, re.S)
    if cp:
        text = cp.group(1)
        for stress_match in re.finditer(r"(\d+)\s*/\s*200", text):
            qn = int(stress_match.group(1))
            inp = int(AUDIT[name]["inp_cnt"])
            par = int(AUDIT[name]["par_cnt"])
            if qn not in (inp, par, 200):
                check("gen_rich", False,
                      f"M['{name}'].cell_para quotes {qn}/200, "
                      f"audit inp={inp} par={par}")

# index.html: card class + badge
idx = (ROOT / "docs/index.html").read_text()
CELL_TO_CLASS = {
    "universal": "universal", "process-conditional": "process",
    "fragile": "fragile", "world-conditional": "world",
}
for m in re.finditer(
    r'<a class="card ([a-z ]+?)"[^>]*href="models/([a-z]+)\.html"',
    idx):
    classes, name = m.group(1).split(), m.group(2)
    if name not in AUDIT: continue
    expected = CELL_TO_CLASS[AUDIT[name]["cell"]]
    check("index.card", expected in classes,
          f"card {name}: classes={classes} expected {expected} "
          f"(cell={AUDIT[name]['cell']})")

# index.html: typology counts
universal_count = sum(1 for r in AUDIT.values() if r["cell"]=="universal")
process_count   = sum(1 for r in AUDIT.values() if r["cell"]=="process-conditional")
fragile_count   = sum(1 for r in AUDIT.values() if r["cell"]=="fragile")
world_count     = sum(1 for r in AUDIT.values() if r["cell"]=="world-conditional")
for cell_name, expected in [
    ("universal", universal_count), ("process-cond\\.", process_count),
    ("fragile", fragile_count), ("world-cond\\.", world_count)]:
    pat = (rf'<span class="[a-z]+">{cell_name}</span></td>'
           rf'<td>[^<]+</td><td class="num">(\d+)</td>')
    m = re.search(pat, idx)
    if m:
        got = int(m.group(1))
        check("typology", got == expected,
              f"typology {cell_name}: html={got} expected={expected}")

# Number of models
total = len(AUDIT)
for f, pat in [
    ("docs/index.html",       rf"(\d+) (?:models|modelled theses|model pages)"),
    ("paper/MODELS_README.md", rf"(\d+) (?:models|SD models)"),
]:
    src = (ROOT / f).read_text()
    found = set(int(x) for x in re.findall(pat, src))
    bad = found - {total}
    if bad:
        check(f, False, f"{f}: stale count {sorted(bad)} (real={total})")

# Print
if issues:
    print(f"Found {len(issues)} stale items:")
    for i in issues: print(i)
    sys.exit(1)
else:
    print("OK — all checked numbers match the audit.")
