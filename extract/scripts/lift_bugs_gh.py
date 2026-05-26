#!/usr/bin/env python3
"""Goel-Okumoto bug-reliability fit using GitHub issue data.

Usage:
  python3 scripts/lift_bugs_gh.py <issue-glob> <project> <out-csv>

Extracts issues labeled 'bug' (or 'Bug') with closed_at timestamps,
builds cumulative-resolved-bugs over time, fits Goel-Okumoto
exponential N(t) = a * (1 - exp(-b*t)) via grid search.
"""

import csv, glob, json, math, os, sys
from datetime import datetime


def iso_to_unix(s):
    if not s: return None
    return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())


def fit_gokumoto(t, N):
    """N(t) = a * (1 - exp(-b*t)); grid search."""
    if len(t) < 5:
        return None, None, 0.0
    a_max = max(N) * 1.2
    best = (None, None, float('inf'))
    for a in [a_max * f for f in [0.8, 1.0, 1.2, 1.5, 2.0, 3.0]]:
        for b in [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4]:
            sse = sum((a * (1 - math.exp(-b * ti)) - Ni)**2 for ti, Ni in zip(t, N))
            if sse < best[2]:
                best = (a, b, sse)
    mean_N = sum(N) / len(N)
    ss_tot = sum((Ni - mean_N)**2 for Ni in N)
    r2 = 1 - best[2] / ss_tot if ss_tot > 0 else 0
    return best[0], best[1], r2


def main(argv):
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 1
    issue_glob, project, out_csv = argv[1], argv[2], argv[3]
    issues = []
    for f in sorted(glob.glob(issue_glob)):
        with open(f) as fh:
            d = json.load(fh)
        if isinstance(d, list):
            issues.extend(d)
        elif isinstance(d, dict) and 'issues' in d:
            issues.extend(d['issues'])

    bugs = []
    for i in issues:
        labels = [l.get('name','').lower() for l in i.get('labels',[]) if isinstance(l, dict)]
        if not any('bug' in l for l in labels):
            continue
        ca = iso_to_unix(i.get('closed_at'))
        if ca is None:
            continue
        bugs.append(ca)

    if len(bugs) < 5:
        print(f"too few bug-issues for {project}: {len(bugs)}", file=sys.stderr)
        return 1

    bugs.sort()
    t0 = bugs[0]
    rel_t = [(b - t0) for b in bugs]
    cum_N = list(range(1, len(bugs) + 1))

    a, b_param, r2 = fit_gokumoto(rel_t, cum_N)
    span_days = (bugs[-1] - bugs[0]) / 86400.0

    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['project','n_bugs_total','n_bugs_closed',
                    'gokumoto_a','gokumoto_b','fit_r2','span_days','seed'])
        w.writerow([project, len(issues), len(bugs),
                    f"{a:.2f}" if a else "",
                    f"{b_param:.3e}" if b_param else "",
                    f"{r2:.4f}",
                    f"{span_days:.1f}", 1])
    print(f"Wrote {out_csv}")
    print(f"  {project}: total_issues={len(issues)} bugs_closed={len(bugs)}")
    print(f"  Goel-Okumoto: a={a:.2f} b={b_param:.3e} R^2={r2:.4f}")
    print(f"  span: {span_days:.1f} days")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
