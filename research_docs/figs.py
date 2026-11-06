"""figs.py: every chart in the docs, drawn from the committed outputs
(outputs/laws/*.json, outputs/evidence/*, sensitivity.md) or by re-running
the original Brooks simulators. Nothing is typed in by hand."""

import csv, json, re, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
LAWS, EV = ROOT / "outputs/laws", ROOT / "outputs/evidence"

C, R, N = "#2a78d6", "#eb6834", "#c9c8c2"      # CONFIRM, REFUTE, neutral
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
SEQ = ["#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]

plt.rcParams.update({
  "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
  "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
  "ytick.color": INK2, "text.color": INK, "axes.grid": True,
  "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
  "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
  "axes.spines.top": False, "axes.spines.right": False,
  "legend.frameon": False})

def card(law): return json.loads((LAWS / f"{law}.json").read_text())

def stacked(ax, labels, rows, title=None):
  "rows: list of (confirm%, refute%, neutral%). Horizontal 100% bars."
  y = np.arange(len(labels))[::-1]
  left = np.zeros(len(rows))
  for k, (col, lab) in enumerate(((C, "CONFIRM"), (R, "REFUTE"),
                                   (N, "neutral"))):
    v = np.array([r[k] for r in rows])
    ax.barh(y, v, left=left, color=col, height=0.62, label=lab,
            edgecolor=SURF, linewidth=2)
    for yi, l, w in zip(y, left, v):
      if w >= 9:
        ax.text(l + w / 2, yi, f"{w:.0f}%", ha="center", va="center",
                fontsize=8.5, color="white" if k < 2 else INK)
    left += v
  ax.set_yticks(y, labels); ax.set_xlim(0, 100)
  ax.set_xlabel("% of sampled worlds"); ax.grid(axis="y", visible=False)
  if title: ax.set_title(title, loc="left")

def save(fig, name, out):
  fig.tight_layout(); fig.savefig(out / name, dpi=130); plt.close(fig)

def t3(d): return d["CONFIRM"], d["REFUTE"], d["neutral"]

# --- results charts ------------------------------------------------------

def robustness(out):
  laws = ["brooks", "aiwork", "archpat", "archpat_cost"]
  fig, axs = plt.subplots(len(laws), 1, figsize=(8, 6.8), sharex=True)
  for ax, law in zip(axs, laws):
    r = card(law)["robustness"]
    stacked(ax, ["±15% (old MC)", "prior over ranges", "uniform"],
            [t3(r[k]) for k in ("local", "prior", "uniform")], law)
    if ax is not axs[-1]: ax.set_xlabel("")
  axs[0].legend(ncol=3, loc="lower left", bbox_to_anchor=(0, 1.18))
  save(fig, "robustness.png", out)

def variants(out):
  for law in ("brooks", "aiwork", "archpat"):
    v = card(law)["variants"]
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(v) + 1.3))
    stacked(ax, list(v), [t3(x["prior"]) for x in v.values()],
            f"{law}: verdicts under prior sampling, per mechanism variant")
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, -0.28))
    save(fig, f"variants_{law}.png", out)

def importance(out):
  laws = ["brooks", "aiwork", "archpat", "archpat_cost"]
  fig, axs = plt.subplots(1, len(laws), figsize=(12, 3.4))
  for ax, law in zip(axs, laws):
    imp = [(k, w) for k, w in card(law)["rules"]["importance"] if w > 0.01]
    ks, ws = zip(*imp[::-1])
    ax.barh(ks, ws, color=C, height=0.6)
    ax.set_xlim(0, 1); ax.set_title(law, loc="left")
    ax.set_xlabel("tree importance"); ax.grid(axis="y", visible=False)
  save(fig, "importance.png", out)

def placements(out):
  rows, labs = [], []
  for law in ("brooks", "aiwork", "archpat_cost"):
    for e in card(law)["evidence"]:
      labs.append(f"{law} @ {e['project']}"); rows.append(t3(e["place"]))
  fig, ax = plt.subplots(figsize=(8, 3))
  stacked(ax, labs, rows, "Real-project placement: P(claim holds | evidence)")
  ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, -0.3))
  save(fig, "placements.png", out)

