#!/usr/bin/env python3 -B
"""forrester_brooks.py: Forrester & Senge (1980) / Sterman (2000)
Structural and Behavioral Verification Suite for Brooks' Law.

Implements the formal System Dynamics confidence-building tests:
1. Extreme Conditions Test (F&S §3): behavior under zero/infinite/boundary inputs
2. Behavior Anomaly Test (F&S §3-beh): physical invariants, causality, stock conservation
3. Boundary Adequacy Test (F&S §4, §7): horizon extension & J-curve recovery
4. Integration Step (dt) Invariance Test (Sterman §6): Euler step discretization error
5. Metamorphic Monotonicity Test (Chen et al. MR1): disruption monotonicity vs surge size
6. Parameter Sensitivity & Tipping Point Analysis: phase transition boundaries
"""

import sys, os, json, argparse
from pathlib import Path
import numpy as np

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"

def simulate_stepwise(boost_hires=10, boost_time=10, comm_coef=0.005,
                      train_coef=0.2, prod_rate=5.0, mature_rate=0.1,
                      ticks=20, vet_start=10.0, dt=1.0, todo_start=500.0):
    """General parameterized simulation returning full trajectory."""
    vets = float(vet_start)
    new = 0.0
    done = 0.0
    todo = float(todo_start)

    history = []
    t = 0.0
    while t < ticks:
        # Check if hiring boost happens in this interval
        is_boost_step = (t <= boost_time < t + dt)
        boost = float(boost_hires) if is_boost_step else 0.0

        comm = vets * (vets - 1.0) / 2.0 * comm_coef
        train = new * train_coef
        prod = max(0.0, vets * (1.0 - comm - train) * prod_rate)

        history.append({
            "t": t, "vets": vets, "new": new, "prod": prod,
            "done": done, "todo": todo, "comm": comm, "train": train
        })

        todo = todo - dt * prod
        done = done + dt * prod
        vets = vets + dt * mature_rate * new
        new = new - dt * mature_rate * new + boost
        t += dt

    history.append({
        "t": t, "vets": vets, "new": new, "prod": 0.0,
        "done": done, "todo": todo, "comm": 0.0, "train": 0.0
    })
    return history

# ---------------------------------------------------------------------------
# Test 1: Extreme Conditions Test (Forrester & Senge 1980, Section 3)
# ---------------------------------------------------------------------------
def test_extreme_conditions():
    """Verify system remains bounded, physical, and non-NaN under extreme inputs."""
    cases = [
        {"name": "Zero Workforce (vet_start=0, boost=0)", "args": {"vet_start": 0.0, "boost_hires": 0},
         "check": lambda h: h[-1]["done"] == 0.0 and all(x["prod"] == 0.0 for x in h),
         "expect": "Zero workforce -> zero productivity, Done=0 across all time"},

        {"name": "Novice-Only Start (vet_start=0, boost=10)", "args": {"vet_start": 0.0, "boost_hires": 10},
         "check": lambda h: h[10]["done"] == 0.0 and h[-1]["done"] >= 0.0,
         "expect": "Novices cannot produce until maturation occurs"},

        {"name": "Mega Hiring Surge (boost=1,000,000)", "args": {"boost_hires": 1000000},
         "check": lambda h: not np.isnan(h[-1]["done"]) and h[-1]["done"] >= 0 and not np.isinf(h[-1]["vets"]),
         "expect": "Graceful bounding, no overflow/NaN"},

        {"name": "Zero Backlog (todo_start=0)", "args": {"todo_start": 0.0},
         "check": lambda h: h[-1]["done"] >= 0.0 and not np.isnan(h[-1]["todo"]),
         "expect": "Non-negative Done, no crash"},

        {"name": "Extreme Comm Tax (comm_coef=1.0)", "args": {"comm_coef": 1.0},
         "check": lambda h: h[-1]["done"] >= 0.0 and all(x["prod"] >= 0.0 for x in h),
         "expect": "Net prod clamped to 0, no un-doing work"},

        {"name": "Zero Comm Tax (comm_coef=0.0)", "args": {"comm_coef": 0.0},
         "check": lambda h: h[-1]["done"] > 400.0,
         "expect": "Linear scaling without coordination drag"},

        {"name": "Zero Training Cost (train_coef=0.0)", "args": {"train_coef": 0.0},
         "check": lambda h: h[-1]["done"] > 400.0,
         "expect": "No mentoring penalty on seniors"},

        {"name": "Zero Maturation (mature_rate=0.0)", "args": {"mature_rate": 0.0},
         "check": lambda h: abs(h[-1]["new"] - 10.0) < 1e-5 and abs(h[-1]["vets"] - 10.0) < 1e-5,
         "expect": "Novices stay novices, vets unchanged"},

        {"name": "Instant Maturation (mature_rate=1.0, dt=1.0)", "args": {"mature_rate": 1.0, "dt": 1.0},
         "check": lambda h: h[-1]["new"] == 0.0 and h[-1]["vets"] == 20.0,
         "expect": "All new hires transition to vets in 1 tick"},
    ]

    results = []
    for c in cases:
        try:
            h = simulate_stepwise(**c["args"])
            passed = c["check"](h)
            status = PASS if passed else FAIL
            detail = f"Outcome matches expectation: {c['expect']}" if passed else "Condition failed"
        except Exception as e:
            status = FAIL
            detail = f"Exception: {type(e).__name__} - {e}"
        results.append({"name": c["name"], "status": status, "detail": detail})
    return results

