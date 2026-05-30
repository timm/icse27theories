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
- 33 SD models in `paper/sd.py` (was 17 → +1 congruence on 2026-05-24
  → +15 buildable-today on 2026-05-25).
- `paper/tests.py` 9-test V&V bank intact.
- `paper/outputs/full_audit.csv` — 33 models × stress matrix + 8-test
  bank (~91% PASS overall on the 18 original; new 15 mostly clean).

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

### Site / docs UX

XX. **Hyperlink scorecard terms to definitions** (deferred 2026-05-25).
    Bare `<code>extreme_eqn</code>`, `mr_*`, `boundary_adq`,
    `anomaly_check`, `stress_matrix cell`, `rq()`, `rq_n`,
    `verdict_n`, `gap_n`, `Cliff's δ / KS` etc. in all 34
    scorecard panels have no link. Do:
    - **A. Build `docs/glossary.html`** — one anchor per term;
      content = formal def + Sterman/F&S/Chen citation + link to
      `paper/tests.py` def line. Single source of truth.
    - **B. Add `<abbr title="…">` tooltips** for hover preview on
      each term in scorecard tables; click goes to glossary anchor.
    - Scope: 8 structural tests + verdict/stress family
      (`rq`, `rq_n`, `verdict`, `verdict_n`, `stress(inputs)`,
      `stress(params)`, `stress_matrix cell`) + stats primitives
      (`Cliff's δ`, `KS`, `median ε`, `gap`, `gap_n`,
      `inp_cnt`, `par_cnt`).
    - Rollout: write rewriter that finds `<code>NAME</code>` in
      `docs/models/*.html` scorecard panels, wraps with `<a>`+`<abbr>`.
      Bake into `gen_rich.py` for regenerated pages; one-shot patch
      for `brooks.html` (manual).

### New model: motif-based congruence (Carlos GH #3, DONE 2026-05-25)

UU. **DONE.** Shipped `congruence_motif()` SD model + `M[]` entry +
    `docs/models/congruence_motif.html` page + index card +
    `extract/lifts/lift_congruence_motif.Rmd` + MODELS_README +
    STATE.md update. Audit profile: CONFIRM gap=-68.78, cell=universal
    (174/154 of 200). Cataldo's 3 matrix-form variants remain
    queued as a separate future model `congruence_cataldo`
    (still needs paper-pull).

    Original entry preserved below for reference.

