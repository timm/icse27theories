# Evidence card: `brooks_late`

**Claim.** adding 10 people to a project that is already late (backlog 1000, 10 vets can do ~775 by t=20) makes it finish later.  
**Lever.** `boost` 0 -> 10; expected y down.  
**Support factors.** Vet, Todo, comm_coef, train_coef, prod_rate, mature_rate, hire_at.  
**Sources.** Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks; outcome = completion time

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units & dimensions | every equation consistent; literals: literal 1 + tick, literal 1 - dev |
| PASS | dead parameters | all params live |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 6 extremes: Vet=0:REFUTE, Vet=100:neutral, Todo=0:neutral, comm_coef=0.05:neutral, prod_rate=0.1:neutral, prod_rate=20:neutral |
| PASS | clamp dependence | 1% of prior backgrounds escape declared bounds; 0% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=1:-87.8 dt=0.25:-90.3 (3%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| PASS | time-horizon adequacy | t=45:CONFIRM(-45); t=80:CONFIRM(-88); t=160:CONFIRM(-138); t=320:CONFIRM(-139) |
| PASS | dose-response monotone | gaps 0:+0, 16.6667:-100, 33.3333:-100, 50:-100, 66.6667:-100, 83.3333:-100, 100:-100 |
| PASS | mechanism knock-out | channels ['comm_coef', 'train_coef'] neutral -> neutral (+1.0) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 5.2, 'REFUTE': 0.7, 'neutral': 94.1} |
| PASS | scale x2 (MR2) | CONFIRM(-88) -> CONFIRM(-14) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 100% / 0% / 0% | -84 [-102, -34] |
| triangular over declared ranges | 11% / 0% / 88% | +0 [-89, +0] |
| uniform over declared ranges | 6% / 1% / 93% | +0 [-41, +0] |

## 3. What decides it? (tree on prior draws, base rate 12% CONFIRM, accuracy 93%)

Importance: `Vet` 0.73, `comm_coef` 0.19, `Todo` 0.07

```
|--- Vet <= 10.426
|   |--- Todo <= 659.701
|   |   |--- class: 0
|   |--- Todo >  659.701
|   |   |--- prod_rate <= 7.673
|   |   |   |--- class: 1
|   |   |--- prod_rate >  7.673
|   |   |   |--- class: 1
|--- Vet >  10.426
|   |--- Vet <= 19.489
|   |   |--- comm_coef <= 0.012
|   |   |   |--- class: 1
|   |   |--- comm_coef >  0.012
|   |   |   |--- class: 0
|   |--- Vet >  19.489
|   |   |--- comm_coef <= 0.004
|   |   |   |--- class: 0
|   |   |--- comm_coef >  0.004
|   |   |   |--- class: 0
```

One-at-a-time tipping points (others at default):

