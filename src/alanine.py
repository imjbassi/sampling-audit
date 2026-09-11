"""
Real-system validation: alanine dipeptide.

WHY THIS SYSTEM AND NOT A PROTEIN.

The toy potentials give exact ground truth but a referee will reasonably ask
whether the effect is an artifact of a hand-built potential and a synthetic
lift. Alanine dipeptide answers that without requiring compute you do not have:

  * its metastable states are defined by the backbone dihedrals (phi, psi),
    which is an assignment derived from chemistry, NOT from any dimensionality
    reduction or clustering method -- so the ground truth stays independent of
    the thing being audited, which is the whole methodological requirement;
  * it is small enough that nanosecond-to-microsecond sampling on one GPU (or
    overnight on CPU) is genuinely ergodic over those basins, so "true" basin
    populations are actually converged rather than assumed;
  * it is the standard validation system in this literature, so reviewers
    already know what the right answer looks like.

The observed features handed to the DR methods are the standard heavy-atom
pairwise distances -- deliberately NOT phi/psi, since feeding the methods the
ground-truth coordinates would trivialise the task.

REQUIRES: openmm, mdtraj  (see requirements-md.txt). This module is optional;
the core toy-system result stands without it.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def simulate(out_dir="data/alanine", ns=100.0, save_ps=1.0, temperature=300.0,
             seed=0, platform=None):
    """platform: 'CPU', 'CUDA', 'OpenCL', or 'Reference'. None auto-selects
    the fastest available, preferring GPU platforms over CPU over Reference."""
    """
    Run alanine dipeptide in implicit solvent and save the trajectory.

    ns=100 at save_ps=1 gives 100,000 frames, which is comfortably enough to
    cover the full budget sweep. On a GPU this is roughly an hour; on CPU
    expect it to run overnight, which is fine.
    """
    try:
        import openmm
        from openmm import app, unit
    except ImportError:
        raise SystemExit(
            "openmm not installed. `conda install -c conda-forge openmm mdtraj` "
            "or `pip install openmm mdtraj`, then re-run."
        )

    os.makedirs(out_dir, exist_ok=True)

    pdb = app.PDBFile(_alanine_pdb_path())
    ff = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")
    system = ff.createSystem(
        pdb.topology,
        nonbondedMethod=app.NoCutoff,
        constraints=app.HBonds,
    )
    integrator = openmm.LangevinMiddleIntegrator(
        temperature * unit.kelvin,
        1.0 / unit.picosecond,
        2.0 * unit.femtoseconds,
    )
    integrator.setRandomNumberSeed(seed)

    # IMPORTANT: leaving the platform unspecified can silently fall back to
    # OpenMM's single-threaded "Reference" platform, which is 10-50x slower
    # than "CPU" (multi-threaded) or a GPU platform. Request explicitly.
    if platform is None:
        names = [openmm.Platform.getPlatform(i).getName()
                 for i in range(openmm.Platform.getNumPlatforms())]
        for pref in ("CUDA", "OpenCL", "CPU", "Reference"):
            if pref in names:
                platform = pref
                break
    plat = openmm.Platform.getPlatformByName(platform)
    props = {}
    if platform == "CPU":
        import os as _os
        props["Threads"] = str(_os.cpu_count() or 1)
    print(f"[alanine] using platform={platform} props={props}")

    sim = app.Simulation(pdb.topology, system, integrator, plat, props)
    sim.context.setPositions(pdb.positions)
    sim.minimizeEnergy()
    sim.context.setVelocitiesToTemperature(temperature * unit.kelvin, seed)

    total_steps = int(ns * 1000 * 1000 / 2)        # 2 fs timestep
    save_every = int(save_ps * 1000 / 2)

    dcd = os.path.join(out_dir, f"traj_seed{seed}.dcd")
    sim.reporters.append(app.DCDReporter(dcd, save_every))
    sim.reporters.append(app.StateDataReporter(
        os.path.join(out_dir, f"log_seed{seed}.txt"), save_every * 50,
        step=True, potentialEnergy=True, temperature=True, speed=True))

    print(f"[alanine] {ns} ns, saving every {save_ps} ps -> {dcd}")
    sim.step(total_steps)
    print("[alanine] done")
    return dcd


def _alanine_pdb_path():
    """Locate the bundled alanine dipeptide structure."""
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "data", "alanine_dipeptide.pdb")
    if os.path.exists(p):
        return p
    raise SystemExit(
        "Missing data/alanine_dipeptide.pdb. Fetch a capped ACE-ALA-NME "
        "structure (e.g. from the OpenMM or MDTraj test systems) and place it "
        "there."
    )


def featurize(dcd, top, feature="heavy_distances"):
    """
    Observed features for the DR methods.

    Deliberately NOT phi/psi: those are the ground truth, and handing them to
    the methods would make the task trivial and the result meaningless.
    """
    import mdtraj as md

    t = md.load(dcd, top=top)
    if feature == "heavy_distances":
        heavy = t.topology.select("element != H")
        pairs = np.array([(i, j) for a, i in enumerate(heavy)
                          for j in heavy[a + 1:]])
        return md.compute_distances(t, pairs), t
    raise ValueError(f"unknown feature set {feature!r}")


def ground_truth_states(traj):
    """
    Basin assignment from backbone dihedrals.

    Standard alanine dipeptide partition in the Ramachandran plane:
        C7eq / alpha_R  : phi < 0, psi > ~ -2.1 rad   (split by psi)
        C7ax / alpha_L  : phi > 0

    Returns integer labels plus the (phi, psi) array for plotting.
    """
    import mdtraj as md

    phi = md.compute_phi(traj)[1].ravel()
    psi = md.compute_psi(traj)[1].ravel()

    labels = np.zeros(len(phi), dtype=int)
    neg = phi < 0
    labels[neg & (psi > 1.0)] = 0          # C7eq (beta / PPII region)
    labels[neg & (psi <= 1.0) & (psi > -2.0)] = 1   # alpha_R
    labels[neg & (psi <= -2.0)] = 0        # wraps back into C7eq
    labels[~neg] = 2                       # alpha_L / C7ax
    return labels, np.stack([phi, psi], axis=1)


def run_sweep(dcd, top, budgets=(250, 500, 1000, 2000, 4000, 8000, 16000,
                                 32000, 64000),
              methods=("pca", "tica", "vae"), seeds=8, kmax=15,
              out="results/alanine_sweep.csv", resume=False):
    """
    Same audit, real molecule.

    Budgets are drawn by uniform thinning of the single long trajectory, which
    is the coverage-matched (`subsample`) condition from the toy experiment.
    The `short` condition is obtained by taking contiguous leading blocks
    instead -- that mirrors an analyst who simply stopped the simulation early.

    Results are appended in batches of 10 rather than written once at the end,
    and `resume` skips conditions already present in `out`. The full grid is a
    multi-hour run dominated by its largest budgets -- n=64,000 alone is most of
    the wall clock -- so an all-or-nothing write loses far too much to a crash
    near the end. This mirrors the same handling in sweep.py.
    """
    import pandas as pd
    from embed import get_embedder
    from selection import all_criteria, CRITERIA
    from cluster import cluster_fixed_k, recovery_metrics

    X_all, traj = featurize(dcd, top)
    labels_all, rama = ground_truth_states(traj)
    n_true = len(np.unique(labels_all))
    print(f"[alanine] {X_all.shape[0]} frames, {X_all.shape[1]} features, "
          f"{n_true} ground-truth basins")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    done = set()
    header_written = False
    if os.path.exists(out) and resume:
        prev = pd.read_csv(out)
        cols = ["mode", "method", "n_frames", "seed"]
        done = set(map(tuple, prev[cols].values))
        header_written = True
        print(f"[resume] {len(done)} conditions already complete")

    def flush(rows):
        nonlocal header_written
        if not rows:
            return []
        pd.DataFrame(rows).to_csv(
            out, mode="a" if header_written else "w",
            header=not header_written, index=False)
        header_written = True
        return []

    rows = []
    for mode in ("short", "subsample"):
        for nf in budgets:
            if nf > len(X_all):
                continue
            for method in methods:
                for seed in range(seeds):
                    if (mode, method, nf, seed) in done:
                        continue
                    rng = np.random.default_rng(seed)
                    if mode == "subsample":
                        start = rng.integers(0, max(1, len(X_all) - nf))
                        idx = np.linspace(0, len(X_all) - 1, nf).astype(int)
                        idx = (idx + start) % len(X_all)
                        idx.sort()
                    else:
                        start = rng.integers(0, max(1, len(X_all) - nf))
                        idx = np.arange(start, start + nf)
                    Xs, ys = X_all[idx], labels_all[idx]

                    kw = {"n_components": 2, "seed": seed}
                    if method == "tica":
                        kw["lag"] = 10
                    if method == "vae":
                        kw["fixed_steps"] = 3000
                    Z = get_embedder(method, **kw).fit_transform(Xs)

                    sel, labs, _ = all_criteria(Z, range(1, kmax + 1), seed=seed)
                    row = {"system": "alanine", "mode": mode, "method": method,
                           "n_frames": nf, "seed": seed, "k_true": n_true,
                           "k_visited": len(np.unique(ys))}
                    for c in CRITERIA:
                        row[f"k_{c}"] = sel.get(c, np.nan)
                        row[f"ari_{c}"] = recovery_metrics(
                            ys, labs.get(c), Z)["ari"]
                    row["ari_oracle_k"] = recovery_metrics(
                        ys, cluster_fixed_k(Z, n_true, seed=seed), Z)["ari"]
                    rows.append(row)
                    print(f"  {mode:<9} {method:<5} n={nf:<6} s={seed} "
                          f"k_bic={row['k_bic']} ARI={row['ari_bic']:.3f}",
                          flush=True)
                    if len(rows) >= 10:
                        rows = flush(rows)

    flush(rows)
    print(f"[alanine] wrote {out}")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("simulate")
    s.add_argument("--ns", type=float, default=100.0)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--platform", default=None,
                   choices=["CPU", "CUDA", "OpenCL", "Reference"],
                   help="omit to auto-select the fastest available")
    a = sub.add_parser("sweep")
    a.add_argument("--dcd", required=True)
    a.add_argument("--top", required=True)
    a.add_argument("--seeds", type=int, default=8)
    a.add_argument("--budgets", nargs="+", type=int, default=None,
                   help="override default budget list, e.g. --budgets 100 250 500 1000 2000 4000")
    a.add_argument("--out", default="results/alanine_sweep.csv",
                   help="output CSV path, e.g. results/alanine_sweep_seed1.csv")
    a.add_argument("--resume", action="store_true",
                   help="skip conditions already present in --out")
    args = ap.parse_args()

    if args.cmd == "simulate":
        simulate(ns=args.ns, seed=args.seed, platform=args.platform)
    else:
        default_small_budgets = [100, 250, 500, 1000, 2000, 4000]
        run_sweep(args.dcd, args.top, seeds=args.seeds,
                 budgets=args.budgets or default_small_budgets,
                 out=args.out, resume=args.resume)
