#!/usr/bin/env python3 -B
"""archpat_evidence.py: are GoF-patterned files really less bug-prone and
more productive than the rest (archpat's born_pat < born_leg and
gen_pat > gen_leg)? Uses the repo's committed pattern4 output.

  python mine/archpat_evidence.py <repo> helix --snapshot 2026-05-24

Per production .java file in the pattern4-scanned modules: bytes at the
snapshot, commits, bug-fix commits (subject regex), SZZ bug-introducing
commits (extract/data/<p>/derived/szz_pairs.csv), all with history
mapped through renames. Negative-binomial GLMs give rate ratios
patterned vs not, controlling size and change volume. Patterned=0 vs 1
is compared, NOT Patterned vs Legacy: Legacy is *defined* by bug count
(assign_file_partition), so using bugs to test it would be circular.
Writes outputs/evidence/archpat_cost_<p>.json and a per-file CSV."""

import argparse, csv, json, math, re, random
from collections import defaultdict
from pathlib import Path
import numpy as np
import statsmodels.api as sm
from gitlog import git, ci

FIX = re.compile(r"\b(fix(e[sd])?|bug|npe|regression)\b", re.I)

def history(repo):
  "Newest-first walk; yields (hash, subject, canonical paths touched)."
  fmt = "%x1e%H|%s"
  alias, recs, cur = {}, [], None
  for line in git(repo, "log", "--no-merges", "-M", "--name-status",
                  f"--format={fmt}").split("\n"):
    if line.startswith("\x1e"):
      cur = dict(hash=line[1:41], msg=line[42:], files=[], ren=[])
      recs.append(cur)
    elif line.strip() and cur:
      parts = line.split("\t")
      if parts[0].startswith("R"): cur["ren"].append((parts[1], parts[2]))
      cur["files"].append(parts[-1])
  for c in recs:                         # newest first: alias = later name
    c["canon"] = {p: alias.get(p, p) for p in c["files"]}
    for old, new in c["ren"]: alias[old] = alias.get(new, new)
    yield c

def table(repo, project, snapshot):
  root = Path("extract/data") / project / "derived"
  pat = defaultdict(set)
  for r in csv.DictReader(open(root / "pattern4/patterned_files.csv")):
    pat[r["file_pathname"]].add(r["pattern_type"])
  mods = {p.split("/")[0] for p in pat}
  rev = git(repo, "rev-list", "-1", f"--before={snapshot}", "HEAD").strip()
  files = {}
  for line in git(repo, "ls-tree", "-r", "-l", rev).split("\n"):
    if not line: continue
    meta, path = line.split("\t", 1)
    if path.split("/")[0] in mods and "/src/main/java/" in path \
       and path.endswith(".java"):
      files[path] = dict(path=path, bytes=int(meta.split()[3]),
                         patterned=int(path in pat), commits=0, fixes=0,
                         szz=0, n_patterns=len(pat.get(path, ())))
  szz = defaultdict(list)
  for r in csv.DictReader(open(root / "szz_pairs.csv")):
    szz[r["fixing_commit_hash"]].append(r["file_path"])
  for c in history(repo):
    for p, q in c["canon"].items():
      if q in files:
        files[q]["commits"] += 1
        files[q]["fixes"] += bool(FIX.search(c["msg"]))
    for p in szz.get(c["hash"], []):
      q = c["canon"].get(p, p)
      if q in files: files[q]["szz"] += 1
  return list(files.values()), rev

def rate_ratio(rows, y, ctl, n=300, seed=1):
  "exp(beta_patterned) from NB GLM y ~ patterned + controls; bootstrap."
  def fit(rs):
    X = np.column_stack([[r["patterned"] for r in rs]] +
                        [[f(r) for r in rs] for f in ctl])
    m = sm.GLM(np.array([r[y] for r in rs]), sm.add_constant(X),
               family=sm.families.NegativeBinomial(alpha=1.0)).fit()
    return math.exp(m.params[1])
  rng = random.Random(seed)
  return fit(rows), [fit([rng.choice(rows) for _ in rows])
                     for _ in range(n)]

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("repo"); ap.add_argument("project")
  ap.add_argument("--snapshot", default="2026-05-24")
  a = ap.parse_args()
  rows, rev = table(a.repo, a.project, a.snapshot)
  out = Path("outputs/evidence"); out.mkdir(parents=True, exist_ok=True)
  with open(out / f"archpat_{a.project}_files.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
    w.writerows(rows)
  size = lambda r: math.log(max(r["bytes"], 1))
  churn = lambda r: math.log1p(r["commits"])
  born, born_b = rate_ratio(rows, "fixes", [size, churn])
  szz, szz_b = rate_ratio(rows, "szz", [size, churn])
  gen, gen_b = rate_ratio([dict(r, other=r["commits"] - r["fixes"])
                           for r in rows], "other", [size])
  npat = sum(r["patterned"] for r in rows)
  f = lambda nm, b: f"{nm} {ci(b)[1]:.2f} [{ci(b)[0]:.2f}, {ci(b)[2]:.2f}]"
  summ = [f"snapshot {rev[:10]}: {len(rows)} production files, "
          f"{npat} patterned",
          f("born_pat/born_leg (fix commits | size, churn)", born_b),
          f("same, SZZ bug-introducing", szz_b),
          f("gen_pat/gen_leg proxy (non-fix commits | size)", gen_b)]
  ev = dict(project=a.project, summary=summ,
            measured={"born_pat": ["x", "born_leg", born_b],
                      "gen_pat": ["x", "gen_leg", gen_b]},
            fixed={"Patterned": 149, "Legacy": 384, "Drift": 0},
            population=f"{a.project}: production Java files in pattern4-"
                       f"scanned modules at {a.snapshot}; stocks from "
                       f"lift_archpat (149 / 384 / 0 Drift)",
            notes=[
    "Cross-sectional: patterned files differ from others in ways other "
    "than patterns (age, centrality, ownership). Rate ratios are "
    "associations, not the effect of migrating a file.",
    "gen proxy = non-fix commits per file; change activity is not "
    "feature delivery (may even signal instability).",
    "The lever itself (migrating Legacy -> Patterned) is unobserved: "
    "pattern4 ran on one snapshot only, so migrate, decay_rate and "
    "the price of migration (mig_cost, mig_bugs) remain priors.",
    "74% of files are 'Other' (neither patterned nor legacy); the "
    "3-stock model has no place for them (boundary adequacy).",
    "Fix commits found by subject regex; SZZ pairs are the repo's "
    "committed B-SZZ output (older history only)."])
  (out / f"archpat_cost_{a.project}.json").write_text(json.dumps(ev))
  print("\n".join(summ))

if __name__ == "__main__":
  main()
