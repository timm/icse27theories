#!/usr/bin/env python3
"""S6 + S3/S5 sweep: run stress matrix + 9-test bank on ALL 18 models.

Writes outputs/full_audit.csv. One row per model with verdict,
2x2 cell label, and PASS/FAIL on each of the 9 tests.
"""

import csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "models"))

import sd
from sd import (diapers, brooks, bugs, debt, sir, rework, learn, brooksq,
                defmap, aiwork, flaky, dora, micro, teamtopo, burnout, aidebt,
                archpat, congruence, stress)
from tests import (boundary_adq, anomaly_check, extreme_eqn,
                   mr_zero_input, mr_monotone, mr_dt_halving,
                   mr_bound_consist, mr_scale, stress_matrix)


MODELS = [diapers, brooks, bugs, debt, sir, rework, learn, brooksq,
          defmap, aiwork, flaky, dora, micro, teamtopo, burnout, aidebt,
          archpat, congruence]

TESTS = [boundary_adq, anomaly_check, extreme_eqn,
         mr_zero_input, mr_monotone, mr_dt_halving,
         mr_bound_consist, mr_scale]


def cell_label(sm):
    iv, pv = sm['inp_verdict'], sm['par_verdict']
    if iv == 'CONFIRM' and pv == 'CONFIRM':
        return 'universal'
    if iv == 'CONFIRM' and pv != 'CONFIRM':
        return 'world-conditional'
    if iv != 'CONFIRM' and pv == 'CONFIRM':
        return 'process-conditional'
    return 'fragile'


def main():
    rows = []
    for fn in MODELS:
        m = fn()
        rq = m.rq()
        sm = stress_matrix(fn, n=200)
        row = {
            'model':      fn.__name__,
            'verdict':    rq['verdict'],
            'gap':        f"{rq['gap']:+.2f}",
            'cell':       cell_label(sm),
            'inp_cnt':    sm['inp_counts']['CONFIRM'],
            'par_cnt':    sm['par_counts']['CONFIRM'],
        }
        for t in TESTS:
            try:
                r = t(fn)
                row[t.__name__] = r['status']
            except Exception as e:
                row[t.__name__] = f'ERR:{type(e).__name__}'
        rows.append(row)

    out_path = "outputs/full_audit.csv"
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path}\n")
    hdr = ['model', 'verdict', 'gap', 'cell', 'inp', 'par'] + \
          [t.__name__[:10] for t in TESTS]
    print(' | '.join(f"{h:<12}" for h in hdr))
    print('-' * (12 * len(hdr) + 3 * (len(hdr) - 1)))
    for r in rows:
        vals = [r['model'], r['verdict'], r['gap'], r['cell'],
                str(r['inp_cnt']), str(r['par_cnt'])] + \
               [r[t.__name__] for t in TESTS]
        print(' | '.join(f"{v:<12}" for v in vals))


if __name__ == "__main__":
    sys.exit(main())
