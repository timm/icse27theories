# SD framework files

These three files live in Tim's working directory (last touched May 1
2026). They are NOT bundled in this handoff because they live with
the rest of his per-machine working copy. When opening this project
in Claude Code, copy them in:

- `sd.py` (~24KB) — 17 SD models as Model(init, step, y, rq, ctrl)
  namedtuples. UPPER inputs / lower params naming convention.
  Includes run(), verdict(), opt(), stress(target='inputs'|'params'|'all').
- `tests.py` (~11KB) — 9-test bank: boundary_adq, anomaly_check,
  extreme_eqn, mr_zero_input, mr_monotone, mr_dt_halving,
  mr_bound_consist, mr_scale. Plus stress_matrix() for 2×2 cell
  classification.
- `results.txt` — last full run with verdict tables. Runs in ~1.5s
  on all 17 models.

The 17 models, in order: diapers, brooks, bugs (Goel-Okumoto), debt
(Cunningham), sir, rework, learn, brooksq, defmap, aiwork, flaky,
dora, micro, teamtopo, burnout, aidebt, archpat.

A proposed 18th — `congruence` — is referenced in STATE.md as the
cheapest new model to build given the radio-silence pipeline that
already works.

## 2×2 stress matrix typology

After running stress_matrix() each model lands in one cell:

```
                 robust to inputs    fragile to inputs
robust to params  universal          world-conditional
fragile to params  process-conditional fragile
```

- `aidebt` is process-conditional (the live empirical debate)
- `archpat` is fragile (most random param draws → neutral verdict)
- worked examples were chosen to span the cells

## Notes worth keeping

- archpat's `pat_strength` is defined in init but unused in step().
  Flag for Ric whether this should drive the step equation.
- aidebt has a regime crossover at tmax ≈ 26 with current params
  (worked example doc: note_aidebt.md in working dir).
- archpat leverage parameters: gen_pat (32%), pay_rate (22%),
  born_leg (20%). decay_rate (Perry-Wolf erosion) only 5.7%.

## Recommended additions in Claude Code

- `note_brooks.md` — to be written alongside `lifts/lift_brooks.Rmd`
- `note_archpat.md` — already exists in working dir, refresh after
  pattern4.jar-based archpat lift completes
- `congruence.py` — new model file when ready
