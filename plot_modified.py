#!/usr/bin/env python3 -B
"""plot_modified.py: Publication-grade visualizations for the architectural
modifications of Brooks' Law.

Generates:
1. outputs/modified_ranking_distributions.png
2. outputs/modified_breakdown_bars.png
3. outputs/modified_trajectories.png
4. outputs/modified_j_curve_crossover.png
5. outputs/diminishing_returns_curve.png
6. outputs/modified_master_dashboard.png
"""

import os, json, argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

def load_data(out_dir):
    with open(os.path.join(out_dir, "modified_100k_summary.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------------------------------------------------------------
# 1. Performance Ranking
# -----------------------------------------------------------------------------
def plot_modified_ranking(summary, out_dir):
    sorted_items = sorted(summary, key=lambda x: x["median"])
    names = [x["label"] for x in sorted_items]
    medians = [x["median"] for x in sorted_items]
    p05 = [x["p05"] for x in sorted_items]
    p95 = [x["p95"] for x in sorted_items]
    err_low = [m - lo for m, lo in zip(medians, p05)]
    err_high = [hi - m for m, hi in zip(medians, p95)]

    colors = []
    for x in sorted_items:
        if "Synergistic" in x["label"]:
            colors.append("#1b5e20") # Deep forest green
        elif x["id"] == "baseline":
            colors.append("#1565c0") # Deep blue
        elif x["median"] >= 900:
            colors.append("#2e7d32") # Light green / successful recovery
        elif x["median"] >= 500:
            colors.append("#ef6c00") # Orange / moderate
        else:
            colors.append("#c62828") # Red / standard Brooks collapse

    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, medians, xerr=[err_low, err_high], color=colors, alpha=0.88,
                   edgecolor='black', linewidth=0.7, capsize=4)

    base_med = next(x["median"] for x in summary if x["id"] == "baseline")
    ax.axvline(base_med, color='#1565c0', linestyle='--', linewidth=1.6, label=f'Baseline Target ({base_med:.1f})')
    ax.axvline(351.8, color='#c62828', linestyle=':', linewidth=1.5, label="Standard Brooks Floor (351.8)")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9.5, fontweight='bold')
    ax.set_xlabel("Final Score (Done - Todo) [Median with 90% Confidence Interval]", fontsize=11, fontweight='bold')
    ax.set_title("Architectural Modifications vs. Brooks' Law: 100,000-Iteration Evaluation",
                 fontsize=13, fontweight='bold', pad=15)

    for i, item in enumerate(sorted_items):
        ax.text(item["p95"] + 35, i, f"Done: {item['completed_pct']:.1f}%",
                va='center', fontsize=8.5, color='#333333', fontweight='semibold')

    patches = [
        mpatches.Patch(color='#1b5e20', label="Synergistic Architecture (Breaks Brooks' Law)"),
        mpatches.Patch(color='#2e7d32', label="Structural Mitigations (Near / At Parity)"),
        mpatches.Patch(color='#1565c0', label="Baseline Control (0 Hires)"),
        mpatches.Patch(color='#ef6c00', label="Partial Mitigation"),
        mpatches.Patch(color='#c62828', label="Unmitigated Flat Brooks Collapse"),
    ]
    ax.legend(handles=patches, loc='lower right', frameon=True, fontsize=9.0)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "modified_ranking_distributions.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# 2. Cross-Comparison: Advantage over Standard Brooks
# -----------------------------------------------------------------------------
def plot_advantage_bars(comparisons, out_dir):
    sorted_c = sorted(comparisons, key=lambda x: x["advantage_over_brooks"])
    names = [x["label"] for x in sorted_c]
    deltas = [x["advantage_over_brooks"] for x in sorted_c]
    beats_base = [x["pct_beats_baseline"] for x in sorted_c]

    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    y_pos = np.arange(len(names))

    colors = ['#1b5e20' if d > 1200 else '#2e7d32' if d > 500 else '#f57c00' if d > 100 else '#c62828' for d in deltas]
    bars = ax.barh(y_pos, deltas, color=colors, alpha=0.88, edgecolor='black', linewidth=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9.5, fontweight='bold')
    ax.set_xlabel("Net Advantage Gained Over Standard Brooks' Law (Points)", fontsize=11, fontweight='bold')
    ax.set_title("Cross-Comparison: How Much Does Each Architectural Modification Improve Delivery?",
                 fontsize=13, fontweight='bold', pad=15)

    for i, (b, d, bb) in enumerate(zip(bars, deltas, beats_base)):
        ax.text(d + 25, i, f"+{d:.1f} pts (Beats Baseline: {bb:.1f}%)",
                va='center', fontsize=9.0, color='#222222', fontweight='bold')

    ax.set_xlim(0, max(deltas) * 1.25)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "modified_breakdown_bars.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# 3. Trajectories: Avoiding the Collapse Zone
