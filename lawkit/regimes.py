"""regimes.py: where does the law hold? (Cartwright's 'horizontal
search' for support factors.) Instead of one verdict, return a map:
robustness at three neighbourhood sizes, 1-D tipping points, readable
rules separating CONFIRM from not, plus scenario & variant sweeps that
always compare the two arms *within* the same scenario/structure."""

import random
from .core import (background, judge, draw, tally, quantiles, spec,
                   CONFIRM, REFUTE)

def robustness(law, n=2000, seed=1, model=None, base=None):
  "P(verdict) under local (+-15%), prior (triangular) and uniform draws."
  out = {}
  for how in ("local", "prior", "uniform"):
    rng = random.Random(seed)
    rs = [judge(law, draw(law, rng, how, base=base, model=model),
                model=model) for _ in range(n)]
    out[how] = dict(tally([v for v, _ in rs]),
                    gap=quantiles([g for _, g in rs]))
  return out

def tipping(law, steps=41):
  "One-factor-at-a-time sweeps: values where the verdict changes."
  res = {}
  for k in law.factors:
    bg = background(law)
    lo, hi = bg[k][1], bg[k][2]
    last, cuts = None, []
    for j in range(steps):
      val = lo + (hi - lo) * j / (steps - 1)
      v, _ = judge(law, {**bg, k: spec(bg, k, val)})
      if last and v != last: cuts.append(f"{last}->{v}@{val:.3g}")
      last = v
    res[k] = cuts
  return res

def rules(law, n=3000, seed=3, depth=3):
  """Shallow tree over prior draws: human-readable 'law holds when ...'.
  Feature importance = which support factors decide the verdict."""
  from sklearn.tree import DecisionTreeClassifier, export_text
  rng = random.Random(seed)
  X, y = [], []
  for _ in range(n):
    bg = draw(law, rng, "prior")
    X.append([bg[k][0] for k in law.factors])
    y.append(int(judge(law, bg)[0] == CONFIRM))
  t = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=50,
                             random_state=seed).fit(X, y)
  imp = sorted(zip(law.factors, t.feature_importances_),
               key=lambda kv: -kv[1])
  return dict(text=export_text(t, feature_names=list(law.factors),
                               decimals=3),
              importance=[(k, round(float(w), 3)) for k, w in imp],
              accuracy=round(float(t.score(X, y)), 3),
              base_rate=round(sum(y) / n, 3))

def scenarios(law, n=1000, seed=1):
  "Each business scenario: local noise around its own background."
  out = {}
  for name, (story, over) in law.scenarios.items():
    base = background(law, over)
    rng = random.Random(seed)
    rs = [judge(law, draw(law, rng, "local", base=base))
          for _ in range(n)]
    out[name] = dict(story=story, over=over, at_default=judge(law, base),
                     **tally([v for v, _ in rs]),
                     gap=quantiles([g for _, g in rs]))
  return out

def variants(law, n=1000, seed=1):
  """Alternative mechanisms for the same claim. Arms are compared within
  each structure, so 'org X beats org Y' is never mistaken for
  'the lever helps inside org X'."""
  out = {}
  for name, (story, factory) in law.variants.items():
    base = background(law, model=factory)
    r = robustness(law, n=n, seed=seed, model=factory, base=base)
    out[name] = dict(story=story, at_default=judge(law, base,
                     model=factory), local=r["local"], prior=r["prior"])
  return out
