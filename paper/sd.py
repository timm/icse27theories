#!/usr/bin/env python3 -B
"""sd.py v2: tiny system dynamics for SE.

Conventions
-----------
* Var names: UPPER = input (state of world), lower = param (process IS).
* Bundle: namedtuple Model(init, step, y, rq, ctrl).
  - init  : {'k': [default, lo, hi]}     (UPPER and lower mixed)
  - step  : (dt, t, u, v) -> None
  - y     : list[(t,row)] -> float       (higher = better)
  - rq    : (bg=None) -> dict {verdict, y0, y1, gap, desc}
  - ctrl  : str, name of the var rq() flips (frozen during stress(target='params'))

Engine
------
run(init, step, dt=1, tmax=20, mode='clip')
  mode='clip'   : clamp states at [lo,hi] each step (default)
  mode='reject' : return None if any state escapes [lo,hi] (anti-cheat)

Stress
------
stress(model_factory, target='inputs'|'params'|'all', n=500, seed=1)
  Background-perturbation harness. ctrl variable is never perturbed.

Optimizer
---------
opt(model_factory, narrow=0.6, ...)
  narrow=1.0 -> sample full [lo,hi]; narrow=0.6 -> shrink to centered 60%.
  narrow<1 prevents the optimizer from "winning" via near-boundary starts.

Refs (see evidence.md for parameter justifications and quotes):
[1]  Brooks (1975)               [9]  Becker et al. METR (2025)
[2]  Goel & Okumoto (1979)        [10] GitHub Engineering RCT (2024)
[3]  Cunningham (1992)            [11] Luo et al. flaky tests (2014)
[4]  Kermack & McKendrick (1927)  [12] Forsgren, Humble, Kim (2018)
[5]  Abdel-Hamid & Madnick (1991) [13] Skelton & Pais (2019)
[6]  Sterman (2000)               [14] Newman (2015)
[7]  Madachy (2008)               [15] DORA wellbeing (2024)
[8]  Harding GitClear (2024)
"""

import math, random
from collections import namedtuple

Model = namedtuple('Model', 'init step y rq ctrl')

class S:
  """Lightweight attribute bag (replaces SimpleNamespace)."""
  def __init__(self, **kw):
    for k, val in kw.items(): setattr(self, k, val)

def make_state(d):
  s = S()
  for k, val in d.items(): setattr(s, k, val)
  return s

# --- Engine -----------------------------------------------------------------

def run(init, step, dt=1, tmax=20, mode='clip'):
  """Simulate. mode='clip' clamps; mode='reject' returns None on escape."""
  u = make_state({k: v[0] for k, v in init.items()})
  out, t = [], 0
  while t < tmax:
    v = make_state(vars(u))
    step(dt, t, u, v)
    for k, (_, lo, hi) in init.items():
      val = getattr(v, k)
      if mode == 'reject' and (val < lo - 1e-9 or val > hi + 1e-9):
        return None
      setattr(v, k, max(lo, min(hi, val)))
    out.append((t, v))
    u = v
    t += dt
  return out

# --- Verdict helper ---------------------------------------------------------

def verdict(desc, y0, y1, expect='down'):
  """Compare baseline rx0 (y0) to delta-perturbed rx1 (y1).
  expect='down' = thesis predicts delta hurts y (y1 < y0 confirms).
  expect='up'   = thesis predicts delta helps y (y1 > y0 confirms)."""
  signed = (y0 - y1) if expect == 'down' else (y1 - y0)
  thresh = max(abs(y0) * 0.05, 0.5)
  v = ('CONFIRM' if signed >  thresh else
       'REFUTE'  if signed < -thresh else 'neutral')
  return {'verdict': v, 'y0': y0, 'y1': y1, 'gap': y1 - y0, 'desc': desc}

# --- Optimizer (with narrow search to prevent boundary-cheating) ------------

