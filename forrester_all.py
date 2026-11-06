#!/usr/bin/env python3 -B
"""forrester_all.py: every Forrester & Senge (1980) test that needs no
project data, plus Sterman's (2000) integration-error test and Chen et
al.'s (1998) metamorphic relations, run on the standard lawkit brooks
model in the default world and in every business scenario.

Each test states its expectation before it runs and can FAIL. Two
validation blocks follow: known answers (hand calculations the harness
must reproduce) and mutants (deliberately broken models each invariant
check must catch).

  python -B forrester_all.py        # -> outputs/forrester_all.{md,json}
"""

import copy, json, math, re, sys, time
from pathlib import Path
from types import SimpleNamespace as S
import lawkit                                   # puts paper/ on sys.path
import sd
from lawkit.laws import LAWS, flat_comm
from lawkit.core import background, gap, judge, spec, CONFIRM, REFUTE
from lawkit import battery, regimes

the = S(n=1000, oat=11, tip=21, eps=1e-6)
PASS, FAIL, WARN, INFO = battery.PASS, battery.FAIL, battery.WARN, "INFO"
LAWS_RUN = ("brooks",)

def row(test, status, detail, ref=""):
  return dict(test=test, status=status, detail=detail, ref=ref)

# --- worlds ---------------------------------------------------------------

def world(law, name, over):
  "The law re-based on one business scenario."
  w = copy.copy(law)
  w.name, w.base = name, {**law.base, **over}
  w.scenarios, w.variants = {}, law.variants
  w.tmax, w.arms = over.get("_tmax", law.tmax), over.get("_arms", law.arms)
  return w

def worlds():
  for law in map(LAWS.get, LAWS_RUN):
    yield law, world(law, "default", {})
    for name, (_, over) in law.scenarios.items():
      yield law, world(law, name, over)

def bg(w, model=None, **kv):
  b = background(w, model=model)
  for k, v in kv.items(): b[k] = spec(b, k, v)
  return b

def traj(w, b, arm, clip=True, model=None, dt=None):
  "States after each step; clip=False keeps the raw equations' values."
  m, dt = (model or w.model)(), dt or w.dt
  init = {k: v for k, v in b.items() if not k.startswith("_")}
  init[w.lever] = spec(init, w.lever, arm)
  tmax = b.get("_tmax", w.tmax)
  if clip: return [s for _, s in sd.run(init, m.step, dt=dt, tmax=tmax)]
  u, out, t = sd.make_state({k: v[0] for k, v in init.items()}), [], 0
  while t < tmax:
    v = sd.make_state(vars(u)); m.step(dt, t, u, v); out.append(v)
    u, t = v, t + dt
  return out

def hire_step(w, b):
  "Index of the step in which the hires arrive."
  return round(b['hire_at'][0] / w.dt)

def first0(r):
  "Index of the step that empties the backlog, else None."
  return next((t for t, s in enumerate(r) if s.Todo <= the.eps), None)

# --- F&S structure tests ----------------------------------------------------

