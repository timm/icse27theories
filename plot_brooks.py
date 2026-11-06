#!/usr/bin/env python3 -B
"""plot_brooks.py: Generate publication-grade visual analytics for Brooks' Law.

Produces 5 distinct visualizations + 1 Master Executive Dashboard:
1. outputs/brooks_ranking_distributions.png: Error-bar & distribution ranking
2. outputs/brooks_breakdown_bars.png: Breakdown chart (Where Brooks holds vs breaks)
3. outputs/brooks_trajectories.png: Net productivity dynamics over time (t=0..20)
4. outputs/brooks_j_curve_horizon.png: J-Curve recovery over extended horizon (t=0..60)
5. outputs/brooks_tipping_heatmap.png: 2D parameter tipping point phase space
6. outputs/brooks_master_dashboard.png: 4-panel executive overview
"""

import os, json, argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Use a clean, modern aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

def load_data(out_dir):
    json_path = os.path.join(out_dir, "brooks_100k_summary.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Missing {json_path}. Run 'make test-100k' first.")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------------------------------------------------------------
# Chart 1: Ranked Performance & Confidence Intervals
# -----------------------------------------------------------------------------
def plot_ranking(summary, out_dir):
    # Sort by median ascending for horizontal bar chart
    sorted_items = sorted(summary, key=lambda x: x["median"])
    names = [x["scenario"] for x in sorted_items]
    medians = [x["median"] for x in sorted_items]
    p05 = [x["p05"] for x in sorted_items]
    p95 = [x["p95"] for x in sorted_items]
    err_low = [m - lo for m, lo in zip(medians, p05)]
    err_high = [hi - m for m, hi in zip(medians, p95)]

    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    y_pos = np.arange(len(names))

    # Color palette based on performance tier
    colors = []
    for x in sorted_items:
        if x["scenario"] == "high_productivity":
            colors.append("#2ca02c") # Vibrant green
        elif x["scenario"] == "baseline":
            colors.append("#1f77b4") # Strong blue
        elif x["scenario"] in ["break_training", "last_minute_panic", "micro_hire"]:
            colors.append("#ff7f0e") # Amber / near-parity
        else:
            colors.append("#d62728") # Crimson / degraded

    bars = ax.barh(y_pos, medians, xerr=[err_low, err_high],
                   color=colors, alpha=0.85, edgecolor='black', linewidth=0.7,
                   capsize=4, error_kw={'elinewidth': 1.2, 'capthick': 1.2, 'ecolor': '#333333'})

    # Draw vertical reference line at baseline median
    base_med = next(x["median"] for x in summary if x["scenario"] == "baseline")
    ax.axvline(base_med, color='#1f77b4', linestyle='--', linewidth=1.5, alpha=0.8,
               label=f'Baseline Median ({base_med:.1f})')
    ax.axvline(0, color='black', linestyle='-', linewidth=0.8, alpha=0.4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight='bold')
    ax.set_xlabel("Final Score (Done - Todo) [Median with 90% Confidence Interval]", fontsize=11, fontweight='bold')
    ax.set_title("Brooks' Law: 100,000-Iteration Treatment Ranking & Performance Intervals",
                 fontsize=13, fontweight='bold', pad=15)

    # Annotate completion rates
    for i, (b, item) in enumerate(zip(bars, sorted_items)):
        x_val = item["p95"] if item["p95"] > 0 else 20
        ax.text(item["p95"] + 30, i, f"Done: {item['completed_pct']:.1f}%",
                va='center', fontsize=8.5, color='#444444', fontweight='semibold')

    # Legend
    legend_patches = [
        mpatches.Patch(color='#2ca02c', label="Breaks Brooks' Law (Hiring Helps)"),
        mpatches.Patch(color='#1f77b4', label="Baseline Control (0 Hires)"),
        mpatches.Patch(color='#ff7f0e', label="Mitigated Friction / Near Parity"),
        mpatches.Patch(color='#d62728', label="Confirms Brooks' Law (Hiring Degrades)"),
    ]
    ax.legend(handles=legend_patches, loc='lower right', frameon=True, fontsize=9.5)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "brooks_ranking_distributions.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# Chart 2: Breakdown Analysis (Where Brooks Holds vs Breaks)