def sens_tables():
  "Parse outputs/laws/sensitivity.md into {section: [(label, C, R)]}."
  secs, cur = {}, None
  for line in (LAWS / "sensitivity.md").read_text(encoding="utf-8").split("\n"):
    if line.startswith("## "): cur = line[3:]; secs[cur] = []
    m = re.match(r"\| (.+?) \| (\d+)% \| (\d+)% \|", line)
    if m and cur: secs[cur].append((m[1], int(m[2]), int(m[3])))
  return secs

def sensitivity(out):
  s = sens_tables()
  for key, name, title in (
      ("archpat", "sens_archpat.png",
       "archpat @ Helix: free vs priced migration"),
      ("brooks", "sens_brooks.png",
       "brooks @ Helix: doubling teams of different sizes"),
      ("aiwork", "sens_aiwork.png",
       "aiwork @ Aider: measured churn + borrowed factors")):
    sec = next(v for k, v in s.items() if k.startswith(key))
    rows = [(c, r, 100 - c - r) for _, c, r in sec]
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(rows) + 1.3))
    stacked(ax, [l for l, _, _ in sec], rows, title)
    ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, -0.3))
    save(fig, name, out)

def breakeven(out):
  txt = (LAWS / "archpat_breakeven.txt").read_text()
  fig, ax = plt.subplots(figsize=(7, 3.4))
  for line, col, lab in zip([l for l in txt.split("\n")
                             if l.startswith("mig_bugs")], (C, R),
                            ("0 debt injected per module",
                             "0.25 debt injected per module")):
    pts = re.findall(r"mig_cost=([\d.]+): C(\d+)/R(\d+)", line)
    x = [float(a) for a, _, _ in pts]; y = [int(b) for _, b, _ in pts]
    ax.plot(x, y, color=col, lw=2, marker="o", ms=8, mec=SURF, mew=2,
            label=lab)
  ax.axhline(50, color=INK2, lw=1, ls="--")
  ax.set_xlabel("mig_cost: feature-items of effort per module migrated")
  ax.set_ylabel("P(CONFIRM) %"); ax.set_ylim(0, 100); ax.set_xlim(-0.05, 2.1)
  ax.text(2.05, 52, "50%: break-even", ha="right", fontsize=8.5, color=INK2)
  ax.set_title("archpat @ Helix: break-even migration price", loc="left")
  ax.legend(loc="upper right")
  save(fig, "breakeven.png", out)

# --- evidence charts -----------------------------------------------------

