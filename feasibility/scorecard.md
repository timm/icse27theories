# Feasibility scorecard — 17 SD models against Helix + open tools

## What "informable" means

At least one parameter or stock of the model can be calibrated from a
CSV that kaiaulu-on-Helix produces (using the open tools below).
"Partial" no longer appears in this table: with the tools added,
either everything required lifts, or fundamental data is missing.

## Tools assumed installed

| tool | role | license |
|---|---|---|
| kaiaulu | parsing + wrappers | (see kaiaulu repo) |
| Perceval | git/mbox parsing | GPLv3 |
| Depends | dependency extraction | MIT |
| scc | LOC metrics | MIT |
| RefactoringMiner | refactor events | MIT |
| pattern4.jar | GoF pattern detection | (Concordia/Tsantalis) |
| PyDriller or SZZ Unleashed | bug-introducing commits | open source |
| Arcan (fallback) | architectural smells | open source |

## Scorecard

| # | model | status | what lifts and from where |
|---|---|---|---|
| 1 | diapers | not informable | toy; no real-world correspondence |
| 2 | brooks | **informable** | late-hire events + veteran velocity from gitlog + identity_match |
| 3 | bugs (Goel-Okumoto) | **informable** | exponential fit on cumulative Bug-type resolution from parse_jira |
| 4 | debt | **informable** | refactor commits (RefactoringMiner) → pay_rate; gitlog churn → born/intr |
| 5 | sir | not informable | epidemic model; deliberately abstract |
| 6 | rework | **informable** | SZZ pairs → failrate without needing JIRA status changelog |
| 7 | learn | **informable** | jr/tr/sr cohorts from commit counts + tenure (gitlog + identity_match) |
| 8 | brooksq | **informable** | brooks ✓ + SZZ on commits in post-hire window for defect injection |
| 9 | defmap | **informable** | release tags partition phases; SZZ pairs → introduction/removal |
| 10 | aiwork | not informable | no AI authorship attribution exists in any open dataset |
| 11 | flaky | not informable | no CI logs in kaiaulu extracts |
| 12 | dora | **informable** | tags → batch_size + deploy_freq; SZZ → CFR; SZZ pairs → MTTR |
| 13 | micro | not informable | no service architecture data; Helix is monolith |
| 14 | teamtopo | not informable | no org chart data |
| 15 | burnout | not informable | no HR/wellbeing data |
| 16 | aidebt | not informable | no AI authorship attribution |
| 17 | archpat | **informable** | pattern4.jar → Patterned partition; RefactoringMiner → gen_pat |
| 18 | congruence (proposed) | **informable** | radio-silence + reply graph (already demonstrated) |

## Summary

```
fully informable now:           10  (was 4 with just kaiaulu)
partial:                         0  (collapsed into informable or not-informable)
fundamentally not informable:    7  (aiwork, aidebt, flaky, micro,
                                    teamtopo, burnout, sir+diapers)
```

## Why the 7 don't move

Single shared cause: **data sources that don't exist in any open
repository**, not just Helix.

| not informable | data we'd need | does it exist anywhere? |
|---|---|---|
| aiwork, aidebt | per-commit AI authorship attribution | not collected by any standard tool |
| flaky | CI logs with retry/flake outcomes | exists for some projects but kaiaulu doesn't parse them |
| micro | service-architecture map | needs ops/k8s/manifest scrape; project-specific |
| teamtopo | org chart + team boundaries | private to companies |
| burnout | HR/wellbeing surveys | private, ethics-gated |

These are NOT failures of the methodology or of Helix. They are gaps
in **what the field collects.** That itself is the paper's headline
finding: 10 models calibrate; the 7 that don't, name a research
agenda.

## Implications for worked-example trio

Old plan: {brooks, archpat, aiwork}.
- brooks: ready ✓
- archpat: was blocked on DV8, now unblocked via pattern4.jar (GoF)
  or Arcan (smells, fallback)
- aiwork: structurally not informable → becomes methodological worked
  example, not empirical

Better trio with the new tools:
- **{brooks, archpat, dora}** — adds DORA metrics on real data;
  resonates with practitioners.
- **{brooks, archpat, brooksq}** — adds defect injection via SZZ;
  resonates with the academy.

Either pairs better with the methodology paper than aiwork did.
aiwork stays in the paper as a methodological case: "the framework
can express this thesis but no data source can calibrate it."

## Sequencing (one work-week)

| pass | tool | output | unlocks |
|---|---|---|---|
| 1 (half day) | RefactoringMiner | refactor events on Helix | debt, archpat (gen_pat) |
| 2 (1 day) | PyDriller B-SZZ | bug intro→fix pairs | brooksq, defmap, rework, dora |
| 3 (1 day) | pattern4.jar | GoF instances per snapshot | archpat (Patterned partition) |
| 4 (1 day) | identity_match port | comm + code alias bridge | sharpens all communication-based lifts |
| 5 (parallel) | run on Helix snapshots | populated CSVs | all 10 |

Total: ~1 work-week. Cheapest empirical investment available right now.
