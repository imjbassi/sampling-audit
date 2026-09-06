"""
Embedding-dimension ablation.

WHY THIS EXISTS

Every result in the main paper uses a 2-component embedding, matching the
dimensionality typically used for free energy surface visualization. This is a
reasonable default but an untested one (flagged as open in `paper/threats.md`
T7): if the sampling-budget inflation effect were substantially smaller at
higher embedding dimension, the paper's practical recommendation would need to
be scoped to low-dimensional visualization specifically rather than stated as
a general property of the projection-plus-selection pipeline.

This script re-runs the core measurement -- reported state count and recovery
as a function of sampling budget -- at n_components in {2, 3, 5} instead of
just 2, so the dimension axis can be checked directly against the main
result rather than assumed not to matter.

SCOPE (deliberately reduced, matching the other follow-up ablations): Prinz
potential only, subsample mode only (the mode the paper's primary claims are
keyed to), a reduced budget grid, 10 seeds. This is a follow-up ablation, not
a primary result, and is sized accordingly.

USAGE
    python src/dim_ablation.py
    python src/dim_ablation.py --dims 2 3 5 --seeds 10
"""

import argparse
import itertools
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from potentials import get_potential                       # noqa: E402
from simulate import NonlinearLift                         # noqa: E402
from sweep import build_latent                              # noqa: E402
from embed import get_embedder                              # noqa: E402
from selection import all_criteria, CRITERIA                # noqa: E402
from cluster import cluster_fixed_k, recovery_metrics       # noqa: E402

DEFAULT_BUDGETS = [500, 1000, 2000, 4000, 8000, 16000]
DEFAULT_DIMS = [2, 3, 5]
DEFAULT_METHODS = ["pca", "tica", "vae"]


def run_condition(potential, lift, method, n_frames, dim, seed, kmax=15,
                  max_frames=16000, dt=1e-3, kT=1.0, stride=10,
                  tica_lag=10, vae_steps=3000):
    t0 = time.time()

    latent = build_latent(potential, "subsample", n_frames, stride, 1, seed,
                          max_frames, dt, kT)
    true_labels = potential.assign_basin(latent)
    X = lift(latent, seed=seed)

    kwargs = {"n_components": dim, "seed": seed}
    if method == "tica":
        kwargs["lag"] = tica_lag
    if method == "vae":
        kwargs["fixed_steps"] = vae_steps

    emb = get_embedder(method, **kwargs)
    Z = emb.fit_transform(X)

    row = {
        "potential": potential.name, "method": method, "n_frames": n_frames,
        "dim": dim, "seed": seed, "k_true": potential.n_states,
    }

    if not np.all(np.isfinite(Z)):
        for crit in CRITERIA:
            row[f"k_{crit}"] = np.nan
            row[f"ari_{crit}"] = np.nan
        row["ari_oracle_k"] = np.nan
        row["degenerate_embedding"] = True
        row["runtime_s"] = time.time() - t0
        return row

    selections, labels_by_crit, _ = all_criteria(
        Z, k_range=range(1, kmax + 1), seed=seed
    )
    for crit in CRITERIA:
        k = selections.get(crit, np.nan)
        lab = labels_by_crit.get(crit)
        m = recovery_metrics(true_labels, lab, Z)
        row[f"k_{crit}"] = k
        row[f"ari_{crit}"] = m["ari"]

    lab_o = cluster_fixed_k(Z, potential.n_states, seed=seed)
    m_o = recovery_metrics(true_labels, lab_o, Z)
    row["ari_oracle_k"] = m_o["ari"]
    row["degenerate_embedding"] = False
    row["runtime_s"] = time.time() - t0
    return row


def main():
    ap = argparse.ArgumentParser(description="Embedding-dimension ablation")
    ap.add_argument("--potential", default="prinz1d",
                    choices=["prinz1d", "mueller_brown"])
    ap.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    ap.add_argument("--budgets", nargs="+", type=int, default=DEFAULT_BUDGETS)
    ap.add_argument("--dims", nargs="+", type=int, default=DEFAULT_DIMS)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--obs-dim", type=int, default=30)
    ap.add_argument("--noise-std", type=float, default=0.05)
    ap.add_argument("--kmax", type=int, default=15)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--tica-lag", type=int, default=10)
    ap.add_argument("--vae-steps", type=int, default=3000)
    ap.add_argument("--lift-seed", type=int, default=0)
    ap.add_argument("--out", default="results/dim_ablation.csv")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    pot = get_potential(args.potential)
    lift = NonlinearLift(latent_dim=pot.dim, obs_dim=args.obs_dim,
                         seed=args.lift_seed, noise_std=args.noise_std)
    max_frames = max(args.budgets)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    done = set()
    header_written = False
    if os.path.exists(args.out) and args.resume:
        prev = pd.read_csv(args.out)
        cols = ["method", "n_frames", "dim", "seed"]
        done = set(map(tuple, prev[cols].values))
        header_written = True
        print(f"[resume] {len(done)} conditions already complete")

    conditions = list(itertools.product(
        args.methods, args.budgets, args.dims, range(args.seeds)
    ))
    print(f"[ablation] potential={pot.name}  conditions={len(conditions)}")

    rows = []
    t_start = time.time()
    for i, (method, nf, dim, seed) in enumerate(conditions, 1):
        if (method, nf, dim, seed) in done:
            continue
        r = run_condition(pot, lift, method, nf, dim, seed, kmax=args.kmax,
                          max_frames=max_frames, stride=args.stride,
                          tica_lag=args.tica_lag, vae_steps=args.vae_steps)
        rows.append(r)
        print(f"[{i:>4}/{len(conditions)}] {method:<5} n={nf:<6} dim={dim} "
             f"seed={seed:<2} k_bic={r['k_bic']} ARI={r['ari_bic']:.3f} "
             f"oracleARI={r['ari_oracle_k']:.3f} ({r['runtime_s']:.1f}s)",
             flush=True)
        if len(rows) >= 10:
            pd.DataFrame(rows).to_csv(
                args.out, mode="a" if header_written else "w",
                header=not header_written, index=False)
            header_written = True
            rows = []

    if rows:
        pd.DataFrame(rows).to_csv(
            args.out, mode="a" if header_written else "w",
            header=not header_written, index=False)
    print(f"[done] {args.out}  elapsed {(time.time()-t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
