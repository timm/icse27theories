# Datasets

## Carlos's Drive folder (May 6 2026)

https://drive.google.com/drive/folders/1CA4eIO6-U4V0SMBQ05VNI-jdnN4ipM02

Contains 6 datasets (including kaiaulu source itself). Each follows
the same trio:
- Source code (git_repo/)
- Git log (often included in the repo clone)
- Communication: mailing list (mod_mbox), GitHub events, or JIRA

Carlos has cleaned the Helix dataset. **Re-fetch the clean Helix from
Drive** before running anything — the existing /home/claude/helix
copy is the pre-cleanup version.

Carlos has more datasets coming from his "hidden stash."

## Helix dataset layout (as previously extracted)

```
helix/
├── git_repo/helix/          # live git clone, 1875+ commits
├── jira/
│   ├── issues/HELIX_*.json       # 797 issues, full REST API format
│   └── issue_comments/HELIX_*.json
├── github/apache_helix/
│   ├── commit/
│   ├── issue/
│   ├── issue_or_pr_comment/
│   └── pull_request/        # 100 records per page, many pages
├── mod_mbox/save_mbox_mail/  # 116 mbox files, 2012-10 onwards
├── bk_mod_mbox/              # 98 older mbox files, overlapping range
└── understand/               # EMPTY — Scitools Understand output,
                              # license-gated, not in extract
```

## Carlos's sanity checks (May 6 email)

**Sanity check #1**: For any "bug count" lift, the chosen
communication source matters. Claude should be able to say which
datasets support a model that needs bug-count and which don't, based
on whether the dataset has JIRA (or equivalent) attached.

**Sanity check #2**: For any model requiring both source code AND
communication, kaiaulu's `identity_match()` must be invoked. JIRA +
mbox: feasible with the standard identity_match. **GitHub**: requires
an extra alias source (the GitHub username ↔ email mapping is not in
the standard extract).

Flag both sanity-check outcomes in every lift's `.Rmd` so Carlos can
see whether the constraint is honored.

## kaiaulu's conf/ already has Helix

`/path/to/kaiaulu/conf/helix.yml` exists in the kaiaulu repo. Fields
to populate when running locally:
- `version_control.log` → path to git_repo/helix/.git
- `mailing_list.mod_mbox` → path to mod_mbox/save_mbox_mail/
- `issue_tracker.jira` → path to jira/
- `issue_tracker.github` → path to github/apache_helix/
- `tool.depends`, `tool.uctags`, `tool.understand` → tool paths (in
  `tools.yml`)

`tools.yml` (top-level) needs:
```yaml
perceval:
  path: ~/perceval/bin/perceval        # or wherever installed
depends:
  jar: ~/depends/depends.jar
scc:
  binary: ~/scc/scc
refactoring_miner:
  jar: ~/RefactoringMiner/RefactoringMiner.jar
pattern4:
  jar: ~/pattern4/pattern4.jar
```

## Other expected datasets (per Carlos)

Carlos mentioned 6 in Drive, including kaiaulu itself. Likely
candidates (based on prior conversation context and Carlos's prior
work):
- Apache Camel
- Apache Geronimo
- Apache Calculator
- JUnit 5
- OpenSSL
(plus kaiaulu itself)

All have conf/<name>.yml files already in kaiaulu — see
`/path/to/kaiaulu/conf/`.
