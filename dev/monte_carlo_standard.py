#!/usr/bin/env python3 -B
"""monte_carlo_standard.py: 100,000-run Monte Carlo of the STANDARD Brooks
model (lawkit LAWS["brooks"]): every scenario and every team structure.

Same equations as lawkit/laws.py, vectorised with NumPy (one array slot
per sampled world). Before reporting, a sample of worlds is re-run through
lawkit itself and must give the same delay (--check).

Each world is run twice (no hire vs hire) with the SAME settings, so every
comparison is paired, inside one scenario / structure.
  local: every factor x U(0.85, 1.15) around the scenario (Part B protocol)
  prior: triangular over each factor's declared range (believable
         worlds); a scenario's own settings stay fixed
Outcome = finish tick (lower is better). delay = finish(hire) - finish(none).
Per-run verdict = lawkit's 5% rule: CONFIRM if delay > max(5% of
finish(none), 0.5); REFUTE if delay < -that; else neutral."""

import sys, math, json, time, random, argparse
from pathlib import Path
import numpy as np
_dev = Path(__file__).resolve().parent                 # dev/
sys.path[:0] = [str(_dev / "paper_patches"), str(_dev.parent / "paper")]
import stats
from lawkit.laws import LAWS, team_comm, person_comm, async_comm
from lawkit.core import background, gap, spec

LAW = LAWS["brooks"]
STRUCT = {  # vectorised twins of the brooks_like(...) arguments in laws.py
  "flat (reference)": {},
  "squads of 10":     dict(comm="team"),
  "mentor pods":      dict(pods=True),
  "async docs + CI":  dict(comm="async", async_train=0.6),
  "staged waves":     dict(waves=5),
  "per-person comm":  dict(comm="person"),
  "shared mentoring": dict(train_share=True)}

def comm_cost(kind, V, c):
  if kind == "team":
    k, m = np.ceil(np.maximum(V, 1) / 10), np.minimum(V, 10)
    return (m * (m - 1) / 2 + k * (k - 1) / 2) * c
  if kind == "person": return 4.5 * (V - 1) * c
  if kind == "async":  return V * np.log2(np.maximum(2, V)) * c * 0.5
  return V * (V - 1) / 2 * c

def simulate(p, hires, comm="flat", pods=False, train_share=False,
             async_train=1.0, waves=1):
  "Finish tick for every world in p (dict of arrays), one arm."
  dt, tmax = LAW.dt, LAW.tmax
  n = len(p["Vet"])
  vet, new = p["Vet"].copy(), np.zeros(n)
  todo, todo0 = p["Todo"].copy(), p["Todo"].copy()
  finish = np.full(n, np.nan)
  t, i = 0.0, 0
  while t < tmax:
    if pods:
      active = np.maximum(0, vet - np.minimum(vet, np.ceil(new / 5)))
      train = np.zeros(n)
    else:
      active = vet
      train = new * p["train_coef"] * async_train
      if train_share: train = train / np.maximum(1, vet)
    x = comm_cost(comm, active, p["comm_coef"]) + train
    heads = np.where(active > 0,
                     active / (1 + p["serial"] * (active - 1)), 0)
    prod = (heads * np.exp(-x) + p["newprod"] * new) * p["prod_rate"]
    rem = np.maximum(p["deadline"] - t, dt)
    with np.errstate(divide="ignore", invalid="ignore"):
      press = np.clip(todo / rem / prod - 1, 0, 1)
    prod = np.where(prod > 0, prod * (1 + p["overtime"] * press), prod)
    with np.errstate(divide="ignore", invalid="ignore"):
      share = np.where(vet + new > 0, new / (vet + new), 0)
    prod = np.where(vet + new > 0, prod * (1 - p["rework"] * (1 + share)),
                    prod)
    prod = np.minimum(prod, todo / dt)
    todo = np.maximum(0, todo - dt * prod)
    h = p["hire_at"]
    pulse = (np.where((h <= t) & (t < h + waves), hires / waves, 0)
             if t == int(t) else 0)              # whole ticks only
    vet, new = (np.maximum(0, vet + dt * p["mature_rate"] * new
                           - dt * p["leave"] * vet),
                np.maximum(0, new - dt * p["mature_rate"] * new + pulse))
    done_now = np.isnan(finish) & (todo <= 1e-9)
    finish[done_now] = t + dt
    t, i = t + dt, i + 1
  late = np.isnan(finish)        # unfinished: extrapolate at planned pace
  finish[late] = i * dt + todo[late] / (todo0[late] / (i * dt))
  return finish

