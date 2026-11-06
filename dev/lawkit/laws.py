"""laws.py: the three worked laws as lawkit specs. Each spec names the
claim, the lever, its support factors, its causal channels, business
scenarios (same mechanism, different world) and variants (same world,
different mechanism). A new law = one more spec in this file."""

import math
import sd
from .core import Law

def _carry(u, v, keys):
  for k in keys: setattr(v, k, getattr(u, k))

# --- Brooks (1975): the standard model ----------------------------------
# One model for every Forrester test, report and future evaluation:
# sd.brooks' communication and training costs, plus the five structures
# Brooks 1975 / Abdel-Hamid & Madnick 1991 name that sd.brooks leaves out,
# a bounded overload (time left for work = exp(-overhead), so effort never
# goes negative), outcome = finish time of a genuinely late project.

def flat_comm(V, c):     return V * (V - 1) / 2 * c
def team_comm(V, c, s=10):
  k = math.ceil(max(V, 1) / s)
  return (min(V, s) * (min(V, s) - 1) / 2 + k * (k - 1) / 2) * c
def person_comm(V, c):   return 4.5 * (V - 1) * c   # = flat at V=10
def async_comm(V, c):    return V * math.log2(max(2, V)) * c * 0.5

# The five extra structures as uncertain settings: off (0) at the default,
# sampled up to an illustrative literature-like value. Ranges are
# assumptions, not measurements.
EXTRA = {'newprod':  [0, 0, 0.5, 'frac'],       # newcomers' own output share
         'leave':    [0, 0, 0.02, 'frac/tick'],  # veteran attrition
         'serial':   [0, 0, 0.2, 'frac/devs'],   # Amdahl: lost per extra dev
         'overtime': [0, 0, 0.2, 'frac'],        # extra effort when behind
         'rework':   [0, 0, 0.15, 'frac'],       # share of output redone
         'deadline': [20, 1, 80, 'tick']}        # what "behind" refers to

def brooks_like(comm=flat_comm, train_share=False, pods=False,
                async_train=1.0, waves=1):
  "The standard Brooks model; arguments give the rival team structures."
  def factory():
    init = {**sd.brooks().init, 'hire_at': [10, 0, 19, 'tick'], **EXTRA}
    def step(dt, t, u, v):
      new, vet = u.New, u.Vet
      active = vet
      if pods:                                  # mentors absorb training
        active = max(0, vet - min(vet, math.ceil(new / 5)))
        train = 0
      else:
        train = new * u.train_coef * async_train
        if train_share: train /= max(1, vet)    # mentoring spread over vets
      x = comm(active, u.comm_coef) + train     # overhead share of time
      heads = active / (1 + u.serial * (active - 1)) if active > 0 else 0
      prod = (heads * math.exp(-x) + u.newprod * new) * u.prod_rate
      rem = max(u.deadline - t, dt)
      if prod > 0:                              # behind schedule -> overtime
        press = min(1, max(0, u.Todo / rem / prod - 1))
        prod = prod * (1 + u.overtime * press)
      if vet + new > 0: prod = prod * (1 - u.rework * (1 + new / (vet + new)))
      prod = min(prod, u.Todo / dt)             # can't finish absent work
      v.Todo = u.Todo - dt * prod
      v.Done = u.Done + dt * prod
      h = u.hire_at                     # pulses only on whole ticks
      pulse = u.boost / waves if h <= t < h + waves and t == int(t) else 0
      v.New = new - dt * u.mature_rate * new + pulse
      v.Vet = vet + dt * u.mature_rate * new - dt * u.leave * vet
      _carry(u, v, ('boost', 'comm_coef', 'train_coef', 'prod_rate',
                    'mature_rate', 'hire_at') + tuple(EXTRA))
    return sd.Model(init, step, sd.brooks().y, None, 'boost')
  return factory

brooks_flat = brooks_like()

def finish_time(out, bg):
  """Brooks claims 'makes it LATER': y = -(finish tick); unfinished work
  is extrapolated at the pace the plan required."""
  dt = out[1][0] - out[0][0]
  for t, s in out:
    if s.Todo <= 1e-9: return -(t + dt)
  pace = bg['Todo'][0] / (len(out) * dt)
  return -(len(out) * dt + out[-1][1].Todo / pace)

