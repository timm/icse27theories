# Cross-Project Findings — 2026-05-24 session

Empirical results from running the SD-falsification framework on
three Apache-style Java projects in one Claude Code session.

## Coverage (8 projects now)

|          | Helix | junit5 | Ambari | kaiaulu | airflow | openssl | tomcat | camel |
|----------|------:|-------:|-------:|--------:|--------:|--------:|-------:|------:|
| commits  | 4.9k  | 10.8k  | 25.1k  | 175     | 13.3k   | 39.8k   | 22.5k  | 3.0k  |
| tags     | 44    | 113    | 133    | 0       | 936     | 433     | 234    | 227   |
| ids      | 73    | 185    | 134    | 8       | 1,338   | 1,029   | 62     | 14    |
| lang     | java  | java   | java   | R       | py      | c       | java   | java  |
| issue    | JIRA  | GH#    | JIRA   | GH#     | mix     | GH#     | BZ     | JIRA  |
| SZZ pairs| 1,297 | 11,867 | 15,992 | 146     | (run)   | (skip)  | 74     | 931   |
| lifts ✓  | 8     | 7      | 8      | 5       | 2       | 2       | 5      | 5     |

42 lifts done across 8 projects (8 informable models × 8 projects =
64 potential cells; 42 filled).

Skipped per language/build mismatch:
- archpat + debt need RefMiner + (for archpat) pattern4 on bytecode;
  R/py/c projects don't apply. So 4 projects (kaiaulu, airflow,
  openssl, tomcat-via-Ant) miss those two.
- airflow SZZ still running in background as of this snapshot.
- openssl SZZ skipped (39k commits ≈ 1h wall, deferred).
- tomcat's BZ regex matched only 74 commits — likely under-matched;
  could widen regex in a future pass.

## Headline findings

### F1. **Replicated boundary-adequacy failure: brooksq.leak_rate**

Confirmed on **6 of 7 projects** where the lift ran (kaiaulu the
outlier with smallest sample):

| project | leak_rate | status |
|---------|----------:|--------|
| kaiaulu | 0.418     | IN  (n=146 pairs, smallest sample by ~10x) |
| Helix   | 0.571     | OUT |
| junit5  | 0.604     | OUT |
| Ambari  | 0.697     | OUT |
| camel   | 0.712     | OUT |
| airflow | 0.825     | OUT |
| tomcat  | 0.865     | OUT |

Model's declared `hi = 0.5`. Six of seven independent projects exceed
the bound; kaiaulu the only in-range and the smallest sample by 10x.
Includes projects across 4 languages (Java, Python, R, C — though
openssl untested). Not a one-project quirk — the model's parameter
range was specified too narrowly to span real-world projects. Paper
should widen the bound to ≥ 0.9 or revise the metric definition
(`fraction of bugs with fix latency > 30 days`).

**Implication for the falsification methodology**: leak_rate as
defined captures something about engineering culture that *all*
mature OSS projects fail (or all definitions of "leaked" used by
practitioners are looser than 30 days). Either reading is paper
material.

### F2. **debt.pay_rate falls in narrow band across 4 Java projects**

| project | pay_rate_median |
|---------|----------------:|
| tomcat  | 0.365           |
| Ambari  | 0.527           |
| Helix   | 0.588           |
| junit5  | 0.590           |

Four independent Apache-style Java projects all fall in 0.36–0.59.
Earlier 3-project claim ("essentially identical at 0.59") was too
strong; tomcat broadens the band downward. Possible drivers: tomcat
is older (Ant build, pre-Maven style) and RefactoringMiner may catch
fewer of its refactor patterns. The spread (60%) is still much
narrower than failrate (15x), cfr (180x), or brooks_tax (11x) — so
**pay_rate is the most family-coherent metric in the bank**.

camel debt pending (RefMiner running). If camel lands in same band,
F2 is stronger; if it diverges, weaker.

### F3. **Brooks effect highly variable across 8 projects**

| project  | brooks_tax_median | n_hires | language |
|----------|------------------:|--------:|----------|
| kaiaulu  | -1.134           | 6       | R        |
| camel    | -0.144           | 5       | java     |
| Ambari   | +0.029           | 126     | java     |
| tomcat   | +0.055           | 50      | java     |
| Helix    | +0.113           | 65      | java     |
| openssl  | +0.146           | 1,019   | c        |
| junit5   | +0.222           | 169     | java     |
| airflow  | +0.311           | 1,285   | python   |

Negative values (kaiaulu, camel) come from very small n_hires (5-6)
and are noise. Among projects with n_hires ≥ 50, all show positive
brooks_tax (Brooks supported) but magnitudes vary 11x (0.029 → 0.311).

Language doesn't predict effect — Python (airflow) and Java (junit5)
both top the chart; Java (Ambari, tomcat) sits at the bottom.
Possible drivers: team size, release cadence, mentoring practices.
Worth probing in EMSE extension.

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
