#!/usr/bin/env python3
"""B-SZZ pass for any project, parameterized by repo + issue regex.

Usage:
  python3 scripts/szz_pass.py <repo-path> <issue-regex> <out-dir>

Example:
  python3 scripts/szz_pass.py data/helix/git_repo "HELIX-(\\d+)" data/helix/derived
  python3 scripts/szz_pass.py data/junit5/git_repo "#(\\d+)"      data/junit5/derived

Outputs <out-dir>/bugfix_commits.csv and <out-dir>/szz_pairs.csv.
"""

import csv, os, re, sys, time

from pydriller import Repository, Git


BUG_PAT = re.compile(
    r"\b(fix|bug|defect|error|issue|broken|null\s*pointer|npe|crash|leak|race)\b",
    re.IGNORECASE,
)


def find_bugfix_commits(repo_path, issue_re):
    pat = re.compile(issue_re, re.IGNORECASE)
    rows, total = [], 0
    for c in Repository(repo_path).traverse_commits():
        total += 1
        msg = c.msg or ""
        keys = pat.findall(msg)
        if keys and BUG_PAT.search(msg):
            rows.append({
                "commit_hash":    c.hash,
                "issue_keys":     ";".join(sorted(set(map(str, keys)))),
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
                        "issue_keys":              fx["issue_keys"],
                        "fixing_date":             fx["date"],
                    })
        except Exception:
            errors += 1
        if (i + 1) % 100 == 0:
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


def main(argv):
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 1
    repo, issue_re, out_dir = argv[1], argv[2], argv[3]
    os.makedirs(out_dir, exist_ok=True)

    t0 = time.time()
    fixes, total = find_bugfix_commits(repo, issue_re)
    print(f"Scanned {total} commits in {time.time()-t0:.1f}s; "
          f"{len(fixes)} bug-fix candidates")
    if not fixes:
        print("WARN: no bug-fix commits matched — check issue_re")
        return 0

    bugfix_csv = os.path.join(out_dir, "bugfix_commits.csv")
    with open(bugfix_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fixes[0].keys()))
        w.writeheader()
        w.writerows(fixes)
    print(f"Wrote {bugfix_csv}")

    t1 = time.time()
    pairs, errors = szz_pairs(repo, fixes)
    print(f"SZZ: {len(pairs)} pairs, {errors} errors, {time.time()-t1:.1f}s")

    cols = ["fixing_commit_hash", "introducing_commit_hash", "file_path",
            "issue_keys", "fixing_date", "introducing_date"]
    pairs_csv = os.path.join(out_dir, "szz_pairs.csv")
    with open(pairs_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(pairs)
    print(f"Wrote {pairs_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
