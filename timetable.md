# TIMETABLE.md — methodology log: "go" → "model insight"

> **READ THIS FIRST.** Hours fall into two categories:
> - **Pre-2026-05-24** = RECONSTRUCTION ESTIMATES from a claude.ai
>   backfill (no wall-clock was logged at the time). Treat as
>   placeholders. The *status* of each cell (which step happened) is
>   real; the *durations* are not.
> - **2026-05-24 onward** = LOGGED to nearest 0.5h as work happens.
>   These are the trustworthy numbers going forward.
>
> Replace estimated numbers with logged times as opportunities arise.

## Legend

- `N`    estimated or logged hours
- `0*`   automated / bulk — marginal per-model time ≈ 0; cost sits
         in the shared `sd.py` / `tests.py` rows (no double-count)
- `—`    never attempted before 2026-05-24
- `n/a`  structurally impossible (model can't reach this step)
- `~`    prefix = partial / skeleton only
- **bold** = logged 2026-05-24 work; all unbold = claude.ai
  reconstruction

## Steps

S0 thesis+cite · S1 code Model in sd.py · S2 structure verify + RQ ·
S3 extreme conditions · S4 dimensional (`dim_check` — NOT BUILT) ·
S5 rq verdict · S6 stress matrix · S7 identify data tool ·
S8 install tool · S9 fetch dataset · S10 derived data → CSV/JSON ·
S11 write lift.Rmd · S12 run lift → outputs/lift_<m>_<proj>.csv

Future steps S13–S20 (param plausibility, boundary adq, calibrated
rq rerun, behavior reprod/pred, family-member, verdict write-up,
Carlos PR review).

**Update 2026-05-24**:
- **S3+S5+S6 sweep DONE for all 18 models** via `scripts/full_audit.py`
  → `outputs/full_audit.csv`. Stress typology populated: 10 universal,
  5 process-conditional, 3 fragile, 1 world-conditional. 9-test bank
  pass rate ~91% (most FAILs are mr_monotone or boundary_adq on
  long-horizon ctrl sweeps).
- **S13 + S14 DONE for 8 models** via `scripts/boundary_check.py` →
  `outputs/boundary_check.csv`. Three findings:
    - brooksq.leak_rate = 0.571 **out_of_range** (model hi=0.5)
    - archpat.Legacy   = 384   **out_of_range** (model hi=200)
    - learn.train_rate = 1.0   **at_boundary** (yearly-slice method
      overstates rate)
- **S15 (calibrated rq rerun) DONE for 8 models** via
  `scripts/calibrate.py` → `outputs/calibrated_verdicts.csv`. All
  eight retain CONFIRM at default + calibrated; gap magnitudes
  shift meaningfully:
    - brooksq: -45.9 → -58.7 (Helix's leak_rate strengthens thesis)
    - debt:    -56.7 → -8.83 (Helix's pay_rate blunts thesis)
    - dora:    -45.4 → -20.0 (low arrival_rate eases pressure)
    - learn:   -5.28 → -6.54 (more Jr → more starvation when Sr=0)
    - archpat: +229  → +390  (Helix's bigger Legacy strengthens repair)
    - brooks/rework/defmap: no direct override possible (notes in CSV)

## Per-model table

| model      | S0  | S1  | S2  | S3 | S4 | S5 | S6  | S7  | S8     | S9     | S10    | S11      | S12     | total | notes |
|------------|-----|-----|-----|----|----|----|-----|-----|--------|--------|--------|----------|---------|-------|---|
| diapers    | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | toy demonstrator; not informable by design |
| brooks     | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.5**| **0.1**| —      | ~1.0     | **0.5** | **~4.1** | **lift_brooks_helix.csv** ✓ brooks_tax_median = 0.113 (thesis ✓). S11 skeleton predated today; today S8/S9/S12 + bug fixes to S11 |
| bugs       | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | —      | 0*     | —      | —        | —       | ~2.0  | Goel-Okumoto; S7=JIRA (kaiaulu-native); not lifted yet |
| debt       | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.0**| **0.0**| **0.5**| **0.5**  | **0.5** | **~3.0** | **lift_debt_helix.csv** ✓ pay_rate = 0.59 ≫ born = 0.25 (Helix pays down) |
| sir        | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | epidemic model; no SE data map |
| rework     | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.0**| **0.0**| **0.0**| **0.5**  | **0.5** | **~2.5** | **lift_rework_helix.csv** ✓ failrate = 0.019 (safe regime) |
| learn      | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.0**| **0.0**| **0.0**| **0.5**  | **0.5** | **~2.5** | **lift_learn_helix.csv** ✓ Jr=43, Tr=21, Sr=9 (top-heavy junior); train_rate=1.0 **at boundary** |
| brooksq    | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.5**| **0.1**| **0.5**| **0.5**  | **0.5** | **~3.6** | **lift_brooksq_helix.csv** ✓ brooks side ✓ + inj_increase = 0 (quality thesis ✗) |
| defmap     | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.0**| **0.0**| **0.0**| **0.5**  | **0.5** | **~2.5** | **lift_defmap_helix.csv** ✓ tst_proxy = 0.375 (low-tst bad regime; 876 leaked vs 421 caught) |
| aiwork     | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | no AI authorship attribution; structurally dark |
| flaky      | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | no CI flake logs |
| dora       | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | 0.5 | **0.0**| **0.0**| **0.0**| **0.5**  | **0.5** | **~2.5** | **lift_dora_helix.csv** ✓ batch = 73.9 (high-batch), cfr = 0.049, MTTR ≈ 88d |
| micro      | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | no service-architecture data |
| teamtopo   | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | no org-chart data |
| burnout    | 0.5 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~1.5  | no HR/wellbeing data |
| aidebt     | 1.0 | 0.5 | 0.5 | 0* | —  | 0* | 0*  | n/a | n/a    | n/a    | n/a    | n/a      | n/a     | ~2.0  | richer S0 (note_aidebt.md, regime crossover tmax≈26); no AI attribution → S7+ n/a; paper's "methodological case" |
| archpat    | 1.0 | 0.5 | 0.5 | 0* | —  | 0* | 0.5 | 0.5 | **0.5**| 0*     | **1.0**| ~1.5     | **0.5** | **~5.5** | **lift_archpat_helix.csv** ✓ Patterned=149, Legacy=384, Drift=0, Other=1452 (5 helix modules). **pattern4 CLI breakthrough** — IS callable via `java -jar pattern4.jar -target <classes> -output <xml>`. Maven + Helix compile + pattern4 + multi-module aggregation all ran in this session. Calibrated archpat gap +229 → +390 (Helix's larger Legacy strengthens repair thesis). |
| congruence | 0.5 | **0.3** | **0.1** | **0** | —  | **0** | **0** | 0.5 | 0.5    | 0*     | 0*     | —        | —       | **~1.9** | **SD model coded today** (broker_loss ctrl; CONFIRM gap -314.85, strongest in bank). Lift blocked: mbox not on this machine (was on Claude.ai sandbox). S10 reusable when mbox fetched |

**Per-model subtotal (pre-2026-05-24 est): ~35.5h**
**Per-model logged 2026-05-24: ~6.7h** (sums of bold cells above —
includes shared install/data work double-attributed for traceability;
see grand totals below for de-duplicated figure)

## Shared infrastructure

These don't map cleanly to per-model S0–S12. Hours lumped here.

| artifact                                 | maps to              | hours    | notes |
|------------------------------------------|----------------------|----------|---|
| sd.py engine (run, verdict, opt, stress) | S1/S5/S6 machinery   | ~10.0    | substrate for all 17 models; biggest single cost |
| tests.py 9-test bank                     | S3/S5/S6 machinery   | ~8.0     | boundary/anomaly/extreme + 5 metamorphic; runs all 17 in ~1.5s |
| kaiaulu schema audit (kaiaulu_notes/)    | S7/S10 prep          | ~4.0     | read 7 R source files; found 5 kaiaulu bugs |
| feasibility scorecard                    | S7 (all models)      | ~3.5     | 17-model triage + open-tool survey |
| Helix data exploration                   | S9 prep              | ~3.0     | extract + structure understanding |
| radio_silence smell port                 | S10 (congruence)     | ~5.0     | R→Python port; reusable across models |
| **2026-05-24 install round**             | S8 (shared)          | **~1.0** | logged: PyDriller venv, Java/Temurin, R 4.6, kaiaulu pkg, RefactoringMiner, pattern4.jar download |
| **2026-05-24 derived data**              | S10 (shared)         | **~0.5** | logged: 1297 SZZ pairs (Python script, ~12s) + 21945 refactorings (RefactoringMiner pass, ~7min unattended) |
| **2026-05-24 tools.yml + helix.yml**     | S8 (shared)          | **~0.5** | logged: kaiaulu canonical schema; date-format + identity_match bug fixes propagated to all .Rmd |

**Shared subtotal: ~33.5h estimated + ~2.0h logged = ~35.5h**

## Grand totals

| bucket                            | hours  | source |
|-----------------------------------|--------|---|
| pre-2026-05-24 per-model          | ~35.5  | claude.ai estimate |
| pre-2026-05-24 shared             | ~33.5  | claude.ai estimate |
| 2026-05-24 logged (de-duplicated) | ~3.5   | this session — shared install + 6 lift-specific runs |
| **total to date**                 | **~72.5** | mixed |

## Breakdown commentary

Pre-data work (S0–S6 across 17 models) was front-loaded into a shared
substrate. The framework third (sd.py + tests.py + schema audit ≈ 22h)
pays off everywhere; per-model S0–S2 bulk ≈ 25h wrote 17 models
together so marginal cost per model is minutes, not hours. Helix-
specific prep (data extract ≈ 3h, feasibility ≈ 3.5h, radio_silence
port ≈ 5h) plus two lift skeletons (brooks + archpat ≈ 2.5h) bring
pre-2026-05-24 to ~69h.

The 2026-05-24 session added **6 lifts end-to-end on Helix** —
brooks, brooksq, debt, rework, defmap, dora — in **~3.5h logged**.
That cost includes one shared install round, one shared derived-data
pass, plus six per-model runs at ~0.5h each.

**Marginal cost pattern**: first lift in a session = install overhead
+ first-pipeline-bug debugging (Perceval date-format mismatch,
identity_match needing new `label` arg, tools.yml schema vs canonical
kaiaulu). Subsequent lifts on the same dataset = lift.Rmd write +
helper functions + one run. So the sixth lift cost roughly 10% of the
first.

## Status table — the real signal

What actually happened, ignoring hour estimates:

| model      | pre-data done | data tool ID'd | tool installed       | data on disk | lift written | **lift ran ✓** |
|------------|:-:|:-:|:-:|:-:|:-:|:-:|
| diapers    | ✓ | n/a | n/a | n/a | n/a | n/a |
| brooks     | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| bugs       | ✓ | ✓   | —   | —   | —   | — |
| debt       | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| sir        | ✓ | n/a | n/a | n/a | n/a | n/a |
| rework     | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| learn      | ✓ | ✓   | (shared) | (shared) | ✓ | **✓** |
| brooksq    | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| defmap     | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| aiwork     | ✓ | n/a | n/a | n/a | n/a | n/a |
| flaky      | ✓ | n/a | n/a | n/a | n/a | n/a |
| dora       | ✓ | ✓   | ✓   | ✓   | ✓   | **✓** |
| micro      | ✓ | n/a | n/a | n/a | n/a | n/a |
| teamtopo   | ✓ | n/a | n/a | n/a | n/a | n/a |
| burnout    | ✓ | n/a | n/a | n/a | n/a | n/a |
| aidebt     | ✓ | n/a | n/a | n/a | n/a | n/a |
| archpat    | ✓ | ✓   | ✓ (pattern4 CLI works) | ✓ + compiled bytecode | ✓ | **✓** |
| congruence | ✓ (today) | ✓ | ✓ | (mbox local?) | — | — |

**8 of 18 lifted on Helix in one session** (brooks, brooksq, debt,
rework, defmap, dora, learn, archpat). 7 structurally dark (data
missing field-wide). 1 SD model coded today but lift blocked at S9
(congruence — mbox not on this machine). **1 untouched at S12:
bugs** (needs JIRA dump from Carlos's Drive).

## Caveats

1. **Numbers ≠ measurements.** Pre-2026-05-24 hours are claude.ai
   reconstructions from prior conversations, not logged time. Don't
   cite them. Cite status, not duration.
2. **`0*` is real**, not a typo. Automation means the per-model cost
   of running S3/S5/S6 is fractions of a second; the cost is in
   building the engine (counted once in the shared row).
3. **S4 (dimensional consistency) was never built**. Listed for
   completeness; not blocking any current work.
4. **archpat hours include a dead-end**. Today's session discovered
   the canonical Concordia pattern4.jar is GUI-only with no CLI main
   method, and needs compiled Java bytecode (`mvn install`-built)
   anyway. The S8 logged hour reflects "downloaded jar + discovered
   blocker" — not a working install.
5. **The 7 structurally-dark models** (aiwork, flaky, micro, teamtopo,
   burnout, aidebt, sir/diapers) lose hours at S7+ to `n/a` not
   because they're cheap but because they're impossible. Their
   methodological-case write-up (paper section on "framework
   expresses; no data calibrates") is *uncounted* and will take
   real time.
6. **Carlos PR review (would-be S20)** is *uncounted* and will
   dominate the non-coding cost once lifts start landing as kaiaulu
   PRs.
7. **Hour-vs-insight ratio misleads.** A 0.5h lift might produce a
   falsification finding (e.g. brooksq's `inj_rate_increase = 0`
   median) that's worth a paper section. Hours don't measure value,
   just throughput.
8. **Today's per-model "0.0" cells** mean "the work was fully shared
   with another model's run." E.g. rework/defmap/dora/debt's S8/S9/S10
   = 0.0 because they ride on top of brooksq's SZZ pass and debt's
   RefMiner pass. The non-shared work is the lift.Rmd + helper
   functions (S11) + the run (S12).

## Update protocol

- Round to nearest 0.5h.
- When a new step completes for a model, update both the model row
  AND the session log below.
- Don't wait until end-of-session — update as work happens.
- If a step is decisively unreachable, mark `n/a` with one-line
  reason.

## Session log

### 2026-05-24

Logged **~5h** active session time. Outputs:
- **pattern4.jar CLI breakthrough** — the earlier "GUI-only" memory
  note was wrong. Working invocation:
  `java -jar pattern4.jar -target <classes-dir> -output <xml>`.
  Detected 147 pattern instances on helix-core (State 57, Adapter
  42, Singleton 24, etc).
- **lift_archpat_helix.csv** — Patterned=149, Legacy=384, Drift=0,
  Other=1452 (5 helix modules aggregated, n=1985 files). 8th lift
  complete. archpat now in S13/S14/S15 pipelines too.
- **congruence SD model coded** (sd.py +35 lines); CONFIRM gap
  -314.85; ALL_MODELS now 18-strong. Lift requires mbox download.
- 7 lift CSVs in `outputs/` (brooks, brooksq, debt, rework, defmap,
  dora, learn)
- `outputs/boundary_check.csv` — S13/S14 pass on 7 models;
  1 out_of_range (brooksq.leak_rate), 1 at_boundary (learn.train_rate)
- `outputs/calibrated_verdicts.csv` — S15 calibrated `rq()` rerun on
  7 models; all retain CONFIRM, gaps shift meaningfully (debt
  thesis blunted ~7x, brooksq thesis strengthened ~30%)
- 1 explicit falsification result: brooksq quality thesis NOT
  supported on Helix (`inj_rate_increase = 0` median)
- 2 thesis-regime confirmations: defmap (low-tst bad regime),
  dora (high-batch bad regime)
- 2 thesis-not-triggered: rework (safe failrate), debt (active paydown)
- Shared install + derived data + tools.yml/helix.yml (reusable)
- Discovery: pattern4.jar is GUI-only without CLI main; archpat
  empirical path harder than May-19 estimate suggested
- Discovery: brooksq's model declared `leak_rate hi = 0.5` doesn't
  span observed Helix reality (0.571) — paper material
- Memory persisted (5 files in `~/.claude/projects/.../memory/`)
