# Evidence card: `aiwork`

**Claim.** full AI assistance (ai=1) lowers kept code at t=20.  
**Lever.** `ai` 0 -> 1; expected y down.  
**Support factors.** gen_boost, churn_mult, verify_drag, mature_rate, churn_base.  
**Sources.** GitClear 2024; METR 2025; Peng et al. 2023; sd.aiwork

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units declared | every var has units |
| PASS | dead parameters | all params live |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 3 extremes: gen_boost=2:REFUTE, verify_drag=0:neutral, mature_rate=0:neutral |
| FAIL | clamp dependence | 26% of prior backgrounds escape declared bounds; 24% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=1:-51.7 dt=.25:-51.8 (0%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| PASS | time-horizon adequacy | t=15:CONFIRM(-34); t=20:CONFIRM(-52); t=40:CONFIRM(-122); t=80:CONFIRM(-264) |
| PASS | dose-response monotone | gaps 0:+0, 0.166667:-9, 0.333333:-17, 0.5:-26, 0.666667:-34, 0.833333:-43, 1:-52 |
| PASS | mechanism knock-out | channels ['churn_mult', 'verify_drag'] neutral -> REFUTE (+38.4) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 72.5, 'REFUTE': 22.3, 'neutral': 5.2} |
| PASS | scale x2 (MR2) | CONFIRM(-52) -> CONFIRM(-52) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 100% / 0% / 0% | -52 [-60, -43] |
| triangular over declared ranges | 88% / 8% / 4% | -39 [-100, +17] |
| uniform over declared ranges | 74% / 21% / 5% | -26 [-113, +66] |

## 3. What decides it? (tree on prior draws, base rate 89% CONFIRM, accuracy 93%)

Importance: `gen_boost` 0.42, `verify_drag` 0.40, `mature_rate` 0.09, `churn_mult` 0.07, `churn_base` 0.02

```
|--- verify_drag <= 0.343
|   |--- gen_boost <= 0.829
|   |   |--- churn_mult <= 1.319
|   |   |   |--- class: 1
|   |   |--- churn_mult >  1.319
|   |   |   |--- class: 1
|   |--- gen_boost >  0.829
|   |   |--- mature_rate <= 0.276
|   |   |   |--- class: 1
|   |   |--- mature_rate >  0.276
|   |   |   |--- class: 0
|--- verify_drag >  0.343
|   |--- gen_boost <= 1.348
|   |   |--- churn_base <= 0.071
|   |   |   |--- class: 1
|   |   |--- churn_base >  0.071
|   |   |   |--- class: 1
|   |--- gen_boost >  1.348
|   |   |--- verify_drag <= 0.475
|   |   |   |--- class: 1
|   |   |--- verify_drag >  0.475
|   |   |   |--- class: 1
```

One-at-a-time tipping points (others at default):

- `gen_boost`: CONFIRM->neutral@1.1, neutral->REFUTE@1.3
- `verify_drag`: neutral->CONFIRM@0.05
- `mature_rate`: neutral->CONFIRM@0.025
- no flip inside declared range: churn_mult, churn_base

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| vibe_coding | accept AI output with little review | REFUTE (+50) | 0% / 100% / 0% | +49 [+28, +74] |
| review_gate | strict review: slow but low churn | CONFIRM (-57) | 100% / 0% / 0% | -57 [-73, -41] |
| boilerplate | greenfield CRUD/tests: AI is very fast | REFUTE (+94) | 0% / 100% / 0% | +93 [+73, +117] |
| legacy_expert | METR setting: experts in big familiar repos | CONFIRM (-73) | 100% / 0% / 0% | -73 [-82, -64] |
| copilot_rct | Peng 2023-like: +55% speed, modest churn | REFUTE (+18) | 0% / 99% / 1% | +18 [+9, +28] |
| half_adoption | ai=0.5 instead of 1 | CONFIRM (-26) | 100% / 0% / 0% | -26 [-30, -21] |
| short_sprint | deadline t=5: pipeline delay dominates | CONFIRM (-5) | 100% / 0% / 0% | -5 [-6, -3] |
| slow_review_pipe | code sits in Wip longer (mature 0.05) | CONFIRM (-27) | 100% / 0% / 0% | -27 [-31, -22] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| sd.aiwork | reference | CONFIRM (-52) | 100% / 0% / 0% | 88% / 8% / 4% |
| team learns AI | verify drag decays, tau=8 ticks | CONFIRM (-23) | 100% / 0% / 0% | 69% / 24% / 7% |
| churn costs time | each churned item costs 0.5 items of capacity | CONFIRM (-54) | 100% / 0% / 0% | 86% / 9% / 5% |
| latent defects | churn leaves defects that tax capacity | CONFIRM (-52) | 100% / 0% / 0% | 93% / 4% / 3% |

