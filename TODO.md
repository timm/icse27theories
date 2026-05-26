# TODO.md — handoff for next session (post-compaction)

Snapshot 2026-05-25. Repo `github.com/timm/icse27theories` @ `main`.

## DECIDED

- **Paper**: ICSE 2027 NIER (4pp) first, EMSE follow-up. Topic:
  falsification-based testing of SE system-dynamics models, paired
  with kaiaulu real-data calibration. Anonymous double-blind.
- **Site name**: MYTHS = Models Yielding Testable Hypotheses in Software.
- **Family**: 8 Apache-style OSS projects — Helix, junit5, Ambari,
  kaiaulu, airflow, openssl, tomcat, camel. (cleaned Helix bundle on
  disk now too.)
- **Deliverable format** (Carlos's §3): kaiaulu-vignette-style
  `.Rmd` + companion R helpers in `lifts/functions.R`. Each lift is
  PR-reviewable into kaiaulu as student-style code review.
- **Card ordering**: diapers first, then year-desc. Years are on
  both cards + page titles.
- **Source tiers for the 47-candidate "other" inventory**:
  - **A** = peer-reviewed archival (DOI/IEEE/ACM/journal) — 21 models
  - **B** = book / grey-lit anchor; partial peer-reviewed companion — 15
  - **C** = tacit / named-only / not formally modelled — 11
- **brooks.html is hand-tuned** (`manual=True` in `scripts/gen_rich.py`);
  the other 17 model pages regenerate from gen_rich.py.

## DONE

### Framework
- 18 SD models in `models/sd.py` (added `congruence` as #18 — Newman
  broker-loss thesis, lands in "universal" cell).
- `models/tests.py` 9-test V&V bank intact.
- `outputs/full_audit.csv` — 18 models × stress matrix + 8-test bank
  (~91% PASS overall).

### Lifts (10 informable models × 8 projects, ~63 CSVs in `outputs/`)
- Helix: 10/10 informable lifted (brooks, brooksq, bugs, debt,
  rework, learn, defmap, dora, archpat, congruence).
- Ambari: 8/10.
- tomcat: 8/10.
- camel: 7/10 (archpat blocked by mvn-on-Java-26 dep issues).
- junit5: 7/10 (archpat blocked by Gradle JDK 25 toolchain).
- airflow: 6/10 (Python — no archpat / debt).
- openssl: 6/10 (C — no Java tools).
- kaiaulu: 7/10 (R — no archpat / debt; bugs lifted via GH issues).

### Analyses (S13–S16 in TIMETABLE schema)
- `outputs/boundary_check.csv` — 8 models × 8 projects. **17
  out_of_range cells, 8 at_boundary, 78 in_range.**
- `outputs/calibrated_verdicts.csv` — 9 models recalibrated; all
  retain CONFIRM; gap magnitudes shift meaningfully.
- `outputs/cross_project.csv` — 9 models × 8 projects key-metric grid.
- `findings.md` — 5 F-findings (F0 boundary failures, F1 leak_rate
  7/8, F2 pay_rate convergence, F3 Brooks 11× spread, F4 brooksq
  split verdict).

### Tools installed (no further sudo needed)
- PyDriller 2.9 (`.venv`), Perceval 1.4.7
- R 4.6 + kaiaulu pkg + igraph + jsonlite
- Temurin OpenJDK 26 (user-sudo'd)
- Maven 3.9.16
- RefactoringMiner 3.0.10
- pattern4.jar (Concordia)
- Depends 0.9.7
- scc 3.7.0
- networkx + python-louvain (mbox graph)
- git-filter-repo 2.47.0

### Carlos's §4 sanity checks
- 3/5 kaiaulu wrappers verified: `parse_gitlog`, `parse_line_metrics`,
  `parse_gof_patterns`. 2 have **kaiaulu source bugs** documented in
  `kaiaulu_notes/known_bugs.md` (one-line patches suggested):
  - `parse_dependencies` — reads `<name>.json` but Depends
    `--granularity=file` writes `<name>-file.json`.
  - `parse_java_code_refactoring_json` — (a) `regex=".git"` matches
    `_git` in `git_repo`; (b) parses RefMiner stdout mixed with
    INFO log lines.

### Site (`/docs`)
- GitHub Pages enabled on `/docs`. `.nojekyll` present.
- `docs/index.html` — 18 model cards + "+47 more" card linking to
  other.html. Diapers first, year-desc.
- 18 model pages with 6 panes each (Summary / Model / Lift / Inputs /
  Scorecard / Results) + peer-reviewed References table per page.
- `brooks.html` hand-tuned (~630 lines); the rest regenerate from
  `scripts/gen_rich.py`'s `M` dict.
- `docs/other.html` — 47-candidate inventory + per-candidate tier +
  data-on-disk verdict.
- Site anonymised: no team names. `Anonymous submission · ICSE 2027`
  footer.

### Data
- `~/Downloads/helix/` (pre-cleanup) + `data/helix_clean/`
  (Carlos cleaned, from his Drive bundle). radio_silence reproduces
  identically on both — cleaning didn't affect comm graph.
- 6 dataset zips extracted from `/Users/timm/tmp/Claude SE Models-…zip`.

## LEFT (priority order)

### High value, low effort
1. **Send Rick/Umar status email** — draft in
   `diary/2026-05-25_status_to_rick_umar.md`. Tim's action.
2. **Ping Rick on `archpat.pat_strength`** — declared in init but
   unused in `step()`. Dead code or missing equation?
3. **Anonymous mirror for submission**: `github.com/timm/...` URL
   reveals identity. Use anonymous.4open.science or zip `docs/` as
   supplementary material.

### Buildable today (15 candidates ranked in `docs/other.html`)
4. **9 A-tier with HAVE-data** (ordered by paper impact):
   ownership, orgchurn, pareto, mirroring, little, entropy,
   costchange, deprot, ossfail.
5. **6 B-tier with HAVE-data**: coordn2, scope, ctxswitch, limits,
   successful, linus.

   Net coverage if all 15 built: **33 models with full lifts**.

### Needs new pipeline (~1-2 days each)
6. **15 partial-data candidates** in `other.html`. Most leverage:
   `exposure` (NVD CVE-to-commit pipeline), `flaky` (GH Actions
   retry-pattern parser), `testshape` (path-prefix-based test-tier
   classifier).

### Methodology gaps
7. **Widen `models/sd.py` bounds** per F0:
   `brooksq.leak_rate hi 0.5→1.0`,
   `brooksq.inj_rate hi 0.5→5.0`,
   `archpat.Patterned hi 200→1000`,
   `archpat.Legacy hi 200→3000`,
   `learn.Jr hi 100→2000`,
   `congruence.Brokers hi 20→100`,
   `congruence.Clusters hi 20→100`.
   (Wait for Tim/Ric nod before editing.)
8. **`sd.opt()` calibration pass** — currently rq() reruns at default;
   actual fitting of intr_rate etc not done.
9. **S4 dim_check** still NOT BUILT in `tests.py`. Other tests cover
   most of the ground but the placeholder remains.
10. **Behavior reproduction (S17)** + **behavior prediction (S18)** —
    never attempted. Need monthly historical CSVs to compare against
    sim trajectories.

### Blocked
11. **Pattern4 on junit5** — Gradle pins JDK 25; we have 26. Skip
    or install JDK 25 alongside.
12. **Pattern4 on camel** — Maven dep resolution fails on Java 26
    even with `-Dcheckstyle.skip=true`.
13. **Full Helix JIRA dump** — Carlos's bundle has 50 issues, 0 of
    type Bug. Need full pull or his cleaned JIRA. Until then, `bugs`
    on Helix uses GH issues route.
14. **`drift` / `cace` / `collapse` / `aiwork` / `aidebt`** — no ML
    or AI-authored data on disk. Structurally absent on the family.

## GOTCHAS

1. **macOS HFS+ case-insensitive**: `TIMETABLE.md` and `timetable.md`
   are the SAME file. Don't write to both expecting separate.
2. **Perceval date format**: `"Tue Jun 21 18:56:46 2011 -0700"`
   (git default), NOT `"%Y-%m-%d %H:%M:%S"`. Use
   `format = "%a %b %d %H:%M:%S %Y %z"` everywhere.
3. **kaiaulu `identity_match` signature**: now requires
   `label = "identity_id"` (or `"raw_name"`). Without it: "argument
   'label' is missing". Older templates omit it.
4. **kaiaulu `parse_dependencies` bug**: reads `<name>.json` not
   `<name>-file.json`. One-line patch documented in
   `kaiaulu_notes/known_bugs.md`. Until patched, call Depends
   directly via `java -jar tools/depends/...`.
5. **kaiaulu `parse_java_code_refactoring_json` bugs**: (a) the
   `.git`-strip regex eats `_git_` in path. (b) parses RefMiner
   stdout that contains INFO log lines. Until patched, call
   RefMiner directly via `tools/RefactoringMiner-…/bin/RefactoringMiner`.
6. **pattern4 CLI**: `java -jar pattern4.jar -target <classes-dir>
   -output <xml>` (NOT GUI-only despite Main-Class). Earlier session
   memory had this wrong; corrected in
   `~/.claude/projects/.../memory/reference_pattern4_gotcha.md`.
7. **learn methodology fix**: 365-day slice + 365-day Jr cutoff
   saturated `train_rate` at 1.0 for all 8 projects. **Use 90-day
   slices (annualised)** —
   `estimate_transition_rates(slice_days = 90)`. Already wired.
8. **camel detached HEAD on tag camel-1.6.0**: `git -C
   data/camel/git_repo log` shows 2,994 commits. RefMiner on `main`
   branch finds 65,803 commits — full history. Always specify
   `main` for camel ops.
9. **camel mvn fails on Java 26** — even with `-Dcheckstyle.skip=true`.
   archpat lift on camel deferred.
10. **junit5 Gradle pins JDK 25** via toolchains. Skip archpat lift
    on junit5 unless you install JDK 25.
11. **GitHub 100MB hard limit** — `data/tomcat/mbox/tomcat-dev.mbox`
    (1.6GB) and 5 zips (160–770MB) were blocked. `.gitignore`
    now covers `data/*/mbox/*.mbox`, `data/_zips/`,
    `data/*/mod_mbox/`, `data/*/bk_mod_mbox/`, `data/*/pipermail/`,
    `data/*/jira/`, `data/*/github/`, `data/*/derived/refminer*.json`,
    `data/helix_clean/`, `data/*/git_repo/`. If push ever fails on
    100MB again, run `scripts/fix_gh_push.sh` (uses git-filter-repo;
    destructive history rewrite — user must authorize).
12. **Anonymous URL still reveals identity**: `github.com/timm/…`
    contains username. Don't share the repo URL as supplementary
    material; use anonymous.4open.science mirror.
13. **Congruence model defaults match Helix's measured values**
    (Brokers=3, Clusters=5). Partly circular — model was tuned to
    a prior radio_silence run. Treat airflow (4/7) + tomcat (39/33)
    as the real falsification test bed for congruence.
14. **Bugs lift R port uses grid-search Goel-Okumoto** (6×6 = 36
    candidates). Replace with `nls()` or `optim()` for publication.
15. **`scripts/gen_rich.py` is the source of truth** for 17 model
    pages. Edits to `docs/models/<name>.html` will be overwritten
    on next regen. To preserve hand-tuning, set `manual=True` in
    the `M[<name>]` dict — generator skips. (`brooks` already is.)
16. **The `docs/index.html` is HAND-edited**, not generated.
    Regenerating model pages won't touch the index. If you add a
    new model, update both `gen_rich.py` and the index by hand.
17. **diary/ vs NOTES.md**: `NOTES.md` is Tim's personal session
    diary (his own writing). `diary/` is shared correspondence
    archive (collaborator emails + prompt drafts). Don't write
    Claude-generated content into `NOTES.md`.

## KEY DOCS POINTERS

- `findings.md` — 5 F-findings, paper-prose.
- `TIMETABLE.md` — per-model wall-clock log, S0–S20 schema.
- `sanity.md` — per-cell bug-count + identity-bridge status (Carlos §1+§2).
- `STATE.md` — original framing + 2026-05-24/25 session update.
- `NOTES.md` — Tim's personal session diary (don't auto-edit).
- `diary/` — emails, prompts, status drafts.
- `kaiaulu_notes/known_bugs.md` — kaiaulu source bugs (5 total).
- `docs/index.html` — site root.
- `docs/other.html` — 47-candidate inventory.
- `scripts/gen_rich.py` — site regeneration. `M[<name>]` dict is
  single edit-point per model.
- `outputs/` — 63+ CSVs (lifts, audits, comparisons).

## ONE-LINE NEXT STEP

Pick one of the 15 buildable candidates from `docs/other.html`
(ownership recommended — Bird et al's regression is the cleanest
paper anchor) and write `lifts/lift_ownership.Rmd` + add the entry
to `gen_rich.py`'s `M["ownership"]` block.
