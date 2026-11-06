# Forrester & Senge (1980) System Dynamics Verification: Brooks' Law

Reference: Forrester, J. W., & Senge, P. M. (1980). *Tests for building confidence in system dynamics models*. TIMS Studies in the Management Sciences, 14, 209-228.

## 1. Extreme Conditions Tests (F&S Section3)

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`PASS`** | Zero Workforce (vet_start=0, boost=0) | Outcome matches expectation: Zero workforce -> zero productivity, Done=0 across all time |
| **`PASS`** | Novice-Only Start (vet_start=0, boost=10) | Outcome matches expectation: Novices cannot produce until maturation occurs |
| **`PASS`** | Mega Hiring Surge (boost=1,000,000) | Outcome matches expectation: Graceful bounding, no overflow/NaN |
| **`PASS`** | Zero Backlog (todo_start=0) | Outcome matches expectation: Non-negative Done, no crash |
| **`PASS`** | Extreme Comm Tax (comm_coef=1.0) | Outcome matches expectation: Net prod clamped to 0, no un-doing work |
| **`PASS`** | Zero Comm Tax (comm_coef=0.0) | Outcome matches expectation: Linear scaling without coordination drag |
| **`PASS`** | Zero Training Cost (train_coef=0.0) | Outcome matches expectation: No mentoring penalty on seniors |
| **`PASS`** | Zero Maturation (mature_rate=0.0) | Outcome matches expectation: Novices stay novices, vets unchanged |
| **`PASS`** | Instant Maturation (mature_rate=1.0, dt=1.0) | Outcome matches expectation: All new hires transition to vets in 1 tick |

## 2. Behavior Anomaly & Invariant Tests (F&S Section3-beh)

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`PASS`** | Causality Invariant (t < boost_time unaffected) | Past trajectory strictly invariant to future hiring event |
| **`PASS`** | Work Done Monotonicity (d(Done)/dt >= 0) | Done is non-decreasing across all ticks (min delta: 0.00) |
| **`PASS`** | Headcount Conservation (Vets + New = Total) | Headcount exactly conserved (10 before t=10, 20 after t=10) |
| **`PASS`** | Non-negative Stock Domain | All state variables strictly non-negative |

## 3. Boundary Adequacy & J-Curve Test (F&S Section4, Section7)

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`PASS`** | Boundary Adequacy & J-Curve Horizon Test | No crossover found within 120 ticks. |

## 4. Integration Step (dt) Invariance Test (Sterman Section6)

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`WARN`** | Integration Step Invariance (Sterman dt halving) | Max relative discretization error = 28.18% (dt=1.0: 352.5, dt=0.05: 275.0) |

## 5. Metamorphic Monotonicity Sweep (MR1)

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`PASS`** | Metamorphic Monotonicity (MR1: More Hires -> Worse Delivery) | Monotonically non-increasing: scores=[1050.0, 805.3, 423.8, 352.5, 352.5, 352.5, 352.5] |

## 6. Parameter Bifurcation & Tipping Points

| Status | Test Name | Findings & Details |
| :---: | :--- | :--- |
| **`PASS`** | Bifurcation & Tipping Point Analysis | Brooks Law ceases to hold when: requires joint reduction with training OR none found OR none found in [0.1, 1.0]. |

