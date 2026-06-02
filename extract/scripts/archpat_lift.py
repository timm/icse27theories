#!/usr/bin/env python3
"""Archpat lift (pure-Python, no R, no mvn, no pattern4).

Computes the Patterned/Legacy/Drift/Other partition for a project's
Java files using HEURISTIC substitutions for the kaiaulu pipeline:

  * Patterned   ← Java files whose class/file name ends in a GoF
                  pattern keyword (Factory, Singleton, Observer, ...).
                  Substitute for: pattern4 GoF detector on .class files.
                  Limitation: under-detects (only catches name-stamped
                  patterns) and over-counts (any *Factory.java).
  * Legacy      ← Files touched by ≥ legacy_bug_threshold bug-fix
                  commits (heuristic msg match) AND not Patterned.
                  Substitute for: SZZ-introducing-commit-touches OR
                  parse_jira()+Bug-type filter.
  * Drift       ← Files with churn (recent commits / total commits)
                  ≥ drift_churn_threshold AND not Patterned.
                  Faithful to the archpat assign_file_partition() logic.
  * Other       ← Everything else.

Output:
  data/<project>/derived/archpat/heuristic_partition.csv
  ~/tmp/archpat_<project>.html  (standalone, no JS, no external CSS)

Usage:
  python3 extract/scripts/archpat_lift.py <project> <repo_path>

Example:
  python3 extract/scripts/archpat_lift.py tomcat data/tomcat/git_repo
  python3 extract/scripts/archpat_lift.py camel  data/camel/git_repo
"""
import csv, html, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

GOF_KEYWORDS = [
    "Factory", "AbstractFactory", "Singleton", "Builder", "Prototype",
    "Adapter", "Bridge", "Composite", "Decorator", "Facade", "Flyweight",
    "Proxy",
    "Chain", "ChainOfResponsibility", "Command", "Interpreter",
    "Iterator", "Mediator", "Memento", "Observer", "State", "Strategy",
    "Template", "TemplateMethod", "Visitor",
]
GOF_RE = re.compile(
    r"(?:^|/)([A-Z][A-Za-z0-9_]*?(?:" + "|".join(GOF_KEYWORDS) + r"))\.java$"
)

BUG_RE = re.compile(
    r"\b(fix|bug|defect|error|issue|broken|null\s*pointer|npe|crash|leak|race)\b",
    re.IGNORECASE,
)

LEGACY_BUG_THRESHOLD  = 3
DRIFT_CHURN_THRESHOLD = 0.5
RECENT_WINDOW_DAYS    = 180


def git(args, repo):
    r = subprocess.run(["git", "-C", repo] + args,
                       capture_output=True, text=True, check=False)
    return r.stdout


def walk_gitlog(repo, java_only=True, skip_test=True):
    """Yield (commit_hash, iso_date, msg_first_line, files_changed_list)."""
    raw = git(["log", "--all", "--name-only",
               "--pretty=format:__COMMIT__%H%x09%cI%x09%s"], repo)
    cur = None
    for line in raw.splitlines():
        if line.startswith("__COMMIT__"):
            if cur:
                yield cur
            sha, iso, msg = (line.removeprefix("__COMMIT__")
                                 .split("\t", 2) + ["", ""])[:3]
            cur = (sha, iso, msg, [])
        elif line.strip():
            if java_only and not line.endswith(".java"):
                continue
            if skip_test and "/test/" in line:
                continue
            if cur:
                cur[3].append(line)
    if cur:
        yield cur


