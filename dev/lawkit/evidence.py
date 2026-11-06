"""evidence.py: 'it worked there' -> 'will it work here?'
(Cartwright & Hardie 2012). Real-project data is used to *place a
project in the law's regime map*, not to re-estimate the law's average
effect. Measured support factors are fixed from their bootstrap
samples; unmeasured ones keep their prior. The output is
P(claim holds | what we know about this project) and, for every
unmeasured factor, how much measuring it would settle the verdict."""

import random
from .core import (background, judge, draw, spec, tally, quantiles,
                   entropy, CONFIRM)

class Evidence:
  """measured: {factor: [bootstrap values]}          absolute estimate
               {factor: ("x", other, [ratios])}      factor = r * other
     fixed   : {factor: value}                       known exactly
     notes   : list of construct-validity caveats (the 'long chain')."""
  def __init__(i, law, project, measured=None, fixed=None, notes=(),
               population=""):
    i.law, i.project, i.population = law, project, population
    i.measured, i.fixed, i.notes = measured or {}, fixed or {}, notes

  def known(i):
    return set(i.measured) | set(i.fixed)

  def sample(i, rng):
    bg = draw(i.law, rng, "prior", base=background(i.law, i.fixed),
              keep=set(i.fixed))
    for k, ev in i.measured.items():
      if isinstance(ev, tuple):
        _, other, rs = ev
        val = rng.choice(rs) * bg[other][0]
      else:
        val = rng.choice(ev)
      bg[k] = spec(bg, k, val)
    return bg

def place(ev, n=2000, seed=1):
  rng = random.Random(seed)
  rs = [judge(ev.law, ev.sample(rng)) for _ in range(n)]
  return dict(tally([v for v, _ in rs]), gap=quantiles([g for _, g in rs]))

def voi(ev, n=2000, seed=1, bins=4):
  """Expected reduction in verdict entropy from learning each unknown
  factor (to quartile precision). Ranks 'what to measure next'."""
  rng = random.Random(seed)
  rows = []
  for _ in range(n):
    bg = ev.sample(rng)
    rows.append((bg, judge(ev.law, bg)[0] == CONFIRM))
  p = sum(c for _, c in rows) / n
  out = []
  for k in ev.law.factors:
    if k in ev.known(): continue
    xs = sorted(rows, key=lambda r: r[0][k][0])
    h, ps = 0, []
    for b in range(bins):
      chunk = xs[b * n // bins:(b + 1) * n // bins]
      pb = sum(c for _, c in chunk) / len(chunk)
      ps.append(round(pb, 2))
      h += len(chunk) / n * entropy(pb)
    out.append(dict(factor=k, gain=round(entropy(p) - h, 3),
                    p_by_quartile=ps))
  return dict(p_confirm=round(p, 3), entropy=round(entropy(p), 3),
              ranked=sorted(out, key=lambda d: -d["gain"]))
