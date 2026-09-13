"""Independent-equilibrium control for the BIC component-count result.

This removes trajectory autocorrelation and dimensionality reduction entirely.
Samples are drawn independently from a gridded Boltzmann distribution in each
synthetic potential's exact latent coordinates, then full-covariance GMMs are
selected by BIC. If selected component count still changes with n, neither
temporal correlation nor projection learning is required for that behavior.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from potentials import get_potential
from selection import _fit_gmms


DEFAULT_BUDGETS = [250, 500, 1000, 2000, 4000, 8000, 16000, 32000]


def equilibrium_grid(potential, points_1d=20001, points_2d=240, kT=1.0):
    """Grid points and normalized Boltzmann weights over the stated domain."""
    if potential.dim == 1:
        points = np.linspace(*potential.domain, points_1d).reshape(-1, 1)
    else:
        gx = np.linspace(*potential.domain[0], points_2d)
        gy = np.linspace(*potential.domain[1], points_2d)
        x, y = np.meshgrid(gx, gy)
        points = np.column_stack([x.ravel(), y.ravel()])
    energy = np.asarray(potential.potential(points), dtype=float).reshape(-1)
    logw = -(energy - np.nanmin(energy)) / kT
    weights = np.exp(np.clip(logw, -745, 0))
    weights /= weights.sum()
    return points, weights


def run(potentials=("mueller_brown", "prinz1d"), budgets=DEFAULT_BUDGETS,
        seeds=10, kmax=15, n_init=5, out="results/iid_equilibrium_control.csv"):
    rows = []
    max_n = max(budgets)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    for name in potentials:
        pot = get_potential(name)
        grid, weights = equilibrium_grid(pot)
        for seed in range(seeds):
            rng = np.random.default_rng(seed)
            sample = grid[rng.choice(len(grid), size=max_n, p=weights)]
            for n in budgets:
                x = sample[:n]
                x = (x - x.mean(0, keepdims=True)) / (x.std(0, keepdims=True) + 1e-12)
                fits = _fit_gmms(x, range(1, kmax + 1), seed=seed, n_init=n_init)
                k = min(fits, key=lambda j: fits[j].bic(x))
                row = {
                    "potential": name, "mode": "iid_equilibrium",
                    "method": "exact_latent", "n_frames": n, "seed": seed,
                    "k_true": pot.n_states, "k_bic": k,
                    "hit_ceiling_bic": int(k == kmax),
                }
                rows.append(row)
                print(f"[iid] {name} seed={seed} n={n} k_bic={k}", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[iid] wrote {len(rows)} conditions to {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--potentials", nargs="+",
                    default=["mueller_brown", "prinz1d"])
    ap.add_argument("--budgets", nargs="+", type=int, default=DEFAULT_BUDGETS)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--kmax", type=int, default=15)
    ap.add_argument("--n-init", type=int, default=5)
    ap.add_argument("--out", default="results/iid_equilibrium_control.csv")
    a = ap.parse_args()
    run(a.potentials, a.budgets, a.seeds, a.kmax, a.n_init, a.out)


if __name__ == "__main__":
    main()
