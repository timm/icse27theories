# Testing SE laws: what Brooks, aiwork and archpat taught us, and a protocol for the next law

*Status: 2026-10-28. Reproduce with `make laws evidence sensitivity`
(evidence needs clones of apache/helix and Aider-AI/aider). Per-law
detail lives in the evidence cards next to this file:
[brooks](brooks_card.md) (the standard Brooks model),
[aiwork](aiwork_card.md), [archpat](archpat_card.md),
[archpat_cost](archpat_cost_card.md), [sensitivity](sensitivity.md).*

## TL;DR

1. **None of the three laws is true or false on its own terms.** Each
   is a *capacity* (Cartwright) that shows up only when particular
   support factors are present. The useful output is the map of where
   it holds, plus a test of whether a given project sits inside it.
2. **All three turn on the price of pulling the lever:** coordination
   for Brooks, verification for aiwork, migration for archpat. In
   every case the original model either fixed that price or left it
   out, and git history records it worst.
3. **Real data mostly overturned the defaults.**
   - Helix's onboarding drag is about 1/24 of the Brooks default, and
     its coordination optimum is about 5.4 veterans. So doubling Helix's
     typical 3-person core *helps*; doubling it at its peak size
     (6–8) *hurts*.
   - Aider's AI-written lines churn about 1.33× as much as the same
     author's own lines, stable across two model generations. The
     default assumes 3×.
   - Helix's patterned files are only modestly safer than other files
     (0.68–0.83×, against an assumed 0.25×) and no more productive
     (1.05×, against an assumed 2.5×).
4. **Sample size bought nothing.** 100k Monte Carlo runs at ±15% give
   "100% CONFIRMED". The same Brooks claim sampled over its declared
   ranges holds in about 10% of worlds. Robustness depends on how big
   the neighbourhood is, not on how many runs.
5. **The structural battery is necessary but was too weak.** The
   existing 8-test bank passes archpat on every test, yet archpat has
   a dead parameter, a hard-coded benefit channel and free migration.
   Tests must state their expectation first and check the declared
   mechanism, or they can't fail.

---

## 1. What was done

| piece | file(s) | what it is |
|---|---|---|
| generic framework | `lawkit/` | Law spec → 10-test battery → regime map → scenarios → variants → real-project placement → value of information |
| law specs | `lawkit/laws.py` | brooks (the one standard model: late project, finish time, five literature structures, bounded overload), aiwork, archpat, archpat_cost; 8–14 business scenarios and 4–7 mechanism variants each |
| evidence miners | `mine/*.py` | plain-git miners (no Perceval needed) for Helix and Aider |
| runs | `run_laws.py`, `sensitivity.py` | cards + sensitivity tables |
| regression tests | `lawkit/test_lawkit.py` | lawkit reproduces `sd.py` exactly; detectors fire where they should |

"Forrester and metamorphic tests" from the original plan are the
battery's Forrester & Senge / Sterman structure tests plus Chen et al.
metamorphic relations. "Dynamic tests from real-world scenarios" became
evidence placement (section 4).

## 2. Corrections to the earlier Brooks work

These change headline claims in `project_status_report.md`, so they
come first.

