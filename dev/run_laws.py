#!/usr/bin/env python3 -B
"""run_laws.py: run the full lawkit pipeline on one or more laws.

  python run_laws.py                 # brooks aiwork archpat
  python run_laws.py aiwork -n 500   # quicker

Writes outputs/laws/<law>.json and outputs/laws/<law>_card.md. If
outputs/evidence/<law>_*.json exist (from mine/*.py), they are placed
in the regime map too."""

import argparse, json, time
from pathlib import Path
from lawkit.laws import LAWS
from lawkit import battery, regimes, evidence, card

OUT, EV = Path("outputs/laws"), Path("outputs/evidence")

def load_evidence(law):
  longer = [k for k in LAWS if k.startswith(law.name + "_")]
  for f in sorted(EV.glob(f"{law.name}_*.json")):
    if any(f.stem.startswith(k + "_") for k in longer): continue
    d = json.loads(f.read_text())
    meas = {k: (tuple(v) if isinstance(v, list) and len(v) == 3 and
                isinstance(v[0], str) else v)
            for k, v in d["measured"].items()}
    yield d, evidence.Evidence(law, d["project"], meas, d.get("fixed"),
                               d.get("notes", []), d.get("population", ""))

def run(law, n):
  t0 = time.time()
  R = dict(battery=battery.battery(law),
           robustness=regimes.robustness(law, n=n),
           tipping=regimes.tipping(law),
           rules=regimes.rules(law, n=max(1000, n)),
           scenarios=regimes.scenarios(law, n=n // 2),
           variants=regimes.variants(law, n=n // 2), evidence=[])
  for d, ev in load_evidence(law):
    R["evidence"].append(dict(project=ev.project, population=ev.population,
                              measured=d.get("summary", []),
                              notes=ev.notes, place=evidence.place(ev, n),
                              voi=evidence.voi(ev, n)))
  OUT.mkdir(parents=True, exist_ok=True)
  (OUT / f"{law.name}.json").write_text(json.dumps(R, indent=1,
                                                   default=str))
  (OUT / f"{law.name}_card.md").write_text(card.card(law, R),
                                           encoding="utf-8")
  print(f"{law.name}: {time.time()-t0:.1f}s -> {OUT}/{law.name}_card.md")
  return R

if __name__ == "__main__":
  p = argparse.ArgumentParser()
  p.add_argument("laws", nargs="*", default=list(LAWS))
  p.add_argument("-n", type=int, default=2000)
  a = p.parse_args()
  for k in a.laws: run(LAWS[k], a.n)
