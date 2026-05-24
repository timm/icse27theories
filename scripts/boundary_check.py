#!/usr/bin/env python3
"""S13 + S14: param plausibility + boundary adequacy check.

For each model with an outputs/lift_<m>_helix.csv, check whether the
lifted parameter values fall within the model's declared [lo, hi]
ranges in sd.py's init dict. Report:
  - in_range: all lifted params within bounds
  - at_boundary: lifted param == lo or hi
  - out_of_range: lifted param outside bounds (BOUNDARY ADEQUACY FAIL)
"""

import csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.sd import brooks, brooksq, debt, rework, defmap, dora, learn


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
]


def _read_csv(path):
    with open(path) as f:
        return next(csv.DictReader(f))


def classify(val, lo, hi, eps=1e-9):
    if val < lo - eps or val > hi + eps:
        return 'out_of_range'
    if abs(val - lo) <= eps or abs(val - hi) <= eps:
        return 'at_boundary'
    return 'in_range'


def main():
    rows = []
    for name, fn, mapping in CHECKS:
        csv_path = f"outputs/lift_{name}_helix.csv"
        if not os.path.exists(csv_path):
            rows.append({'model': name, 'param': '-', 'lifted': '-',
                         'lo': '-', 'hi': '-', 'status': 'no_csv'})
            continue
        if not mapping:
            rows.append({'model': name, 'param': '(none mapped)',
                         'lifted': '-', 'lo': '-', 'hi': '-',
                         'status': 'no_direct_mapping'})
            continue
        csv_row = _read_csv(csv_path)
        m = fn()
        for param, col in mapping.items():
            if param not in m.init:
                rows.append({'model': name, 'param': param, 'lifted': '-',
                             'lo': '-', 'hi': '-', 'status': 'missing_in_init'})
                continue
            _, lo, hi = m.init[param]
            try:
                val = float(csv_row[col])
            except (KeyError, ValueError):
                rows.append({'model': name, 'param': param,
                             'lifted': csv_row.get(col, 'NA'),
                             'lo': lo, 'hi': hi, 'status': 'unparseable'})
                continue
            rows.append({
                'model':  name,
                'param':  param,
                'lifted': f"{val:.4g}",
                'lo':     lo,
                'hi':     hi,
                'status': classify(val, lo, hi),
            })

    out_path = "outputs/boundary_check.csv"
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path}\n")
    for r in rows:
        flag = {'in_range': ' ', 'at_boundary': '~',
                'out_of_range': '!', 'no_direct_mapping': '·',
                'no_csv': '?', 'missing_in_init': '?',
                'unparseable': '?'}.get(r['status'], '?')
        print(f"  [{flag}] {r['model']:8s} {r['param']:14s} "
              f"lifted={str(r['lifted']):>10s}  "
              f"[{str(r['lo']):>6s}, {str(r['hi']):>6s}]  {r['status']}")


if __name__ == "__main__":
    sys.exit(main())
