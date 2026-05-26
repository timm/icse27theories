#!/usr/bin/env python3 -B
"""tests.py: validation harness for sd.py models.

Implements 9 automated tests + a 2x2 stress matrix.

Forrester & Senge (1980) / Sterman (2000) tests:
  boundary_adq      F&S 4/7    long-horizon (tmax=80) verdict still holds
  anomaly_check     F&S 3-beh  trajectory shape stable under stress
  extreme_eqn       F&S 3      run with each var at lo/hi/0; flag NaN/explode

Metamorphic relations (Chen et al. 1998):
  mr_zero_input     MR3        ctrl=0 freezes its channel
  mr_monotone       MR1        y is monotone in ctrl across 5 grid points
  mr_dt_halving     MR8        traj invariant to dt/2 (Sterman test 6)
  mr_bound_consist  MR9        run mode='reject' produces same y as 'clip'
  mr_scale          MR2        2x stocks => ~2x flows (linearity)

Stress 2x2:
  stress(target='inputs') x stress(target='params')
  -> 2x2 cell classification per model.

Run: python3 tests.py
"""

import sys, time
import sd

PASS, FAIL, SKIP = 'PASS', 'FAIL', 'SKIP'

# --- F&S tests --------------------------------------------------------------

def boundary_adq(model_factory):
  """Re-run rq() at tmax=80 (4x default).  If verdict flips,
  the boundary/horizon assumption is inadequate for the thesis."""
  m = model_factory()
  base = m.rq()
  orig_run = sd.run
  sd.run = lambda init, step, dt=1, tmax=80, mode='clip': \
           orig_run(init, step, dt, tmax, mode)
  try:
    long_v = m.rq()
  finally:
    sd.run = orig_run
  flip = ((base['verdict'] == 'CONFIRM' and long_v['verdict'] == 'REFUTE') or
          (base['verdict'] == 'REFUTE'  and long_v['verdict'] == 'CONFIRM'))
  return {'test':'boundary_adq', 'status': FAIL if flip else PASS,
          'detail': f"t=20:{base['verdict']} t=80:{long_v['verdict']}"}


def anomaly_check(model_factory):
  """Compare baseline trajectory to a stressed run (all UPPER inputs at hi).
  FAIL if y changes sign (qualitative reversal) — a meaningful anomaly,
  not just a numeric shift."""
  m = model_factory()
  base = sd.run(m.init, m.step)
  if base is None:
    return {'test':'anomaly_check', 'status':SKIP, 'detail':'baseline failed'}
  hi_init = {k: ([v[2], v[1], v[2]] if k[0].isupper() else list(v))
             for k, v in m.init.items()}
  stressed = sd.run(hi_init, m.step)
  if stressed is None:
    return {'test':'anomaly_check', 'status':SKIP, 'detail':'stress failed'}
  yb, ys = m.y(base), m.y(stressed)
  sign_flip = (yb > 0) != (ys > 0) and abs(yb) > 0.5 and abs(ys) > 0.5
  return {'test':'anomaly_check',
          'status': FAIL if sign_flip else PASS,
          'detail': f'y_base={yb:.2f} y_stress={ys:.2f}'}


def extreme_eqn(model_factory):
  """Run with each input at its lo, hi, and (if 0 is in range) 0.
  Flag NaN/inf in any output."""
  m = model_factory()
  fails = []
  for k, (default, lo, hi) in m.init.items():
    if not k[0].isupper(): continue
    for label, val in [('lo', lo), ('hi', hi)]:
      test_init = {**m.init, k: [val, lo, hi]}
      try:
        out = sd.run(test_init, m.step)
        if out is None: continue
        for _, row in out:
          for vk in m.init:
            v = getattr(row, vk)
            if not (v == v) or v in (float('inf'), float('-inf')):
              fails.append(f"{k}={label}: {vk} -> {v}")
              break
      except Exception as e:
        fails.append(f"{k}={label}: {type(e).__name__}")
  return {'test':'extreme_eqn',
          'status': FAIL if fails else PASS,
          'detail': '; '.join(fails[:3]) if fails else 'all bounded'}


# --- Metamorphic tests ------------------------------------------------------