def extreme_known(w, model=None):
  "Extreme conditions with answers known in advance."
  b0, a1 = background(w, model=model), w.arms[1]
  h = hire_step(w, b0)
  r = lambda a, **kv: traj(w, bg(w, model, **kv), a, model=model)
  steps = lambda rr: [b - a for a, b in
                      zip([0] + [s.Done for s in rr], [s.Done for s in rr])]
  V0, full = b0['Vet'][0], b0['prod_rate'][0] * w.dt   # one dev, one step
  cases = [
    ("no workforce: Vet=0, nobody hired -> nothing ever done",
     lambda: all(s.Done == 0 for s in r(0, Vet=0))),
    ("no work: Todo=0 -> nothing ever done (both arms)",
     lambda: all(s.Done == 0 for a in (0, a1) for s in r(a, Todo=0))),
    ("talk overload: Vet=10, comm_coef=0.05 (overhead 2.25 of each day) -> "
     "first-step output = capacity x efficiency(2.25), under 15% of capacity",
     lambda: abs(steps(r(0, Vet=10, comm_coef=0.05))[0]
                 - 10 * full * effic(w, 2.25)) < 1e-9
             and steps(r(0, Vet=10, comm_coef=0.05))[0] < 0.15 * 10 * full),
    ("training overload: train_coef=1 -> output the step after the hire "
     "= min(capacity x efficiency(talk + hires x 1), work left)",
     lambda: a1 == 0 or overload_ok(r(a1, train_coef=1), h, V0 * full * effic(
       w, flat_comm(V0, b0['comm_coef'][0]) + a1))),
    ("no learning: mature_rate=0 -> veterans never change",
     lambda: all(abs(s.Vet - V0) < the.eps for s in r(a1, mature_rate=0))),
    ("full learning rate: mature_rate=1 -> newcomers shrink by (1 - dt) "
     "each step after the hire",
     lambda: abs(r(a1, mature_rate=1)[h + 1].New - a1 * (1 - w.dt)) < 1e-9)]
  out = []
  for name, ok in cases:
    try: st = PASS if ok() else FAIL
    except Exception as e: st, name = FAIL, f"{name} ({type(e).__name__})"
    out.append((name, st))
  bad = [n for n, s in out if s == FAIL]
  return row("extreme conditions (known answers)", FAIL if bad else PASS,
             f"{len(out) - len(bad)}/{len(out)} hold" +
             (f"; FAIL: {'; '.join(bad)}" if bad else ""), "F&S 1980 §3")

def overload_ok(rr, h, most):
  "Output in step h+1 = what the team can do, unless less work is left."
  done = rr[h + 1].Done - rr[h].Done
  return abs(done - min(most, rr[h].Todo)) < 1e-9

def effic(_w, x):
  "Share of time left for work at overhead x (bounded overload)."
  return math.exp(-x)

BOUNDARY = [  # (structure in the literature, setting that carries it)
  ("communication overhead grows with pairs", "comm_coef"),
  ("training drains veterans' time", "train_coef"),
  ("newcomers do some work while learning", "newprod"),
  ("some work cannot be split across people", "serial"),
  ("people leave (attrition)", "leave"),
  ("schedule pressure / overtime", "overtime"),
  ("errors and rework", "rework")]

def boundary_structure(w):
  miss = [s for s, k in BOUNDARY if k not in w.init]
  return row("boundary adequacy (structure)", WARN if miss else PASS,
             f"{len(BOUNDARY) - len(miss)}/{len(BOUNDARY)} literature "
             f"structures present" + (f"; missing: {'; '.join(miss)}" if miss
             else " (five as uncertain settings, off at default)"),
             "F&S 1980 §3")

# --- F&S behaviour tests -----------------------------------------------------

