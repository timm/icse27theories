#!/usr/bin/env python3
"""B-SZZ pass on Apache Helix using PyDriller.

Two outputs:
  data/helix/derived/bugfix_commits.csv  — fixing commits (HELIX-NNNN + bug word)
  data/helix/derived/szz_pairs.csv       — (fixing -> introducing, file) triples

Heuristic for "bug-fix commit": message contains a HELIX-NNNN key AND a
bug-word (fix, bug, defect, npe, crash, leak, race, ...). This is the
seed list for B-SZZ. PyDriller's get_commits_last_modified_lines walks
blame on the changed lines to find the introducing commits.

No JIRA data required — uses only commit messages. Refinement using
parsed JIRA Bug-type issues is a TODO once Helix JIRA dump is local.
"""

import csv, os, re, sys, time

from pydriller import Repository, Git

REPO       = "data/helix/git_repo"
OUT_DIR    = "data/helix/derived"
BUGFIX_CSV = os.path.join(OUT_DIR, "bugfix_commits.csv")
PAIRS_CSV  = os.path.join(OUT_DIR, "szz_pairs.csv")

JIRA_PAT = re.compile(r"HELIX-(\d+)", re.IGNORECASE)
BUG_PAT  = re.compile(
    r"\b(fix|bug|defect|error|issue|broken|null\s*pointer|npe|crash|leak|race)\b",
    re.IGNORECASE,
)


def find_bugfix_commits(repo_path):
    rows, total = [], 0
    for c in Repository(repo_path).traverse_commits():
        total += 1
        msg = c.msg or ""
        keys = JIRA_PAT.findall(msg)
        if keys and BUG_PAT.search(msg):
            rows.append({
                "commit_hash":    c.hash,
                "jira_keys":      ";".join(sorted({"HELIX-" + k for k in keys})),
                "author":         c.author.email,
                "date":           c.committer_date.isoformat(),
                "files_touched":  len(c.modified_files),
                "msg_first_line": msg.splitlines()[0][:120].replace(",", " "),
            })
    return rows, total


def szz_pairs(repo_path, fixes):
    g = Git(repo_path)
    pairs, errors = [], 0
    for i, fx in enumerate(fixes):
        try:
            c = g.get_commit(fx["commit_hash"])
            intro_map = g.get_commits_last_modified_lines(c)
            for file_path, intro_commits in intro_map.items():
                for ic in intro_commits:
                    pairs.append({
                        "fixing_commit_hash":      fx["commit_hash"],
                        "introducing_commit_hash": ic,
                        "file_path":               file_path,
                        "jira_keys":               fx["jira_keys"],
                        "fixing_date":             fx["date"],
                    })
        except Exception:
            errors += 1
        if (i + 1) % 50 == 0:
            print(f"  szz: {i+1}/{len(fixes)} fixes, {len(pairs)} pairs")

    intro_dates = {}
    for p in pairs:
        h = p["introducing_commit_hash"]
        if h not in intro_dates:
            try:
                intro_dates[h] = g.get_commit(h).committer_date.isoformat()
            except Exception:
                intro_dates[h] = ""
    for p in pairs:
        p["introducing_date"] = intro_dates.get(p["introducing_commit_hash"], "")
    return pairs, errors


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    t0 = time.time()
    fixes, total = find_bugfix_commits(REPO)
    print(f"Scanned {total} commits in {time.time()-t0:.1f}s; "
          f"{len(fixes)} bug-fix candidates")

    with open(BUGFIX_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fixes[0].keys()))
        w.writeheader()
        w.writerows(fixes)
    print(f"Wrote {BUGFIX_CSV}")

    t1 = time.time()
    pairs, errors = szz_pairs(REPO, fixes)
    print(f"SZZ: {len(pairs)} pairs, {errors} errors, "
          f"{time.time()-t1:.1f}s")

    cols = ["fixing_commit_hash", "introducing_commit_hash", "file_path",
            "jira_keys", "fixing_date", "introducing_date"]
    with open(PAIRS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(pairs)
    print(f"Wrote {PAIRS_CSV}")


if __name__ == "__main__":
    sys.exit(main())
