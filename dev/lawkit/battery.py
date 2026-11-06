"""battery.py: Forrester & Senge (1980) / Sterman (2000) structure tests
plus metamorphic relations (Chen et al. 1998), each with an expectation
stated *before* running, so every test can actually FAIL.

These test the model-as-machine, not the law. A law can only be judged
on a machine that passes them (Cartwright 1999: no nomological machine,
no law)."""

import math
from .core import (background, gap, verdict, judge, draw, spec, tally,
                   CONFIRM, REFUTE, NEUTRAL)
from .units import check as check_dims
import random, sd

PASS, FAIL, WARN, INFO = "PASS", "FAIL", "WARN", "INFO"

def row(test, status, detail, ref):
  return dict(test=test, status=status, detail=detail, ref=ref)

def units(law):
  "Every var has a unit, and every equation joins like units."
  bad = [k for k, v in law.init.items() if len(v) < 4]
  if bad: return row("units & dimensions", FAIL, f"missing units: {bad}",
                     "F&S dimensional consistency")
  bg = {k: v for k, v in background(law).items() if not k.startswith("_")}
  errs, notes = check_dims(law.model(), bg, law.lever, law.arms[1], law.tmax)
  return row("units & dimensions", FAIL if errs else PASS,
             (f"mismatch {errs[0]}" if errs else "every equation consistent")
             + (f"; literals: {', '.join(notes)}" if notes else ""),
             "F&S dimensional consistency")

def dead_params(law, tries=20, seed=4):
  """Param verification: every declared param must move y in some arm,
  at the default or, failing that, in some prior-drawn world (a param
  that acts only together with another, e.g. a deadline that matters
  only once overtime > 0, is live)."""
  rng, dead, via = random.Random(seed), [], []
  bgs = [background(law)] + [draw(law, rng) for _ in range(tries)]
  def moves(bg, k, vals):
    y = lambda val, a: round(gap(law, {**bg, k: spec(bg, k, val)},
                                 arms=(a, a))[1], 9)
    return any(len({y(val, a) for val in vals}) > 1 for a in law.arms)
  for k, v in law.init.items():
    if not k[0].islower() or k == law.lever: continue
    if moves(bgs[0], k, v[:3]): continue
    (via if any(moves(bg, k, v[:3]) for bg in bgs[1:]) else dead).append(k)
  return row("dead parameters", FAIL if dead else PASS,
             f"no influence on y: {dead}" if dead else "all params live" +
             (f" ({', '.join(via)} only together with another factor)"
              if via else ""), "F&S parameter verification")

def extremes(law):
  "Each factor at lo and hi: finite y; report verdict at each extreme."
  bad, flips = [], []
  for k in law.factors:
    for side in (1, 2):
      bg = background(law)
      bg[k] = spec(bg, k, bg[k][side])
      try:
        v, g = judge(law, bg)
        if g is None or not math.isfinite(g): bad.append(f"{k}@{side}")
        elif v != CONFIRM: flips.append(f"{k}={bg[k][0]:g}:{v}")
      except Exception as e:
        bad.append(f"{k}@{side}:{type(e).__name__}")
  return row("extreme conditions", FAIL if bad else PASS,
             (f"crash/NaN: {bad}. " if bad else "all finite. ") +
             f"claim not CONFIRMed at {len(flips)} extremes: " +
             ", ".join(flips[:8]), "F&S extreme conditions")

def clamps(law, n=300, seed=1):
  "Is the verdict produced by state clamping? Re-run in reject mode."
  rng, hit, flip = random.Random(seed), 0, 0
  for _ in range(n):
    bg = draw(law, rng)
    vc, _ = judge(law, bg)
    g, y0 = gap(law, bg, mode="reject")
    if g is None: hit += 1
    if g is None and vc == CONFIRM: flip += 1
  pct = 100 * hit / n
  return row("clamp dependence", FAIL if flip > n * 0.2 else
             WARN if flip else PASS,           # escapes alone are harmless
             f"{pct:.0f}% of prior backgrounds escape declared bounds; "
             f"{100*flip/n:.0f}% are CONFIRMs that need clamping",
             "Sterman boundary/structure; sd.mr_bound_consist")