def invariants(w, model=None):
  """Behaviour anomaly: physical laws the trajectories must obey.
  Raw = equations without the engine's clipping."""
  b, a1 = background(w, model=model), w.arms[1]
  h, T0, V0, cap = (hire_step(w, b), b['Todo'][0], b['Vet'][0],
                    b['prod_rate'][0] * w.dt)
  init = sd.make_state({k: v[0] for k, v in b.items() if not k.startswith("_")})
  raw = {a: traj(w, b, a, clip=False, model=model) for a in (0, a1)}
  cut = {a: traj(w, b, a, model=model) for a in (0, a1)}
  pre = lambda rr: [init] + rr[:-1]
  def eff(u):                                 # raw share of time left
    return effic(w, flat_comm(u.Vet, u.comm_coef) + u.New * u.train_coef)
  def most(u):                                # most work one step allows
    return (u.Vet + u.newprod * u.New) * cap * (1 + u.overtime)
  checks = {
    "people never negative":
      all(s.Vet >= -the.eps and s.New >= -the.eps
          for rr in raw.values() for s in rr),
    "headcount conserved (Vet+New = start + hires)":
      all(abs(s.Vet + s.New - V0 - (a if t >= h else 0)) < 1e-6
          for a, rr in raw.items() for t, s in enumerate(rr)),
    "causality (arms identical before the hire)":
      all(vars(x) == {**vars(y), w.lever: x.__dict__[w.lever]}
          for x, y in zip(raw[0][:h], raw[a1][:h])),
    "work never un-done (Done non-decreasing)":
      all(b2.Done >= a2.Done - the.eps for rr in raw.values()
          for a2, b2 in zip(rr, rr[1:])),
    "nobody exceeds full time (work/step <= Vet x prod_rate x dt)":
      all(s.Done - u.Done <= most(u) + 1e-6 for rr in raw.values()
          for u, s in zip(pre(rr), rr)),
    "no phantom work (raw Done <= backlog)":
      all(s.Done <= T0 + 1e-6 for rr in raw.values() for s in rr),
    "work conserved in the run (Done + Todo = backlog)":
      all(abs(s.Done + s.Todo - T0) < 1e-6 for rr in cut.values() for s in rr)}
  neg = sum(eff(u) < 0 for rr in raw.values() for u in pre(rr))
  tot = sum(len(rr) for rr in raw.values())
  bad = [k for k, ok in checks.items() if not ok]
  out = [row("behaviour anomaly (invariants)", FAIL if bad else PASS,
             f"{len(checks) - len(bad)}/{len(checks)} hold" +
             (f"; FAIL: {'; '.join(bad)}" if bad else ""), "F&S 1980 §4")]
  out.append(row("behaviour anomaly (negative effort hidden by clamp)",
                 WARN if neg else PASS,
                 f"{neg}/{tot} steps have negative raw effort (clamped to 0)",
                 "F&S 1980 §4"))
  return out, checks

def extreme_policy(w):
  "Lever at its extremes: zero policy, maximum policy, inert policy."
  b, a1 = background(w), w.arms[1]
  notes, bad = [], []
  g0, _ = gap(w, b, arms=(0, 0))
  (notes if g0 == 0 else bad).append(f"hire 0: gap {g0:+g} (expect 0)")
  gs = {a: gap(w, b, arms=(0, a))[0] for a in (a1, 100)}
  vh = judge(w, b, arms=(0, 100))[0]
  fin = all(math.isfinite(g) for g in gs.values())
  worse = gs[100] <= gs[a1] + 0.5
  (notes if fin and worse else bad).append(
    f"hire 100: gap {gs[100]:+.0f} vs {gs[a1]:+.0f} at {a1} ({vh}); "
    "expect finite and no better than fewer hires")
  for hh in (0, int(b['hire_at'][2])):
    v, g = judge(w, bg(w, hire_at=hh))
    notes.append(f"hire_at={hh}: {v} ({g:+.0f})")
  f = first0(traj(w, b, 0))
  hh = None if f is None else math.ceil((f + 1) * w.dt)
  if hh is not None and hh < b.get("_tmax", w.tmax) and a1:
    g, _ = gap(w, bg(w, hire_at=hh))
    (notes if abs(g) < the.eps else bad).append(
      f"hire after finish (t={hh}): gap {g:+g} (expect 0)")
  else: notes.append("hire after finish: n/a (never finishes in horizon)")
  return row("extreme policy", FAIL if bad else PASS,
             "; ".join(bad + notes), "F&S 1980 §4")

