# Project state — SE compartmental models, falsification + Helix calibration

## Intent
A methodology paper (Menzies/Kazman + Umar; Carlos on tooling) on
falsification-based testing of SE system-dynamics models, paired with
real-data calibration via kaiaulu on Apache Helix.

Framing: "What to measure next: model-based triage for SE empirical
research." NIER (ICSE, 4pp) first, EMSE follow-up.

We don't do data collection; we triage what's worth collecting.

## Where things stand

**SD framework** — 33 models implemented as Model(init,step,y,rq,ctrl)
namedtuples in `paper/sd.py`. 9-test bank in `paper/tests.py`. Stress
matrix classifies each model into universal / process-conditional /
world-conditional / fragile. Counts: 14 universal · 12 process-cond ·
4 fragile · 3 world-cond. Run time ~3 s on all 33 (was 1.5 s on 18).
History: started at 18 (original Sterman/Forrester catalogue). Added
15 more on 2026-05-25 from the buildable-today candidates in
`docs/other.html` (ownership, mirroring, pareto, ossfail, ctxswitch,
limits, orgchurn, costchange, scope, deprot, linus, entropy, little,
coordn2, successful).

**Helix data extract** — git_repo (1875+ commits), JIRA (797 issues
fully extracted), GitHub commits/issues/PRs, 116 mbox files from
2012-10 onwards. Carlos uploaded a cleaned version to Drive — see
`data/README.md`. Understand binary outputs are absent (license-gated).

**Radio silence smell — WORKING.** `smells/radio_silence.py` ports
kaiaulu R/smells.R:207 to Python. On Helix: 3 brokers, 4 incidents,
5 Louvain clusters of sizes [42,25,14,13,2]. asebastian@linkedin.com
is the critical boundary spanner between LinkedIn-aligned cluster 3
and the two largest clusters (via mahadev and nehzgnahz).

**Kaiaulu schema audit — DONE.** Walked R/git.R, R/jira.R, R/dv8.R,
R/metric.R, R/src.R, R/identity.R, R/smells.R from the uploaded k.zip.
Definitive parser schemas + known bugs in `kaiaulu_notes/`.

## Feasibility verdict (original 18-model catalogue)
With kaiaulu + 3 open tools (RefactoringMiner, PyDriller-or-SZZ-Unleashed,
Arcan): **10 of 18 are lifted on Helix**, 7 dark because the data
sources don't exist in any open repository, 1 toy (diapers).
Full table in `feasibility/scorecard.md`.

The 15 newer models added 2026-05-25 ship as "pipeline-ready":
SD model defined + V&V cell classified + lift recipe documented, but
the per-project lift run has not been executed yet. Each pipeline-ready
model has an attribute table + tools list in its docs/models/&lt;name&gt;.html
page. See `paper/MODELS_README.md` for the per-model lift-status table.

## Active blockers — none in our way

The 7 not-informable models block on data sources missing FROM THE
FIELD, not from us:
- aiwork, aidebt → no AI authorship attribution exists anywhere
- flaky → no CI logs in any kaiaulu pipeline
- micro → no service architecture data
- teamtopo → no org chart
- burnout → no HR/wellbeing data
- sir, diapers → deliberately abstract

This is itself the paper's headline finding: the field has tools for
code-and-bug-tracker signal but not for these five categories.

## Carlos's new requests (May 6 email)

1. **Deliverable format shift**: produce `.Rmd` notebooks + companion
   `.R` functions file in kaiaulu style, not prose reports. He branches
   into kaiaulu as a PR and code-reviews. See `lifts/` for templates.
