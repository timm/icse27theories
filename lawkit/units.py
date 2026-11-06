"""units.py: Forrester & Senge (1980) dimensional consistency. Steps a
model on unit-carrying numbers (Q): every + or - must join like units,
and every stock must keep its declared unit. Literal constants (the 1
in V-1) take the unit of whatever they meet; each such use is noted
so a reader can judge it."""

import re

class DimError(Exception): pass

NOTES = set()

def parse(s):
  "'items/dev/tick' -> {item:1, dev:-1, tick:-1}; 'frac' -> {}."
  d, sign = {}, 1
  for tok in re.findall(r"[*/]|[\w-]+(?:\^-?\d+)?", s):
    if tok in "*/": sign = -1 if tok == "/" else 1; continue
    name, _, p = tok.partition("^")
    if name.endswith("s") and len(name) > 3: name = name[:-1]  # devs->dev
    if name != "frac": d[name] = d.get(name, 0) + sign * int(p or 1)
    sign = 1
  return {k: p for k, p in d.items() if p}

def show(d):
  up = [k + (f"^{p}" if p > 1 else "") for k, p in sorted(d.items()) if p > 0]
  dn = [k + (f"^{-p}" if p < -1 else "") for k, p in sorted(d.items()) if p < 0]
  return ("*".join(up) or "1") + "".join("/" + x for x in dn)

def _val(o): return o.x if isinstance(o, Q) else o

class Q:
  "A number with units."
  def __init__(i, x, d): i.x, i.d = x, {k: p for k, p in d.items() if p}
  def _join(i, o, f, op):
    if isinstance(o, Q):
      if o.d != i.d: raise DimError(f"{show(i.d)} {op} {show(o.d)}")
      return Q(f(i.x, o.x), i.d)
    if o and i.d: NOTES.add(f"literal {o:g} {op} {show(i.d)}")
    return Q(f(i.x, o), i.d)
  def _mul(i, o, p):
    if not isinstance(o, Q):
      return 0 if o == 0 else Q(i.x * o if p > 0 else i.x / o, i.d)
    d = dict(i.d)
    for k, e in o.d.items(): d[k] = d.get(k, 0) + p * e
    return Q(i.x * o.x if p > 0 else i.x / o.x, d)
  def __add__(i, o):      return i._join(o, lambda a, b: a + b, "+")
  def __sub__(i, o):      return i._join(o, lambda a, b: a - b, "-")
  def __rsub__(i, o):     return i._join(o, lambda a, b: b - a, "-")
  def __mul__(i, o):      return i._mul(o, 1)
  def __truediv__(i, o):  return i._mul(o, -1)
  def __rtruediv__(i, o): return Q(o / i.x, {k: -p for k, p in i.d.items()})
  def __neg__(i):         return Q(-i.x, i.d)
  def __float__(i):       return float(i.x)
  def __int__(i):         return int(i.x)
  def __lt__(i, o): return i.x <  _val(o)
  def __le__(i, o): return i.x <= _val(o)
  def __gt__(i, o): return i.x >  _val(o)
  def __ge__(i, o): return i.x >= _val(o)
  def __eq__(i, o): return i.x == _val(o)
  __hash__ = None
  __radd__, __rmul__ = __add__, __mul__

def check(m, bg, lever, arm, tmax):
  """Step model m from background bg (lever at arm) for tmax ticks on
  unit-carrying state. Returns (errors, literal notes)."""
  import sd
  NOTES.clear()
  dims = {k: parse(v[3]) for k, v in bg.items() if len(v) > 3}
  u = sd.make_state({k: Q(arm if k == lever else v[0], dims.get(k, {}))
                     for k, v in bg.items()})
  dt, errs = Q(1, {"tick": 1}), []
  for t in range(tmax):
    v = sd.make_state(vars(u))
    try: m.step(dt, Q(t, {"tick": 1}), u, v)       # time carries units too
    except DimError as e: return [f"t={t}: {e}"], sorted(NOTES)
    for k, want in dims.items():
      got = getattr(v, k)
      if isinstance(got, Q) and got.d != want:
        errs.append(f"{k}: declared {show(want)}, step gives {show(got.d)}")
      elif not isinstance(got, Q): setattr(v, k, Q(got, want))
    if errs: return [f"t={t}: " + "; ".join(errs)], sorted(NOTES)
    u = v
  return [], sorted(NOTES)