def boundary_behaviour_policy(w):
  """Behaviour: is any literature structure still missing? Policy: does
  the recommendation survive each rival team structure?"""
  b = background(w)
  v0, g0 = judge(w, b)
  miss = [s for s, k in BOUNDARY if k not in w.init]
  pol = [(k, *judge(w, background(w, model=f), model=f))
         for k, (_, f) in w.variants.items() if k != "flat (reference)"]
  flips = [f"{n}: {v} ({g:+.0f})" for n, v, g in pol if v != v0]
  same = [n for n, v, _ in pol if v == v0]
  return [row("boundary adequacy (behaviour)", WARN if miss else PASS,
              f"missing: {'; '.join(miss)}" if miss else
              "no structure missing: all seven are in the model; their "
              "effect is explored by behaviour/policy sensitivity",
              "F&S 1980 §4"),
          row("boundary adequacy (policy)", WARN if flips else PASS,
              f"default {v0} ({g0:+.0f}); recommendation kept under "
              f"{len(same)}/{len(pol)} rival team structures" +
              (f"; changes: {'; '.join(flips)}" if flips else ""),
              "F&S 1980 §5")]

def mode(w, b):
  "Shape of the hire arm's output after the hire."
  r, h = traj(w, b, w.arms[1]), hire_step(w, b)
  done = [0] + [s.Done for s in r]
  prod = [q - p for p, q in zip(done, done[1:])]
  f = first0(r)
  if f is not None and f <= h: return "finished before hire"
  post = prod[h + 1:(f if f is not None else len(prod))]
  if not post or min(post) >= 0.95 * prod[h]: return "no dip"
  low = post.index(min(post))
  return ("dip then recovers" if max(post[low:]) >= prod[h]
          else "dip, no recovery")

def behaviour_sensitivity(w):
  "Does the shape of the behaviour change across plausible values?"
  b = background(w)
  base, moved = mode(w, b), []
  for k in w.factors:
    lo, hi = b[k][1], b[k][2]
    seen = {}
    for j in range(the.oat):
      val = lo + (hi - lo) * j / (the.oat - 1)
      seen.setdefault(mode(w, bg(w, **{k: val})), []).append(val)
    if len(seen) > 1:
      moved.append(f"{k}: " + ", ".join(
        f"{m} [{min(vs):.3g}..{max(vs):.3g}]" for m, vs in seen.items()))
  return row("behaviour sensitivity", WARN if moved else PASS,
             f"default shape '{base}'" +
             (f"; shape changes with {'; '.join(moved)}" if moved else
              "; same shape across every factor's range"), "F&S 1980 §4")

def policy_sensitivity(w):
  "Does the recommendation flip across plausible values?"
  r, tips = regimes.robustness(w, n=the.n), regimes.tipping(w, the.tip)
  p = r["prior"]
  top = max((CONFIRM, REFUTE, "neutral"), key=lambda k: p[k])
  cuts = [f"{k}: {', '.join(c)}" for k, c in tips.items() if c]
  st = PASS if p[top] >= 90 and not cuts else WARN
  return row("policy sensitivity", st,
             f"prior {p[CONFIRM]:.0f}/{p[REFUTE]:.0f}/{p['neutral']:.0f}, "
             f"uniform {r['uniform'][CONFIRM]:.0f}/{r['uniform'][REFUTE]:.0f}/"
             f"{r['uniform']['neutral']:.0f} (C/R/n %); flips: " +
             ("; ".join(cuts) if cuts else "none"), "F&S 1980 §5")

BATTERY_NAMES = {  # lawkit battery row -> the F&S / Sterman / Chen test it is
  "units & dimensions": "dimensional consistency (F&S §3)",
  "dead parameters": "structure: every parameter matters (F&S §3)",
  "extreme conditions": "extreme conditions, every factor at lo/hi (F&S §3)",
  "clamp dependence": "behaviour anomaly: verdicts made by clipping (F&S §4)",
  "integration step (dt)": "integration error (Sterman 2000)",
  "time-horizon adequacy": "boundary adequacy in time (F&S §3/§4)",
  "dose-response monotone": "metamorphic MR1: more hires, steadier harm (Chen)",
  "mechanism knock-out": "structure: declared causes do the work (F&S §3)",
  "refutability (uniform)": "policy sensitivity: can any world refute? (F&S §5)",
  "scale x2 (MR2)": "metamorphic MR2: double stocks, same verdict (Chen)"}