# -----------------------------------------------------------------------------
def plot_breakdown(breakdowns, out_dir):
    # Sort by percentage of hiring helping descending
    sorted_b = sorted(breakdowns, key=lambda x: x["pct_better_than_base"])
    names = [x["scenario"] for x in sorted_b]
    hurts = [x["pct_worse_than_base"] for x in sorted_b]
    helps = [x["pct_better_than_base"] for x in sorted_b]
    tied = [x["pct_tied"] for x in sorted_b]

    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    y_pos = np.arange(len(names))

    p1 = ax.barh(y_pos, hurts, color='#d62728', alpha=0.85, edgecolor='black', linewidth=0.6, label='Hiring Hurts (Confirms Brooks)')
    p2 = ax.barh(y_pos, helps, left=hurts, color='#2ca02c', alpha=0.85, edgecolor='black', linewidth=0.6, label='Hiring Helps (Breaks Brooks)')
    p3 = ax.barh(y_pos, tied, left=[h + p for h, p in zip(hurts, helps)], color='#bcbd22', alpha=0.7, edgecolor='black', linewidth=0.6, label='Parity / Tied')

    ax.axvline(50, color='black', linestyle=':', linewidth=1.5, alpha=0.7, label='50% Crossover Threshold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight='bold')
    ax.set_xlabel("Percentage of 100,000 Stochastic Iterations (%)", fontsize=11, fontweight='bold')
    ax.set_title("Where Does Brooks' Law Hold vs. Break? (Paired Comparison with Baseline)",
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlim(0, 100)

    # Value text labels on bars
    for i, b in enumerate(sorted_b):
        if b["pct_worse_than_base"] >= 15:
            ax.text(b["pct_worse_than_base"] / 2, i, f"{b['pct_worse_than_base']:.1f}%",
                    ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)
        if b["pct_better_than_base"] >= 15:
            ax.text(b["pct_worse_than_base"] + b["pct_better_than_base"] / 2, i, f"{b['pct_better_than_base']:.1f}%",
                    ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)

    ax.legend(loc='lower left', frameon=True, fontsize=9.5)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "brooks_breakdown_bars.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# Chart 3: Net Productivity Trajectories Over Time
# -----------------------------------------------------------------------------
def plot_trajectories(out_dir):
    from monte_carlo_brooks import SCENARIOS, simulate_vectorized
    key_scenarios = [
        ("baseline", "Baseline (No Hires)", "#1f77b4", "-", 2.5),
        ("brooks_law", "Standard Brooks (10 Hires @ t=10)", "#d62728", "-", 2.5),
        ("massive_surge", "Massive Surge (50 Hires @ t=10)", "#8c564b", "--", 2.0),
        ("high_productivity", "High Productivity (prod_rate=15)", "#2ca02c", "-", 2.5),
        ("break_training", "No Training Drag (train_coef=0)", "#ff7f0e", "-.", 2.0),
        ("early_hire", "Early Hire (10 Hires @ t=2)", "#9467bd", ":", 2.0),
    ]

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ticks = 20

    # Deterministic reference run (noise factor = 1.0)
    noise_one = {k: np.ones(1) for k in ["comm", "train", "prod", "mature", "todo"]}

    for key, label, color, style, width in key_scenarios:
        params = SCENARIOS[key].copy()
        params["ticks"] = ticks
        res = simulate_vectorized(1, params, noise_one)
        traj = res["prod_trajectory"][:, 0]
        ax.plot(range(ticks), traj, label=label, color=color, linestyle=style, linewidth=width, marker='o', markersize=4)

    # Shaded negative zone
    ax.axhspan(-1400, 0, color='#ffebee', alpha=0.6, zorder=0)
    ax.text(1, -200, "CRITICAL COLLAPSE ZONE: Coordination & Training Friction Halts Output",
            fontsize=9.5, color='#c62828', fontweight='bold', style='italic')

    ax.axvline(10, color='gray', linestyle=':', linewidth=1.2, label='Hiring Surge Event (t=10)')
    ax.axhline(0, color='black', linewidth=1.0)

    ax.set_xlabel("Project Timeline (Ticks)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Net Productivity (Units of Work / Tick)", fontsize=11, fontweight='bold')
    ax.set_title("Productivity Dynamics: How Hiring Freezes Progress Under Different Archetypes",
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_ylim(-1350, 75)
    ax.set_xlim(0, 19)
    ax.legend(loc='lower left', frameon=True, fontsize=9.0)
    plt.tight_layout()
    out_file = os.path.join(out_dir, "brooks_trajectories.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# Chart 4: The J-Curve Recovery (Long Horizon)
# -----------------------------------------------------------------------------
def plot_j_curve(out_dir):
    from forrester_brooks import simulate_stepwise
    horizons = 60
    todo_initial = 3000.0

    base_h = simulate_stepwise(boost_hires=0, ticks=horizons, todo_start=todo_initial)
    boost_h = simulate_stepwise(boost_hires=10, boost_time=10, ticks=horizons, todo_start=todo_initial)

    t_vals = [x["t"] for x in base_h]
    base_done = [x["done"] for x in base_h]
    boost_done = [x["done"] for x in boost_h]

    diff_done = [b - a for a, b in zip(base_done, boost_done)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), dpi=300, sharex=True)

    # Subplot 1: Cumulative Work Delivered
    ax1.plot(t_vals, base_done, label="Baseline (10 Veterans, 0 Hires)", color='#1f77b4', linewidth=2.5)
    ax1.plot(t_vals, boost_done, label="Brooks Intervention (10 Hires @ t=10)", color='#d62728', linewidth=2.5)
    ax1.axvline(10, color='gray', linestyle=':', label='Hiring Event (t=10)')
    ax1.set_ylabel("Cumulative Work Done", fontsize=10.5, fontweight='bold')
    ax1.set_title("The Classic J-Curve Dynamics of Brooks' Law (Extended 60-Tick Horizon)", fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left', frameon=True, fontsize=9.5)

    # Subplot 2: Net Cumulative Advantage (Boost - Baseline)
    ax2.plot(t_vals, diff_done, color='#6a1b9a', linewidth=2.5, label='Net Work Delta (Intervention - Baseline)')
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.9)
    ax2.fill_between(t_vals, diff_done, 0, where=np.array(diff_done) <= 0, color='#ef5350', alpha=0.3, label="Brooks' Law Deficit (Worse)")
    ax2.fill_between(t_vals, diff_done, 0, where=np.array(diff_done) >= 0, color='#66bb6a', alpha=0.3, label="Long-Term Payoff (Better)")

    # Find crossover tick
    crossover = next((t for t, d in zip(t_vals, diff_done) if t > 10 and d >= 0), None)
    if crossover:
        ax2.axvline(crossover, color='#2e7d32', linestyle='--', linewidth=1.5)
        ax2.text(crossover + 1, np.min(diff_done) * 0.5, f"Crossover Payoff Point: t={crossover:.0f}",
                 fontweight='bold', color='#2e7d32', fontsize=9.5)

    ax2.set_xlabel("Project Timeline (Ticks)", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Advantage vs. Baseline", fontsize=10.5, fontweight='bold')
    ax2.legend(loc='lower right', frameon=True, fontsize=9.5)

    plt.tight_layout()
    out_file = os.path.join(out_dir, "brooks_j_curve_horizon.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# Chart 5: Parameter Tipping Point Phase Space Heatmap
# -----------------------------------------------------------------------------
def plot_phase_space(out_dir):
    from forrester_brooks import simulate_stepwise
    comm_vals = np.linspace(0.0005, 0.008, 25)
    train_vals = np.linspace(0.02, 0.35, 25)

    Z = np.zeros((len(train_vals), len(comm_vals)))

    for i, tr in enumerate(train_vals):
        for j, cm in enumerate(comm_vals):
            base = simulate_stepwise(boost_hires=0, comm_coef=cm, train_coef=tr, ticks=20)
            boost = simulate_stepwise(boost_hires=10, boost_time=10, comm_coef=cm, train_coef=tr, ticks=20)
            score_diff = (boost[-1]["done"] - boost[-1]["todo"]) - (base[-1]["done"] - base[-1]["todo"])
            Z[i, j] = score_diff

    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    X, Y = np.meshgrid(comm_vals * 1000, train_vals)

    # Diverging colormap: Red = Hiring Hurts, Green = Hiring Helps
    max_abs = max(abs(np.min(Z)), abs(np.max(Z)))
    c = ax.contourf(X, Y, Z, levels=30, cmap='RdYlGn', vmin=-max_abs, vmax=max_abs, alpha=0.9)
    cbar = fig.colorbar(c, ax=ax)
    cbar.set_label("Net Score Delta vs Baseline (Green = Hiring Helps, Red = Hiring Hurts)", fontsize=10, fontweight='bold')

    # Contour line for the exact tipping point (Zero frontier)
    cs = ax.contour(X, Y, Z, levels=[0.0], colors='black', linewidths=2.0, linestyles='--')
    ax.clabel(cs, inline=True, fmt='Tipping Boundary (Score Delta = 0)', fontsize=9.5)

    # Plot Default Brooks location
    ax.plot(0.005 * 1000, 0.2, 'ko', markersize=10, markerfacecolor='white', markeredgewidth=2.5)
    ax.text(0.005 * 1000 + 0.15, 0.2, "Standard Brooks' Law\n(Default: comm=0.005, train=0.2)",
            fontsize=9.5, fontweight='bold', color='#b71c1c')

    ax.set_xlabel("Communication Coefficient (comm_coef * 10^-3 per pair)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Training Cost (train_coef fraction / new hire)", fontsize=11, fontweight='bold')
    ax.set_title("Parameter Phase Space: Where Does Brooks' Law Transition from Harm to Benefit?",
                 fontsize=12.5, fontweight='bold', pad=15)

    plt.tight_layout()
    out_file = os.path.join(out_dir, "brooks_tipping_heatmap.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

# -----------------------------------------------------------------------------
# Chart 6: Master Executive Dashboard (4-in-1 Panel)
# -----------------------------------------------------------------------------
def plot_master_dashboard(summary, breakdowns, out_dir):
    fig = plt.figure(figsize=(18, 12), dpi=300)
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.25)

    # Panel 1: Rankings
    ax1 = fig.add_subplot(gs[0, 0])
    sorted_items = sorted(summary, key=lambda x: x["median"])
    names = [x["scenario"] for x in sorted_items]
    medians = [x["median"] for x in sorted_items]
    p05 = [x["p05"] for x in sorted_items]
    p95 = [x["p95"] for x in sorted_items]
    err_low = [m - lo for m, lo in zip(medians, p05)]
    err_high = [hi - m for m, hi in zip(medians, p95)]
    colors = ['#2ca02c' if x["scenario"]=="high_productivity" else '#1f77b4' if x["scenario"]=="baseline" else '#ff7f0e' if x["scenario"] in ["break_training", "last_minute_panic", "micro_hire"] else '#d62728' for x in sorted_items]
    ax1.barh(np.arange(len(names)), medians, xerr=[err_low, err_high], color=colors, alpha=0.85, edgecolor='black', linewidth=0.6, capsize=3)
    ax1.set_yticks(np.arange(len(names)))
    ax1.set_yticklabels(names, fontsize=8.5, fontweight='bold')
    ax1.set_title("A. Treatment Ranking & 90% Confidence Intervals", fontsize=11.5, fontweight='bold')
    ax1.set_xlabel("Final Score (Done - Todo)", fontsize=9.5)

    # Panel 2: Breakdown Bars
    ax2 = fig.add_subplot(gs[0, 1])
    sorted_b = sorted(breakdowns, key=lambda x: x["pct_better_than_base"])
    b_names = [x["scenario"] for x in sorted_b]
    hurts = [x["pct_worse_than_base"] for x in sorted_b]
    helps = [x["pct_better_than_base"] for x in sorted_b]
    ax2.barh(np.arange(len(b_names)), hurts, color='#d62728', alpha=0.85, label='Hiring Hurts')
    ax2.barh(np.arange(len(b_names)), helps, left=hurts, color='#2ca02c', alpha=0.85, label='Hiring Helps')
    ax2.set_yticks(np.arange(len(b_names)))
    ax2.set_yticklabels(b_names, fontsize=8.5, fontweight='bold')
    ax2.set_title("B. Breakdown Rate: Where Brooks' Law Holds vs. Breaks", fontsize=11.5, fontweight='bold')
    ax2.set_xlabel("% of 100,000 Runs", fontsize=9.5)
    ax2.legend(loc='lower left', fontsize=8.5)

    # Panel 3: Trajectories
    ax3 = fig.add_subplot(gs[1, 0])
    from monte_carlo_brooks import SCENARIOS, simulate_vectorized
    noise_one = {k: np.ones(1) for k in ["comm", "train", "prod", "mature", "todo"]}
    traj_lines = [
        ("baseline", "Baseline", "#1f77b4", "-"),
        ("brooks_law", "Standard Brooks", "#d62728", "-"),
        ("massive_surge", "Massive Surge", "#8c564b", "--"),
        ("high_productivity", "High Productivity", "#2ca02c", "-"),
        ("break_training", "No Training Drag", "#ff7f0e", "-."),
    ]
    for key, label, c, s in traj_lines:
        params = SCENARIOS[key].copy()
        params["ticks"] = 20
        res = simulate_vectorized(1, params, noise_one)
        ax3.plot(range(20), res["prod_trajectory"][:, 0], label=label, color=c, linestyle=s, linewidth=2.0)
    ax3.set_ylim(-1350, 70)
    ax3.set_title("C. Net Productivity Collapse Dynamics (t=0..20)", fontsize=11.5, fontweight='bold')
    ax3.set_xlabel("Timeline (Ticks)", fontsize=9.5)
    ax3.set_ylabel("Net Productivity", fontsize=9.5)
    ax3.legend(loc='lower left', fontsize=8.5)

    # Panel 4: J-Curve
    ax4 = fig.add_subplot(gs[1, 1])
    from forrester_brooks import simulate_stepwise
    b_base = simulate_stepwise(boost_hires=0, ticks=50, todo_start=2500.0)
    b_boost = simulate_stepwise(boost_hires=10, boost_time=10, ticks=50, todo_start=2500.0)
    diff = [(y["done"] - y["todo"]) - (x["done"] - x["todo"]) for x, y in zip(b_base, b_boost)]
    t_span = [x["t"] for x in b_base]
    ax4.plot(t_span, diff, color='#6a1b9a', linewidth=2.2, label='Intervention Advantage')
    ax4.axhline(0, color='black', linewidth=0.8)
    ax4.fill_between(t_span, diff, 0, where=np.array(diff) <= 0, color='#ef5350', alpha=0.35, label='Brooks Deficit')
    ax4.fill_between(t_span, diff, 0, where=np.array(diff) >= 0, color='#66bb6a', alpha=0.35, label='Long-Horizon Payoff')
    ax4.set_title("D. Horizon Boundary: Worse-Before-Better (J-Curve)", fontsize=11.5, fontweight='bold')
    ax4.set_xlabel("Timeline (Ticks)", fontsize=9.5)
    ax4.set_ylabel("Net Advantage vs Baseline", fontsize=9.5)
    ax4.legend(loc='lower right', fontsize=8.5)

    fig.suptitle("BROOKS' LAW SYSTEM DYNAMICS: COMPREHENSIVE EMPIRICAL & VISUAL LANDSCAPE",
                 fontsize=15, fontweight='bold', y=0.98)
    out_file = os.path.join(out_dir, "brooks_master_dashboard.png")
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    return out_file

def main():
    parser = argparse.ArgumentParser(description="Plot visual landscape for Brooks' Law")
    parser.add_argument("--out-dir", default="outputs", help="Output directory")
    args = parser.parse_args()

    data = load_data(args.out_dir)
    summary = data["summary"]
    breakdowns = data["breakdowns"]

    print("\n[*] Generating high-resolution visual analytics...")
    f1 = plot_ranking(summary, args.out_dir)
    print(f"  [+] Chart 1: Ranking & Distributions -> {f1}")
    f2 = plot_breakdown(breakdowns, args.out_dir)
    print(f"  [+] Chart 2: Breakdown Bars -> {f2}")
    f3 = plot_trajectories(args.out_dir)
    print(f"  [+] Chart 3: Productivity Trajectories -> {f3}")
    f4 = plot_j_curve(args.out_dir)
    print(f"  [+] Chart 4: J-Curve Horizon Dynamics -> {f4}")
    f5 = plot_phase_space(args.out_dir)
    print(f"  [+] Chart 5: Tipping Point Phase Space Heatmap -> {f5}")
    f6 = plot_master_dashboard(summary, breakdowns, args.out_dir)
    print(f"  [+] Chart 6: Master Executive Dashboard (4-in-1) -> {f6}")
    print("\n[+] All 6 visual analytics successfully generated in 'outputs/'.\n")

if __name__ == "__main__":
    main()