def ci(xs):
  s = sorted(xs); return s[len(s) // 20], s[len(s) // 2], s[-len(s) // 20 - 1]

def g3(x): return f"{x:.3g}" if abs(x) >= 1e-4 else "0"

def dotci(ax, labels, vals, ref=None, log=False):
  y = np.arange(len(labels))[::-1]
  for yi, v in zip(y, vals):
    lo, md, hi = ci(v)
    ax.plot([lo, hi], [yi, yi], color=C, lw=2)
    ax.plot(md, yi, "o", color=C, ms=8, mec=SURF, mew=2)
    ax.annotate(f"{g3(md)} [{g3(lo)}, {g3(hi)}]", (md, yi), xytext=(0, 9),
                textcoords="offset points", ha="center", fontsize=8.5,
                color=INK2)
  if ref:
    for yi, r in zip(y, ref):
      if r is not None:
        ax.plot(r, yi, "D", color=R, ms=7, mec=SURF, mew=1.5)
  ax.set_yticks(y, labels); ax.grid(axis="y", visible=False)
  ax.set_ylim(-0.6, len(labels) - 0.2)
  if log: ax.set_xscale("log")

def brooks_params(out):
  d = json.loads((EV / "brooks_helix.json").read_text())["measured"]
  fig, axs = plt.subplots(1, 2, figsize=(10, 2.4))
  for ax, k, ref, lim in ((axs[0], "comm_coef", 0.005, (0, 0.075)),
                          (axs[1], "train_coef", 0.2, (0, 0.25))):
    dotci(ax, [k], [d[k]], [ref]); ax.set_xlim(*lim)
    ax.set_title(f"Helix {k}", loc="left", fontsize=10)
  fig.suptitle("estimate, 90% CI (blue) vs model default (orange)",
               x=0.01, ha="left", fontsize=9.5, color=INK2)
  save(fig, "brooks_params.png", out)

def churn(out):
  fig, axs = plt.subplots(1, 2, figsize=(11, 3.2),
                          gridspec_kw={"width_ratios": [1.3, 1]})
  ax = axs[0]
  labs, vals = [], []
  for proj, era in (("aider", "2024-25 (Claude/GPT-4o era)"),
                    ("aider2023", "2023-24 (GPT-4 era)")):
    rows = list(csv.DictReader(open(EV / f"aiwork_{proj}_pairs.csv")))
    for lo, hi, s in ((3, 20, "3-20 lines"), (21, 80, "21-80 lines")):
      for ai in ("True", "False"):
        sub = [r for r in rows if r["ai"] == ai and
               lo <= int(r["added"]) <= hi]
        if len(sub) < 15: continue
        a = sum(int(r["added"]) for r in sub)
        k = sum(int(r["kept"]) for r in sub)
        labs.append((era, s, ai == "True", len(sub))); vals.append(1 - k / a)
  y = np.arange(len(vals))[::-1]
  ax.barh(y, [100 * v for v in vals], height=0.62,
          color=[C if l[2] else N for l in labs], edgecolor=SURF, lw=2)
  for yi, v in zip(y, vals):
    ax.text(100 * v + 1, yi, f"{100*v:.0f}%", va="center", fontsize=8.5,
            color=INK2)
  ax.set_yticks(y, [f"{e[:7]} · {s} · {'AI' if a else 'human'} (n={n})"
                    for e, s, a, n in labs], fontsize=8.5)
  ax.set_xlabel("lines gone within 14 days (%)"); ax.set_xlim(0, 80)
  ax.set_title("Aider, same author: 14-day churn", loc="left")
  ax.grid(axis="y", visible=False)
  ax.legend(handles=[Patch(color=C, label="AI-tagged commit"),
                     Patch(color=N, label="human commit")], loc="lower right")
  ms = [json.loads((EV / f"aiwork_{p}.json").read_text())["measured"]
        ["churn_mult"] for p in ("aider", "aider2023")]
  dotci(axs[1], ["2024-25", "2023-24"], ms, [2.0, 2.0])
  axs[1].set_xlim(-0.1, 2.6)
  axs[1].set_ylim(-0.6, 1.6)
  axs[1].set_title("churn_mult: measured (blue)\nvs sd.aiwork default "
                   "2.0 (orange)", loc="left", fontsize=9.5)
  save(fig, "churn.png", out)

def archpat_ratios(out):
  m = json.loads((EV / "archpat_cost_helix.json").read_text())
  b = json.loads((EV / "archpat_cost_helix.json").read_text())
  fig, ax = plt.subplots(figsize=(9, 2.6))
  labs = ["bug ratio (fix commits)", "productivity ratio (non-fix commits)"]
  dotci(ax, labs, [m["measured"]["born_pat"][2], m["measured"]["gen_pat"][2]],
        [0.25, 2.5], log=True)
  ax.set_xlim(0.15, 6); ax.axvline(1, color=INK2, lw=1, ls="--")
  ax.set_xticks([0.25, 0.5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"])
  ax.set_title("Helix, patterned ÷ other files: measured 90% CI (blue)\n"
               "vs sd.archpat assumption (orange); dashed = no difference",
               loc="left", fontsize=9.5)
  save(fig, "archpat_ratios.png", out)

# --- review-of-Brooks charts (re-run the original simulators) --------------

def confound(out):
  from brooks_modifications import MODIFIED_MODELS, simulate_modified_vectorized
  sim = lambda k, h: simulate_modified_vectorized(k, 1, boost_hires=h,
                                                  ticks=20)["final_scores"][0]
  flat0 = sim("standard_brooks", 0)
  ks = list(MODIFIED_MODELS)
  rep = [sim(k, 10) - flat0 for k in ks]
  own = [sim(k, 10) - sim(k, 0) for k in ks]
  y = np.arange(len(ks))[::-1]
  fig, ax = plt.subplots(figsize=(8.5, 3.8))
  ax.barh(y + 0.18, rep, 0.34, color=N, label="as reported: vs FLAT team, 0 hires")
  ax.barh(y - 0.18, own, 0.34, color=C, label="fair: vs SAME architecture, 0 hires")
  for yi, a, b in zip(y, rep, own):
    for dy, v in ((0.18, a), (-0.18, b)):
      ax.text(v + (12 if v >= 0 else -12), yi + dy, f"{v:+.0f}", va="center",
              ha="left" if v >= 0 else "right", fontsize=8, color=INK2)
  ax.axvline(0, color=INK, lw=1)
  ax.set_yticks(y, [MODIFIED_MODELS[k]["name"].split(" (")[0] for k in ks])
  ax.set_xlim(-900, 750); ax.grid(axis="y", visible=False)
  ax.set_xlabel("effect of 10 hires on final score at t=20 (positive = hiring helps)")
  ax.set_title("Same simulator, two baselines", loc="left")
  ax.legend(loc="upper left", bbox_to_anchor=(0, -0.2), ncol=1)
  save(fig, "confound.png", out)

def saturation(out):
  from forrester_brooks import simulate_stepwise
  fig, ax = plt.subplots(figsize=(8, 3.4))
  for col, s in zip(SEQ, (0, 1, 2, 5, 10, 50)):
    h = simulate_stepwise(boost_hires=s)
    ax.plot([x["t"] for x in h[:-1]], [x["prod"] for x in h[:-1]],
            color=col, lw=2, label=f"{s} hires")
  ax.axvline(10, color=INK2, lw=1, ls="--")
  ax.text(10.2, 2, "hire at t=10", color=INK2, fontsize=8.5)
  ax.set_xlabel("tick"); ax.set_ylabel("production / tick")
  ax.set_title("Original model: 5, 10 or 50 hires all freeze output at 0",
               loc="left")
  ax.legend(ncol=6, loc="upper left", bbox_to_anchor=(0, -0.22),
            fontsize=8.5)
  save(fig, "saturation.png", out)

def team_optimum(out):
  "History (Part B review, issue 8): the original model's comm wall."
  V = np.linspace(1, 30, 300)
  fig, ax = plt.subplots(figsize=(8, 3.2))
  for c, col, lab in ((0.005, C, "c = 0.005 (sd.brooks default)"),
                      (0.023, R, "c = 0.023 (earlier Helix estimate)")):
    out_ = np.maximum(0, V * (1 - c * V * (V - 1) / 2))
    ax.plot(V, out_, color=col, lw=2, label=lab)
    vs = (2 + np.sqrt(4 + 24 / c)) / 6
    ax.plot(vs, vs * (1 - c * vs * (vs - 1) / 2), "o", color=col, ms=8,
            mec=SURF, mew=2)
    ax.annotate(f"V* ≈ {vs:.1f}", (vs, vs * (1 - c * vs * (vs - 1) / 2)),
                xytext=(6, 6), textcoords="offset points", fontsize=8.5,
                color=INK2)
  ax.set_xlabel("veterans V"); ax.set_ylabel("team output  V·(1 − c·V(V−1)/2)")
  ax.set_title("Original model: output peaks at V*, hits 0 near 2V*",
               loc="left")
  ax.legend(loc="upper right")
  save(fig, "team_optimum.png", out)

def team_optimum_std(out):
  "The standard model (bounded overload): output peaks at V*, then decays."
  V = np.linspace(1, 30, 300)
  hx = json.loads((EV / "brooks_helix.json").read_text())["measured"]
  ch = sorted(hx["comm_coef"])[len(hx["comm_coef"]) // 2]
  f = lambda v, c: v * np.exp(-c * v * (v - 1) / 2)
  fig, ax = plt.subplots(figsize=(8, 3.2))
  for c, col, lab in ((0.005, C, "c = 0.005 (model default)"),
                      (ch, R, f"c = {ch:.3f} (Helix estimate)")):
    ax.plot(V, f(V, c), color=col, lw=2, label=lab)
    vs = (1 + np.sqrt(1 + 16 / c)) / 4              # V(2V - 1) = 2/c
    ax.plot(vs, f(vs, c), "o", color=col, ms=8, mec=SURF, mew=2)
    ax.annotate(f"V* ≈ {vs:.1f}", (vs, f(vs, c)), xytext=(6, 6),
                textcoords="offset points", fontsize=8.5, color=INK2)
  ax.set_xlabel("veterans V")
  ax.set_ylabel("team output  V·exp(−c·V(V−1)/2)")
  ax.set_title("Standard model: output peaks at V*, then decays (never 0)",
               loc="left")
  ax.legend(loc="upper right")
  save(fig, "team_optimum_std.png", out)

ALL = [robustness, variants, importance, placements, sensitivity, breakeven,
       brooks_params, churn, archpat_ratios, confound, saturation,
       team_optimum, team_optimum_std]

def build(out):
  out.mkdir(parents=True, exist_ok=True)
  for f in ALL: f(out)
