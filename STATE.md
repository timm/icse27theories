# Project state — SE compartmental models, falsification + Helix calibration

## Intent
A methodology paper (Menzies/Kazman + Umar; Carlos on tooling) on
falsification-based testing of SE system-dynamics models, paired with
real-data calibration via kaiaulu on Apache Helix.

Framing: "What to measure next: model-based triage for SE empirical
research." NIER (ICSE, 4pp) first, EMSE follow-up.

We don't do data collection; we triage what's worth collecting.

## Where things stand

**SD framework** — 17 models implemented as Model(init,step,y,rq,ctrl)
namedtuples in `models/sd.py`. 9-test bank in `models/tests.py`. Stress
matrix classifies each model into universal / process-conditional /
world-conditional / fragile. Currently aidebt sits in process-conditional
(live empirical debate); archpat sits in fragile. Run time ~1.5s on all 17.

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

## Feasibility verdict for the 17 models
With kaiaulu + 3 open tools (RefactoringMiner, PyDriller-or-SZZ-Unleashed,
Arcan): **10 of 17 models become fully informable on Helix**, 7 stay
not informable because the data sources don't exist in any open
repository. Full table in `feasibility/scorecard.md`.

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
