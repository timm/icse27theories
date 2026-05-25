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
| SZZ pairs   | 1,297          | 11,867        | 15,992         |
| refactor evts| 21,945        | 36,204        | 66,037         |
| lifts done  | 8              | 7             | 8              |

**Helix and Ambari both fully lifted (8/8 informable models). junit5
has 7/8 (archpat blocked by Gradle JDK toolchain mismatch — junit5
requires JDK 25, host has Temurin 26).** Total: 23 lifts across 3
projects in one session.

## Headline findings

### F1. **Replicated boundary-adequacy failure: brooksq.leak_rate**

Confirmed on **all three** projects:

| project | leak_rate |
|---------|----------:|
| Helix   | 0.571     |
| junit5  | 0.604     |
| Ambari  | 0.697     |

Model's declared `hi = 0.5`. Three independent Apache-style Java
projects all exceed the bound, monotonically. Not a one-project
quirk — the model's parameter range was specified too narrowly to
span real-world projects. The paper should either widen the bound or
revise the metric definition (`fraction of bugs with fix latency >
30 days`).

### F2. **debt.pay_rate is convergent across projects**

| project | pay_rate_median |
|---------|----------------:|
| Helix   | 0.588           |
| junit5  | 0.590           |
| Ambari  | 0.527           |

Three independent Apache-style Java projects all fall in 0.5–0.6.
Either a real property of how Java OSS projects evolve, or a stable
artifact of RefactoringMiner's detection convention. Either way,
defensible as an observation. Spread is ~12%; the other lifted
metrics (failrate, cfr, brooks_tax) spread by 5–14x.

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

### F4. **brooksq quality thesis: SPLIT empirical verdict across 3 projects**

| project | inj_rate_increase | verdict on thesis        |
|---------|------------------:|--------------------------|
| Helix   | 0.000             | neutral / not triggered   |
| junit5  | -0.011            | mild *refutation*         |
| Ambari  | +0.094            | clear support             |

Brooks's quality-of-output claim ("late hires inject more bugs") is
mixed across projects: Ambari confirms, junit5 mildly refutes, Helix
sits at the boundary. The brooks-velocity side (F3) holds in all 3
projects but with very different magnitudes; the brooks-quality side
is project-dependent.

This split — same hypothesis, divergent verdicts on three
projects — is itself paper material: it argues against claiming
Brooks-Q as a universal SE law without a project-aware caveat.

### F5. **Project regimes for defmap and dora are predicted-bad**

| metric              | Ambari | Helix | junit5 | bad regime says |
|---------------------|-------:|------:|-------:|-----------------|
| defmap.tst_proxy    | 0.098  | 0.375 | 0.150  | low = bad       |
| dora.batch_size     | 48.3   | 73.9  | 38.4   | high = bad      |
| dora.cfr            | 0.341  | 0.049 | 0.272  | high = bad      |
| dora.MTTR_days      | 154    | 88    | 73     | high = bad      |

All three projects operate in the **predicted-bad** regime for these
models. Ambari has the worst defmap (0.098) and longest MTTR (154d)
— consistent with its heavyweight enterprise-Hadoop deployment
profile. junit5 has the smallest batches but highest junit-specific
CFR (likely an issue-tag artifact).

Across the 3 projects, no single project escapes the predicted-bad
regime in *any* of these four metrics. That's a strong family-member
consistency on the "world is in the bad regime" side of the
thesis-state.

### F6. **rework thesis trigger varies by project**

| project | failrate_median | rework regime              |
|---------|----------------:|----------------------------|
| Helix   | 0.019           | safely below 0.5 threshold |
| junit5  | 0.273           | approaching, not at it     |
| Ambari  | 0.274           | approaching, not at it     |

junit5 and Ambari are essentially tied (0.27) and 14x above Helix
(0.019). No project is *in* the rework-dominates regime (≥ 0.5), but
two of three sit close enough that small operational changes could
tip them. Helix has plenty of headroom.

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