| # | issue | evidence | consequence |
|---|---|---|---|
| B1 | **Modified architectures were compared against the *flat* baseline.** Squads and async-docs already beat flat with zero hires (1455 and 1334 vs 1050). | `brooks_modifications.simulate_modified_vectorized`, 0 vs 10 hires per architecture | Measured within each architecture at t=20, hiring still **hurts** in 5 of 6: squads −507, async −665, waves −659, mentor pods −10. Only "synergistic" helps (+145). "Ambassadors restore the crossover at t=11" really says squads beat a flat clique; it says nothing about hiring. |
| B2 | **Score rewards phantom work.** `Done − Todo` keeps rising after the backlog hits 0. | baseline 1050 = done 775 − todo (−275) | Early finishers bank imaginary output. `sd.py` clamps, so its numbers differ. |
| B3 | **Saturation, not the law, produced "100%".** brooks_law, massive_surge and steep_learning give identical results (352.6). | even 5 hires zero all production for 4+ ticks (`train = 5×0.2 = 1.0`) | The verdict is the `max(0, ·)` clamp: each newcomer costs every veteran 20% of their time, i.e. 2 FTE per newcomer. Real Helix data: 0.012 (section 4). |
| B4 | **The ±15% noise is uniform, not triangular as the report says**, and it only covers the neighbourhood of the defaults. | `monte_carlo_brooks.py` noise factors | Local robustness 68–100%; over declared ranges about 10% (the paper's own stress matrix already says "fragile", 12/200). |
| B5 | **Tests that cannot fail.** The boundary-adequacy and tipping-point tests return PASS even with "no crossover found" / "none found". The modified-model invariants print "All physical invariants held" whatever the status. | `forrester_brooks.py`, `forrester_modified.py` | Reported confidence is overstated. |
| B6 | **Report prose is hard-coded.** It says early_hire, break_training and fast_onboarding "break the law", while the table beside it shows CONFIRMED/AMBIGUOUS. | `write_markdown_report` | Regenerate the prose from the data. |
| B7 | **The default Brooks project is not late.** Ten veterans finish 500 items by t≈13 < 20. | `brooks_late` scenario `on_time_project` | Brooks's antecedent ("a late project") was false in the default world. `brooks_late` fixes this (Todo=1000, outcome = completion time). |
| B8 | **The flat clique comm term kills any team above ~20** (comm ≥ 1). | tipping `Vet: CONFIRM→neutral@22.5` | Contradicted by every Apache project with 20+ active developers. The structure fails a family-member test against reality. |

Also in `paper/`: `full_audit.py` swaps the world-/process-conditional
labels relative to `tests.py` and the README typology (this affects
aidebt, not these three laws). The committed `full_audit.csv` still
shows `ERR:ValueError` for extreme_eqn and mr_scale; the uncommitted
`tests.py` 4-tuple fix resolves that.

## 3. Results per law

### Brooks (the standard model)

*Since 2026-11-06 lawkit keeps one Brooks model for every test and report:*
- a late project (backlog 1000), scored by finish time;
- `sd.brooks`' communication and training costs, plus five literature
  structures as uncertain settings (newcomer output, attrition,
  unsplittable work, overtime, rework), each off at the default;
- bounded overload (time left for work = exp(-overhead));
- dt 0.125.

*The four earlier Brooks models are archived in
`outputs/archive/2026-11-06_before_standard_brooks/`.*

- **Machine:** all 10 structure tests pass. The time-step error is 1%.
  The knock-out passes: with talking and training neutralised, hiring helps,
  +2. Every data-free Forrester test passes (`outputs/forrester_all.md`).
- **Robustness:** ±15%: 100% CONFIRM. Prior: 44 / 16 / 40
  (CONFIRM / REFUTE / neutral). Uniform: 27 / 33 / 40.
- **Default effect:** 10 hires delay the finish by 11 ticks (25 → 36).
  The earlier straight-line model said 88, because its overloaded teams
  froze at zero output.
- **Decided by team size and talking cost** (importance `Vet` 0.66,
  `comm_coef` 0.25, `leave` 0.09). The coordination optimum is
  V\*: V(2V − 1) = 2/c, i.e. V\* ≈ 14 for c=0.005 and ≈ 5.4 for Helix's
  c≈0.038. The law holds when the post-hire team overshoots V\*. It
  fails for small cores (`small_core`: REFUTE, +51). Tipping point on
  team size: 7.5.
- **Timing barely matters once the project is truly late:** early, mid
  and last-minute hires all CONFIRM (−12, −11, −9).
- **Variants:** squads (−5), async (−3) and per-person communication (−6)
  shrink the delay. Mentor pods and shared mentoring remove it at the
  default.
- **Helix** (152 months; re-fitted with the same bounded formula):
  c = 0.038 [0.021, 0.066], train = 0.008 [0, 0.037], and newcomers who
  stay are productive almost at once.
  - Doubling the median core of 3 → **REFUTE 70%** (hiring helps).
  - Doubling 6 or 8 → **CONFIRM 87–94%**.
  - Doubling 12 is outside Helix's observed range (max 8): extrapolation.
  - Policy sensitivity within Helix's measured values:
    `outputs/forrester_all.md` §2.
- **Aider** (one maintainer plus drive-bys): REFUTE 87%. The support
  factors for Brooks are absent.

### aiwork (does full AI use lower kept code?)

- **Machine:** knock-out passes (removing churn and verify drag makes AI
  help, +38). The FAIL is a real structural defect: churn + mature
  outflow can exceed the Wip stock in one tick (`churn_base` up to 1,
  `churn_mult` up to 5), so 24% of CONFIRMs exist only because a
  negative stock is clamped to 0. Bound the outflows.
- **Robustness:** ±15%: 100%. Prior: 88%. Uniform: 74%.
- **Decided by speed vs verification, not churn.** Importance:
  `gen_boost` 0.42, `verify_drag` 0.40, `churn_mult` 0.07.
  Approximate steady-state condition for AI to *help*:
  (1 + gen_boost)(1 − verify_drag) > 1 + churn_mult · churn_base /
  (mature_rate + churn_base). The defaults give 0.78 < 1.40, so AI
  hurts mainly because default AI is *slower* (1.3 × 0.6), with churn
  secondary.
- **Scenarios split cleanly:** vibe_coding, boilerplate and
  copilot_rct REFUTE; review_gate, legacy_expert, half_adoption and
  short_sprint CONFIRM. METR, GitClear and Peng sample different
  regions, which agrees with the repo's existing `grid_aiwork`
  reading.
- **Aider evidence** (same author, same period, size-stratified
  14-day blame survival): AI 49.7% vs human 37.2% churn →
  **churn_mult = 0.35 [0.18, 0.54]**. The GPT-4 era (2023-05..2024-06)
  gives **0.32 [0.16, 0.52]**. The churn premium is real, about 6×
  smaller than the default, and stable across model generations.
- **Placement:** measured churn alone → CONFIRM 65%. With METR-like
  speed/verify factors borrowed → 100%; with Peng-like → 3% (REFUTE
  85%). What to measure next: `verify_drag` (gain 0.34), then
  `gen_boost` (0.15). Neither is visible in git.

### archpat (does aggressive migration to patterns repair a bad project?)

- **Machine, reference model:** the dead parameter `pat_strength` FAILs.
  The knock-out FAILs: with patterned code given the same productivity
  and bug rate as legacy, migration still helps (+27), via the
  hard-coded `pay × (1 + 0.5·share)`. Migration is free: `available`
  is computed and never used.
- **Robustness (reference):** ±15%: 100%. Prior: 65%. Uniform: 59%.
  Decided by `gen_leg` / `gen_pat` and `born_*`.
- **Mechanism variants reverse it.** Give migration a price (4 items
  per module) and prior CONFIRM falls from 66% to 20% (REFUTE 59%).
  Add refactoring-induced bugs (Bavota 2012) and pressure-driven
  erosion and it becomes 4% CONFIRM / 88% REFUTE.
- **Helix evidence** (674 production files, 149 patterned; NB-GLM
  controlling size and churn): fix-commit rate ratio
  **0.83 [0.71, 0.93]**, SZZ bug-introduction ratio **0.68 [0.54,
  0.86]** (model assumes 0.25), productivity proxy **1.05 [0.91,
  1.27]** (assumes 2.5).
- **Placement:** with free migration, Helix CONFIRMs (82%). With an
  uncertain price it REFUTEs (94%). The measured ratios barely move
  either number. **Break-even (Helix stocks): migrating a module must
  cost less than about 1 feature-item of effort with no injected bugs,
  or less than about 0.1 if each migration injects 0.25 debt.** That
  price is the measurement that decides the law, and it can be
  measured: RefactoringMiner + SZZ, both kaiaulu-wrapped.

## 4. A conclusive strategy for testing SE laws (goal 1)

What each test family can establish, judged by what actually changed
a conclusion in this study:

| test family | establishes | cannot establish | changed a conclusion here? |
|---|---|---|---|
| Forrester/Sterman structure + metamorphic | the model is a coherent machine (no dead knobs, no hidden channels, no clamp-made verdicts) | that the law is true anywhere | **Yes**: found 7 model defects (B3, B7, B8, archpat ×3, aiwork overshoot) |
| Monte Carlo at ±15% | precision of the default verdict | robustness | **No**: always "100%" |
| Sampling over declared ranges | how much the claim depends on the author's priors | where real projects are | **Yes**: 100% → 6–11% (Brooks) |
| Regime map (tipping + rules) | which support factors decide, and thresholds (V\*, the aiwork inequality, archpat break-even) | which side a real project is on | **Yes**: turned verdicts into conditions |
| Business scenarios | consequences in named worlds | whether those worlds exist | Partly: exposed B7 (not late) |
| Mechanism variants | whether the verdict survives rival structures | which structure is right | **Yes**: archpat reverses |
| Real-project placement | P(law holds here \| measured support factors) | the law's average effect | **Yes**: Helix flips Brooks and archpat |
| Value of information | what to measure next | — | **Yes**: always pointed away from what git records |

**Recommended order** (cheap → expensive; stop when a step fails):

1. **Claim hygiene.** State the lever, arms, outcome *in the law's own
   words*, the antecedent (e.g. "late"), the support factors and the
   causal channels. Stop if the default world violates the antecedent.
2. **Machine battery.** Stop on a dead parameter, a failed knock-out, a
   dt-flip, or clamp-made CONFIRMs above 20%.
3. **Three-neighbourhood robustness.** Never report one number.
4. **Regime map**, then derive the dimensionless threshold
   analytically where possible.
5. **Rival mechanisms** for the term that prices the lever.
6. **Placement** on at least two populations that differ in the
   deciding factor, with a written caveat chain per estimate.
7. **VOI → next measurement**, phrased as a tool + column (kaiaulu
   function where one exists).

**Verdict format.** "`L` plays a causal role in `Y` in populations
where `S` holds; Helix satisfies `S` with probability p; the deciding
unknown is `F`." Not "the law is CONFIRMED".

## 5. Reading the results through Cartwright

- **It worked there vs. it will work here** (Cartwright & Hardie 2012).
  METR, Peng and GitClear each show "it worked there". Section 6 of
  each card asks the policy question for a named project. The two
  answers diverge: Brooks holds in the textbook world and fails for
  Helix's typical core.
- **Laws as capacities in nomological machines** (Cartwright 1983,
  1989, 1999). A law shows up only inside a shielded arrangement of
  support factors. The regime map *is* the machine description: for
  Brooks, a late project + post-hire team > V\*(c) + training drag
  that's large relative to pre-deadline output. Outside it, "adding
  people" is just adding capacity.
- **The causal cake / INUS** (Mackie 1965). The lever is one slice.
  `rules()` and `tipping()` find the other slices. The knock-out
  test checks that the slices the model *declares* are the ones doing
  the work; archpat failed this, because a hidden slice baked the
  conclusion in.
- **Vertical and horizontal search.** Vertical: re-describe the lever
  more abstractly until it travels ("adding people" → "adding
  coordination load past the optimum"; "using AI" → "trading
  verification time for generation speed"; "migrating to patterns" →
  "paying a migration price for lower future defect rates").
  Horizontal: list the support factors that must be present
  (variants + scenarios).
- **Evidence for use is a long chain.** Data → construct → parameter →
  model → verdict. Every mined number carries its caveat list
  (commits ≠ productivity; within-author ≠ randomised; cross-sectional
  pattern associations ≠ the effect of migrating). Sensitivity
  tables show which link holds the weight. For archpat it's the
  *unmeasured* price, not the measured ratios.
- **The streetlight.** VOI always ranked the factor git can't see
  (verification time, migration price, lateness) above the one it
  can (churn, file bug rates). That points the measurement agenda,
  rather than collecting more of what is easy.
- **Borrowing support factors needs a similarity argument.** Plugging
  METR's or Peng's speed/verify numbers into Aider swings the verdict
  from 100% to 3%. Which population Aider resembles is an empirical
  claim that has to be argued, not assumed.
- **Gold standards don't travel by themselves.** The within-author
  Aider design is strong on internal validity (same person, same
  months, same files) and still says nothing about teams with real
  code review. Rigour at the study site does not license export.

## 6. A generic framework for future SE laws (goal 2)

Implemented as `lawkit/` (see its README). A new law is one `Law(...)`
spec plus, optionally, one miner that writes
`outputs/evidence/<law>_<project>.json`. On the untouched `sd.debt`
it immediately reports a hard-coded channel (knock-out FAIL) and a
claim no background in its ranges can refute (100% CONFIRM). Those
are the same failure types found in archpat.

**Reusable knowledge each run extracts:**

1. **A defect catalogue for models**: dead parameters, hard-coded
   channels, clamp-made verdicts, outflow overshoot, outcome ≠ the
   law's words, antecedent false by default. These recur across the
   35 `sd.py` models and can be checked automatically.
2. **Regime thresholds** in dimensionless form (V\*, the aiwork
   inequality, the archpat break-even price). These travel between
   projects where raw parameters don't.
3. **A measurement agenda** (VOI), mapped to tools and columns.
4. **A cross-law heuristic: price the lever first.** Every "doing L
   improves/hurts Y" law is a claim about the sign of
   (benefit − price of L). Before building anything, ask (a) what
   pulling L costs, (b) is that cost in the model, and (c) is it in
   any data source. Missing (b) gives a tautology (archpat); missing
   (c) gives an undecidable verdict (aiwork).
5. **A composition path.** `resources.txt` sketches chaining Brooks →
   aiwork → archpat. lawkit composes laws as one Law over a combined
   model whose factors are the union of the parts' factors. The
   battery then checks the joint machine, and VOI ranks unknowns
   across the chain. Not built yet; the specs are designed so it can
   be.

## 7. Limitations and next steps

- **Python, not `.Rmd` + `.R`.** The miners use plain git, not kaiaulu
  (no R on this machine). Porting `mine/` to kaiaulu notebooks per
  Carlos's format is mechanical but not done. Identity merging
  (`identity_match`) isn't applied.
- **Two projects, one ecosystem each.** Brooks and archpat have Helix
  only (Ambari has pattern4 output too); aiwork has Aider only. No
  other open repo with AI attribution turned up (kaiaulu has none).
  That scarcity is itself a finding.
- **Priors I chose.** The archpat_cost price priors (mode 2
  items/module, 0.25 debt/module) and the aiwork scenario values are
  my judgement. The break-even table exists so readers can replace
  them.
- **Next measurements, by VOI:**
  1. archpat `mig_cost` / `mig_bugs`: RefactoringMiner
     (`parse_java_code_refactoring_json`) + SZZ, in the style of
     Bavota et al. 2012, on Helix and Ambari.
  2. aiwork `verify_drag`: review latency and review-comment counts on
     AI-tagged vs. untagged PRs (GitHub API).
  3. Brooks lateness: JIRA fixVersion due dates (`parse_jira`), so
     "late" is observed rather than assumed.
- **Model fixes to upstream to `paper/sd.py`:** use completion time for
  brooks; bound the aiwork outflows; for archpat, use `available`
  and price migration, remove or wire `pat_strength`, and make the
  0.5 paydown a declared parameter.

## References

Abdel-Hamid & Madnick 1991, *Software Project Dynamics*. Bavota et
al. 2012, "When does a refactoring induce bugs?", SCAM. Becker et al.
2025 (METR). Brooks 1975. Cartwright 1983, *How the Laws of Physics
Lie*; 1989, *Nature's Capacities and their Measurement*; 1999, *The
Dappled World*; 2007, *Hunting Causes and Using Them*. Cartwright &
Hardie 2012, *Evidence-Based Policy: A Practical Guide to Doing It
Better*. Chen et al. 1998 (metamorphic testing). Forrester & Senge
1980. GitClear (Harding) 2024. Mackie 1965 (INUS). Peng et al. 2023.
Perry & Wolf 1992. Scholtes et al. 2016, "From Aristotle to
Ringelmann", EMSE. Sterman 2000, *Business Dynamics*.