def worlds(bg, n, how, rng, keep=()):
  """Sample n worlds around background bg (same rules as
  lawkit.core.draw). keep = the scenario's own settings, held fixed
  under 'prior' so the scenario stays that scenario."""
  p = {k: np.full(n, float(v[0])) for k, v in bg.items()
       if not k.startswith("_")}
  for k in LAW.factors:
    if how == "prior" and k in keep: continue
    d, lo, hi = bg[k][0], bg[k][1], bg[k][2]
    if how == "local":
      p[k] = np.clip(d * rng.uniform(0.85, 1.15, n), lo, hi)
    elif lo < hi:
      p[k] = rng.triangular(lo, min(max(d, lo), hi), hi, n)
  return p

def cliffs_ks(xs, ys):
  "Exact Cliff's delta (xs vs ys) and KS statistic, O(n log n)."
  ys_s = np.sort(ys)
  gt = np.searchsorted(ys_s, xs, "left").sum()
  lt = (len(ys) - np.searchsorted(ys_s, xs, "right")).sum()
  grid = np.union1d(xs, ys)
  cx = np.searchsorted(np.sort(xs), grid, "right") / len(xs)
  cy = np.searchsorted(ys_s, grid, "right") / len(ys)
  return (gt - lt) / (len(xs) * len(ys)), float(np.abs(cx - cy).max())

def summarise(name, story, f0, f1, rng):
  delay = f1 - f0
  thr = np.maximum(0.05 * np.abs(f0), 0.5)
  later, earlier = delay > thr, delay < -thr
  cd, ks = cliffs_ks(f1, f0)
  k = rng.choice(len(f0), min(2000, len(f0)), replace=False)
  eps = float(np.std(f0[k])) * stats.the.stats.eps
  same = stats.same(f1[k].tolist(), f0[k].tolist(), eps)
  q = lambda a, x: float(np.percentile(a, x))
  pl, pe = 100 * later.mean(), 100 * earlier.mean()
  return dict(
    name=name, story=story,
    finish_no_hire_median=q(f0, 50), finish_hire_median=q(f1, 50),
    delay_median=q(delay, 50), delay_mean=float(delay.mean()),
    delay_sd=float(delay.std()), delay_p05=q(delay, 5),
    delay_p95=q(delay, 95), delay_iqr=q(delay, 75) - q(delay, 25),
    finished_by_80_no_hire_pct=100 * float((f0 <= LAW.tmax).mean()),
    finished_by_80_hire_pct=100 * float((f1 <= LAW.tmax).mean()),
    pct_later=pl, pct_earlier=pe, pct_no_difference=100 - pl - pe,
    cliffs_delta=float(cd), cliffs_size=size(cd), ks_stat=ks,
    same_by_stats_py=bool(same),
    verdict=("HOLDS (hiring delays)" if pl > 70 else
             "BREAKS (hiring helps)" if pe > 70 else "MIXED"),
    _delay=delay)

def size(d):    # Romano et al. 2006 thresholds
  a = abs(d)
  return ("negligible" if a < 0.147 else "small" if a < 0.33 else
          "medium" if a < 0.474 else "large")

def check(bg, p, hires, f0, f1, factory, k=150):
  "Re-run k sampled worlds through lawkit; delays must agree."
  worst = 0
  for j in range(k):
    b = {key: list(v) for key, v in bg.items()}
    for f in LAW.factors: b[f][0] = float(p[f][j])
    g, y0 = gap(LAW, b, model=factory, arms=(0, hires))
    worst = max(worst, abs(-g - (f1[j] - f0[j])), abs(-y0 - f0[j]))
  return worst

