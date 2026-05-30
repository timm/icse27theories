#!/usr/bin/env python3
"""S13 + S14: param plausibility + boundary adequacy check.

For each model with an outputs/lift_<m>_helix.csv, check whether the
lifted parameter values fall within the model's declared [lo, hi]
ranges in sd.py's init dict. Report:
  - in_range: all lifted params within bounds
  - at_boundary: lifted param == lo or hi
  - out_of_range: lifted param outside bounds (BOUNDARY ADEQUACY FAIL)
"""

import csv, sys
from pathlib import Path

HERE    = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
sys.path.insert(0, str(HERE))
from sd import (brooks, brooksq, debt, rework, defmap, dora, learn,
                archpat, congruence)


CHECKS = [
    ('brooks',  brooks,  {}),
    ('brooksq', brooksq, {
        'inj_rate':  'inj_rate_pre_med',
        'leak_rate': 'leak_rate',
    }),
    ('debt', debt, {
        'pay_rate':  'pay_rate_median',
        'born_rate': 'born_rate_median',
    }),
    ('rework', rework, {
        'failrate': 'failrate_median',
    }),
    ('defmap', defmap, {}),  # tst_proxy unit mismatch
    ('dora', dora, {
        'batch_size':   'batch_size',
        'arrival_rate': 'arrival_rate',
        'rec_rate':     'rec_rate',
    }),
    ('learn', learn, {
        'Jr':           'Jr_n',
        'Tr':           'Tr_n',
        'Sr':           'Sr_n',
        'train_rate':   'train_rate',
        'promote_rate': 'promote_rate',
    }),
    ('archpat', archpat, {
        'Patterned': 'Patterned_n',
        'Legacy':    'Legacy_n',
    }),
    ('congruence', congruence, {
        'Brokers':  'Brokers_n',
        'Clusters': 'Clusters_n',
    }),
]


def classify(val, lo, hi, eps=1e-9):
    if val < lo - eps or val > hi + eps:
        return 'out_of_range'
    if abs(val - lo) <= eps or abs(val - hi) <= eps:
        return 'at_boundary'
    return 'in_range'


PROJECTS = ['helix', 'junit5', 'ambari', 'kaiaulu', 'airflow',
            'openssl', 'tomcat', 'camel']


def _load_lifts():
    by_cell = {}
    with (OUTPUTS / "lifts.csv").open() as f:
        for row in csv.DictReader(f):
            by_cell.setdefault((row["model"], row["project"]), {})[row["metric"]] = row["value"]
    return by_cell


def main():
    lifts = _load_lifts()
    rows = []
    for proj in PROJECTS:
        for name, fn, mapping in CHECKS:
            csv_row = lifts.get((name, proj), {})
            if not csv_row or not mapping:
                continue
            m = fn()
            for param, col in mapping.items():
                if param not in m.init:
                    continue
                spec = m.init[param]
                lo, hi = spec[1], spec[2]
                try:
                    val = float(csv_row[col])
                except (KeyError, ValueError):
                    continue
                rows.append({
                    'project': proj,
                    'model':   name,
                    'param':   param,
                    'lifted':  f"{val:.4g}",
                    'lo':      lo,
                    'hi':      hi,
                    'status':  classify(val, lo, hi),
                })

    out_path = OUTPUTS / "boundary_check.csv"
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path}\n")
    only_violations = [r for r in rows if r['status'] != 'in_range']
    print(f"Violations + boundary-touches ({len(only_violations)} of {len(rows)} cells):")
    for r in only_violations:
        flag = {'at_boundary': '~', 'out_of_range': '!'}.get(r['status'], '?')
        print(f"  [{flag}] {r['project']:8s} {r['model']:10s} {r['param']:14s} "
              f"lifted={str(r['lifted']):>10s}  [{str(r['lo']):>6s}, {str(r['hi']):>6s}]")


if __name__ == "__main__":
    sys.exit(main())
