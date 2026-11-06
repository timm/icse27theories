"""gitlog.py: tiny git-log reader shared by the evidence miners.
Plain git only (no Perceval/kaiaulu) so it runs anywhere; the column
names mirror kaiaulu's parse_gitlog where they overlap."""

import subprocess, datetime as dt, random

SEP = "\x1e"

def git(repo, *args):
  return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                        text=True, encoding="utf-8", errors="replace",
                        check=True).stdout

def commits(repo, *extra):
  """[{hash, author_name, author_email, when, msg, files{path:(add,del)}}]
  oldest first, merges excluded."""
  fmt = "%x1e%H|%an|%ae|%at|%s"         # %x1e: argv-safe on Windows
  out, cur = [], None
  for line in git(repo, "log", "--no-merges", "--numstat", "-M",
                  f"--format={fmt}", *extra).split("\n"):  # not splitlines:
                                                           # it eats \x1e
    if line.startswith(SEP):
      h, an, ae, at, msg = line[1:].split("|", 4)
      cur = dict(hash=h, author_name=an, author_email=ae.lower(),
                 when=dt.datetime.fromtimestamp(int(at), dt.timezone.utc),
                 msg=msg, files={})
      out.append(cur)
    elif line.strip() and cur is not None:
      a, d, path = line.split("\t", 2)
      if "=>" in path: path = renamed(path)
      cur["files"][path] = (int(a) if a != "-" else 0,
                            int(d) if d != "-" else 0)
  return out[::-1]

def renamed(p):
  "numstat rename forms: 'a/{x => y}/b' or 'x => y' -> new path."
  if "{" in p:
    pre, rest = p.split("{", 1)
    mid, post = rest.split("}", 1)
    new = mid.split(" => ")[1]
    return (pre + new + post).replace("//", "/")
  return p.split(" => ")[1]

def month(t):
  return t.year * 12 + t.month - 1

def boot(xs, f, n=1000, seed=1):
  "Bootstrap distribution of statistic f over list xs."
  rng = random.Random(seed)
  return [f([rng.choice(xs) for _ in xs]) for _ in range(n)]

def ci(bs):
  s = sorted(bs)
  return s[len(s) // 20], s[len(s) // 2], s[-len(s) // 20 - 1]