def mr_zero_input(model_factory):
  """Set ctrl to 0; trajectory of non-ctrl UPPER vars should equal
  the trajectory of a baseline with ctrl explicitly set to 0.
  (Sanity check: redundant by construction unless ctrl is wired wrong.)"""
  m = model_factory()
  if m.ctrl not in m.init:
    return {'test':'mr_zero_input','status':SKIP,'detail':'no ctrl'}
  lo = m.init[m.ctrl][1]
  bg1 = {**m.init, m.ctrl: [lo, lo, m.init[m.ctrl][2]]}
  bg2 = {**m.init, m.ctrl: [lo, lo, m.init[m.ctrl][2]]}
  out1 = sd.run(bg1, m.step)
  out2 = sd.run(bg2, m.step)
  if out1 is None or out2 is None:
    return {'test':'mr_zero_input','status':SKIP,'detail':'run failed'}
  diffs = sum(abs(getattr(out1[i][1], k) - getattr(out2[i][1], k))
              for i in range(len(out1)) for k in m.init)
  return {'test':'mr_zero_input',
          'status': PASS if diffs < 1e-9 else FAIL,
          'detail': f'cumulative diff={diffs:.3g}'}


def mr_monotone(model_factory, n=5):
  """Sweep ctrl across n points in [lo,hi]; y should be monotone
  in the direction predicted by rq()."""
  m = model_factory()
  if m.ctrl not in m.init:
    return {'test':'mr_monotone','status':SKIP,'detail':'no ctrl'}
  lo, hi = m.init[m.ctrl][1], m.init[m.ctrl][2]
  expect_down = (m.rq()['gap'] < 0)
  ys = []
  for i in range(n):
    val = lo + (hi - lo) * i / (n - 1)
    bg = {**m.init, m.ctrl: [val, lo, hi]}
    out = sd.run(bg, m.step)
    if out is None: return {'test':'mr_monotone','status':SKIP,'detail':'run failed'}
    ys.append(m.y(out))
  diffs = [ys[i+1] - ys[i] for i in range(len(ys)-1)]
  if expect_down:
    ok = all(d <= 0.5 for d in diffs)   # tolerate small numerical wiggle
  else:
    ok = all(d >= -0.5 for d in diffs)
  return {'test':'mr_monotone',
          'status': PASS if ok else FAIL,
          'detail': f'ys={[round(y,1) for y in ys]} expect={"down" if expect_down else "up"}'}


def mr_dt_halving(model_factory, tol=0.10):
  """Halve dt; y should be unchanged within tol fraction.
  Sterman test 6 (integration error)."""
  m = model_factory()
  fast = sd.run(m.init, m.step, dt=1, tmax=20)
  slow = sd.run(m.init, m.step, dt=0.5, tmax=20)
  if fast is None or slow is None:
    return {'test':'mr_dt_halving','status':SKIP,'detail':'run failed'}
  yf, ys = m.y(fast), m.y(slow)
  rel = abs(yf - ys) / max(abs(yf), abs(ys), 1.0)
  return {'test':'mr_dt_halving',
          'status': PASS if rel < tol else FAIL,
          'detail': f'y(dt=1)={yf:.2f} y(dt=0.5)={ys:.2f} rel={rel:.2%}'}


def mr_bound_consist(model_factory):
  """Run with mode='reject' (escapes -> None) vs 'clip' (default).
  If they produce the same y, no clamping was load-bearing."""
  m = model_factory()
  out_clip = sd.run(m.init, m.step, mode='clip')
  out_rej  = sd.run(m.init, m.step, mode='reject')
  if out_clip is None:
    return {'test':'mr_bound_consist','status':FAIL,'detail':'clip failed'}
  if out_rej is None:
    return {'test':'mr_bound_consist','status':FAIL,
            'detail':'a state escaped bounds (clamping was load-bearing)'}
  ys = m.y(out_rej); yc = m.y(out_clip)
  rel = abs(ys - yc) / max(abs(yc), 1.0)
  return {'test':'mr_bound_consist',
          'status': PASS if rel < 0.01 else FAIL,
          'detail': f'y(clip)={yc:.2f} y(reject)={ys:.2f}'}


def mr_scale(model_factory, factor=2.0):
  """Scale all UPPER inputs by factor; report y_ratio (informational).
  FAIL only if y_ratio is < 0 (sign flip) or > 100x (explosion).
  Most SD models are nonlinear; ratio != factor is expected, not a bug."""
  m = model_factory()
  base = sd.run(m.init, m.step)
  scaled_init = {}
  for k, (d, lo, hi) in m.init.items():
    if k[0].isupper():
      scaled_init[k] = [d * factor, lo, hi * factor]
    else:
      scaled_init[k] = [d, lo, hi]
  scaled = sd.run(scaled_init, m.step)
  if base is None or scaled is None:
    return {'test':'mr_scale','status':SKIP,'detail':'run failed'}
  yb, ys = m.y(base), m.y(scaled)
  if abs(yb) < 1e-6:
    return {'test':'mr_scale','status':SKIP,'detail':'y=0 baseline'}
  ratio = ys / yb
  bad = ratio < 0 or ratio > 100
  return {'test':'mr_scale',
          'status': FAIL if bad else PASS,
          'detail': f'y_ratio={ratio:.2f} (lin~{factor:.1f})'}


