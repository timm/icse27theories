# paper/ — MYTHS inference layer

Reproducible artifact for ICSE 2027. Reviewer types `make`, sees the
five F-findings in <30 seconds. No R, no Perceval, no kaiaulu.

## Files

- `sd.py` (~44 KB) — **35** SD models as `Model(init, step, y, rq, ctrl)`
  namedtuples. UPPER inputs / lower params naming convention. Includes
  the engine: `run()`, `verdict()`, `opt()`, `stress(target='inputs'|'params'|'all')`.
- `tests.py` — 9-test V&V bank: `boundary_adq`, `anomaly_check`,
  `extreme_eqn`, `mr_zero_input`, `mr_monotone`, `mr_dt_halving`,
  `mr_bound_consist`, `mr_scale`. Plus `stress_matrix()` for 2×2 cell
  classification.

## Scorecard structure (standard, all 35 model pages)

Every `docs/models/<name>.html` carries the same 18-row V&V scorecard
in Panel 5. Auto-derived from CSVs by `docs/scripts/gen_rich.py`'s
`render_scorecard_table()`. Rows divide into two tiers:

**Tier 1 — Prudence (model survives sanity)**
- 8 structural tests from `full_audit.csv` cols 12–19:
  `boundary_adq`, `anomaly_check`, `extreme_eqn`, `mr_zero_input`,
  `mr_monotone`, `mr_dt_halving`, `mr_bound_consist`, `mr_scale`.

**Tier 2 — Effect claims (cell typology + verdicts)**
- `rq() single-shot` + gap (from `verdict`)
- `rq_n N=100 + Cliff's δ / KS` + gap_n + sd0/sd1/ε (from `verdict_n`)
- `stress(inputs)` count /200 + `stress(params)` count /200
- `2×2 cell` (universal / process-conditional / world-conditional / fragile)

**Tier 3 — Data-tier prudence (auto from lift CSVs)**
- `param_plausibility` — count of in_range / at_boundary / out_of_range
  rows in `boundary_check.csv` for this model. PASS / warn / FAIL.
- `boundary_adq_data` — PASS iff any lifted value reaches or exceeds
  declared `[lo, hi]`. warn iff all strictly inside (range not tested
  at edges). N/A iff no lift rows.
- `calibrated_rq_rerun` — from `calibrated_verdicts.csv`. Reports
  CONFIRM stable, REFUTE-changed, or N/A (no overridable params).
- `family_member_coherence` — project count from `lifts.csv`. Sign
  tally is hand-tuned per model; only `brooks.html` carries a sign
  count today.
- `behavior_reproduction` — `not run` globally; needs monthly historical
  ground-truth vs sim trajectory.

Model pages without lifts (e.g. `aiwork`, `burnout`, `aidebt`,
`teamtopo`, `flaky`, `micro`, `sir`, `diapers`) display `N/A · no
lift rows` honestly on the data-tier rows. This makes the "structurally
absent data category" finding visible at scorecard glance.

Two pages are hand-tuned (`manual=True` in `gen_rich.py`):
- `brooks.html` — full hand-written prose throughout; data-tier rows
  conform to the same 5-row schema.
- `diapers.html` — toy demonstrator; no lift relevance.
- `full_audit.py` — runs the stress matrix + 9-test bank across all 35
  models. Writes `outputs/full_audit.csv`.
- `calibrate.py` — CSV-anchored verdicts. Reads `outputs/lift_<model>_<project>.csv`,
  substitutes lifted values into `model.init`, re-runs `rq()`, writes
  `outputs/calibrated_verdicts.csv`.
- `cross_project.py` — per-(model, project) metric table → `outputs/cross_project.csv`.
- `boundary_check.py` — flags lifted params outside their `[lo, hi]`
  range (F0 source). Writes `outputs/boundary_check.csv`.
- `outputs/` — every CSV. ~65 files. Including the lift CSVs whose
  upstream extraction lives in `extract/`.
- `Makefile` — targets to run all of the above + per-finding reports.

## The 35 models

Year-tagged. Diapers is the toy demonstrator.

