#!/usr/bin/env python3
"""S15: plug calibrated lift values into sd.py models, rerun rq().

For each model with an outputs/lift_<m>_helix.csv, build a calibrated
init dict (default + Helix-lifted values), run model.rq(bg=calib),
and compare to baseline model.rq() (synthetic defaults).

Output: outputs/calibrated_verdicts.csv with columns:
  model, default_verdict, default_gap, calib_verdict, calib_gap,
  changes_verdict, notes

Mappings are per-model and conservative: when a lift quantity doesn't
map 1:1 to a model param (unit mismatch or derived metric), we skip
that override and note it.
"""

import csv, sys
from pathlib import Path

HERE    = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
LIFTS   = OUTPUTS / "lifts.csv"
sys.path.insert(0, str(HERE))
from sd import (brooks, brooksq, debt, rework, defmap, dora, learn,
                archpat, congruence)


def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def _load_lifts():
    """Read long-form outputs/lifts.csv into {(model, project): {metric: value}}."""
    by_cell = {}
    with LIFTS.open() as f:
        for row in csv.DictReader(f):
            key = (row["model"], row["project"])
            by_cell.setdefault(key, {})[row["metric"]] = row["value"]
    return by_cell


_LIFTS_CACHE = None
def _lift_row(model, project="helix"):
    global _LIFTS_CACHE
    if _LIFTS_CACHE is None:
        _LIFTS_CACHE = _load_lifts()
    return _LIFTS_CACHE.get((model, project), {})


def _override_init(init, overrides, notes):
    """Return a copy of init with overrides applied; record any clipping."""
    bg = {k: list(v) for k, v in init.items()}
    for k, val in overrides.items():
        if k not in bg:
            notes.append(f"skipped: '{k}' not in model.init")
            continue
        spec = bg[k]
        lo, hi = spec[1], spec[2]
        clipped = _clip(float(val), lo, hi)
        if clipped != float(val):
            notes.append(f"clipped {k}: {val:.3g} -> [{lo},{hi}] => {clipped:.3g}")
        bg[k][0] = clipped
    return bg


def calibrate_brooks(_csv_row):
    """brooks_tax_median is a DERIVED metric from velocity comparison,
    not a direct model param. Without lifted comm_coef/train_coef we
    cannot directly override. Report baseline only and note the gap."""
    m = brooks()
    notes = ["brooks_tax_median is derived (post-hire velocity drop), not a direct "
             "input to brooks(); comm_coef/train_coef not lifted; no calib applied"]
    default_v = m.rq()
    return default_v, default_v, notes


def calibrate_brooksq(csv_row):
    """brooksq.init has comm_coef, train_coef, inj_rate, leak_rate.
    The lift gives inj_rate_pre/post and leak_rate directly. Use the
    pre-hire median for inj_rate (steady-state), and lifted leak_rate."""
    m = brooksq()
    overrides = {
        'inj_rate':  float(csv_row['inj_rate_pre_med']),
        'leak_rate': float(csv_row['leak_rate']),
    }
    notes = []
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


def calibrate_debt(csv_row):
    """debt.init has pay_rate, born_rate, intr_rate. Lift gives
    pay_rate_median + born_rate_median. intr_rate stays at default
    (would need sd.opt() to fit)."""
    m = debt()
    overrides = {
        'pay_rate':  float(csv_row['pay_rate_median']),
        'born_rate': float(csv_row['born_rate_median']),
    }
    notes = ["intr_rate left at default; would need sd.opt() to fit"]
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


def calibrate_rework(csv_row):
    """rework.init.failrate is the ctrl variable. rq() flips it
    between 0.1 and 0.7 to test the thesis — overriding failrate
    background doesn't change the rq comparison endpoints. We
    instead override code_rate / qa_rate / fix_rate if we had them,
    but the lift only gives failrate. Report baseline only."""
    m = rework()
    notes = [f"failrate_median = {csv_row['failrate_median']} (Helix safe regime, "
             "below thesis-trigger 0.5); rq() ctrl is failrate so bg override moot"]
    default_v = m.rq()
    return default_v, default_v, notes


def calibrate_defmap(_csv_row):
    """defmap.init.tst is the ctrl. Lift gives tst_proxy in [0,1] but
    model's tst is [0,10] (multiplicative in step()). UNIT MISMATCH —
    don't override."""
    m = defmap()
    notes = ["tst_proxy is ratio (caught/injected) in [0,1]; model's tst "
             "is multiplicative coef in [0,10]; unit mismatch, no calib applied"]
    default_v = m.rq()
    return default_v, default_v, notes