# Tests whose WARN *is* the research result (F&S: sensitivity says which
# values matter; only real data says which values are true).
FINDINGS = ("policy sensitivity", "behaviour sensitivity",
            "boundary adequacy (policy)",
            "boundary adequacy in time (F&S §3/§4)")
FINDING = "finding: the law is conditional; resolving it needs real data. "
DEAD = "structure: every parameter matters (F&S §3)"
REFUTE_T = "policy sensitivity: can any world refute? (F&S §5)"

def relabel(w, rows, live):
  "WARN on a finding -> INFO; per-scenario dead knob -> INFO if model-live."
  for r in rows:
    t, scen = r["test"], w.name != "default"
    if r["status"] == WARN and (t in FINDINGS or (t == REFUTE_T and scen)):
      r["status"], r["detail"] = INFO, FINDING + r["detail"]
    elif r["status"] == FAIL and t == DEAD and scen and live:
      r["status"] = INFO
      r["detail"] = ("inactive in this scenario; every parameter is live in "
                     "the default world. " + r["detail"])
  return rows

def suite(w, live=True):
  rows = [dict(r, test=BATTERY_NAMES.get(r["test"], r["test"]))
          for r in battery.battery(w)]
  rows += [extreme_known(w), boundary_structure(w)]
  rows += invariants(w)[0]
  rows += [extreme_policy(w)] + boundary_behaviour_policy(w)
  rows += [behaviour_sensitivity(w), policy_sensitivity(w)]
  return relabel(w, rows, live)

# --- validation ------------------------------------------------------------

def known_answers():
  "Hand calculations the standard model must reproduce exactly."
  w = world(LAWS["brooks"], "default", {})
  b, out = background(w), []
  r0, r10 = traj(w, b, 0), traj(w, b, 10)
  rate = 10 * math.exp(-45 * 0.005) * 5
  out.append(("output per tick, 10 veterans: 10 x e^(-45 x 0.005) x 5 = "
              f"{rate:.3f}", f"{r0[0].Done / w.dt:.3f}",
              abs(r0[0].Done / w.dt - rate) < 1e-9))
  fin = math.ceil(1000 / (rate * w.dt)) * w.dt
  y0 = gap(w, b)[1]
  out.append((f"no-hire finish = ceil(1000 / ({rate:.3f} x {w.dt})) steps "
              f"= tick {fin:g}", f"{-y0:g}", abs(-y0 - fin) < 1e-9))
  h = hire_step(w, b)
  after = (r10[h + 1].Done - r10[h].Done) / w.dt
  want = 10 * math.exp(-(0.225 + 10 * 0.2)) * 5
  out.append(("output right after 10 hires = 10 x e^(-(0.225 + 10 x 0.2)) x "
              f"5 = {want:.3f} (slowed, not frozen)", f"{after:.3f}",
              abs(after - want) < 1e-9))
  best = max(range(1, 41),
             key=lambda V: V * math.exp(-0.005 * V * (V - 1) / 2))
  vstar = (1 + math.sqrt(1 + 8 * 2 / 0.005)) / 4
  out.append((f"team optimum V* from V(2V - 1) = 2/c (c = 0.005) is "
              f"{vstar:.1f} -> {round(vstar)}", f"{best}", best == round(vstar)))
  return out

def mutant(kind, name="brooks"):
  "A brooks model with one deliberate defect."
  base = LAWS[name].model
  def factory():
    m = base()
    def step(dt, t, u, v):
      m.step(dt, t, u, v)
      if kind == "leak": v.Vet -= 0.1 * dt * u.mature_rate * u.New
      if kind == "future": v.Done -= dt * 0.01 * u.boost
      if kind == "superhuman":
        x = 0.5 * u.Vet * u.prod_rate * dt; v.Done += x; v.Todo -= x
      if kind == "undo" and t == u.hire_at:     # hire step: lose 1 + output
        x = v.Done - u.Done + 1; v.Done -= x; v.Todo += x
      if kind == "phantom": v.Done += 1
    return sd.Model(m.init, step, m.y, None, 'boost')
  return factory