def dt_halving(law):
  bg, d = background(law), law.dt
  out = {dt: gap(law, bg, dt=dt) for dt in (d, d / 2, d / 4)}
  vs = {dt: verdict(law, *out[dt]) for dt in out}
  g1, g4 = out[d][0], out[d / 4][0]
  rel = abs(g1 - g4) / max(abs(g4), 1)
  st = FAIL if len(set(vs.values())) > 1 else WARN if rel > .1 else PASS
  return row("integration step (dt)", st,
             f"gap dt={d:g}:{g1:+.1f} dt={d / 4:g}:{g4:+.1f} ({rel:.0%}); "
             f"verdicts {list(vs.values())}", "Sterman test 6")

def horizon(law):
  "Boundary adequacy in time: does the verdict reverse later (J-curve)?"
  bg, seen = background(law), []
  for t in (law.tmax // 2 + 5, law.tmax, 2 * law.tmax, 4 * law.tmax):
    seen.append((t, *judge(law, bg, tmax=t)))
  vs = [v for _, v, _ in seen]
  st = WARN if len(set(vs)) > 1 else PASS
  return row("time-horizon adequacy", st, "; ".join(
    f"t={t}:{v}({g:+.0f})" for t, v, g in seen), "F&S 4/7 boundary")

def dose(law, n=7):
  "MR1: y should move monotonically as the lever is turned up."
  bg, a0, a1 = background(law), *law.arms
  hi = max(a1, bg[law.lever][2])
  pts = [a0 + (hi - a0) * j / (n - 1) for j in range(n)]
  gs = [gap(law, bg, arms=(a0, p))[0] for p in pts]
  sign = -1 if law.expect == "down" else 1
  d = [sign * (b - a) for a, b in zip(gs, gs[1:])]
  up, mono = False, True          # harm may first shrink (below a sweet
  for x in d:                     # spot), but must never shrink again
    if x > 0.5: up = True         # once it has started to grow
    elif x < -0.5 and up: mono = False
  return row("dose-response monotone", PASS if mono else WARN,
             "gaps " + ", ".join(f"{p:g}:{g:+.0f}" for p, g in
                                 zip(pts, gs)), "Chen MR1")

def knockout(law):
  """Mechanism check: neutralise every declared causal channel; the
  claimed effect must vanish. If it survives, the effect flows through
  an undeclared (often hard-coded) path."""
  if not law.channels:
    return row("mechanism knock-out", INFO, "no channels declared", "")
  bg = background(law)
  for k, val in law.channels.items():
    bg[k] = spec(bg, k, bg[val][0] if isinstance(val, str) else val)
  v, g = judge(law, bg)
  return row("mechanism knock-out", FAIL if v == CONFIRM else PASS,
             f"channels {list(law.channels)} neutral -> {v} ({g:+.1f})",
             "Cartwright capacities / causal cake")

def free_lunch(law, n=1000, seed=2):
  "If no background in the declared ranges refutes, the claim is built in."
  rng = random.Random(seed)
  t = tally([judge(law, draw(law, rng, "uniform"))[0] for _ in range(n)])
  st = WARN if t[REFUTE] == 0 or t[CONFIRM] == 0 else PASS
  return row("refutability (uniform)", st,
             f"uniform over ranges: {t}", "Popper; anti-tautology")

def scale(law):
  "MR2: doubling every stock should not reverse the verdict."
  bg = background(law)
  v0, g0 = judge(law, bg)
  for k, s in bg.items():
    if k[0].isupper() and k in law.init: bg[k] = spec(bg, k, 2 * s[0])
  v1, g1 = judge(law, bg)
  flip = {v0, v1} == {CONFIRM, REFUTE}          # MR2 forbids a reversal
  return row("scale x2 (MR2)", WARN if flip else PASS,
             f"{v0}({g0:+.0f}) -> {v1}({g1:+.0f})", "Chen MR2")

TESTS = [units, dead_params, extremes, clamps, dt_halving, horizon,
         dose, knockout, free_lunch, scale]

def battery(law):
  return [t(law) for t in TESTS]