def rank(rows):
  "Scott-Knott-style tiers (stats.bestRanks) on delay: 1 = least harm."
  by = {r["name"]: r for r in rows}
  rest = {k: r["_delay"][:1000].tolist() for k, r in by.items()}
  tier = 1
  while rest:
    for k in stats.bestRanks(rest):
      by[k]["rank"] = tier
      rest.pop(k)
    tier += 1

def batch(jobs, n, seed, do_check):
  out = []
  for how in ("local", "prior"):
    rows = []
    for name, story, bg, hires, kw, factory, keep in jobs:
      rng = np.random.default_rng(seed)       # common random numbers
      p = worlds(bg, n, how, rng, keep)
      t0 = time.time()
      f0, f1 = simulate(p, 0, **kw), simulate(p, hires, **kw)
      err = check(bg, p, hires, f0, f1, factory) if do_check else 0
      r = summarise(name, story, f0, f1, rng)
      r.update(protocol=how, runs=n, check_max_abs_error=err)
      rows.append(r)
      print(f"  {how:5} {name:18} later {r['pct_later']:5.1f}% "
            f"earlier {r['pct_earlier']:5.1f}% delay "
            f"{r['delay_median']:+7.2f}  check {err:.1e} "
            f"({time.time() - t0:.0f}s)", flush=True)
    rank(rows)
    out += rows
  return out

COLS = ["protocol", "rank", "name", "finish_no_hire_median",
        "finish_hire_median", "delay_median", "delay_mean", "delay_sd",
        "delay_p05", "delay_p95", "delay_iqr", "finished_by_80_no_hire_pct",
        "finished_by_80_hire_pct", "pct_later", "pct_earlier",
        "pct_no_difference", "cliffs_delta", "cliffs_size", "ks_stat",
        "same_by_stats_py", "verdict", "runs", "check_max_abs_error",
        "story"]

def write(rows, path, first):
  with open(path, "w", encoding="utf-8") as f:
    f.write(",".join([first if c == "name" else c for c in COLS]) + "\n")
    for r in rows:
      cell = lambda c: (f"{r[c]:.3f}" if isinstance(r[c], float) else
                        f'"{r[c]}"' if c in ("story", "name") else
                        str(r[c]))
      f.write(",".join(cell(c) for c in COLS) + "\n")

def main(the):
  sc = [("default", "standard world: 10 vets, backlog 1000, 10 hires at "
         "t=10", {}, 10)]
  for k, (story, over) in LAW.scenarios.items():
    sc.append((k, story, over, over.get("_arms", (0, 10))[1]))
  jobs = [(k, s, background(LAW, o), h, {}, None, tuple(o))
          for k, s, o, h in sc]
  var = [(k, LAW.variants[k][0], background(LAW, model=LAW.variants[k][1]),
          10, kw, LAW.variants[k][1], ()) for k, kw in STRUCT.items()]
  print(f"Standard Brooks model, {the.runs:,} worlds per row")
  print("scenarios:")
  a = batch(jobs, the.runs, the.seed, the.check)
  print("team structures (default world):")
  b = batch(var, the.runs, the.seed, the.check)
  out = Path(the.out_dir); out.mkdir(exist_ok=True)
  write(a, out / "brooks_std_100k_stats.csv", "scenario")
  write(b, out / "brooks_std_100k_structures.csv", "structure")
  drop = lambda rs: [{k: v for k, v in r.items() if k != "_delay"}
                     for r in rs]
  json.dump(dict(model='lawkit LAWS["brooks"]', runs=the.runs,
                 seed=the.seed, scenarios=drop(a), structures=drop(b)),
            open(out / "brooks_std_100k_summary.json", "w"), indent=1)
  print(f"wrote {out}/brooks_std_100k_stats.csv, "
        f"brooks_std_100k_structures.csv, brooks_std_100k_summary.json")

if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--runs", type=int, default=100000)
  ap.add_argument("--seed", type=int, default=1)
  ap.add_argument("--out-dir", default="outputs")
  ap.add_argument("--no-check", dest="check", action="store_false")
  main(ap.parse_args())