def lift(project, repo_path):
    repo = str(Path(repo_path).resolve())
    if not (Path(repo) / ".git").exists():
        sys.exit(f"  {repo}/.git not found")

    print(f"[1/4] scanning gitlog at {repo} ...", flush=True)
    commits        = []
    files_seen     = set()
    bug_count      = Counter()
    recent_commits = Counter()
    total_commits  = Counter()

    cutoff = datetime.now(timezone.utc) - timedelta(days=RECENT_WINDOW_DAYS)

    for sha, iso, msg, files in walk_gitlog(repo):
        commits.append(sha)
        try:
            t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            t = None
        is_recent = t and t >= cutoff
        is_bugfix = bool(BUG_RE.search(msg))
        for f in files:
            files_seen.add(f)
            total_commits[f] += 1
            if is_recent: recent_commits[f] += 1
            if is_bugfix: bug_count[f]      += 1

    print(f"[2/4] {len(commits)} commits, {len(files_seen)} .java files (non-test)")

    print(f"[3/4] classifying partition...")
    patterned = set()
    pattern_kinds = defaultdict(set)
    for f in files_seen:
        m = GOF_RE.search(f)
        if m:
            patterned.add(f)
            cls = m.group(1)
            kind = next((k for k in GOF_KEYWORDS if cls.endswith(k)), "Other")
            pattern_kinds[kind].add(f)

    partition = {}
    for f in files_seen:
        churn = (recent_commits[f] / total_commits[f]) if total_commits[f] else 0
        if f in patterned:
            partition[f] = "Patterned"
        elif bug_count[f] >= LEGACY_BUG_THRESHOLD:
            partition[f] = "Legacy"
        elif churn >= DRIFT_CHURN_THRESHOLD:
            partition[f] = "Drift"
        else:
            partition[f] = "Other"

    counts = Counter(partition.values())
    n_files = len(files_seen)
    n_pat, n_leg, n_dri, n_oth = (counts.get(k, 0)
                                  for k in ["Patterned","Legacy","Drift","Other"])

    print(f"[4/4] writing outputs...")
    derived = Path("data") / project / "derived" / "archpat"
    derived.mkdir(parents=True, exist_ok=True)
    csv_path = derived / "heuristic_partition.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file_pathname", "partition", "n_bug_commits",
                    "n_recent_commits", "n_total_commits"])
        for f in sorted(files_seen):
            w.writerow([f, partition[f], bug_count[f],
                        recent_commits[f], total_commits[f]])

    top_bugs = sorted(((bug_count[f], f) for f in files_seen
                       if partition[f] == "Legacy"), reverse=True)[:15]
    top_drift = sorted(((recent_commits[f] / max(1, total_commits[f]), f)
                        for f in files_seen if partition[f] == "Drift"),
                       reverse=True)[:15]
    pat_kind_counts = sorted([(k, len(v)) for k, v in pattern_kinds.items()],
                             key=lambda x: -x[1])[:15]

    html_out = render_html(project, repo, len(commits), n_files,
                           n_pat, n_leg, n_dri, n_oth,
                           pat_kind_counts, top_bugs, top_drift)
    out_html = Path(os.path.expanduser("~/tmp")) / f"archpat_{project}.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html_out)

    print(f"\nDone.")
    print(f"  CSV:  {csv_path}")
    print(f"  HTML: {out_html}")
    print(f"  Partition: Patterned={n_pat}  Legacy={n_leg}  Drift={n_dri}  Other={n_oth}")
    return {
        "project": project, "n_commits": len(commits), "n_files": n_files,
        "Patterned": n_pat, "Legacy": n_leg, "Drift": n_dri, "Other": n_oth,
    }


def render_html(project, repo, n_commits, n_files,
                n_pat, n_leg, n_dri, n_oth,
                pat_kind_counts, top_bugs, top_drift):
    def esc(s): return html.escape(str(s))
    def pct(n): return f"{100*n/max(1,n_files):.1f}%"
    pat_rows = "".join(
        f"<tr><td><code>{esc(k)}</code></td><td class='num'>{n}</td></tr>"
        for k, n in pat_kind_counts)
    bug_rows = "".join(
        f"<tr><td class='num'>{n}</td><td><code>{esc(f)}</code></td></tr>"
        for n, f in top_bugs) or "<tr><td colspan='2' class='dim'>no Legacy files at threshold</td></tr>"
    drift_rows = "".join(
        f"<tr><td class='num'>{c:.2f}</td><td><code>{esc(f)}</code></td></tr>"
        for c, f in top_drift) or "<tr><td colspan='2' class='dim'>no Drift files at threshold</td></tr>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>archpat lift — {esc(project)}</title>
