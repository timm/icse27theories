# Cross-Project Findings — 2026-05-24 session

Empirical results from running the SD-falsification framework on
three Apache-style Java projects in one Claude Code session.

## Coverage

|             | Helix          | junit5        | Ambari         |
|-------------|----------------|---------------|----------------|
| commits     | 4,898          | 10,784        | 25,090         |
| tags        | 44             | 113           | 133            |
| identities  | 73             | 185           | 134            |
| span        | 14.8 years     | 11 years      | 14+ years      |
| issue scheme| JIRA HELIX-N   | GH #N         | JIRA AMBARI-N  |
| lifts done  | 8              | 7             | 2 (+SZZ pending)|

Helix is fully lifted (8/8 informable models). junit5 has 7/8 (archpat
blocked by Gradle JDK toolchain mismatch). Ambari has brooks + learn
done, others awaiting SZZ pass.

## Headline findings

### F1. **Replicated boundary-adequacy failure: brooksq.leak_rate**

Lifted on both Helix (0.571) and junit5 (0.604). Model's declared
`hi = 0.5`. Both projects exceed the bound. Not a Helix quirk — the
model's parameter range was specified too narrowly to span real-world
projects. The paper should either widen the bound or revise the
metric definition.

### F2. **debt.pay_rate is convergent across projects**

Helix: 0.588. junit5: 0.590. Two independent Java OSS projects show
essentially identical refactoring-activity-per-90-day-window. Either
a real property of how Java OSS projects evolve, or a stable artifact
of RefactoringMiner's detection. Either way, defensible as an
observation.

### F3. **Brooks effect varies 8x across projects**

| project | brooks_tax_median |
|---------|------------------:|
| Ambari  | 0.029            |
| Helix   | 0.113            |
| junit5  | 0.222            |

Brooks thesis (late hires hurt veteran velocity) is supported on all
three but with very different magnitudes. junit5 shows the strongest
effect; Ambari the weakest. Possible explanations: different team-size
distributions, different mentoring practices, different release
cadences. Worth probing in EMSE extension.

### F4. **brooksq quality thesis NOT supported on Helix**

`inj_rate_increase` median = 0.0 on Helix; -0.011 on junit5 (slight
*decrease*). Brooks's quality-of-output claim ("late hires inject
more bugs") fails on both projects' median. The brooks-velocity side
(F3) holds; the brooks-quality side falsifies.

This is the cleanest single-thesis falsification result from the
session.

### F5. **Project regimes for defmap and dora are predicted-bad**

| metric              | Helix       | junit5     | thesis-bad threshold |
|---------------------|------------:|-----------:|---------------------:|
| defmap.tst_proxy    | 0.375       | 0.150      | model says low = bad |
| dora.batch_size     | 73.9        | 38.4       | model says high = bad|
| dora.cfr            | 0.049       | 0.272      | high = bad           |

Both projects operate in the **predicted-bad** regime for these
models. defmap predicts high leaked defects under low tst — Helix
confirms (876 leaked vs 421 caught). dora predicts CFR rises with
batch size — both projects in elevated-CFR territory.

### F6. **rework thesis NOT triggered on Helix; mildly triggered on junit5**

Helix failrate=0.019 (safely below 0.5 dominance threshold). junit5
failrate=0.273 (still below 0.5 but 14x higher). Helix isn't even
near the rework-dominates regime; junit5 is approaching but not at
it. Thesis predictions never reach the verdict-domain on these
projects' operating points.

### F7. **Calibrated `rq()` gaps shift meaningfully without flipping verdicts**

All 8 models keep their default CONFIRM verdict under calibrated
backgrounds, but gap magnitudes change up to 7x:

|         | default gap | calibrated gap | effect            |
|---------|------------:|---------------:|-------------------|
| brooksq | -45.9       | -58.7          | strengthened 30%  |
| debt    | -56.7       | -8.83          | blunted 7x        |
| dora    | -45.4       | -20.0          | blunted 2x        |
| learn   | -5.28       | -6.54          | strengthened 25%  |
| archpat | +229        | +390           | strengthened 70%  |

Helix's high `pay_rate` blunts the debt thesis (effective paydown);
its high `leak_rate` and `Legacy` count strengthen brooksq + archpat
theses (the project is closer to model-predicted regimes).

### F8. **Stress-matrix typology covers all 4 cells**

18-model audit:
- 10 **universal** (debt, sir, rework, defmap, aiwork, flaky, dora,
  teamtopo, congruence + one duplicate above)
- 5 **process-conditional** (diapers, bugs, learn, micro, burnout)
- 3 **fragile** (brooks, brooksq, archpat)
- 1 **world-conditional** (aidebt — the regime-crossover model)

That all 4 cells of the 2x2 are populated is itself a methodology
robustness signal. congruence (new this session) lands in the most
robust cell.

## Methodology footnotes

- **pattern4.jar IS CLI-callable** despite GUI-default manifest.
  Invocation: `java -jar pattern4.jar -target <classes> -output <xml>`.
  Earlier session memory was wrong; corrected in
  `~/.claude/.../reference_pattern4_gotcha.md`.
- **kaiaulu API drift since templates were written**: parse_gitlog
  emits `Tue Jun 21 18:56:46 2011 -0700` date format (not
  `YYYY-MM-DD HH:MM:SS` per template); `identity_match` now requires
  `label = "identity_id"` argument. Both patched in the lifts.
- **learn.train_rate boundary touch was a methodology artifact**.
  Using slice_days=365 with jr_max_days=365 forced every surviving
  Jr to graduate, saturating train_rate at 1.0. Fixed with 90-day
  slices annualised.
- **Java 26 (Temurin) compiles Helix** via `mvn compile -pl helix-core
  -am -DskipTests` (~1min, 950 .class files). Same Java 26 cannot
  build junit5 because junit5's Gradle toolchain pins JDK 25.

## Hours

Logged ~5.5h of active session today. See `TIMETABLE.md` for the
per-step breakdown. Pre-2026-05-24 hours are claude.ai
reconstructions, not measurements.
