# Evidence card: `brooks`

**Claim.** adding 10 people to a project that is already late (backlog 1000, 10 vets can do ~800 by t=20) makes it finish later.  
**Lever.** `boost` 0 -> 10; expected y down.  
**Support factors.** Vet, Todo, comm_coef, train_coef, prod_rate, mature_rate, hire_at, newprod, leave, serial, overtime, rework.  
**Sources.** Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks; outcome = completion time; extra structures and bounded overload

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units & dimensions | every equation consistent; literals: literal 1 + tick, literal 1 - dev |
| PASS | dead parameters | all params live (deadline only together with another factor) |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 6 extremes: Vet=0:REFUTE, Vet=100:neutral, Todo=0:neutral, train_coef=0:neutral, prod_rate=0.1:neutral, prod_rate=20:neutral |
| PASS | clamp dependence | 0% of prior backgrounds escape declared bounds; 0% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=0.125:-11.0 dt=0.03125:-11.1 (1%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| PASS | time-horizon adequacy | t=45:CONFIRM(-11); t=80:CONFIRM(-11); t=160:CONFIRM(-11); t=320:CONFIRM(-11) |
| PASS | dose-response monotone | gaps 0:+0, 16.6667:-23, 33.3333:-92, 50:-102, 66.6667:-103, 83.3333:-103, 100:-103 |
| PASS | mechanism knock-out | channels ['comm_coef', 'train_coef'] neutral -> REFUTE (+2.2) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 26.9, 'REFUTE': 33.8, 'neutral': 39.3} |
| PASS | scale x2 (MR2) | CONFIRM(-11) -> CONFIRM(-50) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 100% / 0% / 0% | -11 [-14, -8] |
| triangular over declared ranges | 44% / 16% / 40% | -1 [-60, +24] |
| uniform over declared ranges | 27% / 33% / 40% | +2 [-42, +118] |

## 3. What decides it? (tree on prior draws, base rate 46% CONFIRM, accuracy 83%)

Importance: `Vet` 0.66, `comm_coef` 0.25, `leave` 0.09

```
|--- Vet <= 35.838
|   |--- Vet <= 24.620
|   |   |--- Vet <= 4.940
|   |   |   |--- class: 0
|   |   |--- Vet >  4.940
|   |   |   |--- class: 1
|   |--- Vet >  24.620
|   |   |--- comm_coef <= 0.013
|   |   |   |--- class: 1
|   |   |--- comm_coef >  0.013
|   |   |   |--- class: 0
|--- Vet >  35.838
|   |--- comm_coef <= 0.008
|   |   |--- leave <= 0.006
|   |   |   |--- class: 0
|   |   |--- leave >  0.006
|   |   |   |--- class: 1
|   |--- comm_coef >  0.008
|   |   |--- leave <= 0.012
|   |   |   |--- class: 0
|   |   |--- leave >  0.012
|   |   |   |--- class: 0
```

One-at-a-time tipping points (others at default):

- `Vet`: REFUTE->CONFIRM@7.5, CONFIRM->neutral@47.5
- `Todo`: neutral->CONFIRM@425
- `train_coef`: neutral->CONFIRM@0.05
- `prod_rate`: neutral->CONFIRM@1.09, CONFIRM->neutral@12.5
- no flip inside declared range: comm_coef, mature_rate, hire_at, newprod, leave, serial, overtime, rework

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| early_hire | hire at t=2 instead of t=10 | CONFIRM (-12) | 100% / 0% / 0% | -12 [-16, -8] |
| last_minute | panic hire 2 ticks before deadline | CONFIRM (-9) | 99% / 0% / 1% | -8 [-11, -5] |
| micro_hire | hire 1 person | neutral (-1) | 34% / 0% / 66% | -1 [-1, -1] |
| massive_surge | hire 50 people | CONFIRM (-102) | 100% / 0% / 0% | -100 [-105, -94] |
| small_core | 10 hires onto a core team of 2 | REFUTE (+51) | 0% / 100% / 0% | +48 [+36, +59] |
| high_prod | very productive devs | neutral (+0) | 2% / 0% / 98% | +0 [+0, +0] |
| fast_onboard | mature_rate 0.5 | CONFIRM (-3) | 84% / 0% / 16% | -3 [-5, -0] |
| steep_learning | spaghetti code: slow, costly onboarding | CONFIRM (-64) | 100% / 0% / 0% | -62 [-75, -49] |
| async_remote | comm_coef 0.001 | CONFIRM (-6) | 100% / 0% / 0% | -6 [-8, -5] |
| no_training | no mentoring drag | neutral (+1) | 0% / 43% / 57% | +1 [+0, +2] |
| no_comm | no coordination drag | CONFIRM (-6) | 100% / 0% / 0% | -6 [-7, -4] |
| light_mentoring | each newcomer costs 2% of each vet (not 20%) | neutral (-0) | 12% / 2% / 85% | -0 [-2, +1] |
| on_time_project | antecedent false: backlog 500 (done by t=13) | CONFIRM (-6) | 80% / 0% / 20% | -4 [-8, +0] |
| huge_backlog | backlog 3000 | CONFIRM (-14) | 95% / 0% / 5% | -14 [-23, -4] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| flat (reference) | reference clique | CONFIRM (-11) | 100% / 0% / 0% | 42% / 16% / 42% |
| squads of 10 | Conway/surgical teams: pairs inside a squad + between squads | CONFIRM (-5) | 100% / 0% / 0% | 51% / 6% / 42% |
| mentor pods | ceil(New/5) vets mentor full-time, others untaxed | neutral (+1) | 0% / 21% / 79% | 35% / 19% / 46% |
| async docs + CI | O(N log N) comm, 40% less training | CONFIRM (-3) | 97% / 0% / 3% | 65% / 6% / 29% |
| staged waves | hires arrive in 5 waves | CONFIRM (-11) | 100% / 0% / 0% | 42% / 16% / 42% |
| per-person comm | each dev bears (V-1) channels, not all V(V-1)/2 | CONFIRM (-6) | 100% / 0% / 0% | 62% / 9% / 29% |
| shared mentoring | train_coef is FTE per newcomer, spread over vets | neutral (+0) | 3% / 5% / 92% | 39% / 17% / 44% |

