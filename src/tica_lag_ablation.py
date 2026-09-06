"""
TICA lag/lagged-pair ablation.

WHY THIS EXISTS

Section 6/7 of the paper infers TICA's "warm-up" mechanism from the oracle-k
contrast: TICA's oracle-k recovery is near zero at small budgets and rises
with budget, while PCA's and VAE's do not, which is consistent with TICA's
time-lagged covariance estimate being too unstable at few lagged pairs. That
argument is indirect -- it never actually varies the thing the mechanism is
about (the lag / number of lagged pairs) independently of total budget.

This script does that directly. At each sampling budget, TICA is fit at
several different lag values. If the warm-up story is right:

  - at a FIXED budget, recovery should be worse at LARGER lags (fewer usable
    lagged pairs = n_frames - lag) and better at smaller lags
  - the budget at which TICA "stabilises" should shift with lag: a budget that
    is enough at lag=5 may not be enough at lag=100, because the number of
    lagged pairs at fixed budget shrinks as lag grows

This turns an inferred mechanism into a directly tested one.

SCOPE (deliberately reduced -- this is a follow-up ablation, not a primary
result): Prinz potential only (cleanest of the two, per the main sweep),
budgets 500-16000, lags {5, 10, 20, 50, 100}, 10 seeds, subsample mode only
(the mode the main paper's claims are keyed to).

USAGE
    python src/tica_lag_ablation.py
    python src/tica_lag_ablation.py --lags 5 10 20 50 --seeds 15
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
from embed import TICAEmbedder                              # noqa: E402
from selection import all_criteria                          # noqa: E402
from cluster import cluster_fixed_k, recovery_metrics       # noqa: E402

DEFAULT_BUDGETS = [500, 1000, 2000, 4000, 8000, 16000]
DEFAULT_LAGS = [5, 10, 20, 50, 100]


def run_condition(potential, lift, n_frames, lag, seed, kmax=15,
                  max_frames=16000, dt=1e-3, kT=1.0, stride=10):
    t0 = time.time()

    latent = build_latent(potential, "subsample", n_frames, stride, 1, seed,
                          max_frames, dt, kT)
    true_labels = potential.assign_basin(latent)
    X = lift(latent, seed=seed)

    n_usable_pairs = max(0, len(X) - lag)

    emb = TICAEmbedder(n_components=2, lag=lag, seed=seed)
    Z = emb.fit_transform(X)

    if not np.all(np.isfinite(Z)):
        return {
            "potential": potential.name, "n_frames": n_frames, "lag": lag,
            "seed": seed, "n_usable_pairs": n_usable_pairs,
            "k_true": potential.n_states, "k_bic": np.nan, "ari_bic": np.nan,
            "ari_oracle_k": np.nan, "degenerate_embedding": True,
            "runtime_s": time.time() - t0,
        }

    selections, labels_by_crit, _ = all_criteria(
        Z, k_range=range(1, kmax + 1), seed=seed
    )
    m_bic = recovery_metrics(true_labels, labels_by_crit.get("bic"), Z)

    lab_o = cluster_fixed_k(Z, potential.n_states, seed=seed)
    m_o = recovery_metrics(true_labels, lab_o, Z)

    return {
        "potential": potential.name,
        "n_frames": n_frames,
        "lag": lag,
        "seed": seed,
        "n_usable_pairs": n_usable_pairs,
        "k_true": potential.n_states,
        "k_bic": selections.get("bic", np.nan),
        "ari_bic": m_bic["ari"],
        "ari_oracle_k": m_o["ari"],
        "degenerate_embedding": False,
        "runtime_s": time.time() - t0,
    }


def main():
    ap = argparse.ArgumentParser(description="TICA lag/lagged-pair ablation")
    ap.add_argument("--potential", default="prinz1d",
                    choices=["prinz1d", "mueller_brown"])
    ap.add_argument("--budgets", nargs="+", type=int, default=DEFAULT_BUDGETS)
    ap.add_argument("--lags", nargs="+", type=int, default=DEFAULT_LAGS)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--obs-dim", type=int, default=30)
    ap.add_argument("--noise-std", type=float, default=0.05)
    ap.add_argument("--kmax", type=int, default=15)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--lift-seed", type=int, default=0)
    ap.add_argument("--out", default="results/tica_lag_ablation.csv")
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
        done = set(map(tuple, prev[["n_frames", "lag", "seed"]].values))
        header_written = True
        print(f"[resume] {len(done)} conditions already complete")

    conditions = list(itertools.product(args.budgets, args.lags, range(args.seeds)))
    # skip lags that would leave too few usable pairs at the smallest budget
    # to even attempt (n_frames <= lag means zero usable pairs)
    conditions = [(nf, lag, s) for nf, lag, s in conditions if lag < nf]
    print(f"[ablation] potential={pot.name}  conditions={len(conditions)}")

    rows = []
    t_start = time.time()
    for i, (nf, lag, seed) in enumerate(conditions, 1):
        if (nf, lag, seed) in done:
            continue
        r = run_condition(pot, lift, nf, lag, seed, kmax=args.kmax,
                          max_frames=max_frames, stride=args.stride)
        rows.append(r)
        print(f"[{i:>4}/{len(conditions)}] n={nf:<6} lag={lag:<4} "
             f"pairs={r['n_usable_pairs']:<6} seed={seed:<2} "
             f"k_bic={r['k_bic']} ARI={r['ari_bic']:.3f} "
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
