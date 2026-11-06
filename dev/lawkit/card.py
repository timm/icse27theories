"""card.py: one markdown 'evidence card' per law. Layout follows the
argument a policy-maker needs (Cartwright & Hardie 2012): is the
machine sound -> where does the claim hold -> what breaks it ->
does *this* project sit inside the holding region -> what to measure."""

def _t(d):
  return f"{d['CONFIRM']:.0f}% / {d['REFUTE']:.0f}% / {d['neutral']:.0f}%"

def _g(q):
  return f"{q[1]:+.0f} [{q[0]:+.0f}, {q[2]:+.0f}]"

def card(law, R):
  L = [f"# Evidence card: `{law.name}`", "",
       f"**Claim.** {law.claim}.  ", f"**Lever.** `{law.lever}` "
       f"{law.arms[0]} -> {law.arms[1]}; expected y {law.expect}.  ",
       f"**Support factors.** {', '.join(law.factors)}.  ",
       f"**Sources.** {law.sources}", "",
       "## 1. Is the machine sound? (structure battery)", "",
       "| status | test | detail |", "|---|---|---|"]
  L += [f"| {r['status']} | {r['test']} | {r['detail']} |"
        for r in R["battery"]]
  L += ["", "## 2. How robust is the claim? (CONFIRM / REFUTE / neutral)",
        "", "| neighbourhood | verdicts | gap median [5%, 95%] |",
        "|---|---|---|"]
  for how, lab in (("local", "+-15% around defaults (old MC protocol)"),
                   ("prior", "triangular over declared ranges"),
                   ("uniform", "uniform over declared ranges")):
    d = R["robustness"][how]
    L.append(f"| {lab} | {_t(d)} | {_g(d['gap'])} |")
  ru = R["rules"]
  L += ["", f"## 3. What decides it? (tree on prior draws, base rate "
        f"{ru['base_rate']:.0%} CONFIRM, accuracy {ru['accuracy']:.0%})",
        "", "Importance: " + ", ".join(f"`{k}` {w:.2f}" for k, w in
                                       ru["importance"] if w > 0.01),
        "", "```", ru["text"].rstrip(), "```", "",
        "One-at-a-time tipping points (others at default):", ""]
  L += [f"- `{k}`: {', '.join(v)}" for k, v in R["tipping"].items() if v]
  L += [f"- no flip inside declared range: "
        f"{', '.join(k for k, v in R['tipping'].items() if not v)}", "",
        "## 4. Business scenarios (same mechanism, different world)", "",
        "| scenario | story | default | C/R/n under +-15% | gap |",
        "|---|---|---|---|---|"]
  for k, s in R["scenarios"].items():
    v, g = s["at_default"]
    L.append(f"| {k} | {s['story']} | {v} ({g:+.0f}) | {_t(s)} | "
             f"{_g(s['gap'])} |")
  L += ["", "## 5. Mechanism variants (same world, different structure;"
        " arms compared *within* each structure)", "",
        "| variant | story | default | local C/R/n | prior C/R/n |",
        "|---|---|---|---|---|"]
  for k, s in R["variants"].items():
    v, g = s["at_default"]
    L.append(f"| {k} | {s['story']} | {v} ({g:+.0f}) | {_t(s['local'])}"
             f" | {_t(s['prior'])} |")
  if R.get("evidence"):
    L += ["", "## 6. Will it work *here*? (real-project placement)", ""]
    for e in R["evidence"]:
      L += [f"### {e['project']}", "", f"Population: {e['population']}",
            "", "Measured: " + "; ".join(e["measured"]), "",
            f"**P(claim holds | evidence)** = {_t(e['place'])}, "
            f"gap {_g(e['place']['gap'])}", "",
            "What to measure next (verdict-entropy reduction, "
            "P(CONFIRM) by quartile):", ""]
      L += [f"- `{d['factor']}` gain {d['gain']:.3f} "
            f"{d['p_by_quartile']}" for d in e["voi"]["ranked"][:5]]
      L += ["", "Caveats (the long chain from data to parameter):", ""]
      L += [f"- {n}" for n in e["notes"]] + [""]
  return "\n".join(L) + "\n"
