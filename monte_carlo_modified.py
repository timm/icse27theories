#!/usr/bin/env python3 -B
"""monte_carlo_modified.py: 100,000-run Monte Carlo evaluation and statistical
comparison of architectural modifications to Brooks' Law.

Compares:
- Baseline Control (0 hires)
- Standard Brooks (Unmodified 10 hires @ t=10)
- Mod 1: Ambassador Team Partitioning (Conway's Law / Surgical Teams)
- Mod 2: Dedicated Mentor Pod (Shielded Core Developers)
- Mod 3: Async Documentation & Automated CI/CD (Logarithmic Coordination)
- Mod 4: Staged Wave Influx (Graduated Onboarding Pipeline)
- Mod 5: Synergistic Modern Engineering Org (Combined Stack)
- Stress: Massive Surge (50 hires) under Standard vs. Ambassador vs. Synergistic

Uses:
- stats.py (timm/ezr): Cliff's Delta, KS test, Scott-Knott cluster ranking
"""

import sys, os, time, json, argparse
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "paper"))
import stats

from brooks_modifications import MODIFIED_MODELS, simulate_modified_vectorized

TEST_CONFIGS = [
    {"id": "baseline", "model": "standard_brooks", "hires": 0, "label": "Baseline Control (0 Hires)"},
    {"id": "standard_brooks", "model": "standard_brooks", "hires": 10, "label": "Standard Brooks (10 Hires, Flat)"},
    {"id": "ambassador_10", "model": "ambassador_partitioning", "hires": 10, "label": "Ambassador Partitioning (10 Hires)"},
    {"id": "dedicated_mentor_10", "model": "dedicated_mentor_pod", "hires": 10, "label": "Dedicated Mentors (10 Hires)"},
    {"id": "async_ci_10", "model": "async_documentation_ci", "hires": 10, "label": "Async Documentation & CI (10 Hires)"},
    {"id": "staged_wave_10", "model": "staged_wave_hiring", "hires": 10, "label": "Staged Wave Influx (10 Hires)"},
    {"id": "synergistic_10", "model": "synergistic_modern_org", "hires": 10, "label": "Synergistic Modern Org (10 Hires)"},
    # Stress comparisons with 50 hires
    {"id": "standard_surge_50", "model": "standard_brooks", "hires": 50, "label": "Standard Surge (50 Hires, Flat)"},
    {"id": "ambassador_surge_50", "model": "ambassador_partitioning", "hires": 50, "label": "Ambassador Surge (50 Hires)"},
    {"id": "synergistic_surge_50", "model": "synergistic_modern_org", "hires": 50, "label": "Synergistic Surge (50 Hires)"},
]

def compute_cliffs_delta(xs, ys, sample_size=2000):
    sub_x = np.random.choice(xs, min(sample_size, len(xs)), replace=False)
    sub_y = np.random.choice(ys, min(sample_size, len(ys)), replace=False)
    gt = np.sum(sub_x[:, None] > sub_y[None, :])
    lt = np.sum(sub_x[:, None] < sub_y[None, :])
    return float((gt - lt) / (len(sub_x) * len(sub_y)))

def scott_knott_ranking(score_dict, sample_size=1000):
    inverted = {
        k: [-v for v in np.random.choice(vals, min(sample_size, len(vals)), replace=False)]
        for k, vals in score_dict.items()
    }
    ranks = {}
    current_rank = 1
    remaining = dict(inverted)
    while remaining:
        best_cluster = stats.bestRanks(remaining)
        for k in best_cluster:
            ranks[k] = current_rank
            del remaining[k]
        current_rank += 1
    return ranks

