# data/dropzone/ — refresh entry point

Drop new or updated artifacts here. Then run `make refresh` (from
project root) — the whole site rebuilds and the gates run.

## What to drop

### 1. Lift CSVs (the common case)

Drop files named `lift_<model>_<project>.csv` directly here:

```
data/dropzone/lift_brooks_helix.csv
data/dropzone/lift_archpat_ambari.csv
data/dropzone/lift_congruence_motif_helix.csv
```

Filename pattern is enforced:
- `model` = one of the 35 SD models (`paper/sd.py`)
- `project` = lowercase project name (helix, junit5, ambari, kaiaulu,
  airflow, openssl, tomcat, camel, ...)

Refresh moves them into `paper/outputs/`, melts them into
`lifts.csv`, re-runs `boundary_check` + `calibrate` + `cross_project`
+ `full_audit` + `gen_rich`, and prints a before/after diff.

### 2. Raw project data (heavy path)

Drop a whole project subdir:

```
data/dropzone/<project>/git_repo/
data/dropzone/<project>/mbox/
data/dropzone/<project>/jira/
```

Refresh moves the subdir to `data/<project>/` and triggers
`make render` on the matching `extract/lifts/*.Rmd` notebooks (which
need `Rscript` + perceval + scc + RefactoringMiner + the kaiaulu R
package installed). Output: per-project lift CSVs → same downstream
chain as path #1.

## What NOT to drop

- Generated CSVs (`full_audit.csv`, `boundary_check.csv`, etc.) —
  these are products, not inputs.
- The `lifts.csv` long-form melt — refresh re-builds it from the
  per-project source CSVs.
- Anything matching `.DS_Store`, `*.zip`, `*.bak`, `.git/`.

## How to invoke

From project root:

```bash
make refresh         # full refresh (lift CSVs + raw data path)
make refresh-lifts   # lift CSVs only (skips R toolchain)
```

Both targets print a diff summary at the end.
