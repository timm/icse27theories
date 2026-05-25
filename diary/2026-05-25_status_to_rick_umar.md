# Status update — Rick + Umar (draft)

> **Draft for Tim to review before sending.** Hand-edit greeting,
> tone, anything else. Pull whatever bits are useful.

---

Hi Rick, Umar,

Quick status on the ICSE-27 SD-falsification methodology paper. Tim
ran a long Claude Code session over 2026-05-24/25; this is what the
repo contains as of `<commit-hash>`. Repo:
http://github.com/timm/icse27theories

## What's working end-to-end

**18-model SD framework** (`models/sd.py`) — 17 Tim-coded + 1 new
this session (`congruence`, Newman/broker-loss thesis; lands in
"universal" 2×2 cell).

**8 Apache projects lifted** (Helix, Ambari, junit5, kaiaulu,
airflow, openssl, tomcat, camel):
- Helix: 10/10 informable models calibrated end-to-end
- Others: 6-8/10 each, depending on whether the project has the
  needed comm channel (mbox / JIRA / GH issues) and is compilable
  (Java + Maven projects also get archpat + debt via
  RefactoringMiner + pattern4)

**~60 lift CSVs** in `outputs/`. **5 paper-relevant findings** in
`findings.md`:
- **F0**: 5 model parameters have boundary-adequacy failures across
  multiple projects. The bounds in `sd.py` were specified at
  "small project" scale; mature OSS exceeds them. Recommend widening
  in `models/sd.py` before any further calibration work.
- **F1**: brooksq.leak_rate > model.hi=0.5 on 7 of 8 projects,
  spanning Java/Python/R/C codebases (monotonic 0.42 → 0.93).
  Definitive structural model-bound failure.
- **F2**: debt.pay_rate (refactor-activity proxy via RefactoringMiner)
  is the most family-coherent metric in the bank — 5 Java projects
  fall in 0.36–0.59. Compare to failrate which spreads 15x.
- **F3**: Brooks effect (velocity drop after late hires) varies 11x
  across the 8 projects, with both signs. Project-dependent.
- **F4**: brooksq quality thesis ("late hires inject more bugs")
  gets a **split verdict** on 3 projects — Ambari +0.094 supports,
  Helix 0 neutral, junit5 -0.011 refutes. Argues against a universal
  SE-law framing.

**5 .Rmd notebooks** in kaiaulu vignette style, knit to HTML, ready
to branch into kaiaulu as PRs per Carlos's §3 request:
- `lifts/lift_brooks.Rmd`  (git-only)
- `lifts/lift_bugs.Rmd`    (GH issues, Goel-Okumoto fit)
- `lifts/lift_learn.Rmd`   (git+identity, workforce flow)
- `lifts/lift_archpat.Rmd` (pattern4 + RefactoringMiner + SZZ)
- `lifts/lift_congruence.Rmd` (mbox + identity_match across BOTH
  sources — Carlos's §2 sanity check #2 demonstrated)

## Carlos's §4 sanity check (tool calls without prior knowledge)

| wrapper | tool | status |
|---|---|---|
| parse_gitlog | Perceval | ✓ verified, 44k rows on Helix |
| parse_line_metrics | scc | ✓ verified, 1,835 rows |
| parse_gof_patterns | pattern4 (XML parser) | ✓ verified, 687 rows |
| parse_dependencies | Depends | ✗ kaiaulu filename bug (see kaiaulu_notes/known_bugs.md §"NEW 2026-05-25") |
| parse_java_code_refactoring_json | RefactoringMiner | ✗ kaiaulu path-regex bug + stdout-parsing bug (same notes file) |

3 of 5 verified end-to-end. The 2 failures are kaiaulu source bugs,
not our setup — both have one-line patches suggested in
`kaiaulu_notes/known_bugs.md`. Underlying tools all installed and
working (we use them via direct CLI in `lifts/functions.R`).

## Pattern4 CLI breakthrough

The canonical pattern4.jar at Concordia declares Main-Class:
`gr.uom.java.pattern.gui.MatrixFrame` and opens a Swing GUI on
`java -jar pattern4.jar`. We discovered (reading the decompiled main)
that `MatrixFrame.main(args)` dispatches:

```
if (args.length == 4 && args[0]=="-target" && args[2]=="-output") {
    new Console(inputDir, outputXML);  // batch mode!
}
```

So `java -jar pattern4.jar -target <classes-dir> -output <xml.xml>`
runs the batch detector. Earlier session memory had "pattern4 is
GUI-only" — wrong, corrected.

## What still needs your help

- **Rick**: an `archpat.pat_strength` parameter is declared in
  `models/sd.py:archpat()` init but unused in the `step()` body. We
  flagged it for you in the lift_archpat notebook. Want to know if
  it should drive the step equation.
- **Both**: F0 (the 5-parameter boundary-adequacy failure) suggests
  widening bounds in `models/sd.py`. Before doing that, is the
  "small-scale assumption" intentional (to keep extreme_eqn tests
  meaningful) or just a heuristic Tim picked?
- **Carlos**: re-fetch the cleaned Helix dataset from Drive so we can
  sanity-check that radio_silence numbers reproduce on the cleaned
  copy (per your §1).

## View-mode access to Claude Code project

Claude Code is a local-first CLI — no native view-mode link
analogous to Google Docs sharing. The closest equivalent is
`git clone` the repo and read:

- `findings.md` — paper-relevant observations
- `TIMETABLE.md` — per-model wall-clock + status grid
- `sanity.md` — per-cell bug-count + identity-bridge status
- `STATE.md` — original framing + session updates
- `diary/` — collaborator correspondence archive (this email goes here)
- `outputs/cross_project.csv` — 8-project metric matrix
- `lifts/*.html` — rendered notebooks ready for PR review

If you want a real-time view of the next session, screen-share works.
Anthropic Console projects (for claude.ai) is a separate product
that doesn't apply to the CLI.

## Time budget recap

Pre-session estimate (Claude.ai): ~1 work-week for 3 priority models.

Actual: 8 projects × ~10 lifts each + 5 polished .Rmd notebooks +
3 boundary-adequacy paper findings + 1 SD model addition + 1
methodology fix + 1 tool-CLI breakthrough, all in ~12 hours of
session time across two days.

The factor-of-X overestimate is itself a paper paragraph (see
`NOTES.md` for Tim's running diary on the meta-narrative).

---

Cheers,
Tim (drafted by Claude Code)