MUTANTS = [("leak", "10% of maturing newcomers vanish",
            "headcount conserved (Vet+New = start + hires)"),
           ("future", "future hires lower today's output",
            "causality (arms identical before the hire)"),
           ("superhuman", "everyone does 1.5x full time",
            "nobody exceeds full time (work/step <= Vet x prod_rate x dt)"),
           ("undo", "the hire tick un-does its own output plus one item",
            "work never un-done (Done non-decreasing)"),
           ("phantom", "one extra item 'done' every tick",
            "work conserved in the run (Done + Todo = backlog)")]

def mutants(name="brooks"):
  "(model, defect, check, clean model passes it, mutant caught by it)."
  w = world(LAWS[name], "default", {})
  _, clean = invariants(w)
  out = []
  for kind, story, target in MUTANTS:
    _, checks = invariants(w, model=mutant(kind, name))
    out.append((name, story, target, clean[target], not checks[target]))
  from lawkit.units import check
  m = LAWS[name].model()
  ok, _ = check(m, m.init, "boost", 10, 20)
  bad = {**m.init, 'prod_rate': [5, 0.1, 20, 'items/vet/tick']}
  errs, _ = check(m, bad, "boost", 10, 20)
  out.append((name, "prod_rate labelled items/vet/tick",
              "dimensional consistency", not ok, bool(errs)))
  return out

# --- policy sensitivity with data (F&S §5: stable within real values?) -------

def data_policy(n=None):
  """Re-run policy sensitivity inside Helix's measured comm_coef,
  train_coef and mature_rate (bootstrap samples), for Helix's team sizes.
  PASS = one recommendation in >= 90% of data-consistent worlds."""
  from lawkit.evidence import Evidence, place, voi
  d = json.loads(Path("outputs/evidence/brooks_helix.json").read_text())
  out = []
  for name in LAWS_RUN:
    for v in (3, 6, 8):
      ev = Evidence(LAWS[name], d["project"], d["measured"],
                    {**(d.get("fixed") or {}), "Vet": v, "_arms": [0, v]})
      p = place(ev, n=n or the.n)
      top = max((CONFIRM, REFUTE, "neutral"), key=lambda k: p[k])
      nxt = voi(ev, n=n or the.n)["ranked"][0]
      out.append(dict(law=name, vet=v, confirm=p[CONFIRM], refute=p[REFUTE],
                      neutral=p["neutral"], top=top,
                      status=PASS if p[top] >= 90 else WARN,
                      next=f"{nxt['factor']} (gain {nxt['gain']})"))
  return out

# --- report -----------------------------------------------------------------