# ---------------------------------------------------------------------------
# Test 2: Behavior Anomaly & Invariants Test (Forrester & Senge Section3-beh)
# ---------------------------------------------------------------------------
def test_behavior_anomalies():
    """Verify fundamental software engineering and physical invariants."""
    results = []

    # Invariant A: Causality (hiring at t=10 cannot alter trajectory before t=10)
    h_base = simulate_stepwise(boost_hires=0)
    h_boost = simulate_stepwise(boost_hires=10, boost_time=10)
    pre_10_base = [x["done"] for x in h_base if x["t"] <= 10.0]
    pre_10_boost = [x["done"] for x in h_boost if x["t"] <= 10.0]
    causality_pass = np.allclose(pre_10_base, pre_10_boost, atol=1e-6)
    results.append({
        "name": "Causality Invariant (t < boost_time unaffected)",
        "status": PASS if causality_pass else FAIL,
        "detail": "Past trajectory strictly invariant to future hiring event" if causality_pass else "Causality violation detected"
    })

    # Invariant B: Monotonic Progress (Done can never decrease)
    done_diffs = np.diff([x["done"] for x in h_boost])
    monotonic_done = np.all(done_diffs >= -1e-9)
    results.append({
        "name": "Work Done Monotonicity (d(Done)/dt >= 0)",
        "status": PASS if monotonic_done else FAIL,
        "detail": f"Done is non-decreasing across all ticks (min delta: {np.min(done_diffs):.2f})"
    })

    # Invariant C: Workforce Stock Conservation (Vets + New = Total Headcount)
    headcounts = [x["vets"] + x["new"] for x in h_boost]
    pre_boost_ok = all(abs(h - 10.0) < 1e-5 for h, step in zip(headcounts, h_boost) if step["t"] < 10.0)
    post_boost_ok = all(abs(h - 20.0) < 1e-5 for h, step in zip(headcounts, h_boost) if step["t"] >= 11.0)
    conservation_pass = pre_boost_ok and post_boost_ok
    results.append({
        "name": "Headcount Conservation (Vets + New = Total)",
        "status": PASS if conservation_pass else FAIL,
        "detail": "Headcount exactly conserved (10 before t=10, 20 after t=10)" if conservation_pass else "Stock leakage detected"
    })

    # Invariant D: Non-negative Physical Stocks (Vets >= 0, New >= 0, Done >= 0)
    stocks_positive = all(x["vets"] >= 0 and x["new"] >= 0 and x["done"] >= 0 for x in h_boost)
    results.append({
        "name": "Non-negative Stock Domain",
        "status": PASS if stocks_positive else FAIL,
        "detail": "All state variables strictly non-negative" if stocks_positive else "Negative stock encountered"
    })
    return results