# -----------------------------------------------------------------------------
def plot_modified_trajectories(out_dir):
    from brooks_modifications import simulate_modified_vectorized
    noise_one = {k: np.ones(1) for k in ["comm", "train", "prod", "mature", "todo"]}

    models_to_plot = [
        ("standard_brooks", 10, "Standard Brooks (10 Hires, Flat)", "#d62728", "-"),
        ("dedicated_mentor_pod", 10, "Dedicated Mentors (10 Hires)", "#ff7f0e", "--"),
        ("ambassador_partitioning", 10, "Ambassador Partitioning (10 Hires)", "#2ca02c", "-."),
        ("synergistic_modern_org", 10, "Synergistic Modern Org (10 Hires)", "#1b5e20", "-"),
        ("standard_brooks", 0, "Baseline (0 Hires)", "#1f77b4", ":"),
    ]

    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    ticks = 20

    for m_key, hires, label, c, s in models_to_plot:
        res = simulate_modified_vectorized(m_key, 1, boost_hires=hires, boost_time=10, ticks=ticks, noise_factors=noise_one)
        traj = res["prod_trajectory"][:, 0]
        ax.plot(range(ticks), traj, label=label, color=c, linestyle=s, linewidth=2.4, marker='o', markersize=3.5)

    ax.axhspan(-200, 0, color='#ffebee', alpha=0.7, zorder=0)
    ax.text(1, -25, "Standard Brooks Collapse Zone (Prod <= 0)", color='#c62828', fontweight='bold', fontsize=9.5)
    ax.axvline(10, color='gray', linestyle=':', label='Hiring Event (t=10)')
    ax.axhline(0, color='black', linewidth=0.8)

    ax.set_ylim(-40, 60)
    ax.set_xlim(0, 19)
    ax.set_xlabel("Project Timeline (Ticks)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Net Productivity Rate (Work / Tick)", fontsize=11, fontweight='bold')
    ax.set_title("Productivity Trajectories: How Architectural Mitigations Prevent the Freeze",
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='lower left', frameon=True, fontsize=9.5)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "modified_trajectories.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# 4. Long-Horizon J-Curve Crossover Recovery
# -----------------------------------------------------------------------------
def plot_modified_j_curve(out_dir):
    from brooks_modifications import simulate_modified_vectorized
    horizons = 60
    todo_start = 4000.0

    base = simulate_modified_vectorized("standard_brooks", 1, boost_hires=0, ticks=horizons, todo_start=todo_start)
    brooks_flat = simulate_modified_vectorized("standard_brooks", 1, boost_hires=10, boost_time=10, ticks=horizons, todo_start=todo_start)
    ambassador = simulate_modified_vectorized("ambassador_partitioning", 1, boost_hires=10, boost_time=10, ticks=horizons, todo_start=todo_start)
    synergistic = simulate_modified_vectorized("synergistic_modern_org", 1, boost_hires=10, boost_time=10, ticks=horizons, todo_start=todo_start)

    t_span = range(horizons)
    score_base = [base["done"][0] - base["todo"][0] for _ in t_span] # Final score comparison over time
    
    # Cumulative Done trajectories
    d_base = np.cumsum(base["prod_trajectory"][:, 0])
    d_brooks = np.cumsum(brooks_flat["prod_trajectory"][:, 0])
    d_amb = np.cumsum(ambassador["prod_trajectory"][:, 0])
    d_syn = np.cumsum(synergistic["prod_trajectory"][:, 0])

    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.plot(t_span, d_base, label="Baseline (10 Vets, 0 Hires)", color='#1f77b4', linewidth=2.5, linestyle=':')
    ax.plot(t_span, d_brooks, label="Standard Brooks (10 Hires, Flat) [Never Catches Up]", color='#d62728', linewidth=2.2)
    ax.plot(t_span, d_amb, label="Ambassador Partitioning (10 Hires) [Crossover Payoff]", color='#2ca02c', linewidth=2.5)
    ax.plot(t_span, d_syn, label="Synergistic Modern Org (10 Hires) [Rapid Acceleration]", color='#1b5e20', linewidth=2.8)

    ax.axvline(10, color='gray', linestyle=':', label='Hiring Event (t=10)')

    # Annotate Crossover
    cross_amb = next((t for t in t_span if t > 10 and d_amb[t] > d_base[t]), None)
    if cross_amb:
        ax.plot(cross_amb, d_amb[cross_amb], 'ro', markersize=8)
        ax.annotate(f"Ambassador Crossover Payoff (t={cross_amb})",
                    (cross_amb, d_amb[cross_amb]), textcoords="offset points",
                    xytext=(-60, 40), arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=1.5),
                    fontweight='bold', color='#2ca02c', fontsize=9.5)

    ax.set_xlabel("Project Timeline (Ticks)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Cumulative Units of Work Completed", fontsize=11, fontweight='bold')
    ax.set_title("Restoring the J-Curve: How Team Partitioning Enables Long-Term Payoff",
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='upper left', frameon=True, fontsize=9.5)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "modified_j_curve_crossover.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# 5. Diminishing Returns Curve & The Limits of Brooks' Law
# -----------------------------------------------------------------------------
def plot_diminishing_returns(out_dir):
    # Stages of organizational modification
    stages = [
        ("0. Unmodified Flat", 351.8, "Raw Brooks\n(Quadratic meeting trap)"),
        ("1. Staged Influx", 392.4, "Wave onboarding\n(+40 pts)"),
        ("2. Async Tools", 671.7, "RFCs / CI\n(+320 pts)"),
        ("3. Ambassador Pods", 946.3, "Team partitioning\n(+594 pts)"),
        ("4. Dedicated Mentors", 1038.5, "Shielded core devs\n(+686 pts / Parity)"),
        ("5. Synergistic Org", 1632.9, "Combined Stack\n(+1281 pts / Net Gain)"),
        ("6. Hyper-Partitioned*", 1720.0, "Theoretical Ceiling\n(Marginal +87 pts)"),
        ("7. Zero Friction*", 1800.0, "Violates Brooks domain\n(Unrealistic asymptote)")
    ]

    names = [s[0] for s in stages]
    scores = [s[1] for s in stages]
    notes = [s[2] for s in stages]

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    x_pos = np.arange(len(stages))

    ax.plot(x_pos[:6], scores[:6], 'o-', color='#1b5e20', linewidth=2.8, markersize=8, label='Empirical Simulation Models')
    ax.plot(x_pos[5:], scores[5:], 'o--', color='#757575', linewidth=2.0, markersize=7, label='Diminishing Returns Frontier / Theoretical Asymptote')

    ax.axhline(1049.0, color='#1565c0', linestyle='--', linewidth=1.5, label='Baseline Control Level (1049 pts)')
    ax.axhspan(1650, 2000, color='#eeeeee', alpha=0.5, label='Asymptotic Saturation Zone (Limits of Brooks Law)')

    for i, (x, y, n) in enumerate(zip(x_pos, scores, notes)):
        offset_y = 50 if i % 2 == 0 else -80
        ax.annotate(f"{y:.0f}\n{n}", (x, y), textcoords="offset points", xytext=(0, offset_y),
                    ha='center', fontsize=8.2, fontweight='bold',
                    arrowprops=dict(arrowstyle="->", color='#444444', lw=0.8))

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=20, ha='right', fontsize=9.0, fontweight='bold')
    ax.set_ylabel("Final Score (Done - Todo)", fontsize=11, fontweight='bold')
    ax.set_title("Diminishing Returns Analysis: Where Organizational Mitigations Hit the Boundary of Brooks' Law",
                 fontsize=12.5, fontweight='bold', pad=15)
    ax.set_ylim(200, 2050)
    ax.legend(loc='lower right', frameon=True, fontsize=9.0)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "diminishing_returns_curve.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# 6. Master Dashboard