## 6. Will it work *here*? (real-project placement)

### aider

Population: aider: commits by Paul Gauthier 2024-07-01..2025-07-01, AI = /\(aider\)/

Measured: (from saved pairs); blamed pairs: AI 428, human 373 (dropped 0 renamed/deleted); strata used [(3, 20), (21, 80)]; 14-day churn: AI 49.7%, human 37.2%; churn_mult = ratio - 1 = 0.35 [0.18, 0.54]

**P(claim holds | evidence)** = 64% / 26% / 9%, gap -16 [-83, +60]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `verify_drag` gain 0.336 [0.2, 0.55, 0.83, 1.0]
- `gen_boost` gain 0.151 [0.92, 0.73, 0.59, 0.34]
- `churn_base` gain 0.009 [0.56, 0.64, 0.67, 0.71]
- `mature_rate` gain 0.002 [0.67, 0.67, 0.61, 0.62]

Caveats (the long chain from data to parameter):

- Within-author, within-period comparison controls author skill and project phase, not task type: the author chooses which tasks to give the AI (selection on difficulty).
- GitClear churn construct: lines rewritten/removed within 14 days; moved lines count as churned (blame -w, no -C).
- Pairs whose file was renamed or deleted by +14d are dropped (unknown survival), biasing churn down for both arms.
- Only churn_mult is measured. gen_boost and verify_drag (the factors that decide the verdict) are invisible in git history.
- AI attribution is self-declared by the tool/author; unlabelled AI use in the 'human' arm would shrink the measured difference.

### aider2023

Population: aider2023: commits by Paul Gauthier, paul-gauthier 2023-05-01..2024-07-01, AI = /\(aider\)/

Measured: (from saved pairs); blamed pairs: AI 197, human 475 (dropped 0 renamed/deleted); strata used [(3, 20)]; 14-day churn: AI 53.2%, human 39.9%; churn_mult = ratio - 1 = 0.32 [0.16, 0.52]

**P(claim holds | evidence)** = 64% / 27% / 9%, gap -16 [-83, +61]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `verify_drag` gain 0.351 [0.2, 0.52, 0.85, 1.0]
- `gen_boost` gain 0.142 [0.91, 0.73, 0.58, 0.35]
- `churn_base` gain 0.008 [0.57, 0.62, 0.66, 0.71]
- `mature_rate` gain 0.002 [0.66, 0.67, 0.61, 0.62]

Caveats (the long chain from data to parameter):

- Within-author, within-period comparison controls author skill and project phase, not task type: the author chooses which tasks to give the AI (selection on difficulty).
- GitClear churn construct: lines rewritten/removed within 14 days; moved lines count as churned (blame -w, no -C).
- Pairs whose file was renamed or deleted by +14d are dropped (unknown survival), biasing churn down for both arms.
- Only churn_mult is measured. gen_boost and verify_drag (the factors that decide the verdict) are invisible in git history.
- AI attribution is self-declared by the tool/author; unlabelled AI use in the 'human' arm would shrink the measured difference.