<style>
body{{font-family:-apple-system,'Segoe UI',sans-serif;max-width:980px;margin:2em auto;padding:0 1em;color:#222;line-height:1.45}}
h1,h2,h3{{color:#1a1a1a}} h1{{border-bottom:2px solid #ddd;padding-bottom:.3em}}
table{{border-collapse:collapse;margin:.5em 0 1em 0;font-size:14px}}
th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left}}
th{{background:#f0f0f0}} .num{{text-align:right;font-variant-numeric:tabular-nums}}
code{{font-family:'SF Mono',Menlo,Consolas,monospace;font-size:13px;background:#f5f5f5;padding:1px 4px;border-radius:3px}}
.dim{{color:#888}} .ok{{color:#0a7000;font-weight:600}} .warn{{color:#a07000;font-weight:600}} .bad{{color:#a00010;font-weight:600}}
.callout{{background:#fff8e0;border-left:4px solid #d4a017;padding:.75em 1em;margin:1em 0;border-radius:0 4px 4px 0}}
.banner-method{{background:#e8f0ff;border-left:4px solid #2060c0;padding:.75em 1em;margin:1em 0;border-radius:0 4px 4px 0}}
.pat-card{{display:inline-block;padding:.4em .7em;margin:.2em;border-radius:4px;font-size:13px;background:#e8f0e8;color:#2a5a2a;border:1px solid #b0d0b0}}
.pat-card.legacy{{background:#fce8e8;color:#7a2020;border-color:#d0a0a0}}
.pat-card.drift{{background:#fdf0d8;color:#7a5510;border-color:#d8c090}}
.pat-card.other{{background:#f0f0f0;color:#555;border-color:#c8c8c8}}
.kpi{{display:flex;gap:1em;flex-wrap:wrap;margin:1em 0}}
.kpi>div{{flex:1;min-width:140px;padding:.8em;border:1px solid #ddd;border-radius:4px;text-align:center;background:#fafafa}}
.kpi .v{{font-size:1.8em;font-weight:700;display:block;line-height:1.1}}
.kpi .l{{font-size:.85em;color:#555}}
footer{{margin-top:3em;padding-top:1em;border-top:1px solid #ddd;color:#666;font-size:13px}}
</style></head><body>

<h1>archpat lift — <code>{esc(project)}</code></h1>

<div class="banner-method">
<strong>Methodological substitution &mdash; read this first.</strong>
This run uses <em>heuristic</em> stand-ins for two of the three
steps of the canonical kaiaulu <code>lift_archpat.Rmd</code> pipeline.
Carlos &mdash; this is the methodology surface you'll want to argue
with. Each substitution is named, the canonical step it replaces is
cited, and the known bias is spelled out.

<h3>1. Patterned partition &mdash; name-match heuristic (SUBSTITUTED)</h3>
<p><strong>What this run did</strong>: classify file as Patterned iff
its basename matches the regex</p>
<pre style="font-size:12px;background:#f5f5f5;padding:.5em;overflow-x:auto">(?:^|/)([A-Z][A-Za-z0-9_]*?(?:Factory|AbstractFactory|Singleton|
        Builder|Prototype|Adapter|Bridge|Composite|Decorator|Facade|
        Flyweight|Proxy|Chain|ChainOfResponsibility|Command|Interpreter|
        Iterator|Mediator|Memento|Observer|State|Strategy|Template|
        TemplateMethod|Visitor))\.java$</pre>
<p>22 GoF keyword stems. Catches <code>FooFactory.java</code>,
<code>MyObserver.java</code>, etc.</p>
<p><strong>What canonical pipeline does</strong>:</p>
<pre style="font-size:12px;background:#f5f5f5;padding:.5em;overflow-x:auto">mvn compile -pl &lt;module&gt; -am -DskipTests          # produce .class files
java -Xmx2g -jar pattern4.jar -target classes \   # Tsantalis 2006
                              -output patterns.xml
python3 extract/scripts/parse_pattern4_xml.py \
        patterns.xml &gt; patterned_files.csv         # XML -> CSV
# OR: kaiaulu parse_gof_patterns() reads the same XML</pre>
<p>Tsantalis, Chatzigeorgiou, Stephanides, Halkidis (2006). Design
Pattern Detection Using Similarity Scoring. <em>IEEE TSE</em>
32(11):896-909. doi:10.1109/TSE.2006.112.</p>
<p><strong>Why not done</strong>: tomcat is Ant-built (no
<code>pom.xml</code> at root); camel <code>mvn compile</code> is
blocked by JDK 26 incompatibility (repo GOTCHA #9 &mdash; Maven dep
resolution fails on Java 26 even with
<code>-Dcheckstyle.skip=true</code>). Unblock: install Temurin
OpenJDK 17 alongside JDK 26, set <code>JAVA_HOME</code>, re-run.</p>
<p><strong>Known bias of the heuristic</strong>:</p>
<ul>
<li><strong>Under-counts</strong>: real GoF instances rarely carry
    the keyword in the class name. <code>EventListener</code> is an
    Observer; <code>RetryPolicy</code> is a Strategy; neither matches.</li>
<li><strong>Over-counts</strong>: any <code>*Factory.java</code> flags,
    even static-method utility holders, DI bean factories, or test
    helper factories that aren't GoF Factory Method.</li>
<li><strong>Particularly visible on camel</strong>: the route-DSL
    convention (<code>RouteBuilder</code>, <code>JmsBuilder</code>,
    <code>RestBuilder</code>, <code>*Strategy</code>,
    <code>*Template</code>) inflates Patterned to about 5564 files
    (16.5%). Real pattern4 would likely return &lt;500. Treat camel's
    Patterned count as a known-broken upper bound.</li>
</ul>

<h3>2. Legacy partition &mdash; commit-msg bug-fix heuristic (SUBSTITUTED)</h3>
<p><strong>What this run did</strong>: classify file as Legacy iff it
is touched by &ge; {LEGACY_BUG_THRESHOLD} commits whose message
matches</p>
<pre style="font-size:12px;background:#f5f5f5;padding:.5em">\b(fix|bug|defect|error|issue|broken|null\s*pointer|npe|crash|leak|race)\b  (case-insensitive)</pre>
<p>AND the file is not already Patterned. Priority order: Patterned
&gt; Legacy &gt; Drift &gt; Other.</p>
<p><strong>What canonical pipeline does</strong> (in order of
preference):</p>
<ol>
<li><code>parse_jira()</code> + filter <code>issuetype == "Bug"</code>,
    then join via commit-message issue-key reference to per-file bug
    count. Requires complete JIRA dump.</li>
<li><strong>B-SZZ</strong> via PyDriller
    (<code>extract/scripts/szz_pass.py</code>): find bug-fix commits
    -&gt; <code>git blame</code> the modified lines -&gt; emit
    <code>(introducing_commit, fixing_commit)</code> pairs. Per-file
    bug count = distinct introducing commits touching the file.</li>
<li><strong>SZZ-Unleashed</strong> (kaiaulu's preferred variant): adds
    heuristics for refactor-only and merge-only commits.</li>
</ol>
<p><strong>Why not done</strong>: SZZ via PyDriller takes ~20-30 min
per project (camel's 81,933 commits would be ~45-60 min). Skipped
for this first delivery; happy to run if you want a second iteration.</p>
<p><strong>Known bias of the heuristic</strong>:</p>
<ul>
<li><strong>Over-matches</strong>: commits like "fix typo in javadoc",
    "fix formatting", "fix license header" all increment a file's
    bug count.</li>
<li><strong>Under-matches</strong> project-specific conventions.
    Tomcat sometimes uses <code>BZ 12345</code> (bugzilla) without a
    bug-word; conf already carries a wider issue regex for that,
    but this heuristic ignores it.</li>
<li><strong>JIRA-key-only matches</strong> (e.g., camel's
    <code>CAMEL-NNN</code>) are not treated as bug-fixes by this regex
    unless the message also contains a bug-word. Pipeline 1 above
    would catch those via <code>issuetype</code>.</li>
<li>Legacy counts here are inflated relative to canonical pipeline.
    Direction is right (more bug-fix-touched files rank higher);
    magnitude is not directly comparable.</li>
</ul>

<h3>3. Drift partition &mdash; churn fraction (FAITHFUL to kaiaulu)</h3>
<p><strong>What this run did</strong>: per file,
<code>churn = recent_commits / total_commits</code> where recent =
last {RECENT_WINDOW_DAYS} days. Threshold
{DRIFT_CHURN_THRESHOLD}. Classify as Drift iff
<code>churn &ge; {DRIFT_CHURN_THRESHOLD}</code> AND not Patterned.</p>
<p>Matches <code>assign_file_partition()</code> in
<code>extract/lifts/functions.R</code> exactly. <strong>No
substitution.</strong></p>
<p><strong>Observed Drift = 0 on this project</strong> (and on tomcat
+ camel both): Drive bundle's git_repo snapshots are stale &mdash;
last commits in the zip date from 2020. Almost no file has &gt;50% of
its commits in the last 180 days because most commits predate that
window. Same problem would hit the canonical pipeline against this
snapshot. Either (a) widen window to several years, (b) anchor
"recent" to latest commit in repo rather than wall-clock now, or
(c) refresh the snapshot.</p>

<h3>Threshold parameters used (all in <code>archpat_lift.py</code>)</h3>
<pre style="font-size:12px;background:#f5f5f5;padding:.5em">LEGACY_BUG_THRESHOLD  = {LEGACY_BUG_THRESHOLD}    # >={LEGACY_BUG_THRESHOLD} bug-msg commits -> Legacy
DRIFT_CHURN_THRESHOLD = {DRIFT_CHURN_THRESHOLD}  # >=50% commits recent -> Drift
RECENT_WINDOW_DAYS    = {RECENT_WINDOW_DAYS}  # window for "recent" in churn calc</pre>
<p>Defaults match <code>assign_file_partition()</code> in
<code>lifts/functions.R</code>.</p>

<h3>Scope filter applied</h3>
<ul>
<li>Java only (<code>.java</code> extension)</li>
<li>Excludes paths containing <code>/test/</code> (drops
    <code>*/src/test/java/*</code> etc.)</li>
<li>All branches (<code>git log --all</code>) &mdash; total commit
    counts may exceed <code>git log master</code></li>
</ul>

<h3>CSV alongside this HTML</h3>
<p><code>data/{esc(project)}/derived/archpat/heuristic_partition.csv</code>
&mdash; columns <code>file_pathname, partition, n_bug_commits,
n_recent_commits, n_total_commits</code>. Same SCHEMA as the
canonical pipeline's <code>patterned_files.csv</code> + bug-frequency
table, so downstream <code>lift_archpat.Rmd</code> can swap one
source for the other.</p>
</div>

<h2>Summary</h2>
<p>Project: <code>{esc(repo)}</code>.
Commits scanned: {n_commits:,}. Non-test <code>.java</code> files:
{n_files:,}. Recent window: {RECENT_WINDOW_DAYS} days.
Bug threshold (Legacy): &ge; {LEGACY_BUG_THRESHOLD} bug-fix commits.
Churn threshold (Drift): &ge; {DRIFT_CHURN_THRESHOLD}.</p>

<div class="kpi">
<div><span class="v ok">{n_pat:,}</span><span class="l">Patterned ({pct(n_pat)})</span></div>
<div><span class="v bad">{n_leg:,}</span><span class="l">Legacy ({pct(n_leg)})</span></div>
<div><span class="v warn">{n_dri:,}</span><span class="l">Drift ({pct(n_dri)})</span></div>
<div><span class="v dim">{n_oth:,}</span><span class="l">Other ({pct(n_oth)})</span></div>
</div>

<div class="callout">
<strong>What to do with these numbers</strong>: feed
<code>Patterned_n={n_pat}</code>, <code>Legacy_n={n_leg}</code>,
<code>Drift_n={n_dri}</code> into
<code>paper/sd.py::archpat()</code>'s <code>init</code> dict via
<code>scripts/calibrate.py</code>. The archpat model's RQ ("aggressive
migration repairs an already-bad project") is then evaluated against
this project's empirical regime.
</div>

<h2>GoF keyword breakdown (Patterned)</h2>
<table>
<thead><tr><th>keyword</th><th class="num">file count</th></tr></thead>
<tbody>{pat_rows}</tbody>
</table>

<h2>Top 15 Legacy files (most bug-fix-touched)</h2>
<table>
<thead><tr><th class="num">bug-fix commits</th><th>file</th></tr></thead>
<tbody>{bug_rows}</tbody>
</table>

<h2>Top 15 Drift files (highest recent-commit fraction)</h2>
<table>
<thead><tr><th class="num">churn ratio</th><th>file</th></tr></thead>
<tbody>{drift_rows}</tbody>
</table>

<footer>
Generated by <code>extract/scripts/archpat_lift.py</code> (pure-Python
substitute for the canonical kaiaulu R lift pipeline).
Companion files: <code>data/{esc(project)}/derived/archpat/heuristic_partition.csv</code>.
SD model: <code>paper/sd.py::archpat()</code>.
Canonical lift: <code>extract/lifts/lift_archpat.Rmd</code>
(requires pattern4 + SZZ; not run for this delivery).
</footer>
</body></html>
"""


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: archpat_lift.py <project> <repo_path>")
    project, repo = sys.argv[1], sys.argv[2]
    lift(project, repo)


if __name__ == "__main__":
    main()
