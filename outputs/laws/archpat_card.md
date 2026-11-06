# Evidence card: `archpat`

**Claim.** aggressive migration to patterns (1.5 vs 0.2) raises Feat - mean(Debt) of an already-bad project.  
**Lever.** `migrate` 0.2 -> 1.5; expected y up.  
**Support factors.** Patterned, Legacy, Debt, decay_rate, drift_to_legacy, gen_pat, gen_leg, born_pat, born_leg, intr_rate, pay_rate.  
**Sources.** Perry & Wolf 1992; Martin 2008; Bavota et al. 2012; sd.archpat

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units declared | every var has units |
| FAIL | dead parameters | no influence on y: ['pat_strength'] |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 3 extremes: Legacy=0:neutral, gen_pat=0.1:REFUTE, born_pat=1:REFUTE |
| WARN | clamp dependence | 34% of prior backgrounds escape declared bounds; 19% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=1:+228.7 dt=.25:+228.6 (0%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| PASS | time-horizon adequacy | t=15:CONFIRM(+149); t=20:CONFIRM(+229); t=40:CONFIRM(+542); t=80:CONFIRM(+1127) |
| PASS | dose-response monotone | gaps 0.2:+0, 0.5:+64, 0.8:+121, 1.1:+171, 1.4:+215, 1.7:+254, 2:+288 |
| FAIL | mechanism knock-out | channels ['gen_pat', 'born_pat'] neutral -> CONFIRM (+26.8) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 58.3, 'REFUTE': 12.9, 'neutral': 28.8} |
| PASS | scale x2 (MR2) | CONFIRM(+229) -> CONFIRM(+351) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 100% / 0% / 0% | +227 [+183, +275] |
| triangular over declared ranges | 65% / 10% / 24% | +67 [-111, +359] |
| uniform over declared ranges | 59% / 14% / 26% | +58 [-264, +463] |

## 3. What decides it? (tree on prior draws, base rate 65% CONFIRM, accuracy 79%)

Importance: `gen_leg` 0.40, `born_leg` 0.24, `born_pat` 0.15, `pay_rate` 0.14, `gen_pat` 0.07

```
|--- gen_leg <= 0.817
|   |--- gen_pat <= 0.737
|   |   |--- gen_leg <= 0.497
|   |   |   |--- class: 1
|   |   |--- gen_leg >  0.497
|   |   |   |--- class: 0
|   |--- gen_pat >  0.737
|   |   |--- born_leg <= 0.164
|   |   |   |--- class: 1
|   |   |--- born_leg >  0.164
|   |   |   |--- class: 1
|--- gen_leg >  0.817
|   |--- born_leg <= 0.348
|   |   |--- born_pat <= 0.255
|   |   |   |--- class: 1
|   |   |--- born_pat >  0.255
|   |   |   |--- class: 0
|   |--- born_leg >  0.348
|   |   |--- pay_rate <= 0.200
|   |   |   |--- class: 0
|   |   |--- pay_rate >  0.200
|   |   |   |--- class: 1
```

One-at-a-time tipping points (others at default):

- `Legacy`: neutral->CONFIRM@5
- `gen_pat`: REFUTE->neutral@0.245, neutral->CONFIRM@0.318
- `born_pat`: CONFIRM->neutral@0.7, neutral->REFUTE@0.975
- no flip inside declared range: Patterned, Debt, decay_rate, drift_to_legacy, gen_leg, born_leg, intr_rate, pay_rate

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| big_bang | rewrite: migrate=2.0 | CONFIRM (+288) | 100% / 0% / 0% | +287 [+230, +348] |
| no_governance | patterns erode 6x faster | CONFIRM (+84) | 100% / 0% / 0% | +83 [+66, +105] |
| already_good | 90 patterned / 10 legacy | CONFIRM (+60) | 93% / 0% / 7% | +59 [+47, +72] |
| debt_crisis | Debt=120 at start | CONFIRM (+209) | 100% / 0% / 0% | +208 [+167, +254] |
| overengineered | abstraction tax: patterned code ships slower | CONFIRM (+38) | 86% / 0% / 14% | +39 [+17, +60] |
| patterns_no_safer | patterned code as bug-prone as legacy | CONFIRM (+161) | 100% / 0% / 0% | +159 [+125, +196] |
| helix_scale | Helix partition: 149 patterned, 384 legacy | CONFIRM (+341) | 100% / 0% / 0% | +346 [+282, +425] |
| short_horizon | evaluate after 8 ticks | CONFIRM (+52) | 100% / 0% / 0% | +52 [+41, +64] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|
| sd.archpat | reference: migration is free | CONFIRM (+229) | 100% / 0% / 0% | 66% / 11% / 23% |
| migration costs | 4 feature-items of effort per module moved | CONFIRM (+74) | 97% / 0% / 3% | 20% / 59% / 21% |
| refactoring bugs | 0.5 debt per module moved (Bavota 2012) | CONFIRM (+153) | 100% / 0% / 0% | 38% / 27% / 34% |
| erosion ~ pressure | decay grows with delivery pressure | CONFIRM (+201) | 100% / 0% / 0% | 64% / 10% / 27% |
| all three | cost + bugs + pressure | REFUTE (-35) | 0% / 69% / 31% | 4% / 88% / 8% |
