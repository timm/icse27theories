#!/usr/bin/env python3
"""S6 + S3/S5 sweep: run stress matrix + 9-test bank on ALL 18 models.

Writes outputs/full_audit.csv. One row per model with verdict,
2x2 cell label, and PASS/FAIL on each of the 9 tests.
"""

import csv, sys
from pathlib import Path

HERE    = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
sys.path.insert(0, str(HERE))

import sd
from sd import (diapers, brooks, bugs, debt, sir, rework, learn, brooksq,
                defmap, aiwork, flaky, dora, micro, teamtopo, burnout, aidebt,
                archpat, congruence, stress,
                # 15 newly added from docs/other.html buildable-today set:
                little, coordn2, entropy, costchange, pareto, linus, mirroring,
                orgchurn, ownership, ossfail, deprot, scope, ctxswitch, limits,
                successful,
                # 1 added 2026-05-26 per domain-expert request:
                maturity,
                # 1 added 2026-05-25 per Carlos GH #3 (motif-based STC):
                congruence_motif)
from tests import (boundary_adq, anomaly_check, extreme_eqn,
                   mr_zero_input, mr_monotone, mr_dt_halving,
                   mr_bound_consist, mr_scale, stress_matrix)


MODELS = [diapers, brooks, bugs, debt, sir, rework, learn, brooksq,
          defmap, aiwork, flaky, dora, micro, teamtopo, burnout, aidebt,
          archpat, congruence, congruence_motif,
          little, coordn2, entropy, costchange, pareto, linus, mirroring,
          orgchurn, ownership, ossfail, deprot, scope, ctxswitch, limits,
          successful, maturity]

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
        m  = fn()
        r1 = m.rq()                              # single-shot (heuristic threshold)
        rn = sd.rq_n(fn, n=100)                  # N-shot stats.same verdict
        sm = stress_matrix(fn, n=200)
        row = {
            'model':       fn.__name__,
            'verdict':     r1['verdict'],        # legacy single-shot
            'gap':         f"{r1['gap']:+.2f}",
            'verdict_n':   rn['verdict'],        # N=100 + stats.same (Cliff's + KS)
            'gap_n':       f"{rn['gap']:+.2f}",
            'sd0_n':       f"{rn['sd0']:.2f}",
            'sd1_n':       f"{rn['sd1']:.2f}",
            'eps_n':       f"{rn['eps']:.2f}",
            'cell':        cell_label(sm),
            'inp_cnt':     sm['inp_counts']['CONFIRM'],
            'par_cnt':     sm['par_counts']['CONFIRM'],
        }
        for t in TESTS:
            try:
                r = t(fn)
                row[t.__name__] = r['status']
            except Exception as e:
                row[t.__name__] = f'ERR:{type(e).__name__}'
        rows.append(row)

    out_path = OUTPUTS / "full_audit.csv"
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path}\n")
    hdr = ['model', 'verdict', 'gap', 'verdict_n', 'gap_n', 'cell', 'inp', 'par'] + \
          [t.__name__[:10] for t in TESTS]
    print(' | '.join(f"{h:<12}" for h in hdr))
    print('-' * (12 * len(hdr) + 3 * (len(hdr) - 1)))
    for r in rows:
        vals = [r['model'], r['verdict'], r['gap'],
                r['verdict_n'], r['gap_n'],
                r['cell'], str(r['inp_cnt']), str(r['par_cnt'])] + \
               [r[t.__name__] for t in TESTS]
        print(' | '.join(f"{v:<12}" for v in vals))


if __name__ == "__main__":
    sys.exit(main())
