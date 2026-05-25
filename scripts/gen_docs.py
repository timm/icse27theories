#!/usr/bin/env python3
"""Generate docs/models/<name>.html for all 18 SD models."""

import csv, html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SD_PY = (ROOT / "models/sd.py").read_text()
OUT_DIR = ROOT / "docs/models"


MODELS = {
    "diapers": dict(
        cite="Toy demonstrator (no real-world referent).",
        cell="dark",
        intro="Smallest possible compartmental model used to demonstrate the framework's machinery. Has no Brooks- or Sterman-style intent — it exists to show the SD harness running end-to-end with one stock and one flow.",
        y_text="Net inflow above a fixed baseline.",
        rq_text="A baseline shift hurts net output. Trivially true by construction.",
        lifted=False,
        lift_blocked="Toy by design. No project data corresponds to its abstract stocks.",
        results="Used as a sanity check that the engine executes a model. Passes structural V&V on cell stress, fails mr_scale and mr_dt_halving (the toy is not physically faithful — by design).",
    ),
    "brooks": dict(
        cite="Brooks, F. P. (1975). The Mythical Man-Month.",
        cell="universal",
        intro="Adding people to a late software project makes it later. Two stocks — Vet (veterans) and New (new hires) — with a productivity tax that falls on veterans when newcomers join (training cost + n·(n−1)/2 communication-pair overhead).",
        y_text="Net work delivered: end.Done − end.Todo.",
        rq_text="boost=10 newcomers at t=10 hurts y compared to boost=0.",
        lifted=True,
        lift_rmd="lifts/lift_brooks.Rmd",
        results="Lifted on 8 OSS projects. Among the 5 with n_hires ≥ 50, all five show positive Brooks tax (newcomers do slow veterans) but the magnitude varies 11x — Ambari 3% to airflow 31%. The 3 noisy small-sample projects gave negative signs. See finding F3.",
    ),
    "bugs": dict(
        cite="Goel, A. L. & Okumoto, K. (1979). Time-dependent error-detection rate model.",
        cell="process-cond.",
        intro="Software-reliability-growth: cumulative defects discovered N(t) follows an exponential approach to an asymptote a. The discovery rate b decays as Latent bugs are removed from the system.",
        y_text="Cumulative Fixed at the end of the run.",
        rq_text="Doubling initial Latent stock approximately doubles eventual Fixed (linearity of recovery process).",
        lifted=True,
        lift_rmd="lifts/lift_bugs.Rmd",
        results="Lifted on 3 projects with bug-classification data: Helix (170 GH-bug-label closed, a=245, R²=0.62), kaiaulu (22 closed, a=26, R²=0.91), camel (185 JIRA-Bug-type resolved, a=178, R²=0.60). All three are in the early-discovery regime — none have saturated, so the linearity claim cannot be falsified yet.",
    ),
    "debt": dict(
        cite="Cunningham, W. (1992). The WyCash Portfolio Management System.",
        cell="universal",
        intro="Technical debt accumulates as you ship fast. The debt then slows down future shipping, creating a feedback loop. Three params: born_rate (new debt per ship), intr_rate (compounding interest on existing debt), pay_rate (debt paid down by refactoring).",
        y_text="Cumulative Feat shipped minus mean Debt over the run.",
        rq_text="Starting Debt=50 (already-indebted project) hurts net feature delivery vs starting Debt=0.",
        lifted=True,
        lift_rmd="lifts/lift_debt.Rmd",
        results="Lifted on 5 Java projects via RefactoringMiner. The pay_rate metric is convergent across projects (0.36–0.59) — by far the most family-coherent metric in the bank. Compare to brooks_tax which spreads 11x. See finding F2.",
    ),
    "sir": dict(
        cite="Kermack, W. O. & McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics.",
        cell="universal",
        intro="Adapted from epidemiology: bad architectural patterns spread through a codebase like a contagious disease. Susceptible files (S), Infected files (I), Recovered files (R, refactored). Beta = infection rate via dependency edges. Gamma = recovery (refactor) rate.",
        y_text="Negative peak Infected — peak severity of the outbreak.",
        rq_text="Tripling initial Infected files raises the peak (hurts y).",
        lifted=False,
        lift_blocked="Needs (anti-pattern × time × dep-graph) — a multi-snapshot pipeline of Depends + pattern4 across release tags. Depends data path opened (file-level dep graph runs on helix-core). Multi-snapshot integration deferred.",
        results="Data path is open but no full lift yet. Single-snapshot Depends produces a 499K JSON dep graph on helix-core. To run the SIR fit, would need the same graph at N release-tag checkouts + per-file pattern instances at the same checkouts.",
    ),
    "rework": dict(
        cite="Abdel-Hamid, T. & Madnick, S. E. (1991). Software Project Dynamics.",
        cell="universal",
        intro="Hidden rework cycle: Req → Dev → Test branches into pass-or-rework. High failure rate trapping work in the Rew loop dominates output. The ctrl is failrate — the fraction of Test outputs that fall back to Rew rather than passing to Done.",
        y_text="Done minus 0.5·mean(WIP) — finishing matters; piling up WIP penalises.",
        rq_text="failrate 0.1 → 0.7 lets rework dominate; net Done collapses.",
        lifted=True,
        lift_rmd="lifts/lift_rework.Rmd",
        results="Lifted on 7 projects via SZZ-introducing-commit count. failrate values 0.019–0.41 — none cross the 0.5 dominance threshold. Helix (0.019) has most headroom; junit5 (0.27) and Ambari (0.27) approach but don't cross. The thesis cannot be falsified on these projects because none operate in its trigger regime.",
    ),
    "learn": dict(
        cite="Sterman, J. (2000). Business Dynamics, ch. 18.",
        cell="process-cond.",
        intro="Workforce-flow pipeline: Jr → Tr → Sr → Ment(or). The senior stock Sr is the ctrl. Thesis: remove seniors (Sr=0) and the training pipeline starves — juniors have no mentors to graduate toward.",
        y_text="Cumulative Sr + Ment at end of run.",
        rq_text="Sr=0 (no seniors) starves training; net output collapses vs Sr=5.",
        lifted=True,
        lift_rmd="lifts/lift_learn.Rmd",
        results="Lifted on 8 projects. Helix has 43 Jr / 21 Tr / 9 Sr (top-heavy junior), train_rate ≈ 0.81. Across the 8 projects, train_rate spans 0.51–0.89 for high-sample projects. Earlier methodology used 365-day slices with the 365-day Jr cutoff, saturating train_rate at 1.0 — fixed to 90-day slices for realistic rates.",
    ),
    "brooksq": dict(
        cite="Brooks (1975) + Madachy, R. (2008). Software Process Dynamics.",
        cell="fragile",
        intro="Brooks's quality side: late hires don't just slow veterans, they also inject more bugs that leak into the field. Five stocks (Vet, New, Done, Bugs, Esc) + inj_rate (injection per Vet-prod) + leak_rate (fraction of bugs not caught quickly).",
        y_text="Done − 5·Esc — escaped bugs penalise heavily.",
        rq_text="boost=10 newcomers at t=10 hurts y = Done − 5·Esc.",
        lifted=True,
        lift_rmd="lifts/lift_brooksq.Rmd",
        results="Lifted on 7 projects via SZZ. brooksq's leak_rate exceeds model.hi=0.5 on 7 of 7 with lift (only kaiaulu 0.42 in-range — smallest sample). Monotonic 0.42→0.93 across 5 languages — structural model-bound failure (F1). On inj_rate_increase, verdict is SPLIT: Ambari +0.094 supports, Helix 0 neutral, junit5 -0.011 mildly refutes (F4).",
    ),
    "defmap": dict(
        cite="Abdel-Hamid & Madnick (1991) — defect-management submodel.",
        cell="universal",
        intro="Defect flow: Injected → Caught (by testing) or → Latent → Prod (field-escape). The ctrl tst (testing intensity) modulates how many defects get Caught before reaching Prod.",
        y_text="−end.Prod − 0.5·end.Latent — negative because we want fewer escaped + fewer pending.",
        rq_text="tst 2.5 → 0.5 (sharp reduction in testing) inflates Prod defects.",
        lifted=True,
        lift_rmd="lifts/lift_defmap.Rmd",
        results="Lifted via SZZ phase-partition. tst_proxy = caught-within-phase / injected-within-phase. Helix 0.375, junit5 0.15, Ambari 0.098, tomcat 0.085. All projects operate in the LOW-tst (predicted-bad) regime, with Helix the least-bad.",
    ),
    "aiwork": dict(
        cite="GitClear (2024) + Becker et al. (METR, 2025): AI churn vs gen tradeoff.",
        cell="universal",
        intro="AI-assisted development creates a churn-vs-gen tradeoff: AI generates more code (raises Kept) but also more churn (raises Churned, the discard rate). The net depends on whether genuine learning happens or just velocity-of-deletion.",
        y_text="Kept − Churned at end of run.",
        rq_text="ai=1 (full AI assist) reduces net Kept code.",
        lifted=False,
        lift_blocked="Per-commit AI-authorship attribution does not exist in any open dataset. GitHub Copilot and similar tools do not tag commits. Would require building an attribution corpus before any project lift is possible.",
        results="Structurally unlifted. Methodological worked example: the framework can express this thesis, but no field data source can calibrate it. That gap is itself a contribution.",
    ),
    "flaky": dict(
        cite="Luo et al. (2014). An empirical analysis of flaky tests.",
        cell="universal",
        intro="Flakiness compounds: flaky tests slow CI feedback → bugs leak into mainline → more flakiness. The model treats Flaky as a stock fed by chaotic interactions in Tests, drained by CI Discipline.",
        y_text="Done − 3·Esc — flakes that mask real bugs cost 3x.",
        rq_text="Flake-mask probability 0.01 → 0.4 dominates output.",
        lifted=False,
        lift_blocked="No CI flake-outcome logs in any kaiaulu pipeline. GitHub Actions logs are public for some OSS projects but no parser exists. Reachable but unbuilt (~1-2 days of focused engineering).",
        results="Highest-priority dark model to lift in future sessions — public data exists, parser missing.",
    ),
    "dora": dict(
        cite="Forsgren, N., Humble, J., & Kim, G. (2018). Accelerate.",
        cell="universal",
        intro="DORA's deploy-cycle dynamic: larger batches → higher change-failure rate (CFR) → longer mean-time-to-recover (MTTR) → bottleneck on the next deploy. Four params: batch_size (ctrl), cfr_coef, arrival_rate, rec_rate.",
        y_text="Deploys − 2·Incidents at end of run.",
        rq_text="batch_size 5 → 50 hurts net Deploys (incidents grow faster than Deploys).",
        lifted=True,
        lift_rmd="lifts/lift_dora.Rmd",
        results="Lifted on 7 projects via tag-deploy + SZZ-CFR-and-MTTR. Helix batch=73.9, MTTR=88d; junit5 batch=38.4, MTTR=73d; openssl batch=54.8, MTTR=686d (huge — old project with infrequent tags). All projects operate above the model's batch=50 threshold or with very long MTTR; the predicted-bad regime is the common case.",
    ),
    "micro": dict(
        cite="Newman, S. (2015). Building Microservices.",
        cell="process-cond.",
        intro="Service-architecture coupling dynamic: more services lower local deploy risk but increase cross-service failure cascades. Stocks track Services, Couplings, and Cascades.",
        y_text="Healthy services − 2·Cascading-failures.",
        rq_text="Coupling threshold breached → cascade dominates.",
        lifted=False,
        lift_blocked="No public service-architecture map for the projects on disk. Microservice OSS projects exist (Netflix Eureka, k8s manifests) but no curated dataset combining git history + service topology.",
        results="Structurally unlifted on the current 8-project family. Would need a microservice-style OSS project + k8s/Helm manifest scrape.",
    ),
    "teamtopo": dict(
        cite="Skelton, M. & Pais, M. (2019). Team Topologies.",
        cell="universal",
        intro="Team-shape constraints throughput: stream-aligned teams in tight coupling produce sub-linear scaling. Cognitive load on each team becomes the bottleneck.",
        y_text="Aggregate team output minus a load penalty.",
        rq_text="Cognitive load ceiling breached → output declines.",
        lifted=False,
        lift_blocked="Org-chart + team-boundary data is private to companies. No open dataset exists.",
        results="Structurally unlifted. Methodological case: framework expresses the thesis, the field does not collect the data.",
    ),
    "burnout": dict(
        cite="DORA wellbeing report (2024) + Maslach inventory.",
        cell="process-cond.",
        intro="Long hours and emotional exhaustion degrade output. Stocks: Energy, Exhaustion, Output. Recovery rate competes with depletion rate.",
        y_text="Cumulative output minus exhaustion penalty.",
        rq_text="Sustained high hours collapse output via exhaustion.",
        lifted=False,
        lift_blocked="HR/wellbeing surveys are private and ethics-gated. Commit-timing proxies (off-hours commits) are weak and don't capture the construct.",
        results="Structurally unlifted. Methodological case alongside aiwork and aidebt.",
    ),
    "aidebt": dict(
        cite="Speculative SE-2026 thesis (composite of GitClear + technical-debt literature).",
        cell="world-cond.",
        intro="AI-generated code accelerates feature delivery but accumulates a deferred debt cost (hidden complexity, less-maintainable patterns). The model exhibits a regime crossover near tmax ≈ 26 — early AI use looks net-positive, late accumulation goes net-negative.",
        y_text="Feat − 0.3·Debt at end of run.",
        rq_text="Long-horizon (tmax > 30) AI-heavy runs become net-negative — the only model with a REFUTE verdict at default init.",
        lifted=False,
        lift_blocked="Same as aiwork: no AI-authorship attribution exists in any open dataset.",
        results="The most interesting dark model. The regime-crossover at tmax ≈ 26 places it in the world-conditional cell (robust to params, fragile to inputs). The only model where the default rq() verdict is REFUTE.",
    ),
    "archpat": dict(
        cite="Martin, R. C. (2008). Clean Architecture. + Perry, D. E. & Wolf, A. L. (1992). Foundations for the study of software architecture.",
        cell="fragile",
        intro="Three architectural regions: Patterned (under good architecture), Legacy (not), Drift (was patterned, eroded). Migration moves Legacy → Patterned at rate proportional to migrate_rate · available_effort. Decay (Perry-Wolf erosion) moves Patterned → Drift.",
        y_text="Feat − Debt at end of run.",
        rq_text="From an already-bad start (Patterned=10, Legacy=90, Debt=40), aggressive migration (migrate=1.5) repairs the project vs slow (migrate=0.2).",
        lifted=True,
        lift_rmd="lifts/lift_archpat.Rmd",
        results="Lifted on Helix and Ambari via pattern4 (GoF) + RefactoringMiner + SZZ. Both projects exceed model.Legacy hi=200 (Helix 384, Ambari 1890); Ambari exceeds Patterned hi=200 (381). Calibrated rq() gap widens from +229 to +390 with Helix's larger Legacy. junit5 lift blocked by Gradle JDK 25 toolchain mismatch.",
    ),
    "congruence": dict(
        cite="Newman, M. E. J. (2015). Networks: An Introduction. + Blondel et al. (2008) Louvain communities.",
        cell="universal",
        intro="Boundary-spanning developers (\"brokers\") hold a fragmented communication graph together. If brokers leave, the graph fragments, sub-communities lose context, net cohesive work collapses.",
        y_text="Cohesion − 5·Clusters — cohesive output minus a fragmentation penalty.",
        rq_text="broker_loss=0.3 (sudden loss of key brokers) fragments project and hurts net cohesion.",
        lifted=True,
        lift_rmd="lifts/lift_congruence.Rmd",
        results="Lifted on 3 projects with mbox: Helix (3 brokers, 5 clusters [42,25,14,13,2]), airflow (4 brokers, 7 clusters), tomcat (39 brokers, 33 clusters). Tomcat's broker + cluster counts BOTH exceed model.hi=20 — third boundary violation in the F0 set. The R version uses identity_match across mbox+git, consolidating ~20% of Helix mbox senders with git authors.",
    ),
}


