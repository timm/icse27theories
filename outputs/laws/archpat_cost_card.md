# Evidence card: `archpat_cost`

**Claim.** aggressive migration to patterns (1.5 vs 0.2) raises Feat - mean(Debt) of an already-bad project when migration has an uncertain price.  
**Lever.** `migrate` 0.2 -> 1.5; expected y up.  
**Support factors.** Patterned, Legacy, Debt, decay_rate, drift_to_legacy, gen_pat, gen_leg, born_pat, born_leg, intr_rate, pay_rate, mig_cost, mig_bugs, pressure.  
**Sources.** Perry & Wolf 1992; Martin 2008; Bavota et al. 2012; sd.archpat; priors on the three missing mechanisms

## 1. Is the machine sound? (structure battery)

| status | test | detail |
|---|---|---|
| PASS | units declared | every var has units |
| FAIL | dead parameters | no influence on y: ['pat_strength'] |
| PASS | extreme conditions | all finite. claim not CONFIRMed at 9 extremes: Patterned=200:neutral, Legacy=0:neutral, decay_rate=0.5:REFUTE, gen_pat=0.1:REFUTE, born_pat=1:REFUTE, intr_rate=0.5:REFUTE, pay_rate=0:REFUTE, mig_cost=10:REFUTE |
| WARN | clamp dependence | 37% of prior backgrounds escape declared bounds; 2% are CONFIRMs that need clamping |
| PASS | integration step (dt) | gap dt=1:+97.0 dt=.25:+96.7 (0%); verdicts ['CONFIRM', 'CONFIRM', 'CONFIRM'] |
| PASS | time-horizon adequacy | t=15:CONFIRM(+44); t=20:CONFIRM(+97); t=40:CONFIRM(+302); t=80:CONFIRM(+677) |
| PASS | dose-response monotone | gaps 0.2:+0, 0.5:+24, 0.8:+47, 1.1:+69, 1.4:+90, 1.7:+110, 2:+127 |
| PASS | mechanism knock-out | channels ['gen_pat', 'born_pat'] neutral -> REFUTE (-81.9) |
| PASS | refutability (uniform) | uniform over ranges: {'CONFIRM': 6.0, 'REFUTE': 86.6, 'neutral': 7.4} |
| PASS | scale x2 (MR2) | CONFIRM(+97) -> CONFIRM(+106) |

## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)

| neighbourhood | verdicts | gap median [5%, 95%] |
|---|---|---|
| +-15% around defaults (old MC protocol) | 100% / 0% / 0% | +97 [+56, +139] |
| triangular over declared ranges | 5% / 83% / 11% | -160 [-680, +50] |
| uniform over declared ranges | 4% / 86% / 10% | -228 [-1146, +42] |

## 3. What decides it? (tree on prior draws, base rate 6% CONFIRM, accuracy 94%)

Importance: `decay_rate` 0.28, `gen_pat` 0.28, `pay_rate` 0.16, `gen_leg` 0.12, `mig_cost` 0.10, `Patterned` 0.05

```
|--- decay_rate <= 0.068
|   |--- gen_pat <= 1.524
|   |   |--- Patterned <= 55.744
|   |   |   |--- class: 0
|   |   |--- Patterned >  55.744
|   |   |   |--- class: 0
|   |--- gen_pat >  1.524
|   |   |--- pay_rate <= 0.312
|   |   |   |--- class: 0
|   |   |--- pay_rate >  0.312
|   |   |   |--- class: 1
|--- decay_rate >  0.068
|   |--- mig_cost <= 1.253
|   |   |--- gen_leg <= 0.806
|   |   |   |--- class: 0
|   |   |--- gen_leg >  0.806
|   |   |   |--- class: 0
|   |--- mig_cost >  1.253
|   |   |--- gen_pat <= 1.956
|   |   |   |--- class: 0
|   |   |--- gen_pat >  1.956
|   |   |   |--- class: 0
```

One-at-a-time tipping points (others at default):