UU. **Add a second congruence model to the bucket — motif-based STC
    (socio-technical congruence) per Cataldo + kaiaulu motif.R.**
    Current `congruence` in `paper/sd.py:839` is the **smells-based**
    variant (Catolino 2019, R/smells.R, radio_silence). Carlos's
    GitHub issue #3 asks for the motif-based variant as a separate
    model, with reference to Cataldo's 3 versions.

    **References (all 4 from Carlos's issue)**:
    1. Catolino 2019 (smells): IEEE 8651329 — already implemented as
       current `congruence`
    2. Paradis/Kazman 2014 → Mauerer et al. 2021 (motif): IEEE 9436025
       and TSE 48(8) 2022 doi:10.1109/TSE.2021.3082074 — the basis for
       the new model
    3. Paradis 2024 comparison paper: sciencedirect S0164121224000104
       — compares both approaches + related literature
    4. Cataldo (multiple, 2008+): 3 distinct congruence variants
       (matrix-based, graph-weighted, task-dependency-graph). Reviewer-
       requested in 2022 submission. Need paper-pull to enumerate.

    **Motif structure** (from local kaiaulu R/motif.R):
    - Triangle: 2 devs communicate when changing same file (+)
    - Anti-triangle: 2 devs DON'T communicate when changing same file (−)
    - Square: 2 devs communicate when changing 2 dep-linked files (+)
    - Anti-square: 2 devs DON'T communicate across dep-linked files (−)

    Congruence_motif = (Triangles + Squares) / (Triangles + AntiTri
    + Squares + AntiSq).

    **SD model sketch** (working name `congruence_motif`):
    - Stocks: `Triangles`, `AntiTri`, `Squares`, `AntiSq`, `Bugs`
    - Inputs (UPPER): `Devs`, `Files`, `DepLinks` — project scale
    - Params (lower):
      - `comm_rate` — ctrl, probability a dev-pair on the same file
        communicates (0=no comm, 1=full comm)
      - `dep_density` — fraction of file-pairs with cross-file deps
      - `bug_rate_per_antimotif` — bugs born per anti-motif event
      - `bug_repair_rate` — bugs paid down per tick
    - Flow logic per tick: enumerate co-touch events → classify into
      4 motifs → AntiTri + AntiSq increment Bugs.
    - y = Bugs at tmax (success = low bugs).
    - rq = "raising comm_rate from 0.2 → 0.8 lowers final Bugs".
      Cataldo's thesis: congruence gap predicts defects.

    **3 Cataldo variants** map to different update rules:
    a. **Matrix-form** (Cataldo 2006): coordination_requirement matrix
       CR = TD ∩ TA, congruence = |CR ∩ CA| / |CR|. Simplest.
    b. **Weighted** (Cataldo 2008): edge weights by frequency.
    c. **Task-graph-based** (Cataldo 2014?): uses task dependency
       graph directly. Need paper-pull.

    For SD: variants collapse into 3 different formulas for the
    `congruence` derived metric in step(). Each gives a different y()
    if Bugs born differently. Could ship as one model with a
    `variant` param ∈ {1,2,3} ctrl switch, OR as 3 separate models.
    Carlos preference TBD.

    **Lift recipe** (confirmed against kaiaulu vignette
    `motif_analysis.html` fetched 2026-05-25):
    ```r
    git_network    <- transform_gitlog_to_bipartite_network(gitlog,
                                                            mode="author-file")
    reply_network  <- transform_reply_to_bipartite_network(replies)
    reply_network  <- bipartite_graph_projection(reply_network,
                          mode = TRUE,
                          weight_scheme_function = weight_scheme_sum_edges)
    file_network   <- transform_r_dependencies_to_network(deps,
                                                          dependency_type="file")
    # merge networks into single combined graph
    g_all <- list(nodes = unique(rbind(...)),
                  edgelist = rbind(git_network$edgelist,
                                   reply_network$edgelist,
                                   file_network$edgelist))
    i_all <- igraph::graph_from_data_frame(d=g_all$edgelist,
                                           directed=FALSE,
                                           vertices=g_all$nodes)
    V(i_all)$color <- ifelse(V(i_all)$color == "black", 1, 2)
    # Count each motif type via subgraph isomorphism (VF2)
    counts <- list()
    for (mt in c("triangle","anti_triangle","square","anti_square")) {
      mg <- motif_factory(mt)
      img <- igraph::graph_from_data_frame(d=mg$edgelist,
                                           directed=FALSE,
                                           vertices=mg$nodes)
      V(img)$color <- ifelse(V(img)$color == "black", 1, 2)
      counts[[mt]] <- igraph::count_subgraph_isomorphisms(
        img, i_all, method="vf2",
        edge.color1=NULL, edge.color2=NULL)
    }
    ```
    Emit `paper/outputs/lift_congruence_motif_<project>.csv` with
    columns: Triangle, AntiTriangle, Square, AntiSquare,
    n_devs, n_files, n_deps. Vignette example on kaiaulu itself
    gave triangle=34, square=32 (anti variants not demonstrated
    there but available via `motif_factory("anti_triangle")` etc.).

    **Congruence formula**: vignette is counts-only; the ratio
    comes from Mauerer 2022 consumer side. Most natural:
    `congruence = (Triangle + Square) / (Triangle + AntiTri + Square + AntiSq)`.
    Verify against Mauerer TSE 2022 §formal definition before
    committing.

    **Cataldo's 3 variants are a SEPARATE track**: matrix-form
    CR ∩ CA / |CR|, NOT graph-motif counts. Vignette doesn't
    reference Cataldo at all. Including the Cataldo variants
    means a second lift pipeline (task-dependency × people-task
    matrices, not igraph motifs). Could ship as a third model
    `congruence_cataldo` distinct from `congruence_motif`. Carlos
    expectation needs clarification: does he want ONE model with
    formula switches, or THREE distinct models
    (smells / motif / cataldo)?

    **Implementation checklist**:
    - [ ] Pull Cataldo's 3 papers; enumerate the variants
    - [ ] Update current `congruence` docstring to say "smells-based
          (Catolino 2019)"; rename internal vars if helpful
    - [ ] Add `congruence_motif()` to sd.py
    - [ ] Add `M["congruence_motif"]` entry to gen_rich.py with rich
          intro1/intro2/rq_text/cell_para/refs (4-paper citation list)
    - [ ] Add to MODELS_README.md table (34→35 models)
    - [ ] Add to full_audit.py MODELS list
    - [ ] Write extract/lifts/lift_congruence_motif.Rmd using kaiaulu
          motif wrappers
    - [ ] Run pipeline: full_audit → melt_lifts → boundary_check →
          calibrate → gen_rich → gates
    - [ ] Note for paper: this model + the existing `congruence` give
          a methodological contrast — same SE thesis (coordination
          gap → defects), two different operationalizations, can the
          framework triage which is the better measurement target?

    **Open questions for Carlos/Rick**:
    - One model with variant=1/2/3 ctrl, or 3 separate models?
    - Should the smells-based `congruence` be renamed
      `congruence_smells` for symmetry?
    - Does the paper want both shipped as the worked-example trio
      (replacing one of brooks/archpat/dora)?

    Big-ticket effort: estimate 1 day of paper-reading + 1 day of
    SD model drafting + 1 day of lift Rmd + audit pass. Wait for
    Carlos prioritisation before starting.

### Model-derived findings re-validation (deferred 2026-05-25)

VV. **Re-validate the May 11 aidebt regime-crossover claim against
    current sd.py.** Claim: leverage measurement = ratio
    `pay_rate / (born_base × (1 + born_ai_mult))`, crossover ≈ 1.5×,
    teams above benefit from AI, teams below degrade. Source: May 11
    chat — model-based reasoning, never grid-validated.

    Status today (2026-05-25):
    - Structurally still valid: aidebt step() line 746-749 retains
      both params; only rename `born_rate` → `born_base`.
    - Quantitatively suspect: default ratio = 0.15/(0.3×2.5) = 0.2,
      well below claimed 1.5× threshold. Default `rq()` reports
      REFUTE +6.50 at tmax=20, CONFIRM at tmax≥30 (per
      MODELS_README.md line 107-108). Regime appears in TIME, not
      param-ratio, as currently configured.
    - Stress matrix backs the "params matter" framing:
      `inp_cnt=183/200` vs `par_cnt=74/200` (37%), cell =
      world-conditional.
    - Prudence dirty: `boundary_adq=FAIL`, `extreme_eqn=ERR`,
      `mr_scale=ERR`. Verdicts should carry that caveat.

    Build `paper/scripts/grid_aidebt.py`:
    1. Sweep `(pay_rate, born_ai_mult)` over their declared `[lo, hi]`
       on a 10×10 grid.
    2. For each cell: run `rq()` at tmax ∈ {10, 20, 30, 50, 80}.
    3. Output 2D verdict heatmap CSV per tmax.
    4. Compute the contour where verdict flips (CONFIRM ↔ REFUTE).
    5. Compare to 1.5× ratio claim.
    6. Fix the 3 prudence FAIL/ERR rows before publishing the
       contour as evidence.

    Output: `paper/outputs/grid_aidebt_tmax<T>.csv` + a figure spec
    for the NIER paper (regime boundary in (pay_rate, born_ai_mult)
    space at chosen tmax). This is publishable — directly anchors
    the methodology paper's "model-based triage of what to measure"
    pitch.

    Parallel: same exercise for `aiwork` via `grid_aiwork.py` sweeping
    `(gen_boost, churn_mult)` — the May 11 chat already produced
    a 6×6 sensitivity table for that pair. Re-derive against current
    sd.py to check numbers reproduce.

### Vignette ↔ docs/models alignment (Carlos GH #1, deferred 2026-05-25)

SS. **Two related fixes for the Rmd-vignette ↔ docs/models drift
    that Carlos flagged in GH issue #1**:

    **(a) Restructure `extract/lifts/` to match kaiaulu vignette
    naming convention**. Today our lifts are named
    `lift_<model>.Rmd`. Kaiaulu's vignettes are named
    `<topic>_<method>.Rmd` (descriptive, kaiaulu's house style).
    Carlos's PR fork already renames them. Proposed map:

    | current name (extract/lifts/) | kaiaulu vignette name (Carlos's fork) |
    |---|---|
    | `lift_archpat.Rmd` | `archpat_gof_pattern_partition.Rmd` |
    | `lift_brooks.Rmd` | `brooks_late_hire_velocity.Rmd` |
    | `lift_brooksq.Rmd` | `brooksq_injection_leak.Rmd` |
    | `lift_bugs.Rmd` | `bugs_goel_okumoto_fit.Rmd` |
    | `lift_congruence.Rmd` | `congruence_radio_silence_brokers.Rmd` |
    | `lift_debt.Rmd` | `debt_refactoring_pay_rate.Rmd` |
    | `lift_defmap.Rmd` | `defmap_bug_caught_ratio.Rmd` |
    | `lift_dora.Rmd` | `dora_four_keys_lift.Rmd` |
    | `lift_learn.Rmd` | `learn_cohort_transitions.Rmd` |
    | `lift_rework.Rmd` | `rework_failrate_estimation.Rmd` |

    Need git mv to preserve history. Cross-link to TODO ZZ
    (data drop-zone) since ingest tool needs to know the canonical
    Rmd locations. Also need to update `paper/Makefile`'s `render`
    target (line 96) to find the renamed files.

    **(b) Build `docs/scripts/sync_vignettes.py` to extract Rmd
    content into gen_rich.py M[] fields.** Pattern proven on
    archpat 2026-05-25 by hand-editing M["archpat"] to mirror
    Carlos's vignette: 6-step method outline, flow diagram,
    pattern4 invocation gotcha, Verdict-on-Helix prose,
    family-comparison table, expanded refs (Gamma, Tsantalis 2006,
    Arcan, MacCormack). Result: docs/models/archpat.html now
    matches kaiaulu vignette content density.

    Generalise the manual archpat exercise into a script:
    1. For each model in {archpat, brooks, brooksq, bugs,
       congruence, debt, defmap, dora, learn, rework}:
    2. Pull the kaiaulu vignette via `gh api repos/timm/kaiaulu/...`
       or `curl` to the raw URL.
    3. Parse Rmd sections: YAML header → metadata; `#` headers →
       sub-sections; ```{r}``` blocks → code chunks; prose
       between chunks → narrative.
    4. Auto-update gen_rich.py M[<name>] fields:
       - `lift_intro` ← Intro section + method outline
       - `attrs_table` ← derived from code chunks' fread/parse calls
       - `tools_table` ← detected from require() + system() calls
       - `results_intro` ← Verdict section
       - `results_discussion` ← Sanity Checks + Boundary findings
       - `refs` ← Bibliography section
    5. Diff old vs new before write; ask before overwriting
       manual edits.
    6. Run after each docs regen (or as a pre-commit hook).

    Open questions:
    - Source of truth for vignette URLs: hard-code the Carlos
      fork URLs, OR have a `vignette_urls.yml` per model.
    - Conflict policy when vignette + manual M[] differ: prefer
      vignette, prefer M[], or interactive?
    - Should rename in (a) happen FIRST so script in (b) can
      use the canonical names?

    Recommended sequence: rename Rmd files (a), update Makefile
    + symlinks for backward compat, build extractor (b),
    one-time backfill, then ongoing sync via pre-commit hook.

### Lift function documentation (deferred 2026-05-25)

TT. **Add inline WHY comments to every function in
    `extract/lifts/functions.R`.** Today each function carries a
    roxygen header (param/return/export) but the function BODY has
    no inline comments explaining the mechanism. Reader can see
    WHAT each line does from the code, but not WHY.

    Reference pattern: `detect_late_hires()` lines 31-46
    (`extract/lifts/functions.R`). Roxygen header is sufficient.
    Body would benefit from comments like:
    - on `first_commits` line: "first commit per identity =
      individual's join date"
    - on `project_start` line: "earliest commit across whole repo
      = project birth"
    - on filter line: "drop founders + early hires; keep only late
      arrivals whose first commit is >365 days after birth"

    833 lines, ~12 exported functions. Per Tim's instruction
    2026-05-25 (review of `lift_congruence.html`): "there are no
    comments in the lift functions. these need to be added."

    **Scope**: every `# ---- <Section> ----` block in functions.R.
    Highest priority (consumed by most lifts):
    - `detect_late_hires()` (used by brooks, brooksq, defmap, rework)
    - `compute_velocity_changes()` (used by brooks)
    - `compute_injection_changes()` (used by brooksq, defmap, rework)
    - `compute_file_churn()` (used by archpat)
    - `assign_file_partition()` (used by archpat)
    - `parse_szz_bugfixes()` (used by all SZZ-based lifts)
    - `parse_mbox_dir()` (used by congruence)
    - `build_reply_edges()` (used by congruence)
    - `detect_radio_silence()` (used by congruence)

    Pattern follows the aiwork docstring + inline-comment exercise
    on 2026-05-25 (see WW). Each non-obvious line gets one short
    WHY. Comments NOT added on lines whose identifier already
    explains intent (CLAUDE.md rule). Run length: budget ~2 min
    per function × 12 = 25 min.

    Audit fail mode: reviewer reading `functions.R` should be able
    to write the lift's prose description without consulting the
    Rmd notebook. Today that's only possible for `detect_late_hires`
    (the most-cited function with prose context elsewhere).

### Model documentation (deferred 2026-05-25)

WW. **Ensure all 34 models in `paper/sd.py` are commented to the
    same standard.** Today most model defs carry only a 1-line
    docstring (citation + RQ). Inline mechanism comments are absent
    on the vast majority. `aiwork` got the canonical treatment
    on 2026-05-25 as the reference pattern: extended docstring
    (citation + stocks + control + RQ + hypothesis basis), inline
    `# unit comment` per init param explaining the meaning, brief
    `# why` comments per non-obvious line in `step()`, comment on
    the `y()` choice, comment on the rq() control-arm semantics.
    Replicate for the other 33 models.

    Priority order (clean first since they get the most page traffic):
    1. **Headline 3**: brooks, brooksq, archpat
    2. **Lifted (10)**: bugs, debt, sir, rework, learn, defmap,
       dora, congruence (already comment-dense in step), plus
       brooks/brooksq above
    3. **Pipeline-ready 15**: ownership, orgchurn, pareto, mirroring,
       little, entropy, costchange, deprot, ossfail, coordn2, scope,
       ctxswitch, limits, successful, linus
    4. **Dark 6**: aidebt, flaky, micro, teamtopo, burnout (sister
       of aiwork)
    5. **Toy**: diapers (trivial, skip)

    Pattern reference: see `aiwork()` after 2026-05-25 edit. Don't
    over-comment (CLAUDE.md says: WHY only, not WHAT). Skip lines
    where identifier name already explains. Focus on:
    - Init param units + meaning when not obvious from name
    - Multiplicative factors in step() (what does `1 + x*y` represent?)
    - Bounds / caps (`min(...)`, `max(...)`) — why?
    - Choice of y() — why this stock as success measure?
    - rq() control-arm interpretation (what does ctrl=0 vs ctrl=1 mean?)

    Audit fail mode: a reviewer reading the .py should be able to
    write the model's RQ description without consulting the docs/
    pages. Today that's only possible for ~3 models.

### Data drop-zone + one-command rebuild (PARTIAL DONE 2026-05-25)

ZZ. **PARTIAL DONE.** Built `data/dropzone/` + `scripts/refresh.py`
    + Makefile targets `refresh` / `refresh-lifts` / `refresh-dry`.
    Lift-CSV path works end-to-end:
    ```
    cp lift_<m>_<p>.csv data/dropzone/
    make refresh-lifts
    ```
    Pipeline: ingest → melt_lifts (guarded — skipped when no source
    CSVs to avoid wiping the frozen lifts.csv) → boundary_check →
    calibrate → cross_project → full_audit → gen_rich → both gates,
    then prints a per-model before/after diff of (cell, verdict,
    verdict_n, gap).

    **Raw-data render path still TODO**: drops of
    `data/dropzone/<project>/git_repo/` etc. get moved to
    `data/<project>/` but auto-knitting `extract/lifts/*.Rmd` is not
    yet wired — needs Rscript + kaiaulu + perceval toolchain check
    + per-project Rmd discovery. For now, refresh.py prints a
    `TODO: run \`make render\` manually` note.

    Original entry preserved below for reference.

ZZ. **Single command to ingest new/updated project data and rebuild
    the entire pipeline.** Today the flow is implicit and manual:
    `data/<project>/` → `extract/lifts/*.Rmd` → `paper/outputs/lift_*.csv`
    → `melt_lifts.py` → `lifts.csv` → `boundary_check.csv` +
    `calibrated_verdicts.csv` → `full_audit.csv` (via gen_rich) →
    `docs/models/*.html`. No documented entry point. No watcher.
    Re-running each stage by hand is error-prone, and the
    `extract/lifts/*.html` already drifted (Rmd newer than html on
    all 9 lifts).

    Build a `data/dropzone/` directory + a `make ingest <project>`
    target that:
    1. Detect new or updated project under `data/<project>/` (or
       symlink from `dropzone/`).
    2. Verify `extract/conf/<project>.yml` exists; if not, generate
       a skeleton + flag for hand-edit (git_repo path, branch, JIRA
       paths).
    3. Render the 9 (or however many) `extract/lifts/*.Rmd`
       notebooks for that project — produces per-project lift CSVs
       in `paper/outputs/`.
    4. Run inference chain: `make inference` (already exists) →
       `lifts.csv`, `boundary_check.csv`, `calibrated_verdicts.csv`,
       `cross_project.csv`, `full_audit.csv`.
    5. Regenerate docs: `python3 docs/scripts/gen_rich.py`.
    6. Run gates: `audit_staleness.py` + `check_pages.py`.
    7. Print diff summary: which scorecard rows changed, which
       findings (F0–F4) shifted.

    Open questions before implementing:
    - One project at a time, or batch all projects under `data/`?
    - Detect change by mtime, content hash, or explicit list?
    - For NEW projects: which conf-yml fields are auto-detectable
      (git_repo, branch via `git symbolic-ref`) vs hand-edit
      (JIRA project key, mbox path)?
    - For schema changes (new metric in lift): does gen_rich.py
      need to learn the new column, or does melt_lifts.py auto-melt?
    - Render needs `Rscript` + working `data/<project>/git_repo/`.
      Currently broken (data/ is empty); ingest tool must verify
      preconditions before rendering.
    - Should ingest auto-update `paper/MODELS_README.md` lift-status
      column ("8/8" → "8/8 + tomcat-v2") or leave manual?

    Smaller scope to start: just a `make refresh` target that
    re-runs steps 4–6 assuming per-project lift CSVs are already
    in place. That covers the "updated audit / new gen_rich logic"
    case without solving the upstream lift-rendering blocker
    (which needs data/ repopulated first).

### Audit coverage gaps (deferred 2026-05-25)

YY. **audit_staleness.py misses prose-embedded lift stats**.
    Currently checks: cell label, inp_cnt/par_cnt, badge counts,
    typology totals, model count. Does NOT check summary statistics
    in page prose that are computed from `lifts.csv`.
    Concrete miss: `brooks.html` Panel 5 row `family_member_coherence`
    says "5/8 positive sign with n_hires ≥ 50; 3/8 noisy with small
    samples". Current lifts.csv gives 6/8 + 2/8 (tomcat n_hires=50
    crosses the threshold). Same drift on Panel 6 line 636
    ("5 of 8 cases, all five").
    Extend `paper/scripts/audit_staleness.py` to:
    - parse prose patterns like `N/M positive sign`, `N of M cases`,
      `N/M show <X>`
    - recompute from lifts.csv per-model
    - flag mismatch
    Also similar prose-embedded counts on other model pages — sweep
    all 34 docs/models/*.html for `\d+/\d+` and `\d+ of \d+` patterns
    that reference lift quantities (sign, threshold, magnitude).

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

   **7a. archpat sub-entry (added 2026-05-25)**: empirical anchor
   from `paper/outputs/boundary_check.csv`:
   - helix: Patterned=149 (in_range), Legacy=384 (1.9× over hi=200)
   - ambari: Patterned=381 (1.9× over), Legacy=1890 (9.5× over)
   Proposed bounds derive from "1.5× max observed":
   - `Patterned hi 200 → 1000` (covers ambari 381 + 2.6× headroom)
   - `Legacy hi 200 → 3000` (covers ambari 1890 + 1.6× headroom)
   Files to edit: `paper/sd.py:789` init dict (only the 2 hi
   values change; lo + default unchanged).
   **Side effects to verify post-edit**:
   - `stress()` redraws over the new range. Triangular sampler
     still peaks at default=10 (Patterned) / 90 (Legacy) so most
     draws stay near defaults; high-end tail now reachable. Cell
     typology may shift from `universal` (currently 129/200 inputs,
     122/200 params CONFIRM) toward `world-conditional` or
     `process-conditional` if Migration can't keep up with much
     larger Legacy stocks. Re-run `full_audit.py` to check.
   - `verdict_n` currently `neutral` with `gap_n=+59`, `eps=185`.
     Wider variance grows sd → eps grows → likely stays neutral.
   - `param_plausibility` row in scorecard should flip
     `FAIL → PASS` for archpat (rows for ambari Patterned + Legacy
     + helix Legacy now in_range).
   - `boundary_adq_data` row may flip `PASS → warn` (no lifted
     values reach the new wider edges).
   - F0 boundary-violation callout in archpat.html
     `scorecard_extras` (gen_rich.py:727) needs rewording or
     removal — currently quotes the old hi=200 + 384/1890/381.

   **Commit sequence** (atomic, gate-checked):
   1. Edit `paper/sd.py:789` two `hi` values.
   2. Run `python3 paper/full_audit.py` → refresh full_audit.csv.
   3. Run `python3 paper/boundary_check.py` → refresh
      boundary_check.csv (status fields will flip).
   4. Run `python3 paper/calibrate.py` → calibrated_verdicts.csv
      may shift (clipping behavior different).
   5. Update `scorecard_extras` for archpat in gen_rich.py:727 to
      reflect new bounds (or remove if all lifts now in_range).
   6. Run `python3 docs/scripts/gen_rich.py` → regenerate 32 pages.
   7. Run `paper/scripts/audit_staleness.py` + `check_pages.py`.
   8. Update `findings.md` F0 row: archpat resolved, remaining
      violations on brooksq + learn + congruence.

   (Sub-entries 7b–7e for the other 5 params follow the same
   recipe; not enumerated until authorization.)
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
