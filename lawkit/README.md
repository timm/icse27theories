# lawkit — testing any SE law, the same way every time

lawkit turns "law X says doing L moves Y" into an **evidence card**:
is the model sound, where does the claim hold, what breaks it, does
*this* project sit where it holds, and what should we measure next.
It works on any `paper/sd.py`-style model (`Model(init, step, y, rq,
ctrl)`), so all 35 models in the catalogue can be plugged in.

```
make laws          # cards for every law in lawkit/laws.py  (~4 min)
make evidence      # mine Helix + Aider (needs clones in $(REPOS))
make sensitivity   # which evidence link carries each verdict
make lawkit-test   # regression tests
```

Outputs: `outputs/laws/<law>_card.md` (+ `.json`), mined evidence in
`outputs/evidence/`, synthesis in `outputs/laws/SYNTHESIS.md`.

## The standard Brooks model

`LAWS["brooks"]` is the one Brooks model for every Forrester test
(`make forrester-all`), report and future evaluation:

- **claim:** adding 10 people to a project that is already late (backlog
  1000) makes it finish later;
- **outcome:** finish time;
- **equations:** `sd.brooks`' communication and training costs, plus
  five literature structures as uncertain settings, each off at the
  default: newcomer output, attrition, unsplittable work, overtime,
  rework;
- **overload:** bounded, time left for work = exp(-overhead);
- **time step:** 0.125.

The Brooks miner (`mine/brooks_evidence.py`) fits this same production
equation, so the evidence and the model agree. The four earlier Brooks
models are archived in `outputs/archive/2026-11-06_before_standard_brooks/`.

## The pipeline

| stage | module | question | can it fail? |
|---|---|---|---|
| 0 claim | `core.Law` | lever, arms, direction, support factors, causal channels | — |
| 1 machine | `battery.py` | is the model a sound machine? 10 tests, expectation stated first | yes: dead params, undeclared channels, clamp-made verdicts, dt flips |
| 2 robustness | `regimes.robustness` | P(CONFIRM) at ±15%, prior, uniform | reports all three; never just one |
| 3 regime map | `regimes.tipping`, `regimes.rules` | which support factors decide, at what thresholds | — |
| 4 worlds | `regimes.scenarios` | business scenarios: same mechanism, different world | — |
| 5 mechanisms | `regimes.variants` | rival structures; arms compared *within* each | — |
| 6 here? | `evidence.place` | P(claim holds \| this project's measured factors) | — |
| 7 next | `evidence.voi` | which unmeasured factor would most settle the verdict | — |

## Adding a law

```python
from lawkit.core import Law
import sd

DEBT = Law(
  "debt", sd.debt, "starting with Debt=50 slows feature delivery",
  lever="Debt", arms=(0, 50), expect="down",
  factors=["born_rate", "pay_rate", "intr_rate"],     # support factors
  channels={"intr_rate": 0},       # causal path(s); knock-out must kill it
  scenarios={"startup": ("fast, sloppy shipping", {"born_rate": 0.6})})
```

(Try it: the knock-out FAILs, because sd.debt's main channel is the
hard-coded `speed = 1 - Debt/100`, not a declared parameter.)

Add it to `LAWS` in `laws.py`, then `python run_laws.py debt`. For
real data, write a miner that emits
`outputs/evidence/<law>_<project>.json`:

```json
{"project": "helix", "population": "who/what/when",
 "measured": {"factor": [bootstrap values...],
              "ratio_factor": ["x", "other_factor", [ratios...]]},
 "fixed": {"Vet": 3, "_arms": [0, 3]},
 "summary": ["human-readable estimates"], "notes": ["caveats"]}
```

## Rules the code enforces (learned the hard way on Brooks)

1. A test that cannot fail is not a test: every battery check states
   its expectation before running.
2. Sample size buys precision, not robustness. Report how big the
   neighbourhood is (±15% vs. declared ranges), not how many runs.
3. Compare arms inside one structure. "Org X with hires beats org Y
   without" is not "hiring helps in org X".
4. The outcome must measure the law's own words (Brooks says
   "later", so the standard `brooks` model measures completion time).
5. Real data places a project in the regime map. It does not
   "confirm the law" as an average effect.
