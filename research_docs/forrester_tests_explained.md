
This section explains each check in `outputs/forrester_all.md` on the **standard
model**. Each test has the same parts:
- **question:** what the test asks, in plain words;
- **how:** how it's run;
- **PASS rule:** what counts as PASS or FAIL;
- **example:** from the default world (10 veterans, backlog 1000, 10 hires at tick 10; finish at 25.1 without hiring, 36.1 with; gap −11);
- **what failing looked like,** where the original model failed;
- **code:** where the function lives.

#### How the code is wired

The tests live in two files:
- [`forrester_all.py`](../forrester_all.py): 9 tests of its own, plus validation, the Helix test and the report;
- [`lawkit/battery.py`](../lawkit/battery.py): the 10 general lawkit tests, which work on any law.

**One run of `python -B forrester_all.py`, step by step:**
1. **`main()`** ([forrester_all.py:485](../forrester_all.py#L485)) runs the validation first: `known_answers()` (L321) and `mutants()` (L375). Then the data test, `data_policy()` (L394).
2. **`worlds()`** (L41) builds the 15 worlds (default + 14 scenarios), using `world()` (L33).
3. **`suite(w)`** ([L310](../forrester_all.py#L310)) runs all 19 tests on one world:
   - first `battery.battery(w)`, the 10 lawkit tests;
   - each lawkit name is renamed to its Forrester name via `BATTERY_NAMES` (L277);
   - then its own 9 tests.
4. **`relabel()`** ([L298](../forrester_all.py#L298)) turns a WARN on a "finding" test (listed in `FINDINGS`, L291) into **INFO**.
5. **`report()`** (L416) writes `outputs/forrester_all.md` and `.json`.

**Shared helpers in `forrester_all.py`:**
- `traj()` (L52): runs one arm and returns every step;
- `hire_step()` (L65): which step the hire lands on;
- `first0()` (L69): the first step where `Todo` hits 0;
- `bg()` (L47): the world with some settings overridden;
- `row()` (L28): one result line.

---

#### V1. Known answers (validation): `known_answers()`, [forrester_all.py:321](../forrester_all.py#L321)

- **Question:** does the simulator reproduce numbers worked out by hand?
- **Example:** four hand calculations, all matching exactly.

  | check | hand calculation | simulator |
  |---|---|---|
  | output, 10 veterans | 10 × e^(−45 × 0.005) × 5 = **39.926** items per tick | 39.926 |
  | finish, no hiring | 1000 ÷ (39.926 × 0.125) → 201 steps = **tick 25.125** | 25.125 |
  | output right after 10 hires | 10 × e^(−(0.225 + 10 × 0.2)) × 5 = **5.403** (slowed, not frozen) | 5.403 |
  | sweet spot | V(2V − 1) = 2/0.005 → V = 14.4 → **14** | 14 |

#### V2. Planted defects (validation): `mutant()` [L347](../forrester_all.py#L347), `mutants()` [L375](../forrester_all.py#L375)

- **Question:** if the model had a bug, would the right test notice?
- **How:** `mutant(kind)` builds a broken copy of the model. `mutants()` checks two things for each: the matching check fails on the copy, and passes on the correct model.
- **Example:** all 6 caught.
  - newcomers vanish → caught by *headcount conserved*;
  - future hires lower today's output → *causality*;
  - 1.5× full time → *nobody over full time*;
  - the hire step undoes work → *work never un-done*;
  - one fake item every tick → *work conserved*;
  - wrong unit label → *dimensional consistency*.
- **Why it matters:** Part B's tests passed a zero-backlog run that "finished" 426 items. These mutants show this harness doesn't have that problem.

---

### A. Structure tests

#### 1. Dimensional consistency (F&S §3): `units()`, [lawkit/battery.py:20](../lawkit/battery.py#L20), which calls `check()` in [lawkit/units.py:63](../lawkit/units.py#L63)

- **Question:** do the units add up in every equation?
- **How:** the model is stepped once on unit-carrying numbers, the `Q` class at [units.py:31](../lawkit/units.py#L31). For example, `Vet` = "10 devs" and `comm_coef` = "0.005 per devs²". Every +, −, × checks the units, and a mismatch raises `DimError`.
- **PASS rule:** no unit errors, and every variable has a unit.
- **Example:**
  - talking = (per devs²) × devs² = a pure fraction ✅;
  - training = (per devs) × devs = a pure fraction ✅.

  So e^(−(talking + training)) is valid. Literal uses like `Vet − 1` are listed as notes rather than rejected.
- **What failing looked like:** the original's labels "per pair", "per new hire" and "items per vet" were three vocabularies for people. The checker couldn't verify that `1 − talking − training` was a pure fraction.

#### 2. Every parameter matters: `dead_params()`, [lawkit/battery.py:32](../lawkit/battery.py#L32)

- **Question:** does every setting actually change something?
- **How:** each setting is set to its low, default and high value, in each arm. If it changes nothing in the default world, it's tried in 20 random believable worlds.
- **PASS rule:** every setting is live somewhere.
- **Example:**
  - `prod_rate` changes the finish time in the default world: live.
  - `deadline` changes nothing in the default world (overtime is 0 there), but does once overtime is on: "live only together with another factor".
- **What failing looks like:** archpat's `pat_strength` is used by no equation, so it's reported as dead.

#### 3. Extreme conditions, every setting at min and max (F&S §3): `extremes()`, [lawkit/battery.py:52](../lawkit/battery.py#L52)

- **Question:** does anything crash or become infinite at the limits?
- **How:** each of the 12 uncertain settings is set to its low and then its high value, one at a time: 24 runs of both arms.
- **PASS rule:** all results are finite. It also *lists* the extremes where the claim isn't CONFIRMed, as information.
- **Example:** all 24 are finite. Not CONFIRMed at:
  - `Vet = 0`: REFUTE. Without veterans the project never finishes, so newcomers are the only hope.
  - `Todo = 0`: neutral (no work).
  - `train_coef = 0`: neutral (no training dip).
  - `prod_rate = 0.1`: neutral (hopelessly slow anyway).
  - `prod_rate = 20`: neutral (finished before the hire).
  - `Vet = 100`: neutral (already swamped by talking).

#### 4. Extreme conditions, known answers: `extreme_known()`, [forrester_all.py:75](../forrester_all.py#L75)

- **Question:** in six extreme cases we know the *exact* answer. Does the model give it?
- **How:** the cases are the list `cases` inside the function. `overload_ok()` (L112) checks the overload case, and `effic()` (L117) is e^(−overhead).
- **PASS rule:** all 6 exact.
- **Example:** 6/6.
  - no team, no hires → nothing done;
  - `Todo = 0` → nothing done;
  - `comm_coef = 0.05` → first-step output = capacity × e^(−2.25), under 15% of capacity;
  - `train_coef = 1` → the step after the hire = capacity × e^(−(0.225 + 10));
  - `mature_rate = 0` → veterans stay at exactly 10;
  - `mature_rate = 1` → newcomers shrink by exactly (1 − 0.125) per step.
- **Difference from test 3:** test 3 checks answers are *finite*; this one checks they're *exactly right*.

#### 5. Declared causes do the work (knock-out): `knockout()`, [lawkit/battery.py:123](../lawkit/battery.py#L123)

- **Question:** does the harm come from Brooks' reasons (talking and training), or from something hidden in the code?
- **How:** the declared channels (`channels={'comm_coef':0, 'train_coef':0}` in `lawkit/laws.py`) are set to 0.
- **PASS rule:** the harm disappears. A CONFIRM here would be a FAIL.
- **Example:** with both causes off, hiring finishes **2.2 ticks earlier** (REFUTE). All the harm came from talking and training.
- **What failing looks like:** archpat and `sd.debt` kept their "law" with the causes off, because of a hard-coded slowdown.

#### 6. Boundary adequacy, structure (F&S §3): `boundary_structure()` [forrester_all.py:130](../forrester_all.py#L130); the checklist is `BOUNDARY` [L121](../forrester_all.py#L121)

- **Question:** does the model contain every mechanism the literature says matters?
- **How:** the 7 structures in `BOUNDARY` are each paired with the setting that carries them: talking (`comm_coef`), training (`train_coef`), newcomer output (`newprod`), unsplittable work (`serial`), attrition (`leave`), overtime (`overtime`), rework (`rework`).
- **PASS rule:** all 7 present.
- **Example:** 7/7. **What failing looked like:** the original had 2 of 7.

#### 7. Boundary adequacy, behaviour (F&S §4): `boundary_behaviour_policy()`, [forrester_all.py:212](../forrester_all.py#L212) (first row)

- **Question:** is anything missing that would change the behaviour?
- **PASS rule:** no structure from `BOUNDARY` is missing.
- **Example:** PASS.
- **What failing looked like:** before the structures were added, this test switched each one on to measure its effect:
  - newcomers 50% productive moved the outcome 15–18%;
  - 1% of veterans leaving per tick: 56–62%;
  - 10% of the work unsplittable: 92%.

  That's more than the 10% limit for each.

#### 8. Boundary adequacy in time (F&S §3/§4): `horizon()`, [lawkit/battery.py:97](../lawkit/battery.py#L97)

- **Question:** is the run long enough to see a late payback (a J-curve)?
- **How:** the same world is run with horizons of 45, 80, 160 and 320 ticks.
- **PASS rule:** the same verdict at every length.
- **Example:** CONFIRM (−11) at all four lengths.
- **What failing looked like:** the original scored at tick 20. Part B needed a special `long_horizon` scenario.

---

### B. Behaviour tests

#### 9. Invariants (7 physical rules): `invariants()`, [forrester_all.py:140](../forrester_all.py#L140)

- **Question:** do basic facts of reality hold at every step?
- **How:** both arms are run **without clipping** (`traj(..., clip=False)`), so a bad equation can't hide. The 7 rules are the dictionary `checks` inside the function:
  1. people never negative;
  2. headcount conserved (veterans + newcomers = 10 + hires);
  3. causality (both arms identical before the hire);
  4. finished work never decreases;
  5. nobody works over full time;
  6. no phantom work (`Done` ≤ backlog);
  7. work conserved (`Done + Todo` = backlog).
- **PASS rule:** all 7 hold at every step.
- **Example:** 7/7.
- **What failing looked like:** the original broke rules 6 and 7. A zero backlog "finished" 426 items, and `Todo` reached −275 in Part B's copy of the equations.

#### 10. Negative effort hidden by clipping: also in `invariants()`, [forrester_all.py:140](../forrester_all.py#L140) (the variable `neg`)

- **Question:** does the raw formula ever give *negative* working time, with a floor hiding it?
- **PASS rule:** 0 such steps.
- **Example:** 0 of 1,280 steps.
- **Honest note:** with e^(−overhead) this can't happen, because the result is always positive. The test exists to catch the original's `1 − overhead`, which gave **−1.225** right after 10 hires and was floored to 0 (the frozen team).

#### 11. Verdicts made by clipping (F&S §4): `clamps()`, [lawkit/battery.py:70](../lawkit/battery.py#L70)

- **Question:** are any CONFIRMs produced only because a value hit a limit?
- **How:** 300 believable worlds are run normally, then in `mode="reject"`, which throws out any run where a value leaves its allowed range.
- **PASS rule:** no CONFIRM needs clamping. More than 20% is a FAIL.
- **Example:** 0% of worlds leave their range, and 0% of CONFIRMs need clamping.
- **What failing looked like:**
  - this is how we found that Part B's "100% hurts" came from the clamp;
  - in aiwork, 24% of CONFIRMs need clamping.

#### 12. Integration error (Sterman 2000): `dt_halving()`, [lawkit/battery.py:86](../lawkit/battery.py#L86)

- **Question:** is part of the answer an arithmetic error from time steps that are too big?
- **How:** run with step 0.125, then 0.0625, then 0.03125.
- **PASS rule:** the verdict never changes (otherwise FAIL), and the gap moves less than 10% (otherwise WARN).
- **Example:** −11.0 → −11.1, a **1%** change.
- **What failing looked like:** the original went from −147.5 (step 1) to −205.6 (step 0.25), a 28% change.

#### 13. MR1, more hires mean steadier harm (Chen et al.): `dose()`, [lawkit/battery.py:107](../lawkit/battery.py#L107)

- **Question:** does the harm behave sensibly as hiring grows?
- **How:** the gap at 0, 17, 33, 50, 67, 83 and 100 hires.
- **PASS rule:** the harm may first shrink (below the sweet spot, a few hires can help). Once it starts growing, it must never shrink again.
- **Example:**

  | hires | 0 | 17 | 33 | 50 | 67 | 83 | 100 |
  |---|---|---|---|---|---|---|---|
  | gap | 0 | −23 | −92 | −102 | −103 | −103 | −103 |

  The harm grows, then levels off.
- **What failing looked like:** in the original, 10 and 50 hires gave the *same* −147.5, because both froze the team.

#### 14. MR2, double everything, same verdict (Chen et al.): `scale()`, [lawkit/battery.py:145](../lawkit/battery.py#L145)

- **Question:** does a project twice as big flip the answer?
- **How:** every stock is doubled: 20 veterans, backlog 2000.
- **PASS rule:** no reversal (CONFIRM ↔ REFUTE).
- **Example:** CONFIRM (−11) → CONFIRM (−50). Twenty veterans are already past the sweet spot, so 10 more hurt more.

#### 15. Extreme policy (F&S §4): `extreme_policy()`, [forrester_all.py:186](../forrester_all.py#L186)

- **Question:** do absurd *decisions* give sensible answers?
- **PASS rule:** all the "must" rows hold.
- **Example:**

  | decision | must | result |
  |---|---|---|
  | hire 0 | gap exactly 0 | 0 ✅ |
  | hire 100 | finite, no better than 10 | −103 vs −11 ✅ |
  | hire at tick 0 / 19 | (reported) | CONFIRM −12 / −8 |
  | hire after the project has finished (tick 26) | gap exactly 0 | 0 ✅ |

---

### C. Policy tests (where INFO appears)

**How INFO arises:** in these tests a non-uniform recommendation gives **WARN**.
`relabel()` ([forrester_all.py:298](../forrester_all.py#L298)) changes that WARN to
**INFO** for the tests listed in `FINDINGS` (L291). There the WARN *is* the
research result ("the law depends on X"), not a model fault. In the JSON and the
detail text these rows begin with *"finding: the law is conditional"*.

#### 16. Can any world refute it? (F&S §5): `free_lunch()`, [lawkit/battery.py:137](../lawkit/battery.py#L137)

- **Question:** is the law built in, so that it can never fail?
- **How:** 1,000 worlds with every setting drawn evenly across its range.
- **PASS rule:** at least one CONFIRM and at least one REFUTE.
- **Example:** 27% CONFIRM / 34% REFUTE / 39% neutral. PASS in all 15 worlds.
- **What failing looks like:** `sd.debt` gives 100% CONFIRM, because its "law" is hard-coded.

#### 17. Boundary adequacy, policy (F&S §5): `boundary_behaviour_policy()`, [forrester_all.py:212](../forrester_all.py#L212) (second row)

- **Question:** does "don't hire" survive a different team organisation?
- **How:** the 6 rival structures from `LAW.variants` (`lawkit/laws.py`). In each, no hire is compared with hire *inside* that structure.
- **PASS rule:** the same verdict under all 6.
- **Example:** CONFIRM under 4/6. The two exceptions:
  - mentor pods → neutral (+1);
  - shared mentoring → neutral (0).

  Both remove the training dip, so the result is **INFO**.
- **The 4 PASS worlds:** micro_hire, massive_surge, small_core and high_prod. There, every structure agrees.

#### 18. Behaviour sensitivity (F&S §4): `behaviour_sensitivity()` [forrester_all.py:246](../forrester_all.py#L246); shapes from `mode()` [L233](../forrester_all.py#L233)

- **Question:** does the *shape* of the response change across believable values?
- **How:** `mode()` classifies the hire run's output after the hire:
  - *finished before hire*;
  - *no dip* (never below 95% of the pre-hire output);
  - *dip then recovers* (climbs back to the pre-hire level);
  - *dip, no recovery*.

  Each setting is swept across 11 values (`the.oat`).
- **PASS rule:** the same shape everywhere.
- **Example:** the default is "dip, no recovery". It changes with:
  - `Vet` (no dip at 0);
  - `Todo` (finished before hire up to 400);
  - `comm_coef` (dip then recovers at 0);
  - `leave` (dip then recovers from 1% per tick).

  So it's **INFO**.

#### 19. Policy sensitivity (F&S §5): `policy_sensitivity()` [forrester_all.py:264](../forrester_all.py#L264); uses `robustness()` and `tipping()` in [lawkit/regimes.py](../lawkit/regimes.py#L11)

- **Question:** does the *recommendation* flip across believable values, and where?
- **How:** 1,000 believable (triangular) worlds and 1,000 evenly drawn worlds, plus a one-setting-at-a-time sweep that finds tipping points.
- **PASS rule:** at least 90% agree, and there are no tipping points.
- **Example:** 42% CONFIRM / 16% REFUTE / 42% neutral. Tipping points:
  - team size: helps below ~10, hurts from 10 to ~50, no difference above;
  - backlog: hurts above ~450;
  - training cost: hurts above ~0.05;
  - productivity: hurts between ~1.1 and ~13.

  So it's **INFO**: these *are* the conditions for Brooks' Law.

---

#### The data test (Helix): `data_policy()`, [forrester_all.py:394](../forrester_all.py#L394)

- **Question:** within Helix's *measured* values, is the recommendation stable?
- **How:** Helix's bootstrap estimates of talking, training and learning rates (`outputs/evidence/brooks_helix.json`) replace the assumed ranges. The team is doubled from sizes Helix actually had.
- **PASS rule:** at least 90% agree.
- **Example:**
  - team 3 → 70% "hiring helps" (WARN; measure attrition next);
  - team 6 → 87% "hurts" (WARN; measure the backlog next);
  - team 8 → 94% "hurts" (**PASS**).

#### Quick reference: test → function

| # | test (as named in the report) | function | file:line |
|---|---|---|---|
| V1 | known answers | `known_answers()` | [forrester_all.py:321](../forrester_all.py#L321) |
| V2 | mutants | `mutant()`, `mutants()` | [forrester_all.py:347](../forrester_all.py#L347), [:375](../forrester_all.py#L375) |
| 1 | dimensional consistency | `units()` → `units.check()` | [battery.py:20](../lawkit/battery.py#L20), [units.py:63](../lawkit/units.py#L63) |
| 2 | every parameter matters | `dead_params()` | [battery.py:32](../lawkit/battery.py#L32) |
| 3 | extreme conditions, min/max | `extremes()` | [battery.py:52](../lawkit/battery.py#L52) |
| 4 | extreme conditions, known answers | `extreme_known()` | [forrester_all.py:75](../forrester_all.py#L75) |
| 5 | declared causes do the work | `knockout()` | [battery.py:123](../lawkit/battery.py#L123) |
| 6 | boundary adequacy, structure | `boundary_structure()` + `BOUNDARY` | [forrester_all.py:130](../forrester_all.py#L130), [:121](../forrester_all.py#L121) |
| 7 | boundary adequacy, behaviour | `boundary_behaviour_policy()` (row 1) | [forrester_all.py:212](../forrester_all.py#L212) |
| 8 | boundary adequacy in time | `horizon()` | [battery.py:97](../lawkit/battery.py#L97) |
| 9 | invariants | `invariants()` | [forrester_all.py:140](../forrester_all.py#L140) |
| 10 | negative effort hidden by clamp | `invariants()` (`neg`) | [forrester_all.py:140](../forrester_all.py#L140) |
| 11 | verdicts made by clipping | `clamps()` | [battery.py:70](../lawkit/battery.py#L70) |
| 12 | integration error | `dt_halving()` | [battery.py:86](../lawkit/battery.py#L86) |
| 13 | MR1 dose–response | `dose()` | [battery.py:107](../lawkit/battery.py#L107) |
| 14 | MR2 scale | `scale()` | [battery.py:145](../lawkit/battery.py#L145) |
| 15 | extreme policy | `extreme_policy()` | [forrester_all.py:186](../forrester_all.py#L186) |
| 16 | can any world refute? | `free_lunch()` | [battery.py:137](../lawkit/battery.py#L137) |
| 17 | boundary adequacy, policy | `boundary_behaviour_policy()` (row 2) | [forrester_all.py:212](../forrester_all.py#L212) |
| 18 | behaviour sensitivity | `behaviour_sensitivity()`, `mode()` | [forrester_all.py:246](../forrester_all.py#L246), [:233](../forrester_all.py#L233) |
| 19 | policy sensitivity | `policy_sensitivity()` | [forrester_all.py:264](../forrester_all.py#L264) |
| D | Helix data test | `data_policy()` | [forrester_all.py:394](../forrester_all.py#L394) |
| — | WARN → INFO for findings | `relabel()`, `FINDINGS` | [forrester_all.py:298](../forrester_all.py#L298), [:291](../forrester_all.py#L291) |
| — | lawkit name → Forrester name | `BATTERY_NAMES` | [forrester_all.py:277](../forrester_all.py#L277) |