def report(results, ka, mu, secs, dp=()):
  tests = list(dict.fromkeys(r["test"] for rows in results.values()
                             for r in rows))
  L = [f"# Forrester tests without project data: the standard brooks model",
       "", f"*Generated by `forrester_all.py` in {secs:.0f}s. Each test "
       "states its expectation first and can FAIL. Statuses: PASS, WARN "
       "(works but has a weakness), FAIL (expectation broken), INFO (a "
       "finding about where the law holds, or a knob a scenario never "
       "exercises; not a model fault). Model: lawkit `brooks` (late "
       "project, finish time, five literature structures, bounded "
       "overload, dt = 0.125).*", "",
       "## 1. Validation of the harness", "",
       "### Known answers (hand calculation vs simulator)", "",
       "| check | simulator | ok |", "|---|---|---|"]
  L += [f"| {a} | {b} | {'PASS' if c else 'FAIL'} |" for a, b, c in ka]
  L += ["", "### Mutants (each check must catch its defect)", "",
        "| model | deliberate defect | check that must fail | clean model "
        "passes it | defect caught |", "|---|---|---|---|---|"]
  L += [f"| {m} | {a} | {b} | {'yes' if c else 'NO'} | "
        f"{'yes' if d else 'NO'} |" for m, a, b, c, d in mu]
  L += ["", "## 2. Policy sensitivity with data (Helix)", "",
        "Forrester & Senge's policy-sensitivity test passes when the "
        "recommendation does not flip *within real-world values*. Here "
        "Helix's measured comm_coef, train_coef and mature_rate "
        "(bootstrap samples, `outputs/evidence/brooks_helix.json`) "
        "replace their priors; the team is doubled from Helix's sizes.", "",
        "| model | Helix team, doubled | CONFIRM | REFUTE | neutral | status "
        "| measure next |", "|---|---|---|---|---|---|---|"]
  L += [f"| {r['law']} | {r['vet']} | {r['confirm']:.0f}% | "
        f"{r['refute']:.0f}% | {r['neutral']:.0f}% | {r['status']} | "
        f"{r['next']} |" for r in dp]
  L += ["", "## 3. Status matrix (rows: tests; columns: worlds)", ""]
  for law in LAWS_RUN:
    ws = [k for k in results if k.startswith(law + "/")]
    L += [f"### {law}", "",
          "| test | " + " | ".join(k.split("/", 1)[1] for k in ws) + " |",
          "|---|" + "---|" * len(ws)]
    for t in tests:
      st = [next((r["status"] for r in results[k] if r["test"] == t), "")
            for k in ws]
      L.append(f"| {t} | " + " | ".join(st) + " |")
    L.append("")
  L += ["## 4. Details per world", ""]
  for k, rows in results.items():
    L += [f"### {k}", "", "| status | test | detail |", "|---|---|---|"]
    L += [f"| {r['status']} | {r['test']} | {r['detail']} |" for r in rows]
    L.append("")
  if EXPLAINED.exists():          # hand-written guide to every test
    L += ["## 5. How each test works (example and code location)", "",
          "*Examples are from the default world of the run that wrote "
          f"`{EXPLAINED.as_posix()}`; check them against sections 1-4 "
          "above after a re-run.*", "",
          EXPLAINED.read_text(encoding="utf-8")]
  return "\n".join(L)

EXPLAINED = Path("research_docs/forrester_tests_explained.md")

def report_only():
  "Rebuild outputs/forrester_all.md from the saved JSON (no re-run)."
  out = Path("outputs")
  d = json.loads((out / "forrester_all.json").read_text())
  old = (out / "forrester_all.md").read_text(encoding="utf-8")
  m = re.search(r"in (\d+)s\.", old)
  (out / "forrester_all.md").write_text(
    report(d["results"], d["known_answers"], d["mutants"],
           float(m.group(1)) if m else 0, d["data_policy"]),
    encoding="utf-8")
  print("-> outputs/forrester_all.md (rebuilt from forrester_all.json)")

def main():
  t0, results, live = time.time(), {}, {}
  for law, w in worlds():
    t = time.time()
    if law.name not in live:
      live[law.name] = battery.dead_params(law)["status"] == PASS
    results[f"{law.name}/{w.name}"] = suite(w, live[law.name])
    print(f"{law.name}/{w.name}: {time.time() - t:.1f}s", flush=True)
  ka, mu = known_answers(), mutants("brooks")
  dp = data_policy()
  out = Path("outputs")
  (out / "forrester_all.json").write_text(json.dumps(
    dict(results=results, known_answers=ka, mutants=mu, data_policy=dp),
    indent=1))
  (out / "forrester_all.md").write_text(
    report(results, ka, mu, time.time() - t0, dp), encoding="utf-8")
  print(f"-> outputs/forrester_all.md ({time.time() - t0:.0f}s)")

if __name__ == "__main__":
  report_only() if "--report-only" in sys.argv else main()
