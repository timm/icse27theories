#!/usr/bin/env python3 -B
"""Minimal runnable slice of timm/ezr for same() + bestRanks().
Verbatim from ezr.py (core) + stats.py, trimmed to the transitive
closure these two functions touch. Repo: http://github.com/timm/ezr"""
import bisect
from math import sqrt
from types import SimpleNamespace as S

# --- config (`the`): only the stats knobs same/bestRanks read ----------
the = S(stats=S(cliffs=0.195, conf=1.36, eps=0.35))

# --- columns (ezr.py, verbatim) ----------------------------------------
class Num:
  """Summarizes a stream of numbers."""
  def __init__(i, txt="", a=0):
    i.txt, i.at, i.n = txt, a, 0
    i.mu=i.m2=i.sd=0; i.heaven=txt[-1:]!="-"

class Sym:
  """Summarizes a stream of symbols."""
  def __init__(i, txt="", a=0):
    i.txt, i.at, i.n, i.has = txt, a, 0, {}

class Data: pass   # name only: add() type-checks against it
class Cols: pass   # name only: add() type-checks against it

def spread(col):
  """Variability (sd or entropy)."""
  return col.sd if Num==type(col) else entropy(col.has)

def add(it, v, w=1):
  """Add value/row to Data, Cols, Num, Sym."""
  if Data is type(it):
    it._centroid = None
    add(it.cols, v, w)
    if w > 0: it.rows.append(v)
    else    : it.rows.remove(v)
  elif Cols is type(it):
    [add(col, v[col.at], w) for col in it.all]
  elif v != "?":
    if Sym == type(it):
      it.n += w
      it.has[v] = w + it.has.get(v, 0)
    elif w < 0 and it.n <= 2:
      it.n = it.mu = it.m2 = it.sd = 0
    else:
      it.n  += w
      delta  = v - it.mu
      it.mu += w * delta / it.n
      it.m2 += w * delta * (v - it.mu)
      it.sd  = sqrt(max(0, it.m2)/(it.n-1)) if it.n > 1 else 0
  return v

def adds(src, it=None):
  """Add multiple items to target."""
  it = it or Num()
  [add(it, v) for v in (src or [])]
  return it

# --- stats.py (verbatim) -----------------------------------------------
def same(xs, ys, eps):
  """Are two lists statistically same?"""
  xs, ys = sorted(xs), sorted(ys)
  n, m = len(xs), len(ys)
  if abs(xs[n//2] - ys[m//2]) <= eps: return True
  gt = sum(bisect.bisect_left(ys, a) for a in xs)
  lt = sum(m - bisect.bisect_right(ys, a) for a in xs)
  if abs(gt - lt) / (n*m) > the.stats.cliffs:
    return False
  ks = lambda v: abs(bisect.bisect_right(xs, v)/n
                     - bisect.bisect_right(ys, v)/m)
  return max(max(map(ks, xs)), max(map(ks, ys))) <= \
         the.stats.conf * ((n+m)/(n*m))**.5

def bestRanks(d):
  """Group treatments tied for best."""
  items = sorted(d.items(), key=lambda kv:
                 sorted(kv[1])[len(kv[1])//2])
  k0, lst0 = items[0]
  best = {k0: adds(lst0, Num(k0))}
  for k, lst in items[1:]:
    if same(lst0, lst, spread(best[k0]) * the.stats.eps):
      best[k] = adds(lst, Num(k))
    else: break
  return best

# --- demo --------------------------------------------------------------
if __name__ == "__main__":
  d = {"A":[0.61,0.63,0.59,0.62,0.60],
       "B":[0.62,0.60,0.64,0.61,0.63],
       "C":[0.80,0.82,0.79,0.81,0.83]}
  best = bestRanks(d)
  print("tied-for-best:", list(best))
  for k,num in best.items():
    print(f"  {k}: mu={num.mu:.3f} sd={num.sd:.3f} n={num.n}")
  print("A vs B same?", same(d["A"], d["B"], 0.02))
  print("A vs C same?", same(d["A"], d["C"], 0.02))
