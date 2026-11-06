# Evidence card: `brooks_fixed`

**Claim.** adding 10 people to a 10-person late project lowers Done-Todo at the deadline.  
**Lever.** `boost` 0 -> 10; expected y down.  
**Support factors.** Vet, Todo, comm_coef, train_coef, prod_rate, mature_rate, hire_at, newprod, leave, serial, overtime, rework.  
**Sources.** Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks; extended: newcomer output, attrition, unsplittable work, overtime, rework; bounded overload

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units & dimensions | every equation consistent; literals: literal 1 + tick, literal 1 - dev |
| PASS | dead parameters | all params live |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 18 extremes: Vet=0:REFUTE, Vet=100:neutral, Todo=0:neutral, Todo=500:neutral, comm_coef=0:neutral, train_coef=0:neutral, prod_rate=0.1:neutral, prod_rate=20:neutral |
| PASS | clamp dependence | 0% of prior backgrounds escape declared bounds; 0% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=0.125:-0.0 dt=0.03125:+0.0 (0%); verdicts ['neutral', 'neutral', 'neutral'] |
| WARN | time-horizon adequacy | t=15:CONFIRM(-104); t=20:neutral(-0); t=40:neutral(-0); t=80:neutral(-0) |
| PASS | dose-response monotone | gaps 0:+0, 16.6667:-77, 33.3333:-180, 50:-191, 66.6667:-191, 83.3333:-192, 100:-192 |
| PASS | mechanism knock-out | channels ['comm_coef', 'train_coef'] neutral -> neutral (+0.0) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 8.9, 'REFUTE': 66.0, 'neutral': 25.1} |
| PASS | scale x2 (MR2) | neutral(-0) -> CONFIRM(-590) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 12% / 0% / 88% | +0 [-72, +0] |
| triangular over declared ranges | 19% / 51% / 30% | +17 [-165, +244] |
| uniform over declared ranges | 8% / 66% / 27% | +33 [-50, +316] |

## 3. What decides it? (tree on prior draws, base rate 21% CONFIRM, accuracy 84%)

Importance: `Vet` 0.75, `prod_rate` 0.09, `comm_coef` 0.09, `newprod` 0.07

```
|--- Vet <= 30.797
|   |--- prod_rate <= 7.221
|   |   |--- Vet <= 20.891
|   |   |   |--- class: 1
|   |   |--- Vet >  20.891
|   |   |   |--- class: 0
|   |--- prod_rate >  7.221
|   |   |--- newprod <= 0.050
|   |   |   |--- class: 1
|   |   |--- newprod >  0.050
|   |   |   |--- class: 0
|--- Vet >  30.797
|   |--- comm_coef <= 0.006
|   |   |--- Vet <= 42.179
|   |   |   |--- class: 1
|   |   |--- Vet >  42.179
|   |   |   |--- class: 0
|   |--- comm_coef >  0.006
|   |   |--- Vet <= 34.221
|   |   |   |--- class: 0
|   |   |--- Vet >  34.221
|   |   |   |--- class: 0
```

One-at-a-time tipping points (others at default):

- `Vet`: REFUTE->CONFIRM@2.5, CONFIRM->neutral@10, neutral->CONFIRM@20, CONFIRM->neutral@47.5
- `comm_coef`: neutral->CONFIRM@0.0075
- `train_coef`: neutral->CONFIRM@0.3
- `prod_rate`: neutral->CONFIRM@0.597, CONFIRM->neutral@4.58
- `mature_rate`: CONFIRM->neutral@0.05
- `hire_at`: CONFIRM->neutral@7.12
- `serial`: neutral->CONFIRM@0.01
- `rework`: neutral->CONFIRM@0.0825
- no flip inside declared range: Todo, newprod, leave, overtime

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| early_hire | hire at t=2 instead of t=10 | CONFIRM (-163) | 79% / 0% / 21% | -124 [-291, +0] |
| last_minute | panic hire 2 ticks before deadline | neutral (+0) | 0% / 0% / 100% | +0 [+0, +0] |
| micro_hire | hire 1 person | neutral (-0) | 0% / 0% / 100% | +0 [-0, +0] |
| massive_surge | hire 50 people | CONFIRM (-191) | 77% / 0% / 23% | -122 [-309, +0] |
| small_core | 10 hires onto a core team of 2 | CONFIRM (-31) | 88% / 7% / 5% | -38 [-75, +11] |
| high_prod | very productive devs | neutral (+0) | 0% / 0% / 100% | +0 [+0, +0] |
| fast_onboard | mature_rate 0.5 | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| steep_learning | spaghetti code: slow, costly onboarding | CONFIRM (-169) | 72% / 0% / 28% | -101 [-288, +0] |
| async_remote | comm_coef 0.001 | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| no_training | no mentoring drag | neutral (-0) | 0% / 0% / 100% | +0 [-0, +0] |
| no_comm | no coordination drag | neutral (+0) | 0% / 0% / 100% | +0 [-0, +0] |
| light_mentoring | each newcomer costs 2% of each vet (not 20%) | neutral (-0) | 0% / 0% / 100% | +0 [-0, +0] |
| long_horizon | deadline at t=50, 4x backlog | CONFIRM (-981) | 97% / 0% / 3% | -738 [-1163, -194] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| flat (sd.brooks) | reference clique | neutral (-0) | 13% / 0% / 87% | 18% / 52% / 30% |
| squads of 10 | Conway/surgical teams: pairs inside a squad + between squads | neutral (+0) | 4% / 0% / 96% | 26% / 4% / 71% |
| mentor pods | ceil(New/5) vets mentor full-time, others untaxed | neutral (-0) | 0% / 0% / 100% | 10% / 57% / 33% |
| async docs + CI | O(N log N) comm, 40% less training | neutral (-0) | 0% / 0% / 100% | 27% / 16% / 57% |
| staged waves | hires arrive in 5 waves | neutral (-0) | 6% / 0% / 94% | 18% / 50% / 32% |
| per-person comm | each dev bears (V-1) channels, not all V(V-1)/2 | neutral (+0) | 5% / 0% / 95% | 29% / 28% / 43% |
| shared mentoring | train_coef is FTE per newcomer, spread over vets | neutral (-0) | 0% / 0% / 100% | 14% / 54% / 32% |