2. **GoF detection is back** — pattern4.jar wrapper exists in kaiaulu;
   only blocker was setup. Replaces our Arcan plan for archpat's
   Patterned partition (closer to Ric's original semantics).
3. **5 tool URLs to enable** — Perceval, Depends, scc, RefactoringMiner,
   pattern4.jar. All loosely-coupled system calls in kaiaulu. See
   `CLAUDE.md` for the install list.
4. **Helix data cleaned** — re-fetch from his Drive folder; the
   existing /home/claude/helix copy is the pre-cleanup version.
5. **Carlos + Rick want view-mode access to the Claude project.**

## Next sequence (in priority order)

1. Install Perceval, Depends, scc, pattern4.jar, RefactoringMiner. Verify
   each by calling kaiaulu's wrapper without prior knowledge of the tool.
2. Re-fetch the cleaned Helix dataset from Drive; re-run radio_silence
   for sanity check that numbers reproduce on the clean copy.
3. Convert radio_silence.py to an `.Rmd` + `.R` pair calling kaiaulu's
   identity_match before the smell pass. Demonstrates Carlos's
   sanity-check #2 (comms + source-code merger).
4. Build `lift_brooks.Rmd` end-to-end — the cleanest of the 10
   informable models, no tooling dependencies beyond git+identity.
5. Build `lift_archpat.Rmd` using pattern4.jar for the GoF partition
   (Ric's original semantics; Arcan stays as a fallback).
6. Build `lift_bugs.Rmd` and `lift_learn.Rmd` — the other two
   tool-free informables.
7. Send Rick a status update; loop in Umar; offer view-mode access
   to Carlos and Rick.

## Worked example trio for the paper

Old plan: {brooks, archpat, aiwork}.
New plan: {brooks, archpat, dora} OR {brooks, archpat, brooksq}.
aiwork shifts from empirical to methodological — "what we cannot
yet measure" — naming the data-collection agenda.

## Files in this handoff

```
STATE.md                  this file
CLAUDE.md                 conventions, tool URLs, forbidden moves
models/                   sd.py, tests.py, results.txt (copy from working dir)
kaiaulu_notes/
  schema_audit.md         verified column names per parser
  known_bugs.md           parse_jira/metric.R mismatch + others
lifts/
  lift_brooks.Rmd         stub — kaiaulu-style template
  lift_archpat.Rmd        stub — corrected from earlier audit
  functions.R             companion helpers, kaiaulu style
smells/
  radio_silence.py        working pipeline
feasibility/
  scorecard.md            10-of-17 table
  tool_landscape.md       RefactoringMiner / SZZ / Arcan / pattern4 survey
data/
  README.md               Drive link, Helix paths, dataset list
```

---

## Update 2026-05-24 → 2026-05-25 (Claude Code session)

**Framework: 33 models** (was 17 → +1 congruence on 2026-05-24 → +15
buildable-today on 2026-05-25). 14 universal · 12 process-cond ·
4 fragile · 3 world-cond. See `paper/MODELS_READme.md` for the full
table.

**Projects lifted: 8 of 8 from Carlos's Drive bundle** (Helix,
junit5, Ambari, kaiaulu, airflow, openssl, tomcat, camel). Coverage:
- Helix: 9/10 informable models (only `bugs` missing — needs full JIRA)
- Ambari: 8/8 Java models
- Tomcat: 8/8 (incl. wider BZ regex)
- Camel: 5/8 (debt pending RefMiner background)
- openssl: 6/8 (no Java tools — no archpat/debt)
- airflow: 6/8 (Python — no archpat/debt)
- kaiaulu: 5/8 (R — no archpat/debt)
- junit5: 7/8 (Gradle JDK toolchain mismatch blocks archpat)

**~60 lift CSVs in `outputs/`** across (model × project) cells.

**Key replicated findings** (`findings.md` for full prose, `sanity.md`
for per-cell status):
- **F0 model-bound failures across 5 params** (25/103 cells flagged):
  brooksq.{leak_rate, inj_rate}, archpat.{Legacy, Patterned},
  learn.Jr, congruence.{Brokers, Clusters}. Bounds were set at
  "small project" scale; mature OSS systematically exceeds.
- **F1 brooksq.leak_rate = 0.5 hi** violated on 7/8 projects
  (monotonic 0.42→0.93 across 5 languages).
- **F2 debt.pay_rate convergent** across 4 Java projects (0.36–0.59).
- **F3 Brooks effect 11x spread** across 8 projects (Ambari 0.029 →
  airflow 0.311 with n_hires ≥ 50).
- **F4 brooksq quality thesis SPLIT** across 3 projects (Ambari
  +0.094 supports, junit5 -0.011 refutes, Helix 0 neutral).

**Tools installed today** (no sudo for most): PyDriller (venv),
Perceval (venv), R 4.6 + kaiaulu pkg + CRAN deps, Temurin OpenJDK 26
(brew --cask, needed user sudo), Maven 3.9.16, scc 3.7.0,
RefactoringMiner 3.0.10, pattern4.jar (CLI breakthrough discovered),
Depends 0.9.7, git-filter-repo 2.47.0, networkx + python-louvain.

**Outstanding**:
- Camel RefMiner still running in background (~24k commits, large)
- `bugs` lift blocked on full Helix JIRA dump (Carlos's Drive has it)
- `sir` data path opened via Depends (multi-snapshot pipeline deferred)
- GH push blocked by 5 files >100MB; `scripts/fix_gh_push.sh`
  prepared (uses git-filter-repo --strip-blobs-bigger-than 100M)

**Key docs**: `findings.md` (paper-relevant observations),
`TIMETABLE.md` (per-model hours), `sanity.md` (per-cell sanity
status), `diary/` (collaborator email archive), `outputs/` (raw CSVs).

---

## Update 2026-05-29 — scorecard data-tier rows standardised

**Scorecard schema unified across all 34 model pages.** Previously
only `brooks.html` (hand-tuned) carried the 5 data-tier prudence rows
(`param_plausibility`, `boundary_adq_data`, `calibrated_rq_rerun`,
`family_member_coherence`, `behavior_reproduction`). The other 33
auto-generated pages showed only structural + effect rows.

Today's change to `docs/scripts/gen_rich.py::render_scorecard_table`
appends those 5 rows auto-derived from `boundary_check.csv`,
`calibrated_verdicts.csv`, and `lifts.csv`. Brooks's hand-tuned
data-tier subtable was rewritten to the same 2-column schema for
uniformity.

**Why this matters**: F0 boundary-adequacy violations (archpat.Legacy
out_of_range on Helix + Ambari, brooksq.leak_rate out_of_range on
10/16, learn.Jr out_of_range on 3/38) now surface at scorecard glance
on every page rather than only via prose callouts on selected pages.

**Models without lift data** (aiwork, aidebt, burnout, teamtopo,
flaky, micro, sir, diapers) display honest `N/A · no lift rows` on
each data-tier row — making the "structurally absent data category"
finding visible at scorecard level.

Schema documented in `paper/MODELS_README.md` under "Scorecard
structure". Total scorecard now 18 rows per page (8 structural prudence
+ 4 effect + 1 cell + 5 data-tier).

Both gates (audit_staleness.py, check_pages.py) pass after the change.