def opt(model_factory, init=None, n=1000, seed=1, dt=1, tmax=20, narrow=0.6):
  """Sample n random starts. narrow shrinks the sample range to a centered
  fraction of [lo,hi] (e.g. narrow=0.6 -> middle 60%).
  Returns dict(init=tightened_ranges, best=(score, params), top=[...])."""
  m = model_factory()
  init0 = m.init if init is None else init
  rng = random.Random(seed)
  rows = []
  for _ in range(n):
    init1 = {}
    for k, (_, lo, hi) in init0.items():
      mid = (lo + hi) / 2
      half = (hi - lo) / 2 * narrow
      init1[k] = [rng.uniform(mid - half, mid + half), lo, hi]
    out = run(init1, m.step, dt, tmax)
    rows.append((m.y(out), {k: init1[k][0] for k in init1}))
  rows.sort(key=lambda r: -r[0])
  top = rows[: max(2, int(n**0.5))]
  new = {}
  for k in init0:
    vs = sorted(r[1][k] for r in top)
    new[k] = [vs[len(vs)//2], vs[0], vs[-1]]
  return {'init': new, 'best': top[0], 'top': top}

# --- Unified stress: target = inputs | params | all -------------------------

def stress(model_factory, target='all', n=500, seed=1):
  """Sample n random backgrounds. target picks which vars to perturb:
    'inputs' : UPPER-cased only
    'params' : lower-cased only (excludes ctrl)
    'all'    : everything except ctrl
  Returns dict(counts={CONFIRM/REFUTE/neutral counts}, refuters=[...])."""
  m = model_factory()
  rng = random.Random(seed)
  counts = {'CONFIRM': 0, 'REFUTE': 0, 'neutral': 0}
  refuters = []

  def perturb(k):
    if k == m.ctrl: return False
    if target == 'inputs':  return k[0].isupper()
    if target == 'params':  return k[0].islower()
    if target == 'all':     return True
    raise ValueError(target)

  for _ in range(n):
    bg = {k: list(v) for k, v in m.init.items()}
    for k, (_, lo, hi) in m.init.items():
      if perturb(k):
        bg[k] = [rng.uniform(lo, hi), lo, hi]
    r = m.rq(bg)
    counts[r['verdict']] += 1
    if r['verdict'] == 'REFUTE':
      refuters.append((bg, r))
  return {'counts': counts, 'refuters': refuters}

# --- Models -----------------------------------------------------------------
# Naming: UPPER = input (world state), lower = param (process configuration).
# Hidden rate constants from v1 are now lifted into init as lowercase params.

def diapers():
  """Toy: weekly diaper supply.  Sat = bulk buy + wash all dirty.
  RQ: skip wash on Sat t=13 -> dirty pileup."""
  init = {'Clean':[100,0,200], 'Dirty':[0,0,200], 'Buy':[0,0,100],
          'Use':[8,0,20], 'wash_amt':[0,0,200], 'skip':[0,0,1]}

  def step(dt, t, u, v):
    sat = int(t) % 7 == 6
    v.Clean = u.Clean + dt * (u.Buy - u.Use)
    v.Dirty = v.Dirty + dt * (u.Use - u.wash_amt)
    v.Buy   = 70 if sat else 0
    v.wash_amt = u.Dirty if sat else 0
    if t == 13 and u.skip > 0.5: v.wash_amt = 0
    v.skip = u.skip

  def y(out):
    return min(r.Clean for _, r in out) - 0.5 * max(r.Dirty for _, r in out)

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("skip wash@t=13 -> Dirty pileup",
                   y(run({**bi, 'skip':[0,0,1]}, step)),
                   y(run({**bi, 'skip':[1,0,1]}, step)), 'down')

  return Model(init, step, y, rq, 'skip')


def brooks():
  """Brooks [1]: late hires hurt.  RQ: boost=10 newcomers @t=10 hurt y."""
  init = {'Vet':[10,0,100], 'New':[0,0,100], 'Done':[0,0,500],
          'Todo':[500,0,500], 'boost':[0,0,100],
          'comm_coef':[0.005,0,0.05], 'train_coef':[0.2,0,1],
          'prod_rate':[5,0.1,20], 'mature_rate':[0.1,0,1]}

  def step(dt, t, u, v):
    comm  = u.Vet * (u.Vet - 1) / 2 * u.comm_coef
    train = u.New * u.train_coef
    prod  = u.Vet * (1 - comm - train) * u.prod_rate
    v.Todo = u.Todo - dt * max(0, prod)
    v.Done = u.Done + dt * max(0, prod)
    v.New  = u.New - dt * u.mature_rate * u.New + (u.boost if t == 10 else 0)
    v.Vet  = u.Vet + dt * u.mature_rate * u.New
    for p in ('boost','comm_coef','train_coef','prod_rate','mature_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Done - end.Todo

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("boost=10 hurts net progress",
                   y(run({**bi, 'boost':[0,0,100]}, step)),
                   y(run({**bi, 'boost':[10,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'boost')


def bugs():
  """Goel-Okumoto [2]: exponential reliability growth.
  RQ: 2x initial Latent -> ~2x eventual Fixed (linearity of recovery)."""
  init = {'Latent':[100,0,200], 'Found':[0,0,200], 'Fixed':[0,0,200],
          'find_rate':[0.15,0.01,0.5], 'fix_rate':[0.5,0.05,1]}

  def step(dt, t, u, v):
    find = u.Latent * u.find_rate
    fix  = u.Found  * u.fix_rate
    v.Latent = u.Latent - dt * find
    v.Found  = u.Found  + dt * (find - fix)
    v.Fixed  = u.Fixed  + dt * fix
    v.find_rate, v.fix_rate = u.find_rate, u.fix_rate

  def y(out):
    """Mid-curve recovery (t=10 of 20): tests scaling, not asymptote.
    Asymptote is always ~1.0 by construction (exponential decay)."""
    mid_idx = len(out) // 2
    return out[mid_idx][1].Fixed

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("2x initial Latent -> ~2x mid-curve Fixed",
                   y(run({**bi, 'Latent':[ 50,0,200]}, step)),
                   y(run({**bi, 'Latent':[100,0,200]}, step)), 'up')

  return Model(init, step, y, rq, 'Latent')


def debt():
  """Cunningham [3]: shipping fast incurs debt; debt slows shipping.
  RQ: starting Debt=50 hurts net feature delivery."""
  init = {'Feat':[1,0,200], 'Debt':[0,0,100], 'Vel':[10,0,20],
          'born_rate':[0.3,0,1], 'intr_rate':[0.10,0,0.5],
          'pay_rate':[0.15,0,1]}

  def step(dt, t, u, v):
    speed = max(0, 1 - u.Debt / 100)
    ship  = (1 + u.Feat * 0.1) * speed
    born  = ship * u.born_rate
    intr  = u.Debt * u.intr_rate
    pay   = u.Debt * u.pay_rate
    v.Feat = u.Feat + dt * ship
    v.Debt = u.Debt + dt * (born + intr - pay)
    v.Vel  = 10 * speed
    v.born_rate, v.intr_rate, v.pay_rate = u.born_rate, u.intr_rate, u.pay_rate

  def y(out):
    end = out[-1][1]
    md = sum(r.Debt for _, r in out) / len(out)
    return end.Feat - md

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("starting Debt=50 slows delivery",
                   y(run({**bi, 'Debt':[ 0,0,100]}, step)),
                   y(run({**bi, 'Debt':[50,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'Debt')


def sir():
  """Kermack-McKendrick [4]: bad-pattern spread.
  RQ: 3x initial I raises peak (-y drops)."""
  init = {'S':[90,0,100], 'I':[10,0,100], 'R':[0,0,100],
          'beta':[0.0051,0,0.05], 'gamma':[0.15,0,1]}

  def step(dt, t, u, v):
    inf = u.beta  * u.S * u.I
    rec = u.gamma * u.I
    v.S = u.S - dt * inf
    v.I = u.I + dt * (inf - rec)
    v.R = u.R + dt * rec
    v.beta, v.gamma = u.beta, u.gamma

  def y(out):
    return -max(r.I for _, r in out)

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("3x initial I raises peak",
                   y(run({**bi, 'I':[10,0,100]}, step)),
                   y(run({**bi, 'I':[30,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'I')


def rework():
  """Abdel-Hamid & Madnick [5]: hidden rework cycle.
  RQ: failrate 0.1 -> 0.7 lets rework dominate."""
  init = {'Req':[100,0,100], 'Dev':[0,0,100], 'Test':[0,0,100],
          'Rew':[0,0,100], 'Done':[0,0,100],
          'code_rate':[0.2,0,1], 'qa_rate':[0.5,0,1],
          'fix_rate':[0.5,0,1], 'failrate':[0.4,0,1]}

  def step(dt, t, u, v):
    code = u.Req  * u.code_rate
    qa   = u.Dev  * u.qa_rate
    fail = u.Test * u.failrate
    pas  = u.Test * (1 - u.failrate)
    fix  = u.Rew  * u.fix_rate
    v.Req  = u.Req  - dt * code
    v.Dev  = u.Dev  + dt * (code - qa + fix)
    v.Test = u.Test + dt * (qa - fail - pas)
    v.Rew  = u.Rew  + dt * (fail - fix)
    v.Done = u.Done + dt * pas
    for p in ('code_rate','qa_rate','fix_rate','failrate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1].Done
    wip = sum(r.Dev + r.Test + r.Rew for _, r in out) / len(out)
    return end - 0.5 * wip

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("failrate 0.7 -> hidden rework dominates",
                   y(run({**bi, 'failrate':[0.1,0,1]}, step)),
                   y(run({**bi, 'failrate':[0.7,0,1]}, step)), 'down')

  return Model(init, step, y, rq, 'failrate')


def learn():
  """Sterman [6]: jr -> tr -> sr workforce flow.
  RQ: removing seniors (Sr=0) starves training."""
  init = {'Jr':[20,0,100], 'Tr':[5,0,100], 'Sr':[5,0,100], 'Ment':[0,0,100],
          'train_rate':[0.10,0,1], 'promote_rate':[0.05,0,1],
          'mentor_rate':[0.02,0,1]}

  def step(dt, t, u, v):
    train   = u.Jr * u.train_rate
    promote = u.Tr * u.promote_rate
    mentor  = u.Sr * u.mentor_rate
    v.Jr   = u.Jr   - dt * train + dt * mentor
    v.Tr   = u.Tr   + dt * (train - promote)
    v.Sr   = u.Sr   + dt * (promote - mentor)
    v.Ment = u.Ment + dt * mentor
    for p in ('train_rate','promote_rate','mentor_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Sr + end.Ment

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("Sr=0 starves training pipeline",
                   y(run({**bi, 'Sr':[5,0,100]}, step)),
                   y(run({**bi, 'Sr':[0,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'Sr')


def brooksq():
  """Brooks [1] + Madachy [7]: late hires hurt quality-adjusted progress.
  RQ: boost=10 hurts y = Done - 5*Esc."""
  init = {'Vet':[10,0,100], 'New':[0,0,100], 'Done':[0,0,500],
          'Todo':[500,0,500], 'Bugs':[0,0,100], 'Esc':[0,0,100],
          'boost':[0,0,100],
          'comm_coef':[0.005,0,0.05], 'train_coef':[0.2,0,1],
          'prod_rate':[5,0.1,20], 'inj_rate':[0.05,0,0.5],
          'leak_rate':[0.10,0,0.5], 'mature_rate':[0.1,0,1]}

  def step(dt, t, u, v):
    comm  = u.Vet * (u.Vet - 1) / 2 * u.comm_coef
    train = u.New * u.train_coef
    prod  = u.Vet * (1 - comm - train) * u.prod_rate
    inj   = max(0, prod) * u.inj_rate
    leak  = u.Bugs * u.leak_rate
    v.Todo = u.Todo - dt * max(0, prod)
    v.Done = u.Done + dt * max(0, prod)
    v.New  = u.New - dt * u.mature_rate * u.New + (u.boost if t == 10 else 0)
    v.Vet  = u.Vet + dt * u.mature_rate * u.New
    v.Bugs = u.Bugs + dt * (inj - leak)
    v.Esc  = u.Esc  + dt * leak
    for p in ('boost','comm_coef','train_coef','prod_rate','inj_rate',
              'leak_rate','mature_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Done - 5 * end.Esc

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("boost=10 hurts quality-adjusted progress",
                   y(run({**bi, 'boost':[ 0,0,100]}, step)),
                   y(run({**bi, 'boost':[10,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'boost')


def defmap():
  """Abdel-Hamid & Madnick [5] defect submodel.
  RQ: tst 2.5 -> 0.5 balloons operational defects."""
  init = {'Cmplx':[20,0,100], 'Dsn':[20,0,100], 'Use':[35,0,100],
          'Injected':[2.43,0,100], 'Caught':[0,0,100],
          'Latent':[0,0,100], 'Prod':[0,0,100],
          'tst':[2.5,0,10], 'intro_c':[0.3,0,1], 'intro_d':[0.2,0,1],
          'detect_coef':[0.4,0,1], 'fail_coef':[0.15,0,1]}

  def step(dt, t, u, v):
    intro  = u.Cmplx * u.intro_c - u.Dsn * u.intro_d
    detect = u.tst * u.Injected * u.detect_coef
    leak   = u.Injected * (1 - u.tst * u.detect_coef)
    fail   = u.Latent * u.Use * u.fail_coef
    v.Injected = u.Injected + dt * intro
    v.Caught   = u.Caught   + dt * detect
    v.Latent   = u.Latent   + dt * (leak - fail)
    v.Prod     = u.Prod     + dt * fail
    for p in ('Cmplx','Dsn','Use','tst','intro_c','intro_d',
              'detect_coef','fail_coef'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return -end.Prod - 0.5 * end.Latent

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("tst=0.5 increases operational defects",
                   y(run({**bi, 'tst':[2.5,0,10]}, step)),
                   y(run({**bi, 'tst':[0.5,0,10]}, step)), 'down')

  return Model(init, step, y, rq, 'tst')


def aiwork():
  """GitClear [8] / METR [9]: AI churn vs gen tradeoff.
  RQ: ai=1 reduces kept code."""
  init = {'Todo':[1000,0,1000], 'Wip':[0,0,500],
          'Kept':[0,0,1000], 'Churned':[0,0,1000],
          'ai':[0,0,1], 'gen_boost':[0.3,0,2], 'churn_mult':[2.0,0,5],
          'verify_drag':[0.4,0,1], 'mature_rate':[0.2,0,1],
          'churn_base':[0.05,0,1]}

  def step(dt, t, u, v):
    gen_boost   = 1 + u.gen_boost * u.ai
    churn_mult  = 1 + u.churn_mult * u.ai
    verify_drag = u.verify_drag * u.ai
    gen   = 10 * gen_boost * (1 - verify_drag)
    add   = min(gen, u.Todo)
    mature = u.Wip * u.mature_rate
    churn  = u.Wip * u.churn_base * churn_mult
    v.Todo    = u.Todo - dt * add
    v.Wip     = u.Wip + dt * (add - mature - churn)
    v.Kept    = u.Kept + dt * mature
    v.Churned = u.Churned + dt * churn
    for p in ('ai','gen_boost','churn_mult','verify_drag',
              'mature_rate','churn_base'):
      setattr(v, p, getattr(u, p))

  def y(out):
    return out[-1][1].Kept

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("ai=1 reduces Kept (METR/GitClear)",
                   y(run({**bi, 'ai':[0,0,1]}, step)),
                   y(run({**bi, 'ai':[1,0,1]}, step)), 'down')

  return Model(init, step, y, rq, 'ai')


def flaky():
  """Luo et al. [11]: flaky tests erode trust -> erode coverage.
  RQ: high flake_rate erodes useful coverage."""
  init = {'Tests':[100,0,500], 'Flakes':[5,0,500], 'Bugs':[0,0,500],
          'flake_rate':[0.02,0,0.2], 'invest_base':[5,0,20],
          'fix_coef':[0.15,0,1], 'leak_coef':[3,0,10]}

  def step(dt, t, u, v):
    cover = u.Tests / max(1, u.Tests + u.Flakes)
    add   = u.invest_base * cover
    flake = u.Tests * u.flake_rate
    fix   = u.Flakes * u.fix_coef * cover
    leak  = u.Flakes / max(1, u.Tests + u.Flakes) * u.leak_coef
    v.Tests = u.Tests + dt * (add - flake)
    v.Flakes = u.Flakes + dt * (flake - fix)
    v.Bugs = u.Bugs + dt * leak
    for p in ('flake_rate','invest_base','fix_coef','leak_coef'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Tests - end.Bugs

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("high flake_rate erodes useful coverage",
                   y(run({**bi, 'flake_rate':[0.02,0,0.2]}, step)),
                   y(run({**bi, 'flake_rate':[0.10,0,0.2]}, step)), 'down')

  return Model(init, step, y, rq, 'flake_rate')


def dora():
  """Forsgren, Humble, Kim [12]: large batches -> CFR up.
  RQ: batch_size 5 -> 50 hurts net deploys."""
  init = {'Wip':[100,0,500], 'Deploys':[0,0,200],
          'Incidents':[0,0,100], 'Recovery':[0,0,200],
          'batch_size':[10,1,100], 'cfr_coef':[0.005,0,0.1],
          'arrival_rate':[8,0,50], 'rec_rate':[0.3,0,1]}

  def step(dt, t, u, v):
    cfr     = min(0.5, u.batch_size * u.cfr_coef)
    cap     = max(0.1, 1 - u.Recovery / 50)
    deploys = min(u.Wip / max(1, u.batch_size), 5) * cap
    new_inc = deploys * cfr
    rec     = u.Incidents * u.rec_rate
    v.Wip       = u.Wip - dt * deploys * u.batch_size + dt * u.arrival_rate
    v.Deploys   = u.Deploys + dt * deploys
    v.Incidents = u.Incidents + dt * (new_inc - rec)
    v.Recovery  = u.Recovery + dt * (new_inc * 2 - u.Recovery * 0.4)
    for p in ('batch_size','cfr_coef','arrival_rate','rec_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Deploys - 2 * end.Incidents

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("batch_size=50 hurts net deploys",
                   y(run({**bi, 'batch_size':[ 5,1,100]}, step)),
                   y(run({**bi, 'batch_size':[50,1,100]}, step)), 'down')

  return Model(init, step, y, rq, 'batch_size')


def micro():
  """Newman [14]: services linear, deps quadratic.
  RQ: high coupling_rate erodes throughput."""
  init = {'Services':[5,1,100], 'Deps':[5,0,500], 'Feat':[0,0,500],
          'coupling_rate':[1.5,0,5], 'svc_growth':[0.5,0,5]}

  def step(dt, t, u, v):
    new_svc  = u.svc_growth
    new_deps = new_svc * u.coupling_rate * (u.Services / 5)
    density  = u.Deps / max(1, u.Services * u.Services)
    fps      = max(0.1, u.Services * (1 - 2 * density))
    v.Services = u.Services + dt * new_svc
    v.Deps     = u.Deps + dt * new_deps
    v.Feat     = u.Feat + dt * fps
    v.coupling_rate, v.svc_growth = u.coupling_rate, u.svc_growth

  def y(out):
    return out[-1][1].Feat

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("high coupling_rate erodes throughput",
                   y(run({**bi, 'coupling_rate':[0.5,0,5]}, step)),
                   y(run({**bi, 'coupling_rate':[3.0,0,5]}, step)), 'down')

  return Model(init, step, y, rq, 'coupling_rate')


def teamtopo():
  """Skelton & Pais [13]: cognitive load = Domain / team.
  RQ: oversized Domain (per team) collapses delivery."""
  init = {'Domain':[5,0,50], 'Delivered':[0,0,500],
          'team':[7,1,20], 'load_thresh':[1.5,0.1,5],
          'domain_growth':[0.3,0,2], 'collapse_coef':[0.8,0,2]}

  def step(dt, t, u, v):
    load = u.Domain / max(1, u.team)
    thr  = u.team * max(0, 1 - max(0, load - u.load_thresh) * u.collapse_coef)
    v.Domain    = u.Domain + dt * u.domain_growth
    v.Delivered = u.Delivered + dt * thr
    for p in ('team','load_thresh','domain_growth','collapse_coef'):
      setattr(v, p, getattr(u, p))

  def y(out):
    return out[-1][1].Delivered

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("oversized Domain collapses delivery",
                   y(run({**bi, 'Domain':[ 5,0,50]}, step)),
                   y(run({**bi, 'Domain':[20,0,50]}, step)), 'down')

  return Model(init, step, y, rq, 'Domain')


def burnout():
  """DORA wellbeing [15]: chronic overload erodes capacity.
  RQ: workload 60 (vs 40) erodes net delivery."""
  init = {'Capacity':[40,10,50], 'Stress':[0,0,100], 'Delivered':[0,0,2000],
          'workload':[40,0,100], 'stress_coef':[1.0,0,5],
          'recover_coef':[0.05,0,1], 'erode_coef':[0.05,0,1]}

  def step(dt, t, u, v):
    actual  = min(u.workload, u.Capacity)
    excess  = max(0, u.workload - u.Capacity)
    d_stress = excess * u.stress_coef - u.Stress * u.recover_coef
    d_cap    = -u.Stress * u.erode_coef + max(0, 40 - u.Capacity) * 0.1
    v.Capacity  = u.Capacity + dt * d_cap
    v.Stress    = u.Stress + dt * d_stress
    v.Delivered = u.Delivered + dt * actual
    for p in ('workload','stress_coef','recover_coef','erode_coef'):
      setattr(v, p, getattr(u, p))

  def y(out):
    return out[-1][1].Delivered

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("workload=60 erodes net delivery",
                   y(run({**bi, 'workload':[40,0,100]}, step)),
                   y(run({**bi, 'workload':[60,0,100]}, step)), 'down')

  return Model(init, step, y, rq, 'workload')


def aidebt():
  """Cunningham [3] + GitClear [8]: AI-coded features carry more debt.
  RQ: ai=1 raises debt enough to depress net (Feat - mean(Debt))."""
  init = {'Feat':[1,0,200], 'Debt':[0,0,100], 'Vel':[10,0,20],
          'ai':[0,0,1], 'born_base':[0.3,0,1], 'born_ai_mult':[1.5,0,5],
          'gen_ai_mult':[0.3,0,2], 'intr_rate':[0.10,0,0.5],
          'pay_rate':[0.15,0,1]}

  def step(dt, t, u, v):
    speed = max(0, 1 - u.Debt / 100)
    ship  = (1 + u.Feat * 0.1) * speed * (1 + u.gen_ai_mult * u.ai)
    rate  = u.born_base * (1 + u.born_ai_mult * u.ai)
    born  = ship * rate
    intr  = u.Debt * u.intr_rate
    pay   = u.Debt * u.pay_rate
    v.Feat = u.Feat + dt * ship
    v.Debt = u.Debt + dt * (born + intr - pay)
    v.Vel  = 10 * speed
    for p in ('ai','born_base','born_ai_mult','gen_ai_mult',
              'intr_rate','pay_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    md = sum(r.Debt for _, r in out) / len(out)
    return end.Feat - md

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("ai=1 raises debt > offsets feature speedup",
                   y(run({**bi, 'ai':[0,0,1]}, step)),
                   y(run({**bi, 'ai':[1,0,1]}, step)), 'down')

  return Model(init, step, y, rq, 'ai')


def archpat():
  """Architectural patterns as repair: Martin Clean Arch [16] + Perry-Wolf [17].
  
  Tests Ric's claim: 'patterns repair existing-bad-software'.
  
  Three regions: Patterned (under good architecture), Legacy (not), Drift
  (was patterned, eroded). Migration moves Legacy -> Patterned at rate
  proportional to migrate_rate * available effort. Decay moves Patterned
  -> Drift at rate decay_rate (architectural erosion: Perry & Wolf 1992).
  Drift converts back to Legacy at a fixed rate.
  
  Debt accumulates in both regions but at different rates: legacy code
  generates more debt per feature than patterned code (factor pat_strength).
  
  RQ: starting from Patterned=10, Legacy=90, Debt=40 (already-bad project),
  does aggressive migration (migrate=1.5) actually repair the project
  vs slow migration (migrate=0.2)?  Ric's strong claim says yes.
  """
  init = {'Patterned':[10,0,200], 'Legacy':[90,0,200],
          'Drift':[0,0,200], 'Debt':[40,0,150], 'Feat':[0,0,2000],
          'migrate':[0.2,0,2], 'decay_rate':[0.05,0,0.5],
          'drift_to_legacy':[0.10,0,1],
          'gen_pat':[1.0,0.1,3], 'gen_leg':[0.4,0.1,3],
          'born_pat':[0.05,0,1], 'born_leg':[0.20,0,1],
          'intr_rate':[0.08,0,0.5], 'pay_rate':[0.15,0,1],
          'pat_strength':[4,1,10]}

  def step(dt, t, u, v):
    speed     = max(0.05, 1 - u.Debt / 150)
    available = (u.Patterned + u.Legacy + u.Drift) * speed
    # migration: legacy -> patterned (costs effort proportional to migrate)
    migration_flow = u.migrate * u.Legacy * 0.05
    # decay: patterned -> drift (architectural erosion)
    decay_flow = u.decay_rate * u.Patterned
    # drift -> legacy (drift fully converts back over time)
    drift_flow = u.drift_to_legacy * u.Drift
    # feature generation (Drift acts like Legacy for shipping)
    gen = (u.Patterned * u.gen_pat
           + (u.Legacy + u.Drift) * u.gen_leg) * speed
    # debt: legacy code generates more debt per feature
    pat_share = u.Patterned / max(1, u.Patterned + u.Legacy + u.Drift)
    born = gen * (u.born_pat * pat_share + u.born_leg * (1 - pat_share))
    intr = u.Debt * u.intr_rate
    pay  = u.Debt * u.pay_rate * (1 + 0.5 * pat_share)  # patterns help paydown
    v.Patterned = u.Patterned + dt * (migration_flow - decay_flow)
    v.Legacy    = u.Legacy    - dt * migration_flow + dt * drift_flow
    v.Drift     = u.Drift     + dt * (decay_flow - drift_flow)
    v.Debt      = u.Debt      + dt * (born + intr - pay)
    v.Feat      = u.Feat      + dt * gen
    for p in ('migrate','decay_rate','drift_to_legacy','gen_pat','gen_leg',
              'born_pat','born_leg','intr_rate','pay_rate','pat_strength'):
      setattr(v, p, getattr(u, p))

  def y(out):
    """Reward features delivered, penalize sustained debt."""
    end = out[-1][1]
    md = sum(r.Debt for _, r in out) / len(out)
    return end.Feat - md

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("aggressive migration repairs already-bad project",
                   y(run({**bi, 'migrate':[0.2,0,2]}, step)),
                   y(run({**bi, 'migrate':[1.5,0,2]}, step)), 'up')

  return Model(init, step, y, rq, 'migrate')


def congruence():
  """Newman [14] / radio-silence (Tim et al.): boundary-spanning
  brokers hold communication-fragmented projects together.
  RQ: broker_loss=0.3 (per step) hurts net coherent work."""
  init = {'Clusters':[5,1,20], 'Brokers':[3,0,20], 'Cohesion':[0,0,500],
          'broker_loss':[0,0,1], 'broker_form':[0.05,0,0.5],
          'fragment_rate':[0.05,0,0.5], 'merge_rate':[0.1,0,0.5],
          'work_rate':[5,0,20]}

  def step(dt, t, u, v):
    # Brokers form proportional to inter-cluster gradient, drain by ctrl.
    form  = u.broker_form * u.Clusters
    drain = u.broker_loss * u.Brokers
    frag  = u.fragment_rate * max(0, u.Clusters - u.Brokers)
    merge = u.merge_rate * u.Brokers
    # Cohesion accrues at work_rate, attenuated by fragmentation.
    coh_gain = u.work_rate * (u.Brokers / max(1, u.Clusters))
    v.Brokers  = max(0, u.Brokers  + dt * (form - drain))
    v.Clusters = max(1, u.Clusters + dt * (frag - merge))
    v.Cohesion = u.Cohesion + dt * coh_gain
    for p in ('broker_loss','broker_form','fragment_rate',
              'merge_rate','work_rate'):
      setattr(v, p, getattr(u, p))

  def y(out):
    end = out[-1][1]
    return end.Cohesion - 5 * end.Clusters

  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("broker_loss=0.3 fragments project, hurts cohesion",
                   y(run({**bi, 'broker_loss':[0.0,0,1]}, step)),
                   y(run({**bi, 'broker_loss':[0.3,0,1]}, step)), 'down')

  return Model(init, step, y, rq, 'broker_loss')


# --- 15 candidate models lifted from docs/other.html (buildable today) -------


def little():
  """Little 1961: WIP = throughput * cycle_time. Holding arrival
  constant, doubling cycle_time inflates WIP and depresses Done.
  RQ: doubling cycle_time hurts throughput."""
  init = {'WIP':[20,0,500], 'Arrival':[5,0,50], 'Done':[0,0,5000],
          'cycle_time':[4,1,30], 'wip_cap':[60,5,200]}
  def step(dt, t, u, v):
    served = min(u.WIP / max(1, u.cycle_time), u.WIP)
    accept = min(u.Arrival, max(0, u.wip_cap - u.WIP))
    v.WIP  = u.WIP  + dt * (accept - served)
    v.Done = u.Done + dt * served
    for p in ('Arrival','cycle_time','wip_cap'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Done
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("doubling cycle_time hurts throughput",
                   y(run({**bi, 'cycle_time':[4,1,30]}, step)),
                   y(run({**bi, 'cycle_time':[12,1,30]}, step)), 'down')
  return Model(init, step, y, rq, 'cycle_time')


def coordn2():
  """Brooks/Curtis: communication-pair count = N*(N-1)/2.
  RQ: doubling N more than doubles coordination cost (superlinear)."""
  init = {'Devs':[5,1,200], 'Done':[0,0,10000],
          'work_per_dev':[10,0,50], 'comm_coef':[0.02,0,0.5]}
  def step(dt, t, u, v):
    pairs = u.Devs * (u.Devs - 1) / 2
    tax   = min(0.9, u.comm_coef * pairs / max(1, u.Devs))
    v.Done = u.Done + dt * u.Devs * u.work_per_dev * (1 - tax)
    for p in ('Devs','work_per_dev','comm_coef'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Done
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("doubling team superlinear-taxes throughput",
                   y(run({**bi, 'Devs':[5,1,200]}, step)),
                   y(run({**bi, 'Devs':[10,1,200]}, step)), 'down')
  return Model(init, step, y, rq, 'Devs')


def entropy():
  """Lehman 1980: software entropy grows monotonically unless paid
  down via refactor. Without refactor effort, defect rate rises.
  RQ: low refactor_rate inflates terminal Complexity."""
  init = {'Complexity':[100,0,5000], 'Bugs':[0,0,5000],
          'work_rate':[10,0,100], 'refactor_rate':[0.05,0,0.5],
          'entropy_coef':[0.02,0,0.5]}
  def step(dt, t, u, v):
    grow    = u.work_rate * u.entropy_coef
    pay     = u.Complexity * u.refactor_rate
    bug_in  = u.Complexity * 0.001
    v.Complexity = max(0, u.Complexity + dt * (grow - pay))
    v.Bugs       = u.Bugs + dt * bug_in
    for p in ('work_rate','refactor_rate','entropy_coef'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Complexity - out[-1][1].Bugs
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("low refactor leaves Complexity high",
                   y(run({**bi, 'refactor_rate':[0.20,0,0.5]}, step)),
                   y(run({**bi, 'refactor_rate':[0.02,0,0.5]}, step)), 'down')
  return Model(init, step, y, rq, 'refactor_rate')


def costchange():
  """Boehm 1981: cost to fix a bug rises ~10x per phase post-discovery.
  RQ: shifting catch from coding to release hurts net delivered value."""
  init = {'Bugs':[20,0,1000], 'Cost':[0,0,1e6],
          'catch_early':[0.6,0,1], 'cost_early':[1,0.1,5],
          'cost_late':[50,1,500]}
  def step(dt, t, u, v):
    e = u.Bugs * u.catch_early
    l = u.Bugs - e
    v.Cost = u.Cost + dt * (e * u.cost_early + l * u.cost_late)
    v.Bugs = max(0, u.Bugs - dt * (e + l) * 0.1)
    for p in ('catch_early','cost_early','cost_late'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Cost
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("shifting catch late inflates total cost",
                   y(run({**bi, 'catch_early':[0.8,0,1]}, step)),
                   y(run({**bi, 'catch_early':[0.2,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'catch_early')


def pareto():
  """Fenton-Ohlsson / Ostrand-Weyuker: ~20% of modules carry ~80%
  of defects, and that hotspot set persists across releases.
  RQ: ignoring hotspots inflates total defect rate."""
  init = {'Hot':[10,0,200], 'Cold':[90,0,2000], 'Bugs':[0,0,5000],
          'hot_bug_rate':[0.4,0,2], 'cold_bug_rate':[0.02,0,0.5],
          'fix_share_hot':[0.5,0,1]}
  def step(dt, t, u, v):
    new_hot  = u.Hot  * u.hot_bug_rate
    new_cold = u.Cold * u.cold_bug_rate
    # Hotspot fixes net more bug-reduction per unit effort (the whole
    # point of Pareto): a hot fix removes 4x more bugs than a cold fix.
    fix_hot  = u.fix_share_hot * 8
    fix_cold = (1 - u.fix_share_hot) * 2
    v.Bugs = max(0, u.Bugs + dt * (new_hot + new_cold - fix_hot - fix_cold))
    for p in ('Hot','Cold','hot_bug_rate','cold_bug_rate','fix_share_hot'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Bugs
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("ignoring hotspots inflates bugs",
                   y(run({**bi, 'fix_share_hot':[0.8,0,1]}, step)),
                   y(run({**bi, 'fix_share_hot':[0.1,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'fix_share_hot')


def linus():
  """Raymond 1999 + Mockus 2002: 'many eyes' review reduces defect
  recurrence. RQ: low review_rate inflates Recurring."""
  init = {'Open':[20,0,500], 'Reviewed':[0,0,5000],
          'Recurring':[0,0,500], 'review_rate':[0.4,0,1],
          'recur_rate':[0.3,0,1]}
  def step(dt, t, u, v):
    rev = u.Open * u.review_rate
    rec = rev * u.recur_rate * (1 - u.review_rate)
    v.Open      = max(0, u.Open - dt * rev + dt * rec)
    v.Reviewed  = u.Reviewed + dt * rev
    v.Recurring = u.Recurring + dt * rec
    for p in ('review_rate','recur_rate'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Reviewed - 3 * out[-1][1].Recurring
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("low review_rate inflates recurrence",
                   y(run({**bi, 'review_rate':[0.6,0,1]}, step)),
                   y(run({**bi, 'review_rate':[0.1,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'review_rate')


def mirroring():
  """MacCormack et al 2006: code DSM mirrors org DSM. Higher mirror
  coefficient predicts cleaner modular boundaries and lower defects.
  RQ: org/code DSM mismatch (low mirror) elevates Bugs."""
  init = {'Modules':[20,1,200], 'Teams':[5,1,50], 'Bugs':[0,0,5000],
          'mirror':[0.7,0,1], 'churn_rate':[2,0,20]}
  def step(dt, t, u, v):
    mismatch = (1 - u.mirror)
    leak     = u.churn_rate * mismatch
    v.Bugs   = u.Bugs + dt * leak * u.Modules / max(1, u.Teams)
    for p in ('Modules','Teams','mirror','churn_rate'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Bugs
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("low mirror inflates defects",
                   y(run({**bi, 'mirror':[0.85,0,1]}, step)),
                   y(run({**bi, 'mirror':[0.30,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'mirror')


def orgchurn():
  """Nagappan/Murphy/Basili 2010: org churn (departures) predicts
  defect bursts. RQ: high churn_rate inflates Bugs."""
  init = {'Devs':[20,1,500], 'Bugs':[0,0,5000],
          'churn_rate':[0.02,0,0.5], 'knowledge':[100,0,1000]}
  def step(dt, t, u, v):
    lost = u.Devs * u.churn_rate
    v.Devs      = max(1, u.Devs - dt * lost + dt * lost * 0.5)
    v.knowledge = max(0, u.knowledge - dt * lost * 5)
    v.Bugs      = u.Bugs + dt * (200 / max(1, u.knowledge)) * 10
    setattr(v, 'churn_rate', u.churn_rate)
  def y(out): return -out[-1][1].Bugs
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("departure spike inflates defect burst",
                   y(run({**bi, 'churn_rate':[0.02,0,0.5]}, step)),
                   y(run({**bi, 'churn_rate':[0.20,0,0.5]}, step)), 'down')
  return Model(init, step, y, rq, 'churn_rate')


def ownership():
  """Bird et al 2011: high minor-author share correlates with
  defect density. RQ: rising minor_share inflates Bugs."""
  init = {'Modules':[50,1,500], 'Bugs':[0,0,5000],
          'minor_share':[0.2,0,1], 'major_quality':[0.95,0,1]}
  def step(dt, t, u, v):
    eff_q = u.major_quality * (1 - u.minor_share) + 0.6 * u.minor_share
    new_b = u.Modules * (1 - eff_q) * 0.5
    v.Bugs = u.Bugs + dt * new_b
    for p in ('Modules','minor_share','major_quality'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Bugs
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("high minor_share inflates defects",
                   y(run({**bi, 'minor_share':[0.10,0,1]}, step)),
                   y(run({**bi, 'minor_share':[0.60,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'minor_share')


def ossfail():
  """Coelho & Valente 2017: low truck factor predicts project death.
  RQ: low truck_factor accelerates Abandonment."""
  init = {'Devs':[5,1,200], 'Activity':[100,0,10000],
          'truck_factor':[2,1,20], 'attrition':[0.05,0,0.5]}
  def step(dt, t, u, v):
    bus_risk = 1 / max(1, u.truck_factor)
    decay    = u.attrition * (1 + bus_risk)
    v.Activity = max(0, u.Activity - dt * u.Activity * decay)
    for p in ('Devs','truck_factor','attrition'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Activity
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("low truck_factor accelerates abandonment",
                   y(run({**bi, 'truck_factor':[8,1,20]}, step)),
                   y(run({**bi, 'truck_factor':[1,1,20]}, step)), 'down')
  return Model(init, step, y, rq, 'truck_factor')


def deprot():
  """Decan/Mens/Constantinou 2018: dep version staleness elevates
  vulnerability surface. RQ: low update_rate inflates Vulns."""
  init = {'Deps':[40,1,500], 'Stale':[20,0,500], 'Vulns':[0,0,500],
          'update_rate':[0.1,0,1], 'vuln_disclose_rate':[0.01,0,0.5]}
  def step(dt, t, u, v):
    fresh_flow = u.Stale * u.update_rate
    new_vuln   = u.Stale * u.vuln_disclose_rate
    v.Stale = max(0, u.Stale + dt * (u.Deps * 0.05 - fresh_flow))
    v.Vulns = u.Vulns + dt * new_vuln
    for p in ('Deps','update_rate','vuln_disclose_rate'):
      setattr(v, p, getattr(u, p))
  def y(out): return -out[-1][1].Vulns
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("low update_rate inflates vulnerabilities",
                   y(run({**bi, 'update_rate':[0.30,0,1]}, step)),
                   y(run({**bi, 'update_rate':[0.02,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'update_rate')


def scope():
  """Boehm/Jones scope creep: when inflow > outflow, backlog grows
  without bound. RQ: high inflow_excess hurts net Done."""
  init = {'Backlog':[100,0,10000], 'Done':[0,0,10000],
          'inflow':[8,0,100], 'outflow':[6,0,100]}
  def step(dt, t, u, v):
    served = min(u.Backlog, u.outflow)
    v.Backlog = u.Backlog + dt * (u.inflow - served)
    v.Done    = u.Done    + dt * served
    for p in ('inflow','outflow'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Done - out[-1][1].Backlog * 0.1
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("inflow >> outflow drowns Done",
                   y(run({**bi, 'inflow':[5,0,100]}, step)),
                   y(run({**bi, 'inflow':[15,0,100]}, step)), 'down')
  return Model(init, step, y, rq, 'inflow')


def ctxswitch():
  """Weinberg / Meyer et al 2014: high per-day file-diversity
  per dev taxes effective throughput.
  RQ: high diversity hurts Done."""
  init = {'Devs':[10,1,200], 'Done':[0,0,10000],
          'work_per_dev':[10,0,50], 'diversity':[2,1,20]}
  def step(dt, t, u, v):
    eff = u.work_per_dev / (1 + 0.4 * (u.diversity - 1))
    v.Done = u.Done + dt * u.Devs * eff
    for p in ('Devs','work_per_dev','diversity'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Done
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("high file-diversity per dev hurts throughput",
                   y(run({**bi, 'diversity':[2,1,20]}, step)),
                   y(run({**bi, 'diversity':[8,1,20]}, step)), 'down')
  return Model(init, step, y, rq, 'diversity')


def limits():
  """Senge limits-to-growth: throughput rises with team size but
  saturates as coordination overhead bites.
  RQ: doubling team near asymptote yields diminishing returns."""
  init = {'Devs':[10,1,500], 'Done':[0,0,1e5],
          'k_per_dev':[10,0,100], 'cap':[200,10,1000]}
  def step(dt, t, u, v):
    raw = u.Devs * u.k_per_dev
    eff = raw / (1 + raw / max(1, u.cap))
    v.Done = u.Done + dt * eff
    for p in ('Devs','k_per_dev','cap'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Done
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("doubling Devs near cap yields diminishing returns",
                   y(run({**bi, 'Devs':[30,1,500]}, step)),
                   y(run({**bi, 'Devs':[60,1,500]}, step)), 'up')
  return Model(init, step, y, rq, 'Devs')


def successful():
  """Merton 1968 Matthew effect: attention concentrates on already-
  attended modules. RQ: high attention_concentration starves the
  unattended modules until net coverage degrades."""
  init = {'Pop':[50,1,500], 'Attended':[10,0,500],
          'Coverage':[0,0,1e5], 'concentration':[0.5,0,1],
          'attention_rate':[3,0,30]}
  def step(dt, t, u, v):
    flow_attn = u.attention_rate * u.concentration
    flow_pop  = u.attention_rate * (1 - u.concentration)
    gain      = u.Attended * flow_attn + (u.Pop - u.Attended) * flow_pop
    starve    = (u.Pop - u.Attended) * u.concentration * 0.5
    v.Coverage = u.Coverage + dt * (gain - starve)
    for p in ('Pop','Attended','concentration','attention_rate'):
      setattr(v, p, getattr(u, p))
  def y(out): return out[-1][1].Coverage
  def rq(bg=None):
    bi = init if bg is None else bg
    return verdict("extreme concentration starves Coverage",
                   y(run({**bi, 'concentration':[0.4,0,1]}, step)),
                   y(run({**bi, 'concentration':[0.9,0,1]}, step)), 'down')
  return Model(init, step, y, rq, 'concentration')


ALL_MODELS = [diapers, brooks, bugs, debt, sir, rework, learn, brooksq,
              defmap, aiwork, flaky, dora, micro, teamtopo, burnout, aidebt,
              archpat, congruence,
              # 15 newly added from docs/other.html buildable-today list:
              little, coordn2, entropy, costchange, pareto, linus, mirroring,
              orgchurn, ownership, ossfail, deprot, scope, ctxswitch, limits,
              successful]


def main():
  print(f"{'model':<10} {'verdict':<8} {'y0':>10} {'y1':>10} {'gap':>10}")
  print("-" * 60)
  for f in ALL_MODELS:
    m = f()
    r = m.rq()
    print(f"{f.__name__:<10} {r['verdict']:<8} {r['y0']:>10.2f} "
          f"{r['y1']:>10.2f} {r['gap']:>+10.2f}")

if __name__ == "__main__":
  main()
