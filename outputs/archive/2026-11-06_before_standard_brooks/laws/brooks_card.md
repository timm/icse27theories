# Evidence card: `brooks`

**Claim.** adding 10 people to a 10-person late project lowers Done-Todo at the deadline.  
**Lever.** `boost` 0 -> 10; expected y down.  
**Support factors.** Vet, Todo, comm_coef, train_coef, prod_rate, mature_rate, hire_at.  
**Sources.** Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units & dimensions | every equation consistent; literals: literal 1 + tick, literal 1 - dev |
| PASS | dead parameters | all params live |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 9 extremes: Vet=0:neutral, Vet=100:neutral, Todo=0:neutral, comm_coef=0:neutral, comm_coef=0.05:neutral, train_coef=0:neutral, prod_rate=0.1:neutral, prod_rate=20:neutral |
| PASS | clamp dependence | 0% of prior backgrounds escape declared bounds; 0% are CONFIRMs that need clamping |
| WARN | integration step (dt) | gap dt=1:-147.5 dt=0.25:-205.6 (28%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| WARN | time-horizon adequacy | t=15:CONFIRM(-148); t=20:CONFIRM(-148); t=40:CONFIRM(-148); t=80:neutral(-0) |
| PASS | dose-response monotone | gaps 0:+0, 16.6667:-148, 33.3333:-148, 50:-148, 66.6667:-148, 83.3333:-148, 100:-148 |
| PASS | mechanism knock-out | channels ['comm_coef', 'train_coef'] neutral -> neutral (+0.0) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 3.9, 'REFUTE': 0.2, 'neutral': 95.9} |
| PASS | scale x2 (MR2) | CONFIRM(-148) -> CONFIRM(-90) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 68% / 0% / 32% | -84 [-274, +0] |
| triangular over declared ranges | 7% / 0% / 93% | +0 [-80, +0] |
| uniform over declared ranges | 4% / 0% / 95% | +0 [+0, +0] |

## 3. What decides it? (tree on prior draws, base rate 7% CONFIRM, accuracy 94%)

Importance: `Vet` 0.59, `prod_rate` 0.19, `hire_at` 0.12, `comm_coef` 0.10

```
|--- Vet <= 12.412
|   |--- prod_rate <= 5.559
|   |   |--- class: 1
|   |--- prod_rate >  5.559
|   |   |--- hire_at <= 7.725
|   |   |   |--- class: 1
|   |   |--- hire_at >  7.725
|   |   |   |--- class: 0
|--- Vet >  12.412
|   |--- Vet <= 22.367
|   |   |--- comm_coef <= 0.011
|   |   |   |--- class: 0
|   |   |--- comm_coef >  0.011
|   |   |   |--- class: 0
|   |--- Vet >  22.367
|   |   |--- comm_coef <= 0.003
|   |   |   |--- class: 0
|   |   |--- comm_coef >  0.003
|   |   |   |--- class: 0
```

One-at-a-time tipping points (others at default):

- `Vet`: neutral->CONFIRM@2.5, CONFIRM->neutral@22.5
- `Todo`: neutral->CONFIRM@438
- `comm_coef`: neutral->CONFIRM@0.00375, CONFIRM->neutral@0.0225
- `train_coef`: neutral->CONFIRM@0.075
- `prod_rate`: neutral->CONFIRM@0.597, CONFIRM->neutral@6.07
- `hire_at`: CONFIRM->neutral@11.4
- no flip inside declared range: mature_rate

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| early_hire | hire at t=2 instead of t=10 | CONFIRM (-768) | 100% / 0% / 0% | -699 [-790, -575] |
| last_minute | panic hire 2 ticks before deadline | neutral (+0) | 0% / 0% / 100% | +0 [+0, +0] |
| micro_hire | hire 1 person | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| massive_surge | hire 50 people | CONFIRM (-148) | 68% / 0% / 32% | -86 [-271, +0] |
| small_core | 10 hires onto a core team of 2 | CONFIRM (-178) | 100% / 0% / 0% | -165 [-217, -124] |
| high_prod | very productive devs | neutral (+0) | 0% / 0% / 100% | +0 [+0, +0] |
| fast_onboard | mature_rate 0.5 | CONFIRM (-120) | 52% / 0% / 48% | -32 [-235, +0] |
| steep_learning | spaghetti code: slow, costly onboarding | CONFIRM (-148) | 68% / 0% / 32% | -86 [-271, +0] |
| async_remote | comm_coef 0.001 | neutral (+0) | 16% / 0% / 84% | +0 [-97, +0] |
| no_training | no mentoring drag | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| no_comm | no coordination drag | neutral (+0) | 7% / 0% / 93% | +0 [-44, +0] |
| light_mentoring | each newcomer costs 2% of each vet (not 20%) | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| long_horizon | deadline at t=50, 4x backlog | CONFIRM (-2986) | 100% / 0% / 0% | -2683 [-3076, -2080] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| flat (sd.brooks) | reference clique | CONFIRM (-148) | 68% / 0% / 32% | 8% / 0% / 92% |
| squads of 10 | Conway/surgical teams: pairs inside a squad + between squads | CONFIRM (-148) | 62% / 0% / 38% | 11% / 0% / 89% |
| mentor pods | ceil(New/5) vets mentor full-time, others untaxed | neutral (-0) | 0% / 0% / 100% | 5% / 3% / 92% |
| async docs + CI | O(N log N) comm, 40% less training | neutral (+0) | 4% / 0% / 96% | 10% / 0% / 90% |
| staged waves | hires arrive in 5 waves | CONFIRM (-109) | 57% / 0% / 43% | 8% / 0% / 92% |
| per-person comm | each dev bears (V-1) channels, not all V(V-1)/2 | CONFIRM (-123) | 60% / 0% / 40% | 11% / 0% / 89% |
| shared mentoring | train_coef is FTE per newcomer, spread over vets | neutral (+0) | 0% / 0% / 100% | 7% / 0% / 93% |
