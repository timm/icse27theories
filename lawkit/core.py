"""core.py: law-agnostic engine. A Law is a causal claim about an
sd.py-style model: pulling `lever` from arms[0] to arms[1] moves y in
direction `expect`, *given* support factors (Cartwright & Hardie 2012).

Everything else in lawkit (battery, regimes, evidence) only talks to
a Law through gap()/verdict() below, so any future SE law plugs in by
writing one Law(...) spec. No law-specific code lives here."""

import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paper"))
import sd

CONFIRM, REFUTE, NEUTRAL = "CONFIRM", "REFUTE", "neutral"

class Law:
  def __init__(i, name, model, claim, lever, arms, expect, factors,
               channels=None, scenarios=None, variants=None, tmax=20,
               sources="", y=None, base=None, dt=1):
    i.name, i.model, i.claim, i.lever = name, model, claim, lever
    i.arms, i.expect, i.factors, i.tmax = arms, expect, factors, tmax
    i.channels  = channels or {}     # {param: neutral value | other var}
    i.scenarios = scenarios or {}    # {name: (story, overrides)}
    i.variants  = variants or {}     # {name: (story, model factory)}
    i.sources   = sources
    i.y         = y                  # outcome override (construct fix)
    i.base      = base or {}         # law-level default overrides
    i.dt        = dt                 # Euler step (Sterman: <= tau/4)
    i.init      = model().init

def spec(init, k, val):
  "Set k to val, widening [lo,hi] if needed (real projects exceed toys)."
  d, lo, hi, *u = init[k]
  return [val, min(lo, val), max(hi, val)] + u

def background(law, over=None, model=None):
  "Default init of (variant) model with overrides {k: value}."
  init = {k: list(v) for k, v in (model or law.model)().init.items()}
  for k, val in {**law.base, **(over or {})}.items():
    if k.startswith("_"): init[k] = val      # _tmax, _arms: run settings
    elif k in init: init[k] = spec(init, k, val)
  return init

def gap(law, bg, model=None, dt=None, tmax=None, arms=None, mode="clip"):
  "y(arm1) - y(arm0) on background bg. None if a run is rejected."
  m = (model or law.model)()
  dt = dt or law.dt
  tmax = tmax or bg.get("_tmax", law.tmax)
  a0, a1 = arms or bg.get("_arms", law.arms)
  bg = {k: v for k, v in bg.items() if not k.startswith("_")}
  for k in getattr(law, "free", ()):            # prior range, not physics
    if k in bg: bg[k] = bg[k][:2] + [math.inf] + bg[k][3:]
  ys = []
  for a in (a0, a1):
    out = sd.run({**bg, law.lever: spec(bg, law.lever, a)}, m.step,
                 dt=dt, tmax=tmax, mode=mode)
    if out is None: return None, None
    ys.append((law.y or (lambda o, b: m.y(o)))(out, bg))
  return ys[1] - ys[0], ys[0]

def verdict(law, g, y0):
  "Same 5%-of-y0 rule as sd.verdict, signed by the claimed direction."
  if g is None: return NEUTRAL
  signed = -g if law.expect == "down" else g
  thresh = max(abs(y0) * 0.05, 0.5)
  return (CONFIRM if signed > thresh else
          REFUTE if signed < -thresh else NEUTRAL)

def judge(law, bg, **kw):
  g, y0 = gap(law, bg, **kw)
  return verdict(law, g, y0), g

def draw(law, rng, how="prior", base=None, model=None, keep=()):
  """Sample a background. how='prior': triangular over declared
  [lo,hi] peaked at default; 'uniform': adversarial; 'local': +-15%
  around base (the old Monte-Carlo protocol). keep = fixed factors."""
  bg = dict(base or background(law, model=model))
  for k in law.factors:
    if k in keep or k not in bg or k.startswith("_"): continue
    d, lo, hi = bg[k][0], bg[k][1], bg[k][2]
    if how == "local":
      v = min(hi, max(lo, d * rng.uniform(0.85, 1.15)))
    else:
      v = sd.sample(rng, d, lo, hi, "uniform" if how == "uniform"
                    else "triangular")
    bg[k] = [v] + bg[k][1:]
  return bg

def tally(vs):
  n = max(1, len(vs))
  return {v: round(100 * sum(x == v for x in vs) / n, 1)
          for v in (CONFIRM, REFUTE, NEUTRAL)}

def quantiles(xs, ps=(0.05, 0.5, 0.95)):
  xs = sorted(x for x in xs if x is not None)
  if not xs: return [math.nan] * len(ps)
  return [xs[min(len(xs) - 1, int(p * len(xs)))] for p in ps]

def entropy(p):
  p = min(max(p, 1e-12), 1 - 1e-12)
  return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