def extract_model_code(name):
    pat = re.compile(
        rf"^def {re.escape(name)}\(\):\n(?P<body>.*?)(?=\n\ndef \w|\nALL_MODELS|\Z)",
        re.M | re.S,
    )
    m = pat.search(SD_PY)
    if not m:
        return f"# could not extract def {name}() from sd.py"
    return f"def {name}():\n{m.group('body')}"


def load_cross_project():
    p = ROOT / "outputs/cross_project.csv"
    if not p.exists():
        return None
    with p.open() as f:
        return list(csv.DictReader(f))


def load_full_audit():
    p = ROOT / "outputs/full_audit.csv"
    if not p.exists():
        return {}
    out = {}
    with p.open() as f:
        for row in csv.DictReader(f):
            out[row["model"]] = row
    return out


def render_lift_status(meta):
    if meta["lifted"]:
        return (
            '<span class="ok">lifted</span>'
            f' &middot; <code>{html.escape(meta["lift_rmd"])}</code>'
        )
    return '<span class="dim">not lifted (data structurally unavailable)</span>'


def render_scorecard_rows(model_name, audit):
    a = audit.get(model_name)
    if not a:
        return '<tr><td colspan="2"><span class="dim">no audit row</span></td></tr>'
    out = []
    for t in ["boundary_adq", "anomaly_check", "extreme_eqn",
              "mr_zero_input", "mr_monotone", "mr_dt_halving",
              "mr_bound_consist", "mr_scale"]:
        v = a.get(t, "")
        cls = {"PASS": "ok", "FAIL": "bad", "SKIP": "dim"}.get(v, "dim")
        out.append(f'<tr><td><code>{t}</code></td>'
                   f'<td class="num"><span class="{cls}">{v}</span></td></tr>')
    rq_v   = a.get("verdict","")
    gap    = a.get("gap","")
    cell   = a.get("cell","")
    inp    = a.get("inp_cnt","")
    par    = a.get("par_cnt","")
    cls_v  = {"CONFIRM":"ok","REFUTE":"bad"}.get(rq_v,"warn")
    out.append(
        f'<tr><td><code>rq() verdict</code></td>'
        f'<td class="num"><span class="{cls_v}">{rq_v}</span>'
        f' &middot; gap {gap}</td></tr>'
        f'<tr><td><code>stress 2&times;2 cell</code></td>'
        f'<td class="num">{cell} '
        f'<span class="dim">(inputs {inp}/200 CONFIRM, params {par}/200)</span></td></tr>'
    )
    return "\n".join(out)


