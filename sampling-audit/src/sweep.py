"""
The experiment.

Design: hold the ground-truth landscape completely fixed. Vary only the
sampling budget and how it was obtained. Repeat over seeds. Ask whether the
number of metastable states each DR pipeline *reports* depends on the budget.

Two sampling modes, and the contrast between them is the heart of the paper:

  short      -- run a trajectory of exactly n_frames saved frames. This is what
                an analyst with a limited compute budget actually has. Two
                things vary at once: how much of the landscape was explored,
                and how many data points the selection criterion sees.

  subsample  -- run ONE long reference trajectory (identical across all budgets
                at a given seed) and thin it uniformly down to n_frames.
                Landscape coverage is now held approximately fixed by
                construction; only the number of points changes.

If the state-count inflation persists under `subsample`, it cannot be explained
by "short trajectories explore less" -- it is the estimator reacting to sample
size. If it vanishes, the effect is an exploration deficit. Either answer is
publishable. What is not publishable is running only `short` and asserting one
of them.

This is the same control structure as a duration-matched comparison: match the
nuisance variable, then re-measure.
"""

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from potentials import get_potential              # noqa: E402
from simulate import NonlinearLift, langevin      # noqa: E402
from embed import get_embedder                    # noqa: E402
from selection import all_criteria, CRITERIA      # noqa: E402
from cluster import (                             # noqa: E402
    cluster_fixed_k,
    recovery_metrics,
    state_population_error,
)

DEFAULT_BUDGETS = [250, 500, 1000, 2000, 4000, 8000, 16000, 32000]
DEFAULT_METHODS = ["pca", "tica", "vae"]

_REF_CACHE = {}


def reference_trajectory(potential, seed, max_frames, stride, dt, kT):
    """One long trajectory per seed, cached, used by the subsample mode."""
    key = (potential.name, seed, max_frames, stride, dt, kT)
    if key not in _REF_CACHE:
        _REF_CACHE[key] = langevin(
            potential, n_steps=max_frames * stride, dt=dt, kT=kT,
            seed=seed, stride=stride,
        )
    return _REF_CACHE[key]


def build_latent(potential, mode, n_frames, stride, n_trajs, seed,
                 max_frames, dt, kT):
    """Return the latent trajectory for one condition."""
    if mode == "subsample":
        ref = reference_trajectory(potential, seed, max_frames, stride, dt, kT)
        if n_frames >= len(ref):
            return ref
        idx = np.linspace(0, len(ref) - 1, n_frames).astype(int)
        return ref[idx]

    per = max(1, n_frames // n_trajs)
    chunks = [
        langevin(potential, n_steps=per * stride, dt=dt, kT=kT,
                 seed=seed * 1000 + j, stride=stride)
        for j in range(n_trajs)
    ]
    return np.concatenate(chunks, axis=0)[:n_frames]


def run_condition(potential, lift, method, n_frames, stride, n_trajs, seed,
                  mode="short", tica_lag=10, vae_steps=4000, n_components=2,
                  kmax=15, max_frames=32000, dt=1e-3, kT=1.0):
    t0 = time.time()

    latent = build_latent(potential, mode, n_frames, stride, n_trajs, seed,
                          max_frames, dt, kT)
    true_labels = potential.assign_basin(latent)
    X = lift(latent, seed=seed)

    kwargs = {"n_components": n_components, "seed": seed}
    if method == "tica":
        kwargs["lag"] = tica_lag
    if method == "vae":
        kwargs["fixed_steps"] = vae_steps

    emb = get_embedder(method, **kwargs)
    Z = emb.fit_transform(X)

    selections, labels_by_crit, curves = all_criteria(
        Z, k_range=range(1, kmax + 1), seed=seed
    )

    counts = np.bincount(true_labels, minlength=potential.n_states)
    row = {
        "potential": potential.name,
        "mode": mode,
        "method": method,
        "n_frames": int(n_frames),
        "stride": stride,
        "n_trajs": n_trajs,
        "seed": seed,
        "k_true": potential.n_states,
        "k_visited": int(len(np.unique(true_labels))),
        # fraction of frames in the rarest true basin: a direct measure of how
        # well this budget actually covered the landscape
        "min_basin_frac": float(counts.min() / max(1, len(true_labels))),
    }

    for crit in CRITERIA:
        k = selections.get(crit, np.nan)
        lab = labels_by_crit.get(crit)
        m = recovery_metrics(true_labels, lab, Z)
        row[f"k_{crit}"] = k
        row[f"ari_{crit}"] = m["ari"]
        row[f"nmi_{crit}"] = m["nmi"]
        row[f"hit_ceiling_{crit}"] = (
            int(k == kmax) if isinstance(k, (int, np.integer)) else np.nan
        )

    lab_o = cluster_fixed_k(Z, potential.n_states, seed=seed)
    m_o = recovery_metrics(true_labels, lab_o, Z)
    row["ari_oracle_k"] = m_o["ari"]
    row["nmi_oracle_k"] = m_o["nmi"]
    row["pop_l1_bic"] = state_population_error(
        true_labels, labels_by_crit.get("bic"), potential.n_states
    )
    row["bic_curve"] = json.dumps(curves.get("bic", {}))
    row["runtime_s"] = time.time() - t0
    return row


def main():
    ap = argparse.ArgumentParser(description="Sampling-budget audit sweep")
    ap.add_argument("--potential", default="mueller_brown",
                    choices=["prinz1d", "mueller_brown"])
    ap.add_argument("--modes", nargs="+", default=["short", "subsample"],
                    choices=["short", "subsample"])
    ap.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    ap.add_argument("--budgets", nargs="+", type=int, default=DEFAULT_BUDGETS)
    ap.add_argument("--strides", nargs="+", type=int, default=[10])
    ap.add_argument("--n-trajs", nargs="+", type=int, default=[1])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--obs-dim", type=int, default=30)
    ap.add_argument("--noise-std", type=float, default=0.05)
    ap.add_argument("--tica-lag", type=int, default=10)
    ap.add_argument("--vae-steps", type=int, default=4000,
                    help="fixed gradient steps, held constant across budgets")
    ap.add_argument("--kmax", type=int, default=15)
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--kT", type=float, default=1.0)
    ap.add_argument("--lift-seed", type=int, default=0)
    ap.add_argument("--out", default="results/sweep.csv")
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
        cols = ["mode", "method", "n_frames", "stride", "n_trajs", "seed"]
        done = set(map(tuple, prev[cols].values))
        header_written = True
        print(f"[resume] {len(done)} conditions already complete")

    conditions = list(itertools.product(
        args.modes, args.methods, args.budgets, args.strides,
        args.n_trajs, range(args.seeds)
    ))
    print(f"[sweep] potential={pot.name}  conditions={len(conditions)}")

    rows = []
    t_start = time.time()
    for i, (mode, method, nf, stride, ntr, seed) in enumerate(conditions, 1):
        if (mode, method, nf, stride, ntr, seed) in done:
            continue
        r = run_condition(
            pot, lift, method, nf, stride, ntr, seed, mode=mode,
            tica_lag=args.tica_lag, vae_steps=args.vae_steps,
            kmax=args.kmax, max_frames=max_frames, dt=args.dt, kT=args.kT,
        )
        rows.append(r)
        print(
            f"[{i:>5}/{len(conditions)}] {mode:<9} {r['method']:<5} "
            f"n={r['n_frames']:<6} s={seed:<2} k_bic={r['k_bic']} "
            f"k_icl={r['k_icl']} ARI={r['ari_bic']:.3f} "
            f"({r['runtime_s']:.1f}s)",
            flush=True,
        )
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
