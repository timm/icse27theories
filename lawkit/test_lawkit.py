"""pytest lawkit/test_lawkit.py -- guards the facts the cards rely on."""
import sd
from lawkit.laws import LAWS
from lawkit.core import background, judge
from lawkit import battery

def test_brooks_standard_default():
  "Late project, finish time: 10 hires delay the finish by 11 ticks."
  assert judge(LAWS["brooks"], background(LAWS["brooks"])) == ("CONFIRM", -11.0)

def test_sd_brooks_fixed():
  "paper/sd.py's own brooks (bugs fixed) still gives its published gap."
  assert sd.brooks().rq()["gap"] == -147.5

def test_aiwork_archpat_match_sd():
  for k, f in (("aiwork", sd.aiwork), ("archpat", sd.archpat)):
    g = judge(LAWS[k], background(LAWS[k]))[1]
    assert abs(g - f().rq()["gap"]) < 1e-6

def test_dead_param_found():
  r = battery.dead_params(LAWS["archpat"])
  assert r["status"] == battery.FAIL and "pat_strength" in r["detail"]

def test_hardcoded_channel_found():
  assert battery.knockout(LAWS["archpat"])["status"] == battery.FAIL

def test_brooks_dims_consistent():
  assert battery.units(LAWS["brooks"])["status"] == battery.PASS

def test_dims_mismatch_found():
  from lawkit.units import check
  bg = {**LAWS["brooks"].model().init,
        'prod_rate': [5, 0.1, 20, 'items/vet/tick']}   # old label
  errs, _ = check(LAWS["brooks"].model(), bg, "boost", 10, 20)
  assert errs and "vet" in errs[0]

def _run(law, **over):
  from lawkit.core import spec
  bg = {k: v for k, v in background(law).items() if not k.startswith("_")}
  for k, val in over.items(): bg[k] = spec(bg, k, val)
  return sd.run(bg, law.model().step, dt=law.dt, tmax=law.tmax)

def test_no_phantom_work():
  assert _run(LAWS["brooks"], Todo=0)[-1][1].Done == 0
  m = sd.brooks(); bg = dict(m.init, Todo=[0, 0, 500, 'items'])
  assert sd.run(bg, m.step)[-1][1].Done == 0          # sd.py fixed: was 500

def test_conserves_work():
  s = _run(LAWS["brooks"])[-1][1]
  assert abs(s.Done + s.Todo - 1000) < 1e-6

def test_brooks_saturation_not_dead():
  assert battery.dead_params(LAWS["brooks"])["status"] == battery.PASS
