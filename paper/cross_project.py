#!/usr/bin/env python3
"""Family-member comparison (S16): cross-project metric table.

Reads outputs/lift_<m>_<proj>.csv for every (model, project) pair on
disk and emits outputs/cross_project.csv — one row per model with
columns per project, plus boundary-status flags.
"""

import csv, sys
from pathlib import Path

HERE    = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
sys.path.insert(0, str(HERE))
from sd import (brooks, brooksq, debt, rework, defmap, dora, learn,
                archpat, congruence)


# Key metric to surface per model.
KEY_METRIC = {
    'brooks':     'brooks_tax_median',
    'brooksq':    'leak_rate',
    'bugs':       'gokumoto_a',
    'debt':       'pay_rate_median',
    'rework':     'failrate_median',
    'defmap':     'tst_median',
    'dora':       'cfr',
    'learn':      'train_rate',
    'archpat':    'Legacy_n',
    'congruence': 'Brokers_n',
}

# Param mapping for boundary check (same as boundary_check.py).
MODEL_FACTORIES = {
    'brooks':     brooks,
    'brooksq':    brooksq,
    'debt':       debt,
    'rework':     rework,
    'defmap':     defmap,
    'dora':       dora,
    'learn':      learn,
    'archpat':    archpat,
    'congruence': congruence,
}

# Maps lift CSV column → model.init parameter (for boundary check).
PARAM_FOR_METRIC = {
    'brooksq.leak_rate':  ('brooksq', 'leak_rate'),
    'debt.pay_rate_median': ('debt', 'pay_rate'),
    'rework.failrate_median': ('rework', 'failrate'),
    'dora.cfr':           None,  # cfr not a direct model param
    'learn.train_rate':   ('learn', 'train_rate'),
    'archpat.Legacy_n':   ('archpat', 'Legacy'),
    'congruence.Brokers_n': ('congruence', 'Brokers'),
}


def _load_lifts():
    """Read long-form outputs/lifts.csv → {(model, project): {metric: value}}."""
    by_cell = {}
    with (OUTPUTS / "lifts.csv").open() as f:
        for row in csv.DictReader(f):
            by_cell.setdefault((row["model"], row["project"]), {})[row["metric"]] = row["value"]
    return by_cell


def main():
    lifts = _load_lifts()
    projects = sorted({p for (_, p) in lifts})
    models   = sorted({m for (m, _) in lifts if m in KEY_METRIC})
    print(f"Projects: {projects}")
    print(f"Models:   {models}")

    rows = []
    for model in models:
        metric = KEY_METRIC[model]
        row = {'model': model, 'key_metric': metric}
        for proj in projects:
            cell = lifts.get((model, proj), {})
            row[proj] = cell.get(metric, '—' if not cell else '')

        # Boundary check using model.init
        param_key = f"{model}.{metric}"
        if param_key in PARAM_FOR_METRIC and PARAM_FOR_METRIC[param_key]:
            mod, par = PARAM_FOR_METRIC[param_key]
            spec = MODEL_FACTORIES[mod]().init[par]
            lo, hi = spec[1], spec[2]
            row['lo'] = lo; row['hi'] = hi
            statuses = []
            for proj in projects:
                v = row[proj]
                try:
                    f = float(v)
                    if f < lo or f > hi:
                        statuses.append(f"{proj}:OUT")
                    elif abs(f - lo) < 1e-9 or abs(f - hi) < 1e-9:
                        statuses.append(f"{proj}:BOUND")
                    else:
                        statuses.append(f"{proj}:in")
                except (ValueError, TypeError):
                    statuses.append(f"{proj}:-")
            row['boundary_status'] = ' '.join(statuses)
        else:
            row['lo'] = '-'; row['hi'] = '-'
            row['boundary_status'] = 'n/a'
        rows.append(row)

    fieldnames = ['model', 'key_metric'] + projects + ['lo', 'hi', 'boundary_status']
    out_path = OUTPUTS / "cross_project.csv"
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out_path}\n")

    # Pretty print
    print(f"{'model':<10} {'metric':<22} " + ''.join(f"{p:<14}" for p in projects)
          + f"{'lo':>6} {'hi':>6}  boundary")
    print('-' * (40 + 14*len(projects) + 25))
    for r in rows:
        vals = ' '.join(f"{str(r[p])[:12]:<13}" for p in projects)
        lo = f"{r['lo']:>6}" if r['lo'] != '-' else '   -  '
        hi = f"{r['hi']:>6}" if r['hi'] != '-' else '   -  '
        print(f"{r['model']:<10} {r['key_metric']:<22} {vals} "
              f"{lo} {hi}  {r['boundary_status']}")


if __name__ == "__main__":
    sys.exit(main())