def run_modified_monte_carlo(n_runs=100000, out_dir="outputs", seed=42):
    np.random.seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*95}")
    print(f" BROOKS' LAW ARCHITECTURAL MODIFICATIONS: {n_runs:,} MONTE CARLO RUNS PER ARCHITECTURE")
    print(f"{'='*95}")

    noise_factors = {
        "comm": np.random.uniform(0.85, 1.15, n_runs),
        "train": np.random.uniform(0.85, 1.15, n_runs),
        "prod": np.random.uniform(0.85, 1.15, n_runs),
        "mature": np.random.uniform(0.85, 1.15, n_runs),
        "todo": np.random.uniform(0.90, 1.10, n_runs),
    }

    results = {}
    for cfg in TEST_CONFIGS:
        cid = cfg["id"]
        print(f"[*] Simulating '{cfg['label']}' ({n_runs:,} runs)...", end=" ", flush=True)
        t0 = time.time()
        res = simulate_modified_vectorized(
            model_key=cfg["model"],
            n_runs=n_runs,
            boost_hires=cfg["hires"],
            boost_time=10,
            ticks=20,
            vet_start=10.0,
            noise_factors=noise_factors
        )
        print(f"done in {time.time()-t0:.2f}s")
        results[cid] = res

    # Statistical Evaluation
    print(f"\n[*] Evaluating non-parametric rankings and paired improvements...")
    summary_table = []
    comparison_table = []
    score_samples = {}

    base_scores = results["baseline"]["final_scores"]
    brooks_scores = results["standard_brooks"]["final_scores"]

    for cfg in TEST_CONFIGS:
        cid = cfg["id"]
        res = results[cid]
        scores = res["final_scores"]
        score_samples[cid] = scores

        med = float(np.median(scores))
        p05 = float(np.percentile(scores, 5))
        p95 = float(np.percentile(scores, 95))
        iqr = float(np.percentile(scores, 75) - np.percentile(scores, 25))
        comp_rate = float(np.mean(res["completed"]) * 100.0)

        # Paired comparison against Baseline Control
        paired_diff_base = scores - base_scores
        pct_beats_base = float(np.mean(paired_diff_base > 0) * 100.0)
        pct_worse_base = float(np.mean(paired_diff_base < 0) * 100.0)
        cd_vs_base = compute_cliffs_delta(scores, base_scores)

        # Paired comparison against Standard Brooks (How much does the modification help?)
        paired_diff_brooks = scores - brooks_scores
        pct_beats_brooks = float(np.mean(paired_diff_brooks > 0) * 100.0)
        median_advantage_over_brooks = float(np.median(paired_diff_brooks))
        cd_vs_brooks = compute_cliffs_delta(scores, brooks_scores)

        summary_table.append({
            "id": cid,
            "label": cfg["label"],
            "model": cfg["model"],
            "hires": cfg["hires"],
            "median": med,
            "mean": float(np.mean(scores)),
            "sd": float(np.std(scores)),
            "p05": p05,
            "p95": p95,
            "iqr": iqr,
            "completed_pct": comp_rate,
            "cliffs_delta_vs_base": cd_vs_base,
            "cliffs_delta_vs_brooks": cd_vs_brooks,
        })

        if cid not in ["baseline", "standard_brooks"]:
            comparison_table.append({
                "id": cid,
                "label": cfg["label"],
                "median_score": med,
                "pct_beats_baseline": pct_beats_base,
                "pct_beats_brooks": pct_beats_brooks,
                "advantage_over_brooks": median_advantage_over_brooks,
                "cliffs_delta_vs_brooks": cd_vs_brooks,
                "verdict": (
                    "SURPASSES BASELINE (Brooks Broken)" if pct_beats_base >= 50.0 else
                    "MITIGATES BROOKS (Significant Recovery)" if pct_beats_brooks >= 90.0 else
                    "MINIMAL MITIGATION"
                )
            })

    # Scott-Knott Clustering
    ranks = scott_knott_ranking(score_samples)
    for row in summary_table:
        row["rank"] = ranks[row["id"]]

    summary_table.sort(key=lambda r: (r["rank"], -r["median"]))

    # Save to outputs
    stats_csv = os.path.join(out_dir, "modified_100k_stats.csv")
    with open(stats_csv, "w", encoding="utf-8") as f:
        f.write("rank,id,label,median,mean,sd,p05,p95,iqr,completed_pct,cliffs_delta_vs_base,cliffs_delta_vs_brooks\n")
        for r in summary_table:
            f.write(f"{r['rank']},{r['id']},\"{r['label']}\",{r['median']:.1f},{r['mean']:.1f},{r['sd']:.1f},"
                    f"{r['p05']:.1f},{r['p95']:.1f},{r['iqr']:.1f},{r['completed_pct']:.1f}%,"
                    f"{r['cliffs_delta_vs_base']:.3f},{r['cliffs_delta_vs_brooks']:.3f}\n")

    comp_csv = os.path.join(out_dir, "modified_100k_comparison.csv")
    with open(comp_csv, "w", encoding="utf-8") as f:
        f.write("id,label,median_score,pct_beats_baseline,pct_beats_brooks,advantage_over_brooks,cliffs_delta_vs_brooks,verdict\n")
        for c in comparison_table:
            f.write(f"{c['id']},\"{c['label']}\",{c['median_score']:.1f},{c['pct_beats_baseline']:.1f}%,"
                    f"{c['pct_beats_brooks']:.1f}%,{c['advantage_over_brooks']:.1f},{c['cliffs_delta_vs_brooks']:.3f},\"{c['verdict']}\"\n")

    json_path = os.path.join(out_dir, "modified_100k_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary_table, "comparisons": comparison_table, "runs": n_runs}, f, indent=2)

    # Console display
    print_console_tables(summary_table, comparison_table, n_runs)
    return summary_table, comparison_table

def print_console_tables(summary, comparisons, n_runs):
    print(f"\n{'='*110}")
    print(f" ARCHITECTURAL RANKING & PERFORMANCE ({n_runs:,} RUNS PER ARCHITECTURE)")
    print(f"{'='*110}")
    print(f"{'Rank':<6}{'Architecture / Configuration':<38}{'Median':<10}{'Mean +/- SD':<18}{'90% Interval':<24}{'Done%':<8}{'Cliff d vs Base':<10}")
    print(f"{'-'*110}")
    for r in summary:
        interval = f"[{r['p05']:.1f}, {r['p95']:.1f}]"
        mean_sd = f"{r['mean']:.1f} +/- {r['sd']:.1f}"
        cd_str = f"{r['cliffs_delta_vs_base']:+.3f}" if r["id"] != "baseline" else "-"
        comp_str = f"{r['completed_pct']:.1f}%"
        print(f"#{r['rank']:<5}{r['label']:<38}{r['median']:<10.1f}{mean_sd:<18}{interval:<24}{comp_str:<8}{cd_str:<10}")

    print(f"\n{'='*115}")
    print(f" CROSS-COMPARISON: HOW MUCH DOES EACH MODIFICATION MITIGATE BROOKS' LAW?")
    print(f"{'='*115}")
    print(f"{'Modification':<36}{'Median':<9}{'Beats Base%':<14}{'Beats Brooks%':<15}{'Delta vs Brooks':<18}{'Verdict':<25}")
    print(f"{'-'*115}")
    for c in comparisons:
        base_str = f"{c['pct_beats_baseline']:.1f}%"
        brooks_str = f"{c['pct_beats_brooks']:.1f}%"
        delta_str = f"{c['advantage_over_brooks']:+.1f} pts"
        print(f"{c['label']:<36}{c['median_score']:<9.1f}{base_str:<14}{brooks_str:<15}{delta_str:<18}{c['verdict']:<25}")
    print(f"{'='*115}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monte Carlo analysis for Brooks modifications")
    parser.add_argument("--runs", type=int, default=100000, help="Number of runs (default: 100,000)")
    parser.add_argument("--out-dir", default="outputs", help="Output directory")
    args = parser.parse_args()

    run_modified_monte_carlo(n_runs=args.runs, out_dir=args.out_dir)
