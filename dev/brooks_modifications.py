#!/usr/bin/env python3 -B
"""brooks_modifications.py: Architectural & Organizational Modifications to Brooks' Law.

Implements 6 distinct architectural interventions to mitigate Brooks' Law:
1. Standard Brooks (Reference Unmodified)
2. Ambassador / Hierarchical Team Partitioning (Conway's Law & Brooks' Surgical Team)
3. Dedicated Mentor Pod (Shielded Core Developers)
4. Asynchronous Documentation & CI/CD (Logarithmic Coordination Scaling)
5. Staged Wave Influx (Graduated Onboarding Pipeline)
6. Synergistic Modern Org (Combined Architectural Stack)

Does NOT modify run_brooks.py.
"""

import math
import numpy as np

MODIFIED_MODELS = {
    "standard_brooks": {
        "name": "Standard Brooks (Unmodified Reference)",
        "desc": "Flat organization: quadratic pairwise communication and universal mentoring drag.",
        "type": "unmodified"
    },
    "ambassador_partitioning": {
        "name": "Ambassador Team Partitioning",
        "desc": "Conway's Law / Surgical Teams: 10-person squads with 1 ambassador per squad.",
        "type": "structural"
    },
    "dedicated_mentor_pod": {
        "name": "Dedicated Mentoring Pod",
        "desc": "Dedicated mentors absorb all onboarding burden, completely shielding core developers.",
        "type": "process"
    },
    "async_documentation_ci": {
        "name": "Async Documentation & Automated CI/CD",
        "desc": "Information broadcast via RFCs and CI test suites; dampens quadratic meeting drag to O(N log N).",
        "type": "tooling"
    },
    "staged_wave_hiring": {
        "name": "Staged Wave Influx",
        "desc": "Pipelines 10 hires in staggered waves of 2 per tick instead of a single flash-mob burst.",
        "type": "cadence"
    },
    "synergistic_modern_org": {
        "name": "Synergistic Modern Engineering Org",
        "desc": "Combined architecture: team partitioning + dedicated mentor pods + async documentation.",
        "type": "synergistic"
    }
}

def step_standard(vets, new, comm_coef, train_coef, prod_rate):
    """Reference Brooks equations (flat clique)."""
    comm = vets * (vets - 1.0) / 2.0 * comm_coef
    train = new * train_coef
    prod = np.maximum(0.0, vets * (1.0 - comm - train) * prod_rate)
    return prod

def step_ambassador(vets, new, comm_coef, train_coef, prod_rate, team_size=10.0):
    """Ambassador hierarchical model: teams of size team_size + 1 ambassador each."""
    num_teams = np.maximum(1.0, np.ceil(vets / team_size))
    # Intra-team channels across all teams
    intra_channels = num_teams * (team_size * (team_size - 1.0) / 2.0)
    # Inter-team channels between ambassadors
    inter_channels = num_teams * (num_teams - 1.0) / 2.0
    total_channels = intra_channels + inter_channels
    comm = (total_channels / np.maximum(1.0, vets)) * comm_coef

    # New hires distributed evenly across teams
    new_per_team = new / num_teams
    train = new_per_team * train_coef
    prod = np.maximum(0.0, vets * (1.0 - comm - train) * prod_rate)
    return prod

def step_dedicated_mentor(vets, new, comm_coef, train_coef, prod_rate, max_mentees_per_mentor=5.0):
    """Dedicated mentors absorb training, shielding remaining core developers."""
    needed_mentors = np.ceil(new / max_mentees_per_mentor)
    actual_mentors = np.minimum(vets, needed_mentors)
    active_devs = np.maximum(0.0, vets - actual_mentors)

    # Active developers only communicate among themselves
    comm = active_devs * (active_devs - 1.0) / 2.0 * comm_coef
    # Active devs suffer 0 training drag (mentors handle it!)
    prod = np.maximum(0.0, active_devs * (1.0 - comm) * prod_rate)
    return prod

