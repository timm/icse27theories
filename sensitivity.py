#!/usr/bin/env python3 -B
"""sensitivity.py: which link in the evidence chain carries each
real-project verdict? Re-places the mined evidence with one link
removed or swapped at a time. Writes outputs/laws/sensitivity.md."""

import json
from pathlib import Path
from lawkit.laws import LAWS
from lawkit.evidence import Evidence, place

EV, OUT = Path("outputs/evidence"), Path("outputs/laws/sensitivity.md")

def ev(law, f, drop=(), fixed=None, extra=None):
  d = json.loads((EV / f).read_text())
  m = {k: (tuple(v) if isinstance(v[0], str) else v)
       for k, v in d["measured"].items() if k not in drop}
  m.update(extra or {})
  return Evidence(LAWS[law], d["project"], m,
                  {**(d.get("fixed") or {}), **(fixed or {})})

def line(label, e):
  p = place(e, n=1500)
  return (f"| {label} | {p['CONFIRM']:.0f}% | {p['REFUTE']:.0f}% | "
          f"{p['gap'][1]:+.0f} |")

def main():
  H = ["| evidence used | CONFIRM | REFUTE | median gap |",
       "|---|---|---|---|"]
  L = ["# Sensitivity of real-project placements", "",
       "## archpat on Helix: free vs priced migration x evidence links",
       ""] + H
  for law in ("archpat", "archpat_cost"):
    f = "archpat_cost_helix.json"
    L += [line(f"{law}: stocks only", ev(law, f, ("born_pat", "gen_pat"))),
          line(f"{law}: + born ratio", ev(law, f, ("gen_pat",))),
          line(f"{law}: + born + gen proxy", ev(law, f))]
  c = json.loads((EV / "brooks_helix.json").read_text())["measured"]
  c = sorted(c["comm_coef"])[len(c["comm_coef"]) // 2]
  vs = (1 + (1 + 16 / c) ** .5) / 4                 # V(2V - 1) = 2/c
  L += ["", "## brooks on Helix: team size vs measured optimum", "",
        f"Helix comm_coef ~{c:.3f} puts the per-team output optimum near "
        f"V* = {vs:.1f} (V(2V - 1) = 2/c, bounded overload).", ""] + H
  for v in (3, 6, 8, 12):
    L.append(line(f"Vet={v}, doubled", ev("brooks", "brooks_helix.json",
                  fixed={"Vet": v, "_arms": [0, v]})))
  L += ["", "## aiwork on Aider: measured churn + borrowed support "
        "factors", "", "Factors git cannot see are borrowed from other "
        "populations; that borrowing is itself a similarity claim.",
        ""] + H
  grid = lambda a, b, n=40: [a + (b - a) * j / (n - 1) for j in range(n)]
  for lab, gb, vd in (("measured churn only (priors elsewhere)", None, None),
                      ("+ METR-like: gen .1-.4, verify .3-.5",
                       grid(.1, .4), grid(.3, .5)),
                      ("+ Peng-like: gen .4-.7, verify .05-.2",
                       grid(.4, .7), grid(.05, .2))):
    extra = {} if gb is None else {"gen_boost": gb, "verify_drag": vd}
    L.append(line(lab, ev("aiwork", "aiwork_aider.json", extra=extra)))
  OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
  print("\n".join(L))

if __name__ == "__main__":
  main()