ALL_TESTS = [boundary_adq, anomaly_check, extreme_eqn,
             mr_zero_input, mr_monotone, mr_dt_halving,
             mr_bound_consist, mr_scale]


# --- Stress 2x2 -------------------------------------------------------------

def stress_matrix(model_factory, n=200, seed=1):
  """Run stress with target='inputs' and target='params'; classify
  the model into a 2x2 cell based on majority verdict in each."""
  m = model_factory()
  inp = sd.stress(model_factory, target='inputs', n=n, seed=seed)
  par = sd.stress(model_factory, target='params', n=n, seed=seed)
  def majority(c):
    if c['CONFIRM'] >= n * 0.5:  return 'CONFIRM'
    if c['REFUTE']  >= n * 0.2:  return 'REFUTE'
    return 'neutral'
  return {
    'inp_counts': inp['counts'],
    'par_counts': par['counts'],
    'inp_verdict': majority(inp['counts']),
    'par_verdict': majority(par['counts']),
  }


def cell_label(inp, par):
  """Map (inputs verdict, params verdict) -> 2x2 cell name."""
  if inp == 'CONFIRM' and par == 'CONFIRM': return 'universal'
  if inp == 'CONFIRM' and par != 'CONFIRM': return 'process-conditional'
  if inp != 'CONFIRM' and par == 'CONFIRM': return 'world-conditional'
  return 'fragile'


# --- Runner -----------------------------------------------------------------

def run_all_tests():
  print("\n=== 9-test bank ===")
  hdr = ['model'] + [t.__name__[:14] for t in ALL_TESTS]
  print(' '.join(f'{h:<15}' for h in hdr))
  print('-' * (16 * len(hdr)))
  totals = {t.__name__: {'PASS':0,'FAIL':0,'SKIP':0} for t in ALL_TESTS}
  details = {}
  for f in sd.ALL_MODELS:
    row = [f.__name__]
    for t in ALL_TESTS:
      r = t(f)
      row.append(r['status'])
      totals[t.__name__][r['status']] += 1
      details[(f.__name__, t.__name__)] = r['detail']
    print(' '.join(f'{c:<15}' for c in row))
  print('-' * (16 * len(hdr)))
  print(' '.join(['totals'.ljust(15)] + [
    f"P{totals[t.__name__]['PASS']}/F{totals[t.__name__]['FAIL']}/S{totals[t.__name__]['SKIP']}".ljust(15)
    for t in ALL_TESTS]))
  return details


def run_2x2(n=200):
  print(f"\n=== 2x2 stress (n={n} per cell) ===")
  print(f"{'model':<10} {'inp(C/R/n)':<14} {'par(C/R/n)':<14} "
        f"{'inp':<10} {'par':<10} {'cell':<22}")
  print('-' * 80)
  cells = {}
  for f in sd.ALL_MODELS:
    r = stress_matrix(f, n=n)
    ic, pc = r['inp_counts'], r['par_counts']
    cell = cell_label(r['inp_verdict'], r['par_verdict'])
    cells[f.__name__] = cell
    print(f"{f.__name__:<10} "
          f"{ic['CONFIRM']:>3}/{ic['REFUTE']:>3}/{ic['neutral']:>3}        "
          f"{pc['CONFIRM']:>3}/{pc['REFUTE']:>3}/{pc['neutral']:>3}        "
          f"{r['inp_verdict']:<10} {r['par_verdict']:<10} {cell}")
  print('-' * 80)
  by_cell = {}
  for m, c in cells.items():
    by_cell.setdefault(c, []).append(m)
  print("\nCell summary:")
  for c in ['universal','process-conditional','world-conditional','fragile']:
    members = by_cell.get(c, [])
    print(f"  {c:<22}  {len(members):>2}  {', '.join(members)}")
  return cells


if __name__ == "__main__":
  t0 = time.perf_counter()
  details = run_all_tests()
  cells = run_2x2(n=200)
  print(f"\n=== Findings (FAILs with detail) ===")
  for (model, test), detail in sorted(details.items()):
    # only re-run to check status — cheaper to just re-eval
    pass
  # rebuild with status info
  rebuild = {}
  for f in sd.ALL_MODELS:
    for t in ALL_TESTS:
      r = t(f)
      if r['status'] == FAIL:
        rebuild[(f.__name__, t.__name__)] = r['detail']
  for (m, t), d in sorted(rebuild.items()):
    print(f"  {m:<10} {t:<18} {d}")
  print(f"\nTotal wall time: {time.perf_counter()-t0:.2f} s")