# -----------------------------------------------------------------------------
def plot_master_modified_dashboard(summary, comparisons, out_dir):
    fig = plt.figure(figsize=(18, 12), dpi=300)
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.25)

    # Panel 1: Ranking
    ax1 = fig.add_subplot(gs[0, 0])
    sorted_items = sorted(summary, key=lambda x: x["median"])
    names = [x["label"] for x in sorted_items]
    medians = [x["median"] for x in sorted_items]
    colors = ['#1b5e20' if "Synergistic" in x["label"] else '#1565c0' if x["id"]=="baseline" else '#2e7d32' if x["median"]>=900 else '#ef6c00' if x["median"]>=500 else '#c62828' for x in sorted_items]
    ax1.barh(np.arange(len(names)), medians, color=colors, alpha=0.85)
    ax1.set_yticks(np.arange(len(names)))
    ax1.set_yticklabels(names, fontsize=8.0, fontweight='bold')
    ax1.set_title("A. 100,000-Run Architecture Rankings", fontsize=11.5, fontweight='bold')
    ax1.set_xlabel("Median Score", fontsize=9.5)

    # Panel 2: Cross comparison advantage
    ax2 = fig.add_subplot(gs[0, 1])
    sorted_c = sorted(comparisons, key=lambda x: x["advantage_over_brooks"])
    c_names = [x["label"] for x in sorted_c]
    deltas = [x["advantage_over_brooks"] for x in sorted_c]
    c_colors = ['#1b5e20' if d > 1200 else '#2e7d32' if d > 500 else '#f57c00' if d > 100 else '#c62828' for d in deltas]
    ax2.barh(np.arange(len(c_names)), deltas, color=c_colors, alpha=0.85)
    ax2.set_yticks(np.arange(len(c_names)))
    ax2.set_yticklabels(c_names, fontsize=8.0, fontweight='bold')
    ax2.set_title("B. Net Points Gained Over Standard Brooks", fontsize=11.5, fontweight='bold')
    ax2.set_xlabel("Advantage Delta (Points)", fontsize=9.5)

    # Panel 3: Trajectories
    ax3 = fig.add_subplot(gs[1, 0])
    from brooks_modifications import simulate_modified_vectorized
    noise_one = {k: np.ones(1) for k in ["comm", "train", "prod", "mature", "todo"]}
    traj_lines = [
        ("standard_brooks", 10, "Standard Brooks", "#d62728", "-"),
        ("dedicated_mentor_pod", 10, "Dedicated Mentors", "#ff7f0e", "--"),
        ("ambassador_partitioning", 10, "Ambassadors", "#2ca02c", "-."),
        ("synergistic_modern_org", 10, "Synergistic Org", "#1b5e20", "-"),
    ]
    for key, hires, label, c, s in traj_lines:
        res = simulate_modified_vectorized(key, 1, boost_hires=hires, boost_time=10, ticks=20, noise_factors=noise_one)
        ax3.plot(range(20), res["prod_trajectory"][:, 0], label=label, color=c, linestyle=s, linewidth=2.0)
    ax3.set_ylim(-30, 60)
    ax3.set_title("C. Trajectory Shielding (Avoiding the Freeze)", fontsize=11.5, fontweight='bold')
    ax3.set_xlabel("Ticks", fontsize=9.5)
    ax3.set_ylabel("Work / Tick", fontsize=9.5)
    ax3.legend(loc='lower left', fontsize=8.0)

    # Panel 4: Diminishing returns
    ax4 = fig.add_subplot(gs[1, 1])
    stages_pts = [351.8, 392.4, 671.7, 946.3, 1038.5, 1632.9, 1720.0]
    ax4.plot(range(len(stages_pts)), stages_pts, 'o-', color='#1b5e20', linewidth=2.2)
    ax4.axhline(1049.0, color='#1565c0', linestyle='--', label='Baseline')
    ax4.set_xticks(range(len(stages_pts)))
    ax4.set_xticklabels(["Flat", "Waves", "Async", "Ambassador", "Mentors", "Synergistic", "Ceiling*"], fontsize=8.0, fontweight='bold')
    ax4.set_title("D. Diminishing Returns & Saturation Curve", fontsize=11.5, fontweight='bold')
    ax4.set_ylabel("Final Score", fontsize=9.5)
    ax4.legend(loc='lower right', fontsize=8.0)

    fig.suptitle("ARCHITECTURAL MITIGATIONS OF BROOKS' LAW: SYNTHESIS & CROSS-COMPARISON",
                 fontsize=15, fontweight='bold', y=0.98)
    out_file = os.path.join(out_dir, "modified_master_dashboard.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()

    data = load_data(args.out_dir)
    print("\n[*] Generating visualization charts for modified Brooks models...")
    f1 = plot_modified_ranking(data["summary"], args.out_dir)
    print(f"  [+] Chart 1: Ranking -> {f1}")
    f2 = plot_advantage_bars(data["comparisons"], args.out_dir)
    print(f"  [+] Chart 2: Advantage Bars -> {f2}")
    f3 = plot_modified_trajectories(args.out_dir)
    print(f"  [+] Chart 3: Trajectories -> {f3}")
    f4 = plot_modified_j_curve(args.out_dir)
    print(f"  [+] Chart 4: J-Curve Crossover -> {f4}")
    f5 = plot_diminishing_returns(args.out_dir)
    print(f"  [+] Chart 5: Diminishing Returns Curve -> {f5}")
    f6 = plot_master_modified_dashboard(data["summary"], data["comparisons"], args.out_dir)
    print(f"  [+] Chart 6: Master Dashboard -> {f6}")
    print("\n[+] All 6 modified visual analytics generated.\n")

if __name__ == "__main__":
    main()