## 6. Will it work *here*? (real-project placement)

### aider

Population: aider: monthly git panel since 2023; lever = doubling a late team of 2 veterans

Measured: months=28; median vets/month=2 (max 3); comm_coef 2.298e-21 [7.866e-30, 0.1421] (not identified); train_coef 5.396e-14 [1.267e-20, 0.007703]; newcomers who stayed: 4; mature_rate/month 1 [0.0005011, 1]

**P(claim holds | evidence)** = 0% / 87% / 13%, gap +12 [+0, +38]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `Todo` gain 0.001 [0.0, 0.0, 0.0, 0.0]
- `comm_coef` gain 0.001 [0.0, 0.0, 0.0, 0.0]
- `prod_rate` gain 0.001 [0.0, 0.0, 0.0, 0.0]
- `hire_at` gain 0.001 [0.0, 0.0, 0.0, 0.0]
- `newprod` gain 0.001 [0.0, 0.0, 0.0, 0.0]

Caveats (the long chain from data to parameter):

- Commits/month stand in for productivity (construct validity: commit size and review work are invisible).
- OSS newcomers are not 'hired' onto a deadline; arrivals follow activity, so train_coef may be biased toward 0 (reverse causation).
- Identity = e-mail address; no kaiaulu identity_match merge.
- mature_rate uses only newcomers still active a year later (survivorship: onboarding looks faster than it is).
- Lateness, prod_rate and backlog are not measured: the project is *assumed* late (Todo=1000), i.e. this tests the counterfactual 'if this team were late'.

### helix

Population: helix: monthly git panel since 2013; lever = doubling a late team of 3 veterans

Measured: months=152; median vets/month=3 (max 8); comm_coef 0.03833 [0.02089, 0.06644]; train_coef 0.008356 [2.39e-18, 0.0373]; newcomers who stayed: 29; mature_rate/month 1 [1, 1]

**P(claim holds | evidence)** = 4% / 71% / 25%, gap +4 [-1, +25]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `leave` gain 0.027 [0.09, 0.06, 0.01, 0.0]
- `serial` gain 0.017 [0.01, 0.02, 0.04, 0.09]
- `prod_rate` gain 0.003 [0.02, 0.05, 0.04, 0.04]
- `newprod` gain 0.003 [0.04, 0.06, 0.04, 0.02]
- `overtime` gain 0.002 [0.03, 0.04, 0.06, 0.03]

Caveats (the long chain from data to parameter):

- Commits/month stand in for productivity (construct validity: commit size and review work are invisible).
- OSS newcomers are not 'hired' onto a deadline; arrivals follow activity, so train_coef may be biased toward 0 (reverse causation).
- Identity = e-mail address; no kaiaulu identity_match merge.
- mature_rate uses only newcomers still active a year later (survivorship: onboarding looks faster than it is).
- Lateness, prod_rate and backlog are not measured: the project is *assumed* late (Todo=1000), i.e. this tests the counterfactual 'if this team were late'.

