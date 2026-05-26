#!/usr/bin/env python3
"""Melt all paper/outputs/lift_<model>_<project>.csv into one long table.

Output: paper/outputs/lifts.csv with columns (model, project, metric, value).
Each source CSV's "project" column is dropped (the filename already encodes it).
All other columns become (metric, value) rows.

Idempotent: re-run any time after extract/lifts/*.Rmd refresh outputs.
"""
import csv, re
from pathlib import Path

HERE    = Path(__file__).resolve().parents[1]
OUTPUTS = HERE / "outputs"
LIFTS   = OUTPUTS / "lifts.csv"
PAT     = re.compile(r"^lift_([a-z]+)_([a-z0-9]+)\.csv$")


def melt():
    rows = []
    for p in sorted(OUTPUTS.glob("lift_*.csv")):
        m = PAT.match(p.name)
        if not m:
            continue
        model, project = m.group(1), m.group(2)
        with p.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Drop the "project" column if present (filename is source of truth).
                row.pop("project", None)
                for metric, value in row.items():
                    if value is None or value == "":
                        continue
                    rows.append((model, project, metric, value))
    return rows


def main():
    rows = melt()
    rows.sort()  # deterministic
    with LIFTS.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "project", "metric", "value"])
        w.writerows(rows)
    n_files   = len(list(OUTPUTS.glob("lift_*.csv")))
    n_models  = len({r[0] for r in rows})
    n_proj    = len({r[1] for r in rows})
    n_metrics = len({(r[0], r[2]) for r in rows})
    print(f"Wrote {LIFTS.relative_to(HERE)}")
    print(f"  {len(rows)} rows from {n_files} source CSVs")
    print(f"  {n_models} models × {n_proj} projects × {n_metrics} (model, metric) pairs")


if __name__ == "__main__":
    main()
