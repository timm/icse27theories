PYTHON ?= python3

.PHONY: all baseline brooks break-comm break-train fast-onboard early-hire massive-surge micro-hire high-productivity long-horizon small-core-team steep-learning last-minute-panic async-remote test-100k test-10k forrester plot landscape clean-outputs test-modified forrester-modified plot-modified all-modified

all: baseline brooks break-comm break-train fast-onboard early-hire massive-surge micro-hire high-productivity long-horizon small-core-team steep-learning last-minute-panic async-remote

# -----------------------------------------------------------------------------
# High-Scale (100,000+ Runs) Monte Carlo & Statistical Analysis Suite
# -----------------------------------------------------------------------------

# Run 100,000 stochastic iterations per scenario, perform non-parametric
# statistical tests (Cliff's Delta, KS test, Scott-Knott ranking), and persist artifacts
test-100k:
	$(PYTHON) monte_carlo_brooks.py all --runs 100000 --out-dir outputs

# Fast 10,000 iteration smoke test
test-10k:
	$(PYTHON) monte_carlo_brooks.py all --runs 10000 --out-dir outputs

# Run Forrester & Senge (1980) System Dynamics verification suite
forrester:
	$(PYTHON) forrester_brooks.py --out-dir outputs

# Generate high-resolution visual plots for all generated outputs
plot:
	$(PYTHON) plot_brooks.py --out-dir outputs

# Complete landscape: runs 100k Monte Carlo + Stats + Forrester Suite + Plots
landscape: test-100k forrester plot

# -----------------------------------------------------------------------------
# Architectural Modifications Suite (Ambassador, Mentors, Async, Synergistic)
# -----------------------------------------------------------------------------

# 100,000-run Monte Carlo evaluation of architectural modifications
test-modified:
	$(PYTHON) monte_carlo_modified.py --runs 100000 --out-dir outputs

# Forrester & Senge structural verification of modified models (J-curve crossover)
forrester-modified:
	$(PYTHON) forrester_modified.py --out-dir outputs

# High-resolution visual analytics for modified models
plot-modified:
	$(PYTHON) plot_modified.py --out-dir outputs

# Run full modification pipeline: 100k MC + Forrester + Plots
all-modified: test-modified forrester-modified plot-modified

# -----------------------------------------------------------------------------
# Single-Shot Educational Scenarios
# -----------------------------------------------------------------------------

baseline:
	$(PYTHON) run_brooks.py baseline

brooks:
	$(PYTHON) run_brooks.py brooks_law

break-comm:
	$(PYTHON) run_brooks.py break_communication

break-train:
	$(PYTHON) run_brooks.py break_training

fast-onboard:
	$(PYTHON) run_brooks.py fast_onboarding

early-hire:
	$(PYTHON) run_brooks.py early_hire

massive-surge:
	$(PYTHON) run_brooks.py massive_surge

micro-hire:
	$(PYTHON) run_brooks.py micro_hire

high-productivity:
	$(PYTHON) run_brooks.py high_productivity

# What if the deadline is pushed back and the timeline is long?
long-horizon:
	$(PYTHON) run_brooks.py long_horizon

# What if 10 hires are dumped onto a tiny core team of 2?
small-core-team:
	$(PYTHON) run_brooks.py small_core_team

# What if the codebase is spaghetti and takes forever to learn?
steep-learning:
	$(PYTHON) run_brooks.py steep_learning_curve

# What if management panics and adds people 2 ticks before launch?
last-minute-panic:
	$(PYTHON) run_brooks.py last_minute_panic

# What if the team is highly async, reducing meeting overhead?
async-remote:
	$(PYTHON) run_brooks.py asynchronous_remote

# -----------------------------------------------------------------------------
# lawkit: generic law pipeline (battery -> regimes -> evidence -> cards)
# REPOS = directory holding clones of helix/ and aider/
# -----------------------------------------------------------------------------
REPOS ?= ../../repos

laws:  ## evidence cards for every law in lawkit/laws.py
	$(PYTHON) -B run_laws.py

evidence:  ## mine real-project support factors (needs git clones in REPOS)
	$(PYTHON) -B mine/brooks_evidence.py $(REPOS)/helix helix
	$(PYTHON) -B mine/brooks_evidence.py $(REPOS)/aider aider --since 2023
	$(PYTHON) -B mine/aiwork_evidence.py $(REPOS)/aider aider \
	  --authors "Paul Gauthier" --ai "\(aider\)" --since 2024-07-01 \
	  --until 2025-07-01 --prefix aider/ --ext .py --per-arm 900
	$(PYTHON) -B mine/aiwork_evidence.py $(REPOS)/aider aider2023 \
	  --authors "Paul Gauthier" "paul-gauthier" --ai "\(aider\)" \
	  --ai-msg "^aider:" --since 2023-05-01 --until 2024-07-01 \
	  --prefix aider/ --ext .py --per-arm 900
	$(PYTHON) -B mine/archpat_evidence.py $(REPOS)/helix helix

sensitivity:  ## which evidence link carries each real-project verdict
	$(PYTHON) -B sensitivity.py

forrester-all:  ## every no-data F&S test on every world of the standard brooks model
	$(PYTHON) -B forrester_all.py

mc-standard:  ## 100k-world Monte Carlo of the standard brooks model (CSV)
	$(PYTHON) -B monte_carlo_standard.py --runs 100000 --out-dir outputs

docs-site:  ## build research_docs/site and serve it on :8765
	$(PYTHON) -B research_docs/build.py
	$(PYTHON) -m http.server 8765 -d research_docs/site

lawkit-test:
	$(PYTHON) -m pytest -q lawkit/test_lawkit.py

clean-outputs:
	rm -rf outputs/*