| Year | Model       | Cell                 | Lift status   |
|-----:|-------------|----------------------|---------------|
| 2024 | aiwork      | universal            | dark          |
| 2024 | aidebt      | world-conditional    | dark          |
| 2024 | burnout     | process-conditional  | dark          |
| 2022 | congruence_motif | universal       | pipeline-ready (Mauerer 2022 STC; companion to congruence) |
| 2019 | teamtopo    | universal            | dark          |
| 2018 | dora        | universal            | 7/8           |
| 2018 | deprot      | universal            | pipeline-ready|
| 2017 | ossfail     | world-conditional    | pipeline-ready|
| 2016 | diapers     | process-conditional  | toy           |
| 2015 | micro       | process-conditional  | dark          |
| 2014 | flaky       | universal            | dark          |
| 2014 | ctxswitch   | process-conditional  | pipeline-ready|
| 2011 | ownership   | world-conditional    | pipeline-ready|
| 2010 | orgchurn    | process-conditional  | pipeline-ready|
| 2008 | brooksq     | fragile              | 7/8           |
| 2008 | congruence  | universal            | 3/8           |
| 2006 | mirroring   | process-conditional  | pipeline-ready|
| 2000 | learn       | process-conditional  | 8/8           |
| 1999 | linus       | universal            | pipeline-ready|
| 1992 | archpat     | fragile              | 2/8           |
| 1992 | debt        | universal            | 5/8           |
| 1992 | pareto      | process-conditional  | pipeline-ready|
| 1991 | rework      | universal            | 7/8           |
| 1991 | defmap      | universal            | 7/8           |
| 1990 | limits      | process-conditional  | pipeline-ready|
| 1981 | costchange  | universal            | pipeline-ready|
| 1981 | scope       | fragile              | pipeline-ready|
| 1980 | entropy     | universal            | pipeline-ready|
| 1979 | bugs        | process-conditional  | 3/8           |
| 1975 | brooks      | fragile              | 8/8           |
| 1975 | coordn2     | process-conditional  | pipeline-ready|
| 1968 | successful  | process-conditional  | pipeline-ready|
| 1961 | little      | universal            | pipeline-ready|
| 1927 | sir         | universal            | 0/8           |

Counts (from `paper/outputs/full_audit.csv` post 2026-05-25 re-run):
23 universal · 7 process-cond · 4 fragile · 1 world-cond.

## 2×2 stress matrix typology

After `stress_matrix()` each model lands in one cell:

```
                  robust to inputs    fragile to inputs
robust to params  universal           world-conditional
fragile to params process-conditional fragile
```

## Headline findings (F0..F4)

- **F0** — 5 model parameters fail boundary-adequacy on multiple projects.
- **F1** — `brooksq.leak_rate` exceeds `hi=0.5` on 7/8 projects.
- **F2** — `debt.pay_rate` convergent across 5 Java projects (0.36–0.59).
- **F3** — Brooks effect varies 11× across 8 projects.
- **F4** — brooksq quality thesis split: Ambari supports, Helix neutral,
  junit5 refutes.

## Reproducing from scratch

```bash
cd paper
python3 full_audit.py        # writes outputs/full_audit.csv
python3 cross_project.py     # writes outputs/cross_project.csv
python3 boundary_check.py    # writes outputs/boundary_check.csv
python3 calibrate.py         # writes outputs/calibrated_verdicts.csv
```

The lift CSVs that `calibrate` / `cross_project` / `boundary_check`
consume are committed in `outputs/`. They were produced by the
extraction pipeline in `../extract/`. Reproducing the lifts themselves
is documented there.

## Caveats worth keeping

- `archpat.pat_strength` is in `init` but unused in `step()`. Open
  question for Rick whether it should drive the step equation.
- `aidebt` has a regime crossover at `tmax ≈ 26` with default params.
  Default `rq()` reports REFUTE at `tmax=20`; CONFIRM at `tmax≥30`.
- `archpat` leverage parameters from prior sensitivity sweep:
  `gen_pat` (32%), `pay_rate` (22%), `born_leg` (20%). `decay_rate`
  (Perry-Wolf erosion) only 5.7%.
- `bugs.gokumoto_a` is fitted via grid search inside the lift, not via
  SciPy — keeps the artifact dependency-free.