- `Patterned`: CONFIRM->neutral@120
- `Legacy`: neutral->CONFIRM@5
- `decay_rate`: CONFIRM->neutral@0.113, neutral->REFUTE@0.2
- `gen_pat`: REFUTE->neutral@0.608, neutral->CONFIRM@0.752
- `gen_leg`: CONFIRM->neutral@1.19, neutral->CONFIRM@1.33
- `born_pat`: CONFIRM->neutral@0.3, neutral->REFUTE@0.525
- `intr_rate`: CONFIRM->neutral@0.212, neutral->REFUTE@0.225
- `pay_rate`: REFUTE->neutral@0.05, neutral->CONFIRM@0.075
- `mig_cost`: CONFIRM->neutral@4, neutral->REFUTE@5.25
- `mig_bugs`: CONFIRM->neutral@0.75, neutral->REFUTE@1.1
- no flip inside declared range: Debt, drift_to_legacy, born_leg, pressure

## 4. Business scenarios (same mechanism, different world)

| scenario | story | default | C/R/n under +-15% | gap |
|---|---|---|---|---|
| big_bang | rewrite: migrate=2.0 | CONFIRM (+127) | 100% / 0% / 0% | +127 [+76, +181] |
| no_governance | patterns erode 6x faster | REFUTE (-59) | 0% / 100% / 0% | -57 [-83, -34] |
| already_good | 90 patterned / 10 legacy | neutral (+13) | 0% / 0% / 100% | +13 [+1, +26] |
| debt_crisis | Debt=120 at start | CONFIRM (+84) | 100% / 0% / 0% | +84 [+48, +126] |
| overengineered | abstraction tax: patterned code ships slower | REFUTE (-81) | 0% / 100% / 0% | -80 [-108, -55] |
| patterns_no_safer | patterned code as bug-prone as legacy | CONFIRM (+49) | 86% / 0% / 14% | +48 [+14, +84] |
| helix_scale | Helix partition: 149 patterned, 384 legacy | REFUTE (-163) | 0% / 86% / 14% | -144 [-247, -35] |
| short_horizon | evaluate after 8 ticks | REFUTE (-15) | 0% / 73% / 27% | -14 [-28, -1] |

## 5. Mechanism variants (same world, different structure; arms compared *within* each structure)

| variant | story | default | local C/R/n | prior C/R/n |
|---|---|---|---|---|

## 6. Will it work *here*? (real-project placement)

### helix

Population: helix: production Java files in pattern4-scanned modules at 2026-05-24; stocks from lift_archpat (149 / 384 / 0 Drift)

Measured: snapshot 2c566eea27: 674 production files, 149 patterned; born_pat/born_leg (fix commits | size, churn) 0.83 [0.71, 0.93]; same, SZZ bug-introducing 0.68 [0.54, 0.86]; gen_pat/gen_leg proxy (non-fix commits | size) 1.05 [0.91, 1.27]

**P(claim holds | evidence)** = 3% / 94% / 4%, gap -547 [-1752, -19]

What to measure next (verdict-entropy reduction, P(CONFIRM) by quartile):

- `gen_leg` gain 0.028 [0.0, 0.01, 0.02, 0.08]
- `pay_rate` gain 0.028 [0.0, 0.0, 0.03, 0.08]
- `mig_bugs` gain 0.015 [0.06, 0.04, 0.01, 0.0]
- `born_leg` gain 0.014 [0.0, 0.01, 0.04, 0.06]
- `mig_cost` gain 0.013 [0.05, 0.05, 0.02, 0.0]

Caveats (the long chain from data to parameter):

- Cross-sectional: patterned files differ from others in ways other than patterns (age, centrality, ownership). Rate ratios are associations, not the effect of migrating a file.
- gen proxy = non-fix commits per file; change activity is not feature delivery (may even signal instability).
- The lever itself (migrating Legacy -> Patterned) is unobserved: pattern4 ran on one snapshot only, so migrate, decay_rate and the price of migration (mig_cost, mig_bugs) remain priors.
- 74% of files are 'Other' (neither patterned nor legacy); the 3-stock model has no place for them (boundary adequacy).
- Fix commits found by subject regex; SZZ pairs are the repo's committed B-SZZ output (older history only).