def step_async_ci(vets, new, comm_coef, train_coef, prod_rate):
    """Logarithmic communication scaling via asynchronous RFCs and automated CI."""
    # O(N log2 N) scaling instead of O(N^2)
    comm = vets * np.log2(np.maximum(2.0, vets)) * (comm_coef * 0.5)
    train = new * (train_coef * 0.6) # Self-serve documentation cuts mentoring burden by 40%
    prod = np.maximum(0.0, vets * (1.0 - comm - train) * prod_rate)
    return prod

def step_synergistic(vets, new, comm_coef, train_coef, prod_rate, team_size=10.0):
    """Combined modern architecture: partitioned teams + dedicated mentors + async tools."""
    num_teams = np.maximum(1.0, np.ceil(vets / team_size))
    intra_channels = num_teams * (team_size * np.log2(team_size) * 0.5)
    inter_channels = num_teams * (num_teams - 1.0) / 2.0
    total_comm = (intra_channels + inter_channels) * (comm_coef * 0.5) / np.maximum(1.0, vets)

    needed_mentors = np.ceil(new / 6.0)
    actual_mentors = np.minimum(vets, needed_mentors)
    active_devs = np.maximum(0.0, vets - actual_mentors)

    prod = np.maximum(0.0, active_devs * (1.0 - total_comm) * prod_rate)
    return prod

def simulate_modified_vectorized(model_key, n_runs, boost_hires=10, boost_time=10,
                                 ticks=20, vet_start=10.0, todo_start=500.0,
                                 comm_coef=0.005, train_coef=0.2, prod_rate=5.0,
                                 mature_rate=0.1, noise_factors=None):
    """Simulate N runs of a specified modified model architecture."""
    dt = 1.0
    if noise_factors is None:
        noise_factors = {
            "comm": np.ones(n_runs), "train": np.ones(n_runs),
            "prod": np.ones(n_runs), "mature": np.ones(n_runs),
            "todo": np.ones(n_runs)
        }

    comm_v = comm_coef * noise_factors["comm"]
    train_v = train_coef * noise_factors["train"]
    prod_v = prod_rate * noise_factors["prod"]
    mature_v = np.clip(mature_rate * noise_factors["mature"], 0.001, 1.0)

    vets = np.full(n_runs, float(vet_start))
    new = np.zeros(n_runs)
    done = np.zeros(n_runs)
    todo = float(todo_start) * noise_factors["todo"]

    prod_trajectory = np.zeros((ticks, n_runs))
    finish_tick = np.full(n_runs, -1, dtype=np.int32)

    for t in range(ticks):
        # Calculate productivity according to model architecture
        if model_key == "standard_brooks":
            prod = step_standard(vets, new, comm_v, train_v, prod_v)
        elif model_key == "ambassador_partitioning":
            prod = step_ambassador(vets, new, comm_v, train_v, prod_v)
        elif model_key == "dedicated_mentor_pod":
            prod = step_dedicated_mentor(vets, new, comm_v, train_v, prod_v)
        elif model_key == "async_documentation_ci":
            prod = step_async_ci(vets, new, comm_v, train_v, prod_v)
        elif model_key == "staged_wave_hiring":
            prod = step_standard(vets, new, comm_v, train_v, prod_v)
        elif model_key == "synergistic_modern_org":
            prod = step_synergistic(vets, new, comm_v, train_v, prod_v)
        else:
            raise ValueError(f"Unknown model_key: {model_key}")

        prod_trajectory[t] = prod
        todo = todo - dt * prod
        done = done + dt * prod

        finished_now = (todo <= 0.0) & (finish_tick == -1)
        finish_tick[finished_now] = t

        # Hiring injection logic
        if model_key == "staged_wave_hiring":
            # Staggered wave: 2 hires per tick from boost_time to boost_time + 4
            if boost_time <= t < boost_time + 5:
                boost = float(boost_hires) / 5.0
            else:
                boost = 0.0
        else:
            boost = float(boost_hires) if t == boost_time else 0.0

        vets = vets + dt * mature_v * new
        new = new - dt * mature_v * new + boost

    final_scores = done - todo
    return {
        "final_scores": final_scores,
        "done": done,
        "todo": todo,
        "finish_tick": finish_tick,
        "completed": (todo <= 0.0),
        "prod_trajectory": prod_trajectory,
    }
