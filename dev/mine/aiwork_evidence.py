#!/usr/bin/env python3 -B
"""aiwork_evidence.py: GitClear-style 14-day churn of AI vs human lines,
same author(s), same period, size-stratified.

  python mine/aiwork_evidence.py <repo> <project> --authors "Paul Gauthier"
      --ai "\\(aider\\)" --since 2024-07-01 --until 2025-07-01
      --prefix aider/ --ext .py

A commit is AI if its author name or Co-authored-by trailer matches
--ai. For sampled (commit, file) pairs, git blame at the last commit
before +14 days counts surviving lines. churn = 1 - survived/added.
churn_mult (sd.aiwork) = churn_AI / churn_human - 1.
Writes outputs/evidence/aiwork_<project>.json + a pairs CSV."""

import argparse, csv, json, random, re, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from gitlog import git, boot, ci

STRATA = ((3, 20), (21, 80), (81, 400))

def log(repo):
  fmt = ("%x1e%H|%an|%at|%(trailers:key=Co-authored-by,valueonly,"
         "separator=%x3B)|%s")
  out, cur = [], None
  for line in git(repo, "log", "--no-merges", "--numstat",
                  f"--format={fmt}").split("\n"):
    if line.startswith("\x1e"):
      h, an, at, tr, msg = line[1:].split("|", 4)
      cur = dict(hash=h, name=an, tr=tr, msg=msg, files={},
                 when=dt.datetime.fromtimestamp(int(at), dt.timezone.utc))
      out.append(cur)
    elif line.strip() and cur:
      a, d, p = line.split("\t", 2)
      if a != "-" and "=>" not in p: cur["files"][p] = int(a)
  return out

def survived(repo, c, path, days):
  when = (c["when"] + dt.timedelta(days=days)).isoformat()
  rev = git(repo, "rev-list", "-1", f"--before={when}", "HEAD").strip()
  try:
    out = git(repo, "blame", "-w", "--line-porcelain", rev, "--", path)
  except Exception:
    return None                            # file gone/renamed: unknown
  return sum(1 for l in out.split("\n") if l.startswith(c["hash"] + " "))

def churn(pairs, strata=STRATA):
  "Mean over size strata of line-weighted churn (strata equally weighted)."
  per = []
  for lo, hi in strata:
    s = [p for p in pairs if lo <= p["added"] <= hi]
    if s:
      per.append(1 - sum(p["kept"] for p in s) / sum(p["added"] for p in s))
  return sum(per) / len(per) if per else float("nan")

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("repo"); ap.add_argument("project")
  ap.add_argument("--authors", nargs="+", required=True)
  ap.add_argument("--ai", required=True)
  ap.add_argument("--ai-msg", help="regex on subject, e.g. '^aider:'")
  ap.add_argument("--since"); ap.add_argument("--until")
  ap.add_argument("--prefix", default=""); ap.add_argument("--ext",
                                                           nargs="+")
  ap.add_argument("--per-arm", type=int, default=240)
  ap.add_argument("--days", type=int, default=14)
  ap.add_argument("--from-pairs", action="store_true",
                  help="reuse the saved pairs CSV (skip git blame)")
  a = ap.parse_args()
  out = Path("outputs/evidence"); out.mkdir(parents=True, exist_ok=True)
  pcsv = out / f"aiwork_{a.project}_pairs.csv"
  if a.from_pairs:
    rows = [dict(r, ai=r["ai"] == "True", added=int(r["added"]),
                 kept=int(r["kept"])) for r in csv.DictReader(open(pcsv))]
    return report(a, rows, "(from saved pairs)", "n/a", out)
  ai_re, rng = re.compile(a.ai, re.I), random.Random(1)
  base = lambda n: re.sub(r"\s*\(.*\)$", "", n)
  arms = {True: [], False: []}
  for c in log(a.repo):
    if base(c["name"]) not in a.authors: continue
    d = c["when"].date().isoformat()
    if (a.since and d < a.since) or (a.until and d >= a.until): continue
    is_ai = bool(ai_re.search(c["name"]) or ai_re.search(c["tr"]) or
                 (a.ai_msg and re.search(a.ai_msg, c["msg"])))
    for p, add in c["files"].items():
      if p.startswith(a.prefix) and (not a.ext or p.endswith(tuple(a.ext))) \
         and 3 <= add <= 400:
        arms[is_ai].append((c, p, add))
  pairs = []
  for is_ai, cands in arms.items():
    k = max(1, a.per_arm // len(STRATA))
    for lo, hi in STRATA:                   # equal sample per stratum
      s = [x for x in cands if lo <= x[2] <= hi]
      pairs += [(is_ai, *x) for x in rng.sample(s, min(k, len(s)))]
  with ThreadPoolExecutor(16) as ex:
    kept = list(ex.map(lambda x: survived(a.repo, x[1], x[2], a.days),
                       pairs))
  rows = [dict(ai=ai, hash=c["hash"][:10], file=p, added=add,
               kept=min(k, add), when=c["when"].date().isoformat())
          for (ai, c, p, add), k in zip(pairs, kept) if k is not None]
  with open(pcsv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
    w.writerows(rows)
  report(a, rows, f"candidates: AI {len(arms[True])}, human "
         f"{len(arms[False])}", len(pairs) - len(rows), out)

def report(a, rows, head, dropped, out):
  A = [r for r in rows if r["ai"]]; H = [r for r in rows if not r["ai"]]
  ok = [s for s in STRATA if all(sum(s[0] <= r["added"] <= s[1]
                                     for r in arm) >= 15 for arm in (A, H))]
  ch = lambda xs: churn(xs, ok)
  cm = [ch(boot(A, lambda z: z, 1, s)[0]) /
        max(1e-9, ch(boot(H, lambda z: z, 1, s + 7)[0])) - 1
        for s in range(1, 801)]
  lo, md, hi = ci(cm)
  summ = [head, f"blamed pairs: AI {len(A)}, human {len(H)} "
          f"(dropped {dropped} renamed/deleted); strata used {ok}",
          f"{a.days}-day churn: AI {ch(A):.1%}, human {ch(H):.1%}",
          f"churn_mult = ratio - 1 = {md:.2f} [{lo:.2f}, {hi:.2f}]"]
  ev = dict(project=a.project, measured={"churn_mult": cm}, summary=summ,
            population=f"{a.project}: commits by {', '.join(a.authors)} "
                       f"{a.since or ''}..{a.until or ''}, AI = /{a.ai}/",
            notes=[
    "Within-author, within-period comparison controls author skill and "
    "project phase, not task type: the author chooses which tasks to "
    "give the AI (selection on difficulty).",
    "GitClear churn construct: lines rewritten/removed within "
    f"{a.days} days; moved lines count as churned (blame -w, no -C).",
    "Pairs whose file was renamed or deleted by +14d are dropped "
    "(unknown survival), biasing churn down for both arms.",
    "Only churn_mult is measured. gen_boost and verify_drag (the factors "
    "that decide the verdict) are invisible in git history.",
    "AI attribution is self-declared by the tool/author; unlabelled AI "
    "use in the 'human' arm would shrink the measured difference."])
  (out / f"aiwork_{a.project}.json").write_text(json.dumps(ev))
  print("\n".join(summ))

if __name__ == "__main__":
  main()
