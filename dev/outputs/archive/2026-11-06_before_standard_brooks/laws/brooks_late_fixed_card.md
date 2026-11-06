# Evidence card: `brooks_late_fixed`

**Claim.** adding 10 people to a project that is already late (backlog 1000, 10 vets can do ~775 by t=20) makes it finish later.  
**Lever.** `boost` 0 -> 10; expected y down.  
**Support factors.** Vet, Todo, comm_coef, train_coef, prod_rate, mature_rate, hire_at, newprod, leave, serial, overtime, rework.  
**Sources.** Brooks 1975; Abdel-Hamid & Madnick 1991; sd.brooks; outcome = completion time; extended: newcomer output, attrition, unsplittable work, overtime, rework; bounded overload

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units & dimensions | every equation consistent; literals: literal 1 + tick, literal 1 - dev |
| PASS | dead parameters | all params live |
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
| flat (sd.brooks) | reference clique | CONFIRM (-11) | 100% / 0% / 0% | 42% / 16% / 42% |
| squads of 10 | Conway/surgical teams: pairs inside a squad + between squads | CONFIRM (-5) | 100% / 0% / 0% | 51% / 6% / 42% |
| mentor pods | ceil(New/5) vets mentor full-time, others untaxed | neutral (+1) | 0% / 21% / 79% | 35% / 19% / 46% |
| async docs + CI | O(N log N) comm, 40% less training | CONFIRM (-3) | 97% / 0% / 3% | 65% / 6% / 29% |
| staged waves | hires arrive in 5 waves | CONFIRM (-11) | 100% / 0% / 0% | 42% / 16% / 42% |
| per-person comm | each dev bears (V-1) channels, not all V(V-1)/2 | CONFIRM (-6) | 100% / 0% / 0% | 62% / 9% / 29% |
| shared mentoring | train_coef is FTE per newcomer, spread over vets | neutral (+0) | 3% / 5% / 92% | 39% / 17% / 44% |