- `Vet`: REFUTE->CONFIRM@5, CONFIRM->neutral@22.5
- `Todo`: neutral->CONFIRM@450
- `comm_coef`: CONFIRM->neutral@0.0225
- `prod_rate`: neutral->CONFIRM@0.597, CONFIRM->neutral@12
- no flip inside declared range: train_coef, mature_rate, hire_at

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| early_hire | hire at t=2 instead of t=10 | CONFIRM (-109) | 100% / 0% / 0% | -107 [-126, -41] |
| last_minute | panic hire 2 ticks before deadline | CONFIRM (-66) | 99% / 0% / 1% | -63 [-79, -27] |
| micro_hire | hire 1 person | CONFIRM (-2) | 79% / 0% / 21% | -2 [-3, -1] |
| massive_surge | hire 50 people | CONFIRM (-100) | 100% / 0% / 0% | -98 [-103, -92] |
| small_core | 10 hires onto a core team of 2 | REFUTE (+43) | 0% / 100% / 0% | +42 [+29, +53] |
| high_prod | very productive devs | neutral (+0) | 1% / 0% / 99% | +0 [+0, +0] |
| fast_onboard | mature_rate 0.5 | CONFIRM (-75) | 100% / 0% / 0% | -71 [-102, -13] |
| steep_learning | spaghetti code: slow, costly onboarding | CONFIRM (-100) | 100% / 0% / 0% | -98 [-103, -92] |
| async_remote | comm_coef 0.001 | CONFIRM (-12) | 100% / 0% / 0% | -12 [-15, -9] |
| no_training | no mentoring drag | CONFIRM (-4) | 57% / 1% / 42% | -2 [-69, +1] |
| no_comm | no coordination drag | CONFIRM (-10) | 100% / 0% / 0% | -10 [-13, -8] |
| light_mentoring | each newcomer costs 2% of each vet (not 20%) | CONFIRM (-15) | 98% / 0% / 2% | -10 [-79, -2] |
| on_time_project | antecedent false: backlog 500 (done by t=13) | CONFIRM (-51) | 74% / 0% / 26% | -33 [-84, +0] |
| huge_backlog | backlog 3000 | CONFIRM (-67) | 100% / 0% / 0% | -65 [-80, -43] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| flat (sd.brooks) | reference clique | CONFIRM (-88) | 100% / 0% / 0% | 12% / 0% / 88% |
| squads of 10 | Conway/surgical teams: pairs inside a squad + between squads | CONFIRM (-11) | 100% / 0% / 0% | 22% / 3% / 75% |
| mentor pods | ceil(New/5) vets mentor full-time, others untaxed | CONFIRM (-2) | 39% / 0% / 61% | 10% / 1% / 89% |
| async docs + CI | O(N log N) comm, 40% less training | CONFIRM (-8) | 100% / 0% / 0% | 22% / 2% / 76% |
| staged waves | hires arrive in 5 waves | CONFIRM (-87) | 100% / 0% / 0% | 12% / 0% / 88% |
| per-person comm | each dev bears (V-1) channels, not all V(V-1)/2 | CONFIRM (-15) | 100% / 0% / 0% | 17% / 1% / 82% |
| shared mentoring | train_coef is FTE per newcomer, spread over vets | CONFIRM (-10) | 93% / 0% / 7% | 11% / 1% / 88% |

## 6. Will it work *here*? (real-project placement)

### aider

Population: aider: monthly git panel since 2023; lever = doubling a late team of 2 veterans

Measured: months=28; median vets/month=2 (max 3); comm_coef 1.446e-18 [5.314e-27, 0.1299] (not identified); train_coef 6.073e-14 [1.883e-19, 0.007528]; newcomers who stayed: 4; mature_rate/month 1 [0.0005011, 1]

**P(claim holds | evidence)** = 0% / 71% / 29%, gap +9 [+0, +34]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `Todo` gain 0.000 [0.0, 0.0, 0.0, 0.0]
- `comm_coef` gain 0.000 [0.0, 0.0, 0.0, 0.0]
- `prod_rate` gain 0.000 [0.0, 0.0, 0.0, 0.0]
- `hire_at` gain 0.000 [0.0, 0.0, 0.0, 0.0]

Caveats (the long chain from data to parameter):

- Commits/month stand in for productivity (construct validity: commit size and review work are invisible).
- OSS newcomers are not 'hired' onto a deadline; arrivals follow activity, so train_coef may be biased toward 0 (reverse causation).
- Identity = e-mail address; no kaiaulu identity_match merge.
- mature_rate uses only newcomers still active a year later (survivorship: onboarding looks faster than it is).
- Lateness, prod_rate and backlog are not measured: the project is *assumed* late (Todo=1000), i.e. this tests the counterfactual 'if this team were late'.

### helix

Population: helix: monthly git panel since 2013; lever = doubling a late team of 3 veterans

Measured: months=151; median vets/month=3 (max 8); comm_coef 0.02327 [0.0139, 0.0323]; train_coef 0.01183 [5.216e-17, 0.02939]; newcomers who stayed: 29; mature_rate/month 1 [1, 1]

**P(claim holds | evidence)** = 1% / 80% / 19%, gap +5 [+0, +20]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `hire_at` gain 0.005 [0.02, 0.01, 0.0, 0.01]
- `Todo` gain 0.001 [0.01, 0.01, 0.01, 0.0]
- `prod_rate` gain 0.001 [0.0, 0.01, 0.01, 0.01]

Caveats (the long chain from data to parameter):

- Commits/month stand in for productivity (construct validity: commit size and review work are invisible).
- OSS newcomers are not 'hired' onto a deadline; arrivals follow activity, so train_coef may be biased toward 0 (reverse causation).
- Identity = e-mail address; no kaiaulu identity_match merge.
- mature_rate uses only newcomers still active a year later (survivorship: onboarding looks faster than it is).
- Lateness, prod_rate and backlog are not measured: the project is *assumed* late (Todo=1000), i.e. this tests the counterfactual 'if this team were late'.