BROOKS = Law(
  "brooks", brooks_flat,
  "adding 10 people to a project that is already late (backlog 1000, "
  "10 vets can do ~800 by t=20) makes it finish later", lever="boost",
  arms=(0, 10), expect="down",
  factors=['Vet', 'Todo', 'comm_coef', 'train_coef', 'prod_rate',
           'mature_rate', 'hire_at'] + [k for k in EXTRA if k != 'deadline'],
  channels={'comm_coef': 0, 'train_coef': 0},
  tmax=80, y=finish_time, base={'Todo': 1000}, dt=0.125,
  sources="Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks; outcome = "
          "completion time; extra structures and bounded overload",
  scenarios={
    "early_hire":      ("hire at t=2 instead of t=10", {'hire_at': 2}),
    "last_minute":     ("panic hire 2 ticks before deadline",
                        {'hire_at': 18}),
    "micro_hire":      ("hire 1 person", {'_arms': (0, 1)}),
    "massive_surge":   ("hire 50 people", {'_arms': (0, 50)}),
    "small_core":      ("10 hires onto a core team of 2", {'Vet': 2}),
    "high_prod":       ("very productive devs", {'prod_rate': 15}),
    "fast_onboard":    ("mature_rate 0.5", {'mature_rate': 0.5}),
    "steep_learning":  ("spaghetti code: slow, costly onboarding",
                        {'mature_rate': 0.02, 'train_coef': 0.4}),
    "async_remote":    ("comm_coef 0.001", {'comm_coef': 0.001}),
    "no_training":     ("no mentoring drag", {'train_coef': 0}),
    "no_comm":         ("no coordination drag", {'comm_coef': 0}),
    "light_mentoring": ("each newcomer costs 2% of each vet (not 20%)",
                        {'train_coef': 0.02}),
    "on_time_project": ("antecedent false: backlog 500 (done by t=13)",
                        {'Todo': 500}),
    "huge_backlog":    ("backlog 3000", {'Todo': 3000})},
  variants={
    "flat (reference)":   ("reference clique", brooks_flat),
    "squads of 10":       ("Conway/surgical teams: pairs inside a squad "
                           "+ between squads", brooks_like(team_comm)),
    "mentor pods":        ("ceil(New/5) vets mentor full-time, others "
                           "untaxed", brooks_like(pods=True)),
    "async docs + CI":    ("O(N log N) comm, 40% less training",
                           brooks_like(async_comm, async_train=0.6)),
    "staged waves":       ("hires arrive in 5 waves", brooks_like(waves=5)),
    "per-person comm":    ("each dev bears (V-1) channels, not all "
                           "V(V-1)/2", brooks_like(person_comm)),
    "shared mentoring":   ("train_coef is FTE per newcomer, spread over "
                           "vets", brooks_like(train_share=True))})
BROOKS.free = ('Vet', 'New')      # 0-100 is a prior on team size, not a cap

# --- aiwork (GitClear 2024 / METR 2025) --------------------------------

def aiwork_like(learn=0, cleanup=0, defects=0):
  def factory():
    base = sd.aiwork()
    init = dict(base.init, Defects=[0, 0, 1000, 'defects'])
    def step(dt, t, u, v):
      drag = u.verify_drag * u.ai * (math.exp(-t / learn) if learn else 1)
      cap = 1 / (1 + u.Defects / 50) if defects else 1
      churn_now = u.Wip * u.churn_base * (1 + u.churn_mult * u.ai)
      gen = 10 * (1 + u.gen_boost * u.ai) * (1 - drag) * cap
      gen = max(0, gen - cleanup * churn_now)
      add = min(gen, u.Todo)
      mature = u.Wip * u.mature_rate
      v.Todo = u.Todo - dt * add
      v.Wip = u.Wip + dt * (add - mature - churn_now)
      v.Kept = u.Kept + dt * mature
      v.Churned = u.Churned + dt * churn_now
      v.Defects = u.Defects + dt * defects * churn_now
      _carry(u, v, ('ai', 'gen_boost', 'churn_mult', 'verify_drag',
                    'mature_rate', 'churn_base'))
    return sd.Model(init, step, base.y, None, 'ai')
  return factory

AIWORK = Law(
  "aiwork", sd.aiwork,
  "full AI assistance (ai=1) lowers kept code at t=20", lever="ai",
  arms=(0, 1), expect="down",
  factors=['gen_boost', 'churn_mult', 'verify_drag', 'mature_rate',
           'churn_base'],
  channels={'churn_mult': 0, 'verify_drag': 0},
  sources="GitClear 2024; METR 2025; Peng et al. 2023; sd.aiwork",
  scenarios={
    "vibe_coding":     ("accept AI output with little review",
                        {'gen_boost': 1.5, 'verify_drag': 0.1,
                         'churn_mult': 4}),
    "review_gate":     ("strict review: slow but low churn",
                        {'gen_boost': 0.5, 'verify_drag': 0.6,
                         'churn_mult': 0.5}),
    "boilerplate":     ("greenfield CRUD/tests: AI is very fast",
                        {'gen_boost': 1.5, 'verify_drag': 0.2,
                         'churn_mult': 1}),
    "legacy_expert":   ("METR setting: experts in big familiar repos",
                        {'gen_boost': 0.2, 'verify_drag': 0.5,
                         'churn_mult': 2.5}),
    "copilot_rct":     ("Peng 2023-like: +55% speed, modest churn",
                        {'gen_boost': 0.55, 'verify_drag': 0.15,
                         'churn_mult': 1}),
    "half_adoption":   ("ai=0.5 instead of 1", {'_arms': (0, 0.5)}),
    "short_sprint":    ("deadline t=5: pipeline delay dominates",
                        {'_tmax': 5}),
    "slow_review_pipe": ("code sits in Wip longer (mature 0.05)",
                         {'mature_rate': 0.05}),
  },
  variants={
    "sd.aiwork":        ("reference", aiwork_like()),
    "team learns AI":   ("verify drag decays, tau=8 ticks",
                         aiwork_like(learn=8)),
    "churn costs time": ("each churned item costs 0.5 items of capacity",
                         aiwork_like(cleanup=0.5)),
    "latent defects":   ("churn leaves defects that tax capacity",
                         aiwork_like(defects=0.3)),
  })