def calibrate_dora(csv_row):
    """dora.init has batch_size (ctrl), cfr_coef, arrival_rate, rec_rate.
    Lift gives batch_size + arrival_rate + rec_rate directly. cfr_coef
    is the SD-internal CFR-per-batch slope; lifted cfr is the OUTPUT
    not the coefficient."""
    m = dora()
    overrides = {
        'arrival_rate': float(csv_row['arrival_rate']),
        'rec_rate':     float(csv_row['rec_rate']),
    }
    notes = [f"batch_size in lift = {csv_row['batch_size']} (Helix operating point); "
             "rq() ctrl is batch_size so override is moot; cfr_coef not lifted"]
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


def calibrate_learn(csv_row):
    """learn.init has Jr/Tr/Sr stocks + train_rate/promote_rate/mentor_rate.
    Lift gives Jr_n, Tr_n, Sr_n, train_rate, promote_rate directly."""
    m = learn()
    overrides = {
        'Jr':           float(csv_row['Jr_n']),
        'Tr':           float(csv_row['Tr_n']),
        'Sr':           float(csv_row['Sr_n']),
        'train_rate':   float(csv_row['train_rate']),
        'promote_rate': float(csv_row['promote_rate']),
    }
    notes = ["mentor_rate left at default; not lifted from gitlog alone"]
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


def calibrate_archpat(csv_row):
    """archpat.init has Patterned, Legacy, Drift stocks + many rate
    params. Lift gives stock counts. ctrl is migrate, so bg override
    is moot for the rq comparison, but stocks shape baseline."""
    m = archpat()
    overrides = {
        'Patterned': float(csv_row['Patterned_n']),
        'Legacy':    float(csv_row['Legacy_n']),
    }
    notes = ["Drift = NA (no recent-churn data); rate params not lifted"]
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


def calibrate_congruence(csv_row):
    """congruence.init has Brokers + Clusters stocks. Lift gives both
    directly from radio_silence mbox analysis."""
    m = congruence()
    overrides = {
        'Brokers':  float(csv_row['Brokers_n']),
        'Clusters': float(csv_row['Clusters_n']),
    }
    notes = ["rate params (broker_form, fragment_rate, merge_rate, "
             "work_rate) not lifted"]
    bg = _override_init(m.init, overrides, notes)
    return m.rq(), m.rq(bg=bg), notes


MODELS = [
    ('brooks',     calibrate_brooks),
    ('brooksq',    calibrate_brooksq),
    ('debt',       calibrate_debt),
    ('rework',     calibrate_rework),
    ('defmap',     calibrate_defmap),
    ('dora',       calibrate_dora),
    ('learn',      calibrate_learn),
    ('archpat',    calibrate_archpat),
    ('congruence', calibrate_congruence),
]


def main():
    out_path = OUTPUTS / "calibrated_verdicts.csv"
    rows = []
    for name, fn in MODELS:
        csv_row = _lift_row(name, project="helix")
        if not csv_row:
            rows.append({'model': name, 'default_verdict': '-',
                         'default_gap': '-', 'calib_verdict': '-',
                         'calib_gap': '-', 'changes_verdict': '-',
                         'notes': f"no lift row for ({name}, helix) in lifts.csv"})
            continue
        try:
            default_v, calib_v, notes = fn(csv_row)
        except Exception as e:
            rows.append({'model': name, 'default_verdict': 'ERROR',
                         'default_gap': '-', 'calib_verdict': '-',
                         'calib_gap': '-', 'changes_verdict': '-',
                         'notes': str(e)})
            continue
        rows.append({
            'model':           name,
            'default_verdict': default_v['verdict'],
            'default_gap':     f"{default_v['gap']:+.3g}",
            'calib_verdict':   calib_v['verdict'],
            'calib_gap':       f"{calib_v['gap']:+.3g}",
            'changes_verdict': default_v['verdict'] != calib_v['verdict'],
            'notes':           ' | '.join(notes) if notes else '',
        })

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path}")
    for r in rows:
        print(f"  {r['model']:10s}  default={r['default_verdict']:7s} "
              f"(gap {r['default_gap']:>8s})  "
              f"calib={r['calib_verdict']:7s} (gap {r['calib_gap']:>8s})  "
              f"changes={r['changes_verdict']}")
        if r['notes']:
            print(f"             notes: {r['notes']}")


if __name__ == "__main__":
    sys.exit(main())
