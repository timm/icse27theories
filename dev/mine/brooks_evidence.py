#!/usr/bin/env python3 -B
"""brooks_evidence.py: estimate Brooks support factors from a git repo.

  python mine/brooks_evidence.py <repo> <project> [--since 2013]

Monthly panel (tick = 1 month). Veterans = active devs with tenure
>= 6 months; New = devs whose first commit is < 6 months old. Fits the
standard lawkit brooks model's own production equation to per-veteran
output (bounded overload),
    y_m = p * exp(-(c * V(V-1)/2 + tr * New))
so c (comm_coef) and tr (train_coef) mean what they mean in the model,
then fits newcomer ramp-up f(k) = 1 - exp(-r (k+1)) for mature_rate.
Writes outputs/evidence/brooks_<project>.json."""

import argparse, json, math, statistics as st
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from gitlog import commits, month, boot, ci

BOTS = ("bot", "noreply@github.com", "jenkins", "dependabot")

def panel(cs, since):
  first, per = {}, defaultdict(lambda: defaultdict(int))
  for c in cs:
    if any(b in c["author_email"] for b in BOTS): continue
    d, m = c["author_email"], month(c["when"])
    first.setdefault(d, m)
    per[m][d] += 1
  rows = []
  for m in sorted(per):
    if m < since * 12: continue
    vets = [d for d in per[m] if first[d] <= m - 6]
    new = sum(1 for d, f in first.items() if m - 6 < f <= m)
    if len(vets) >= 1:
      rows.append((m, len(vets), new, sum(per[m][d] for d in vets) /
                   len(vets)))
  return rows, first, per

def fit(rows):
  V = np.array([r[1] for r in rows], float)
  N = np.array([r[2] for r in rows], float)
  y = np.array([r[3] for r in rows], float)
  f = lambda q: q[0] * np.exp(-(q[1] * V * (V - 1) / 2 + q[2] * N)) - y
  q = least_squares(f, [y.mean(), 0.001, 0.01],
                    bounds=([0, 0, 0], [np.inf, 0.2, 1])).x
  return q

def ramp(first, per, rows, since):
  "Mean newcomer output by month-since-join, relative to vets."
  vet_rate = {m: y for m, _, _, y in rows}
  curves = []
  for d, f in first.items():
    if f < since * 12: continue
    if sum(per[f + k].get(d, 0) for k in range(12, 24)) == 0: continue
    curves.append([per[f + k].get(d, 0) / vet_rate[f + k]
                   if vet_rate.get(f + k) else 0 for k in range(12)])
  return curves

def mature_rate(curves):
  if len(curves) < 3: return math.nan
  g = np.mean(np.array(curves), axis=0)
  k = np.arange(12)
  q = least_squares(lambda q: q[0] * (1 - np.exp(-q[1] * (k + 1))) - g,
                    [min(max(g.max(), .1), 99), 0.2],
                    bounds=([0, 0], [100, 5])).x
  return min(1.0, float(q[1]))           # model range: 1/tick = instant

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("repo"); ap.add_argument("project")
  ap.add_argument("--since", type=int, default=2013)
  a = ap.parse_args()
  rows, first, per = panel(commits(a.repo), a.since)
  q = fit(rows)
  bq = boot(rows, fit, n=300)
  curves = ramp(first, per, rows, a.since)
  bm = [x for x in boot(curves, mature_rate, n=300) if math.isfinite(x)] \
       if len(curves) >= 3 else []
  vet = int(round(st.median(r[1] for r in rows)))
  vmax = max(r[1] for r in rows)
  c_s, t_s = [b[1] for b in bq], [b[2] for b in bq]
  ident = sum(r[1] >= 3 for r in rows) >= 24   # c needs varying pairs
  meas = {"train_coef": t_s}
  if ident: meas["comm_coef"] = c_s
  if bm: meas["mature_rate"] = bm
  fmt = lambda nm, xs: f"{nm} {ci(xs)[1]:.4g} [{ci(xs)[0]:.4g}, " \
                       f"{ci(xs)[2]:.4g}]"
  summ = [f"months={len(rows)}", f"median vets/month={vet} (max {vmax})",
          fmt("comm_coef", c_s) + ("" if ident else " (not identified)"),
          fmt("train_coef", t_s), f"newcomers who stayed: {len(curves)}"]
  if bm: summ.append(fmt("mature_rate/month", bm))
  ev = dict(project=a.project, measured=meas, summary=summ,
            fixed={"Vet": vet, "_arms": [0, vet]},
            population=f"{a.project}: monthly git panel since {a.since}; "
                       f"lever = doubling a late team of {vet} veterans",
            notes=[
    "Commits/month stand in for productivity (construct validity: commit "
    "size and review work are invisible).",
    "OSS newcomers are not 'hired' onto a deadline; arrivals follow "
    "activity, so train_coef may be biased toward 0 (reverse causation).",
    "Identity = e-mail address; no kaiaulu identity_match merge.",
    "mature_rate uses only newcomers still active a year later "
    "(survivorship: onboarding looks faster than it is).",
    "Lateness, prod_rate and backlog are not measured: the project is "
    "*assumed* late (Todo=1000), i.e. this tests the counterfactual "
    "'if this team were late'."])
  out = Path("outputs/evidence"); out.mkdir(parents=True, exist_ok=True)
  (out / f"brooks_{a.project}.json").write_text(json.dumps(ev))
  print("\n".join(summ))

if __name__ == "__main__":
  main()
