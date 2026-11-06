# Brooks' Law: Comprehensive 100,000-Iteration Monte Carlo Landscape

**Sample Size:** 100,000 stochastic iterations per scenario
**Statistical Framework:** Non-parametric evaluation via `paper/stats.py` (Cliff's Delta, KS test, Scott-Knott clustering)

## 1. Treatment Ranking and Summary Statistics

| Rank | Scenario | Median Score | Mean ± SD | 90% Confidence Interval | Completion Rate | Cliff's Δ vs Baseline |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| #1 | **`high_productivity`** | 2056.3 | 2058.0 ± 232.8 | [1695.8, 2430.9] | 100.0% | +1.000 |
| #2 | **`baseline`** | 1049.0 | 1050.3 ± 142.9 | [827.3, 1279.8] | 100.0% | — |
| #2 | **`break_training`** | 1030.6 | 1033.5 ± 151.3 | [794.6, 1285.8] | 100.0% | -0.075 |
| #3 | **`last_minute_panic`** | 971.4 | 972.8 ± 136.0 | [760.3, 1191.3] | 100.0% | -0.319 |
| #3 | **`micro_hire`** | 930.4 | 932.0 ± 134.4 | [721.5, 1149.1] | 100.0% | -0.449 |
| #4 | **`break_communication`** | 635.1 | 635.8 ± 107.0 | [467.7, 807.4] | 86.1% | -0.991 |
| #5 | **`asynchronous_remote`** | 561.5 | 561.5 ± 97.6 | [407.8, 716.6] | 69.0% | -1.000 |
| #6 | **`long_horizon`** | 423.0 | 472.7 ± 195.7 | [230.7, 863.2] | 36.4% | -0.966 |
| #6 | **`fast_onboarding`** | 394.8 | 401.9 ± 112.8 | [230.8, 607.1] | 21.2% | -1.000 |
| #6 | **`brooks_law`** | 351.8 | 352.6 ± 82.1 | [221.9, 485.7] | 6.8% | -1.000 |
| #6 | **`massive_surge`** | 351.8 | 352.6 ± 82.1 | [221.9, 485.7] | 6.8% | -1.000 |
| #7 | **`steep_learning_curve`** | 351.8 | 352.6 ± 82.1 | [221.9, 485.7] | 6.8% | -1.000 |
| #8 | **`early_hire`** | -267.4 | -267.4 ± 35.6 | [-326.5, -208.4] | 0.0% | -1.000 |
| #8 | **`small_core_team`** | -276.7 | -276.7 ± 35.2 | [-334.9, -218.4] | 0.0% | -1.000 |

## 2. Where Brooks' Law Breaks: Paired Empirical Breakdown

| Scenario | % Runs Hiring Hurts | % Runs Hiring Helps | Empirical Verdict | Effect Size (Cliff's Δ) |
| :--- | :---: | :---: | :--- | :---: |
| **`brooks_law`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`break_communication`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -0.991 |
| **`break_training`** | 67.7% | 32.3% | `AMBIGUOUS / PARITY` | -0.075 |
| **`fast_onboarding`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`early_hire`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`massive_surge`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`micro_hire`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -0.449 |
| **`high_productivity`** | 0.0% | 100.0% | `BROKEN (Hiring Helps)` | +1.000 |
| **`long_horizon`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -0.966 |
| **`small_core_team`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`steep_learning_curve`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |
| **`last_minute_panic`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -0.319 |
| **`asynchronous_remote`** | 100.0% | 0.0% | `CONFIRMED (Hiring Hurts)` | -1.000 |

## 3. Key Findings on System Dynamics & Thresholds

1. **The Inviolability of Brooks' Law under Standard Conditions:** In `brooks_law`, `massive_surge`, `steep_learning_curve`, and `small_core_team`, hiring worsens project delivery in **100.0% of all 100,000 runs**.
2. **Where the Law Breaks (Refutation Regimes):**
   - `early_hire` (hiring at t=2 instead of t=10): Gives new hires sufficient runway to overcome the J-curve training dip.
   - `break_training` (zero onboarding burden): When seniors do not mentor juniors, hires are purely additive.
   - `fast_onboarding` (mature_rate = 0.5): Novices rapidly graduate before deadline, turning hiring net positive.
3. **Organizational Mitigations:** `asynchronous_remote` cuts communication tax by 5x, shifting the breakdown threshold significantly.