def render_cross_project_for_model(model_name, cp):
    if cp is None:
        return ""
    row = next((r for r in cp if r["model"] == model_name), None)
    if not row:
        return ""
    metric = row["key_metric"]
    projects = [k for k in row.keys()
                if k not in ("model","key_metric","lo","hi","boundary_status")]
    out = ['<h3>Per-project lifted value</h3>',
           f'<p>Key metric: <code>{html.escape(metric)}</code>. '
           f'Bounds: <code>[{row.get("lo","-")}, {row.get("hi","-")}]</code>.</p>',
           '<table><thead><tr><th>project</th>'
           '<th class="num">value</th><th>status</th></tr></thead><tbody>']
    bs = row.get("boundary_status","").split()
    bs_map = {b.split(":")[0]: b.split(":")[1] for b in bs if ":" in b}
    for p in projects:
        v = row[p]
        st = bs_map.get(p,"-")
        cls = {"OUT":"bad","BOUND":"warn","in":"ok","-":"dim"}.get(st,"dim")
        out.append(f'<tr><td>{p}</td>'
                   f'<td class="num mono">{html.escape(str(v))}</td>'
                   f'<td><span class="{cls}">{st}</span></td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def lift_pane_body(meta):
    if meta["lifted"]:
        return (
            f'<p>The lift is documented end-to-end in '
            f'<code>{html.escape(meta["lift_rmd"])}</code> — kaiaulu-vignette '
            f'style, knit to HTML, branchable into kaiaulu as a PR.</p>'
        )
    return (
        f'<p>This model has not been lifted on any project.</p>'
        f'<div class="callout"><span class="label">why not</span>'
        f'{html.escape(meta["lift_blocked"])}</div>'
        f'<p class="dim">The framework\'s contribution here is methodological: '
        f'the SD form expresses the thesis cleanly, but no field data source '
        f'calibrates it. That gap defines the future-research agenda.</p>'
    )


def attrs_pane_body(meta):
    if meta["lifted"]:
        return (
            '<p>The lift inputs vary by model. See the <code>.Rmd</code> '
            'notebook listed in the Data-lift tab for the specific '
            '(column, source) mapping. Common tools across models: Perceval '
            '(gitlog), kaiaulu identity_match, scc (LOC), RefactoringMiner, '
            'pattern4 (GoF), Depends, PyDriller B-SZZ.</p>'
        )
    return '<p class="dim">No lift has run, so there are no attributes to enumerate.</p>'


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — SD-Theses</title>
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/styles/github-dark.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/languages/python.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/languages/r.min.js"></script>
<script>document.addEventListener("DOMContentLoaded", () => hljs.highlightAll());</script>
</head>
<body>

<header class="nav">
  <div class="inner">
    <span class="brand"><a href="../index.html" style="color:var(--text);text-decoration:none;">SD-Theses</a><span class="sub">/ {name}</span></span>
    <nav>
      <a href="../index.html">all models</a>
    </nav>
  </div>
</header>

<main>

<h1>{name}<span class="tag">{cell} cell</span></h1>
<p class="sub-title">{cite}</p>

<div class="tabs">
  <input type="radio" name="t" id="tab-1" checked>
  <input type="radio" name="t" id="tab-2">
  <input type="radio" name="t" id="tab-3">
  <input type="radio" name="t" id="tab-4">
  <input type="radio" name="t" id="tab-5">
  <input type="radio" name="t" id="tab-6">

  <div class="tab-bar">
    <label for="tab-1">1 &middot; Summary</label>
    <label for="tab-2">2 &middot; Model</label>
    <label for="tab-3">3 &middot; Data lift</label>
    <label for="tab-4">4 &middot; Attributes</label>
    <label for="tab-5">5 &middot; Scorecard</label>
    <label for="tab-6">6 &middot; Results</label>
  </div>

  <div id="panel-1" class="tab-content">
    <h2>What this model says</h2>
    <p>{intro}</p>
    <h2>Success measure <span class="dim">(model.y)</span></h2>
    <p>{y_text}</p>
    <h2>Conjecture <span class="dim">(model.rq)</span></h2>
    <p>{rq_text}</p>
    <h2>Status</h2>
    <p>{lift_status}</p>
  </div>

  <div id="panel-2" class="tab-content">
    <h2>The SD model</h2>
    <p>From <code>models/sd.py</code>:</p>
    <pre><code class="language-python">{model_code}</code></pre>
  </div>

  <div id="panel-3" class="tab-content">
    <h2>Data lift</h2>
    {lift_pane}
  </div>

  <div id="panel-4" class="tab-content">
    <h2>Lift inputs &amp; sources</h2>
    {attrs_pane}
  </div>

  <div id="panel-5" class="tab-content">
    <h2>V&amp;V scorecard</h2>
    <p class="dim">Auto-generated from <code>outputs/full_audit.csv</code>.</p>
    <table><thead><tr><th>test</th><th>result</th></tr></thead><tbody>
{scorecard_rows}
    </tbody></table>
  </div>

  <div id="panel-6" class="tab-content">
    <h2>What we learned</h2>
    <p>{results}</p>
    {cross_project}
  </div>
</div>

</main>

<footer>
  Anonymous submission &middot; ICSE 2027
</footer>

</body>
</html>
"""


def main():
    cp    = load_cross_project()
    audit = load_full_audit()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, meta in MODELS.items():
        model_code = html.escape(extract_model_code(name))
        page = TEMPLATE.format(
            name           = name,
            cell           = meta["cell"],
            cite           = html.escape(meta["cite"]),
            intro          = html.escape(meta["intro"]),
            y_text         = html.escape(meta["y_text"]),
            rq_text        = html.escape(meta["rq_text"]),
            lift_status    = render_lift_status(meta),
            model_code     = model_code,
            lift_pane      = lift_pane_body(meta),
            attrs_pane     = attrs_pane_body(meta),
            scorecard_rows = render_scorecard_rows(name, audit),
            results        = html.escape(meta["results"]),
            cross_project  = render_cross_project_for_model(name, cp),
        )
        (OUT_DIR / f"{name}.html").write_text(page)
        written += 1
    print(f"Wrote {written} pages to {OUT_DIR}/")


if __name__ == "__main__":
    sys.exit(main())