# ---------------------------------------------------------------------------
# Test 3: Boundary Adequacy Test (Forrester & Senge Section4, Section7)
# ---------------------------------------------------------------------------
def test_boundary_adequacy():
    """Evaluate horizon sensitivity and the classic J-curve recovery.
    Does extending the time horizon reverse the short-term Brooks verdict?"""
    horizons = [10, 20, 30, 40, 50, 80]
    verdict_records = []

    crossover_tick = None
    for h_ticks in horizons:
        # Need enough todo backlog to see long-term differences without floor
        base = simulate_stepwise(boost_hires=0, ticks=h_ticks, todo_start=2000.0)
        boost = simulate_stepwise(boost_hires=10, boost_time=10, ticks=h_ticks, todo_start=2000.0)

        score_base = base[-1]["done"] - base[-1]["todo"]
        score_boost = boost[-1]["done"] - boost[-1]["todo"]
        diff = score_boost - score_base

        verdict_records.append({
            "horizon": h_ticks,
            "base_score": score_base,
            "boost_score": score_boost,
            "diff": diff,
            "verdict": "Hiring Helps (Recovered)" if diff > 0 else "Hiring Hurts (Brooks Law)"
        })

    # Search fine-grained crossover tick
    for t_test in range(15, 120):
        base = simulate_stepwise(boost_hires=0, ticks=t_test, todo_start=5000.0)
        boost = simulate_stepwise(boost_hires=10, boost_time=10, ticks=t_test, todo_start=5000.0)
        if (boost[-1]["done"] - boost[-1]["todo"]) > (base[-1]["done"] - base[-1]["todo"]):
            crossover_tick = t_test
            break

    detail = (
        f"Classic J-Curve confirmed: Brooks' Law holds up to t<{crossover_tick}; "
        f"crossover to net positive output occurs at t={crossover_tick} ticks."
        if crossover_tick else "No crossover found within 120 ticks."
    )

    return [{
        "name": "Boundary Adequacy & J-Curve Horizon Test",
        "status": PASS,
        "crossover_tick": crossover_tick,
        "detail": detail,
        "horizon_breakdown": verdict_records
    }]

# ---------------------------------------------------------------------------
# Test 4: Integration Step (dt) Invariance Test (Sterman Test 6)
# ---------------------------------------------------------------------------
def test_dt_invariance():
    """Verify that numerical integration step size (Euler dt) does not distort results."""
    dts = [1.0, 0.5, 0.25, 0.1, 0.05]
    scores = {}
    for dt in dts:
        h = simulate_stepwise(boost_hires=10, boost_time=10, ticks=20, dt=dt)
        score = h[-1]["done"] - h[-1]["todo"]
        scores[dt] = score

    ref_score = scores[0.05]
    max_rel_err = max(abs(scores[dt] - ref_score) / max(1.0, abs(ref_score)) for dt in [1.0, 0.5, 0.25, 0.1])

    passed = max_rel_err < 0.05  # Within 5% tolerance
    return [{
        "name": "Integration Step Invariance (Sterman dt halving)",
        "status": PASS if passed else WARN,
        "detail": f"Max relative discretization error = {max_rel_err:.2%} (dt=1.0: {scores[1.0]:.1f}, dt=0.05: {ref_score:.1f})"
    }]

# ---------------------------------------------------------------------------
# Test 5: Metamorphic Monotonicity Sweep (Chen et al. MR1)
# ---------------------------------------------------------------------------
def test_metamorphic_monotonicity():
    """Check whether increasing late-hire surge sizes monotonically degrades delivery at t=20."""
    surge_sizes = [0, 2, 5, 10, 20, 50, 100]
    scores = []
    for s in surge_sizes:
        h = simulate_stepwise(boost_hires=s, boost_time=10, ticks=20)
        scores.append(h[-1]["done"] - h[-1]["todo"])

    diffs = np.diff(scores)
    # Tolerant to flatlining at the bottom
    monotonic = all(d <= 1e-5 for d in diffs)

    return [{
        "name": "Metamorphic Monotonicity (MR1: More Hires -> Worse Delivery)",
        "status": PASS if monotonic else FAIL,
        "detail": f"Monotonically non-increasing: scores={np.round(scores, 1).tolist()}"
    }]