# --- archpat (Perry & Wolf 1992; Martin 2008) --------------------------

def archpat_like(mig_cost=0, mig_bugs=0, pressure=0):
  def factory():
    base = sd.archpat()
    init = dict(base.init, Feat=[0, 0, 1e7, 'items'],
                mig_cost=[mig_cost, 0, 10, 'items/module'],
                mig_bugs=[mig_bugs, 0, 2, 'debt/module'],
                pressure=[pressure, 0, 2, 'frac'])
    def step(dt, t, u, v):
      tot = u.Patterned + u.Legacy + u.Drift
      speed = max(0.05, 1 - u.Debt / 150)
      mig = u.migrate * u.Legacy * 0.05
      gen = (u.Patterned * u.gen_pat + (u.Legacy + u.Drift) * u.gen_leg
             ) * speed
      decay = u.decay_rate * u.Patterned * (1 + u.pressure * gen /
                                            max(1, tot))
      gen = max(0, gen - u.mig_cost * mig)        # migration is not free
      share = u.Patterned / max(1, tot)
      born = gen * (u.born_pat * share + u.born_leg * (1 - share))
      born += u.mig_bugs * mig                    # refactorings inject bugs
      pay = u.Debt * u.pay_rate * (1 + 0.5 * share)
      drift = u.drift_to_legacy * u.Drift
      v.Patterned = u.Patterned + dt * (mig - decay)
      v.Legacy = u.Legacy + dt * (drift - mig)
      v.Drift = u.Drift + dt * (decay - drift)
      v.Debt = u.Debt + dt * (born + u.Debt * u.intr_rate - pay)
      v.Feat = u.Feat + dt * gen
      _carry(u, v, ('migrate', 'decay_rate', 'drift_to_legacy', 'gen_pat',
                    'gen_leg', 'born_pat', 'born_leg', 'intr_rate',
                    'pay_rate', 'pat_strength', 'mig_cost', 'mig_bugs',
                    'pressure'))
    return sd.Model(init, step, base.y, None, 'migrate')
  return factory

archpat_ref = archpat_like()

ARCHPAT = Law(
  "archpat", archpat_ref,
  "aggressive migration to patterns (1.5 vs 0.2) raises Feat - "
  "mean(Debt) of an already-bad project", lever="migrate",
  arms=(0.2, 1.5), expect="up",
  factors=['Patterned', 'Legacy', 'Debt', 'decay_rate',
           'drift_to_legacy', 'gen_pat', 'gen_leg', 'born_pat',
           'born_leg', 'intr_rate', 'pay_rate'],
  channels={'gen_pat': 'gen_leg', 'born_pat': 'born_leg'},
  sources="Perry & Wolf 1992; Martin 2008; Bavota et al. 2012; sd.archpat",
  scenarios={
    "big_bang":        ("rewrite: migrate=2.0", {'_arms': (0.2, 2.0)}),
    "no_governance":   ("patterns erode 6x faster", {'decay_rate': 0.3}),
    "already_good":    ("90 patterned / 10 legacy",
                        {'Patterned': 90, 'Legacy': 10}),
    "debt_crisis":     ("Debt=120 at start", {'Debt': 120}),
    "overengineered":  ("abstraction tax: patterned code ships slower",
                        {'gen_pat': 0.35}),
    "patterns_no_safer": ("patterned code as bug-prone as legacy",
                          {'born_pat': 0.20}),
    "helix_scale":     ("Helix partition: 149 patterned, 384 legacy",
                        {'Patterned': 149, 'Legacy': 384}),
    "short_horizon":   ("evaluate after 8 ticks", {'_tmax': 8}),
  },
  variants={
    "sd.archpat":         ("reference: migration is free", archpat_ref),
    "migration costs":    ("4 feature-items of effort per module moved",
                           archpat_like(mig_cost=4)),
    "refactoring bugs":   ("0.5 debt per module moved (Bavota 2012)",
                           archpat_like(mig_bugs=0.5)),
    "erosion ~ pressure": ("decay grows with delivery pressure",
                           archpat_like(pressure=1)),
    "all three":          ("cost + bugs + pressure",
                           archpat_like(4, 0.5, 1)),
  })

ARCHPAT_COST = Law(
  "archpat_cost", archpat_like(2, 0.25, 0.5), ARCHPAT.claim +
  " when migration has an uncertain price", lever="migrate",
  arms=ARCHPAT.arms, expect="up",
  factors=ARCHPAT.factors + ['mig_cost', 'mig_bugs', 'pressure'],
  channels=ARCHPAT.channels, scenarios=ARCHPAT.scenarios,
  sources=ARCHPAT.sources + "; priors on the three missing mechanisms",
  variants={})

LAWS = {l.name: l for l in (BROOKS, AIWORK, ARCHPAT, ARCHPAT_COST)}
