# Sanity Status — per-lift bug-count + identity bridge

Carlos's two sanity checks (2026-05-20 email §2):
- **Sanity #1**: bug-count dependency. For lifts that need bug count,
  is the dataset's communication source adequate?
- **Sanity #2**: identity bridge across source+communication. JIRA +
  mbox can use kaiaulu's stock `identity_match`. GitHub requires an
  extra alias source (the GitHub commit data has `author.login` ↔
  `commit.author.email`, which is the bridge).

## Coverage by model

| model     | needs bug count? | source used today              | needs identity bridge? | bridge used today |
|-----------|------------------|--------------------------------|------------------------|-------------------|
| diapers   | n/a              | n/a (toy)                      | n/a                    | n/a               |
| brooks    | no               | gitlog only                    | yes (git only — single source) | identity_match exact |
| bugs      | yes (Bug-type)   | needs JIRA dump (not done)     | no                     | n/a               |
| debt      | no               | RefactoringMiner events        | no                     | n/a               |
| sir       | no               | **Depends file-level graph (NEW path opened 2026-05-25)** | n/a               | n/a               |
| rework    | yes (any bug)    | **commit-msg heuristic + SZZ** | no                     | n/a               |
| learn     | no               | gitlog cohorts                 | yes (git only)         | identity_match exact |
| brooksq   | yes (any bug)    | **commit-msg heuristic + SZZ** | yes (git only)         | identity_match exact |
| defmap    | yes (any bug)    | **commit-msg heuristic + SZZ** | no                     | n/a               |
| aiwork    | n/a              | n/a (no AI attribution)        | n/a                    | n/a               |
| flaky     | n/a              | n/a (no CI logs)               | n/a                    | n/a               |
| dora      | yes (CFR=fix/total) | **commit-msg heuristic + SZZ** | no                  | n/a               |
| micro     | n/a              | n/a (no service arch)          | n/a                    | n/a               |
| teamtopo  | n/a              | n/a (no org chart)             | n/a                    | n/a               |
| burnout   | n/a              | n/a (no HR data)               | n/a                    | n/a               |
| aidebt    | n/a              | n/a (no AI attribution)        | n/a                    | n/a               |
| archpat   | yes (per-file)   | **SZZ-introducing-commit-touch**| no                    | n/a               |
| congruence| no               | mbox reply graph only          | **yes** (mbox + git)   | not yet wired     |

**Bold** = current implementation uses a heuristic source, not the
canonical kaiaulu+JIRA path. Upgrade plan: when JIRA Bug-type filter
arrives (e.g. Carlos's Drive full dump for Helix), tighten SZZ seed
list to JIRA-Bug-type-only.

## Per-project sanity flags

What each project's bug-count source is in the current lifts:

| project  | comm source(s)         | bug-count source        | identity bridge needed | bridge state         |
|----------|------------------------|-------------------------|------------------------|----------------------|
| Helix    | JIRA + mbox + github   | **commit-msg heuristic** (full JIRA dump avail but not loaded) | git-only models: no; congruence: yes | identity_match exact |
| junit5   | github only            | commit-msg `#NNN` heuristic | github → would need login alias source (not loaded) | identity_match exact |
| Ambari   | JIRA + mbox            | **commit-msg heuristic** (JIRA dump not loaded) | git only: no    | identity_match exact |
| kaiaulu  | github                 | commit-msg `#NNN` heuristic | github → alias source needed | identity_match exact |
| airflow  | mbox                   | commit-msg `#NNN` heuristic | mbox + git: yes (not wired) | identity_match exact |
| openssl  | pipermail              | not lifted              | n/a                    | n/a                  |
| tomcat   | mbox                   | commit-msg `BZ` heuristic (under-matches) | mbox + git: yes (not wired) | identity_match exact |
| camel    | JIRA                   | commit-msg `CAMEL-NNN` heuristic (close to ideal — JIRA references are explicit) | git only: no | identity_match exact |

**Notable mismatches**:
- **tomcat's `BZ` regex is undermatched** — only 74 SZZ pairs from
  22k commits. Tomcat commit conventions don't consistently use `BZ`
  prefix. Should widen regex or fetch Tomcat's Bugzilla data.
- **Helix + Ambari have full JIRA dumps available on Carlos's Drive
  but not loaded locally** — bug filter would tighten from "any
  commit mentioning ANY HELIX-N + bug-word" to "any commit mentioning
  HELIX-N where issuetype=Bug". Plausibly 20–40% fewer false-positive
  bug-fix commits.
- **GitHub identity bridge not yet implemented** for junit5, kaiaulu.
  Would need to parse `github/*/commit/*.json` to build the
  `author.login → emails[]` map, then feed to identity_match as
  additional aliases. Probably consolidates ~10% of identities.
- **Mbox + git identity bridge not yet implemented** for airflow,
  tomcat, Ambari, Helix. The mbox sender email is the canonical
  alias key; kaiaulu's `identity_match` with multiple sources merges
  them. Currently we only feed git emails to identity_match. Adding
  mbox emails would catch devs whose mbox-only address differs from
  git-author address.

## Upgrade priority

1. **Load full Helix JIRA dump** — biggest single quality boost; one
   dataset already on disk (partial), the full one is on Carlos's
   Drive folder. Tightens 4 SZZ-based Helix lifts (brooksq, rework,
   defmap, dora) + unlocks `bugs` lift entirely.
2. **Widen tomcat BZ regex** — quick win for tomcat coverage.
3. **GitHub login → email bridge** — quick parse of `github/commit/`
   JSONs for junit5/kaiaulu refines identity_match.
4. **Mbox + git bridge** — feed mbox sender emails to identity_match
   alongside git emails. Refines all 4 mbox-bearing projects.
5. **Pipermail SZZ for openssl** — would unlock 3 more openssl lifts
   if regex tuned to openssl's commit conventions.
6. **sir lift via Depends + pattern4 over time** — Depends now
   producing dep graphs. `sir` needs (anti-pattern × time × dep-graph)
   to model pattern spread. Expensive multi-snapshot pipeline; deferred.