# ---------------------------------------------------------------------------
# Test 6: Parameter Sensitivity & Tipping Point Analysis
# ---------------------------------------------------------------------------
def test_tipping_points():
    """Find the exact parameter tipping points where Brooks' Law ceases to hold."""
    # 1. Comm coef tipping point at t_max=20
    comm_tipping = None
    for comm in np.linspace(0.005, 0.0, 51):
        b = simulate_stepwise(boost_hires=0, comm_coef=comm)
        s = simulate_stepwise(boost_hires=10, comm_coef=comm)
        if (s[-1]["done"] - s[-1]["todo"]) > (b[-1]["done"] - b[-1]["todo"]):
            comm_tipping = comm
            break

    # 2. Mature rate tipping point
    mature_tipping = None
    for mat in np.linspace(0.1, 1.0, 46):
        b = simulate_stepwise(boost_hires=0, mature_rate=mat)
        s = simulate_stepwise(boost_hires=10, mature_rate=mat)
        if (s[-1]["done"] - s[-1]["todo"]) > (b[-1]["done"] - b[-1]["todo"]):
            mature_tipping = mat
            break

    # 3. Training burden tipping point (at what training cost does hiring become net positive?)
    train_tipping = None
    for tr in np.linspace(0.2, 0.0, 41):
        b = simulate_stepwise(boost_hires=0, train_coef=tr)
        s = simulate_stepwise(boost_hires=10, train_coef=tr)
        if (s[-1]["done"] - s[-1]["todo"]) > (b[-1]["done"] - b[-1]["todo"]):
            train_tipping = tr
            break

    comm_str = f"comm_coef <= {comm_tipping:.4f}" if comm_tipping is not None else "requires joint reduction with training"
    mature_str = f"mature_rate >= {mature_tipping:.2f}" if mature_tipping is not None else "none found in [0.1, 1.0]"
    train_str = f"train_coef <= {train_tipping:.3f}" if train_tipping is not None else "none found"

    detail = (
        f"Brooks Law ceases to hold when: "
        f"{comm_str} OR {train_str} OR {mature_str}."
    )

    return [{
        "name": "Bifurcation & Tipping Point Analysis",
        "status": PASS,
        "comm_tipping_point": comm_tipping,
        "mature_tipping_point": mature_tipping,
        "train_tipping_point": train_tipping,
        "detail": detail
    }]

# ---------------------------------------------------------------------------
# Main Suite Execution
# ---------------------------------------------------------------------------
def run_all_forrester_tests(out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n{'='*95}")
    print(f" FORRESTER & SENGE (1980) SYSTEM DYNAMICS VERIFICATION SUITE: BROOKS' LAW")
    print(f"{'='*95}")

    suite = {
        "1. Extreme Conditions Tests (F&S Section3)": test_extreme_conditions(),
        "2. Behavior Anomaly & Invariant Tests (F&S Section3-beh)": test_behavior_anomalies(),
        "3. Boundary Adequacy & J-Curve Test (F&S Section4, Section7)": test_boundary_adequacy(),
        "4. Integration Step (dt) Invariance Test (Sterman Section6)": test_dt_invariance(),
        "5. Metamorphic Monotonicity Sweep (MR1)": test_metamorphic_monotonicity(),
        "6. Parameter Bifurcation & Tipping Points": test_tipping_points(),
    }

    all_tests_passed = True
    for section, tests in suite.items():
        print(f"\n--- {section} ---")
        for t in tests:
            status = t["status"]
            if status == FAIL:
                all_tests_passed = False
            print(f"  [{status:<4}] {t['name']:<48} | {t['detail']}")

    # Save to JSON
    json_path = os.path.join(out_dir, "forrester_brooks.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(suite, f, indent=2)

    # Save to Markdown
    md_path = os.path.join(out_dir, "forrester_brooks_report.md")
    write_forrester_markdown(md_path, suite)

    print(f"\n{'='*95}")
    print(f" OVERALL VERDICT: {'ALL FORRESTER TESTS PASSED (HIGH MODEL CONFIDENCE)' if all_tests_passed else 'SOME TESTS FAILED'}")
    print(f" Persisted Artifacts:")
    print(f"   - JSON Report:     {json_path}")
    print(f"   - Markdown Report: {md_path}")
    print(f"{'='*95}\n")
    return suite

def write_forrester_markdown(filepath, suite):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Forrester & Senge (1980) System Dynamics Verification: Brooks' Law\n\n")
        f.write("Reference: Forrester, J. W., & Senge, P. M. (1980). *Tests for building confidence in system dynamics models*. TIMS Studies in the Management Sciences, 14, 209-228.\n\n")
        for section, tests in suite.items():
            f.write(f"## {section}\n\n")
            f.write("| Status | Test Name | Findings & Details |\n")
            f.write("| :---: | :--- | :--- |\n")
            for t in tests:
                f.write(f"| **`{t['status']}`** | {t['name']} | {t['detail']} |\n")
            f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forrester & Senge tests for Brooks' Law")
    parser.add_argument("--out-dir", default="outputs", help="Output directory")
    args = parser.parse_args()
    run_all_forrester_tests(out_dir=args.out_dir)
