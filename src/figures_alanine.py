"""
Alanine dipeptide figures.

The synthetic systems get their ground-truth panels from the potential itself
(figures.fig1_landscape / fig2_embedding_grid), which has no analogue here: the
ground truth for alanine is a chemical partition of the Ramachandran plane, and
the observed features are heavy-atom distances. So the results panels are
reused unchanged from `figures.py` -- they are driven entirely by the sweep CSV
and are system-agnostic -- and this module adds the two panels that are
specific to the real system:

  fig1_alanine_rama    -- ground truth: (phi, psi) density and the three-region
                          partition. Needs the trajectory, so it is skipped
                          when --dcd is not supplied.
  fig7_tica_lag        -- why TICA's warm-up completes so late under coverage-
                          matched subsampling (Section 6.3).

fig7 is the one worth reading carefully. TICA's lag is specified in frames of
whatever array it is handed, but uniform thinning to n frames from an N-frame
reference imposes a stride of N/n, so a nominal lag of L frames is an effective
physical lag of L * N/n picoseconds at a 1 ps save interval. The effective lag
therefore *shrinks* as the budget grows, and TICA's projection quality tracks
it rather than tracking the budget directly.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze import summarize                                    # noqa: E402
from figures import (PALETTE, LABEL, _save, fig3_state_inflation,  # noqa: E402
                     fig4_criteria, fig5_recovery, fig6_coverage)

# Provenance of the production run: see alanine.simulate() defaults.
REF_FRAMES = 100_000      # 100 ns at a 1 ps save interval
SAVE_PS = 1.0             # ps per saved frame
TICA_LAG = 10             # frames, as passed in alanine.run_sweep()

# Backbone dihedral transitions separating these basins sit around here; the
# line is drawn as an eyeball reference, not as a fitted quantity.
DIHEDRAL_TIMESCALE_PS = 100.0


def effective_lag_ps(n_frames, mode):
    """Physical lag TICA actually sees, in ps.

    `short` takes a contiguous block, so the stride is 1 and the effective lag
    is just the nominal one. `subsample` thins uniformly, so the stride is
    REF_FRAMES / n and the effective lag scales with it.
    """
    n = np.asarray(n_frames, dtype=float)
    stride = np.where(mode == "subsample", REF_FRAMES / n, 1.0)
    return TICA_LAG * stride * SAVE_PS


def fig7_tica_lag(df, outdir="figures_alanine"):
    """TICA warm-up is governed by effective lag, not by budget."""
    d = df[df["method"] == "tica"]
    if d.empty:
        print("  [skip] fig7: no TICA rows")
        return

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.6))

    # (a) oracle-k against budget, one line per mode.
    for mode, ls, mk in (("short", "-", "o"), ("subsample", "--", "s")):
        s = summarize(d[d["mode"] == mode], "ari_oracle_k").sort_values("n_frames")
        if s.empty:
            continue
        axes[0].plot(s["n_frames"], s["mean"], ls, marker=mk, ms=4,
                     color=PALETTE["tica"] if mode == "short" else "#7B3F00",
                     label={"short": "short (stride 1)",
                            "subsample": "subsample (stride N/n)"}[mode])
        axes[0].fill_between(s["n_frames"], s["ci_lo"], s["ci_hi"],
                             color=PALETTE["tica"], alpha=0.12, lw=0)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("sampling budget (saved frames)")
    axes[0].set_ylabel("oracle-k ARI (projection quality)")
    axes[0].set_title("(a) Warm-up against budget")
    axes[0].legend(loc="upper left")
    axes[0].set_ylim(-0.05, 1.02)

    # (b) the same points against the lag TICA actually sees. This separates the
    # two modes rather than collapsing them, which is the point: every
    # `subsample` point is placed by its stride, and the whole 0.25 -> 0.93 jump
    # falls across the 100 ps line, so lag alone accounts for that curve. The
    # `short` points all sit at a fixed 10 ps and still span 0.15 to 0.96, so
    # their spread is sample size alone. Two mechanisms, one per mode.
    for mode, mk in (("short", "o"), ("subsample", "s")):
        s = summarize(d[d["mode"] == mode], "ari_oracle_k").sort_values("n_frames")
        if s.empty:
            continue
        lag = effective_lag_ps(s["n_frames"].values, mode)
        axes[1].plot(lag, s["mean"], linestyle="none", marker=mk, ms=6,
                     color=PALETTE["tica"] if mode == "short" else "#7B3F00",
                     label=mode)
    axes[1].axvline(DIHEDRAL_TIMESCALE_PS, color="k", ls=":", lw=1.4)
    axes[1].text(DIHEDRAL_TIMESCALE_PS * 1.15, 0.05,
                 "dihedral transition\ntimescale", fontsize=7.5, va="bottom")
    axes[1].set_xscale("log")
    axes[1].set_xlabel(r"effective lag $\tau_{\mathrm{eff}} = L\,(N/n)\,\Delta t$  (ps)")
    axes[1].set_ylabel("oracle-k ARI")
    axes[1].set_title("(b) The same points against effective lag")
    axes[1].legend(loc="upper right", title="mode")
    axes[1].set_ylim(-0.05, 1.02)

    fig.suptitle("Thinning a trajectory rescales TICA's lag: warm-up tracks "
                 r"$\tau_{\mathrm{eff}}$, not sample size", y=1.04)
    _save(fig, outdir, "fig7_tica_effective_lag")


def fig1_alanine_rama(dcd, top, outdir="figures_alanine", stride=10):
    """Ground truth: Ramachandran density and the three-region partition."""
    try:
        import mdtraj as md                                        # noqa: F401
    except ImportError:
        print("  [skip] fig1: mdtraj not installed")
        return
    from alanine import ground_truth_states
    import mdtraj as md

    traj = md.load(dcd, top=top, stride=stride)
    labels, rama = ground_truth_states(traj)
    phi, psi = rama[:, 0], rama[:, 1]
    cmap = matplotlib.colors.ListedColormap(["#0072B2", "#D55E00", "#009E73"])
    names = ["C7eq", r"$\alpha_R$", r"$\alpha_L$/C7ax"]

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3))

    axes[0].hexbin(phi, psi, gridsize=70, bins="log", cmap="viridis",
                   extent=(-np.pi, np.pi, -np.pi, np.pi))
    axes[0].set_title("(a) Ramachandran density")

    axes[1].scatter(phi, psi, c=labels, s=1.2, alpha=0.35, cmap=cmap,
                    vmin=0, vmax=2)
    axes[1].set_title(f"(b) Ground-truth basins (k={len(np.unique(labels))})")
    for i, nm in enumerate(names):
        axes[1].scatter([], [], c=[cmap(i)], s=22, label=nm)
    axes[1].legend(loc="lower left", fontsize=7.5)

    pops = np.bincount(labels, minlength=3) / len(labels)
    axes[2].bar(range(3), pops, color=[cmap(i) for i in range(3)])
    axes[2].set_xticks(range(3))
    axes[2].set_xticklabels(names)
    axes[2].set_ylabel("occupancy")
    axes[2].set_title("(c) Basin populations")
    axes[2].grid(axis="x", visible=False)
    for i, p in enumerate(pops):
        axes[2].text(i, p, f"{p:.3f}", ha="center", va="bottom", fontsize=8)

    for a in axes[:2]:
        a.set_xlabel(r"$\phi$ (rad)")
        a.set_ylabel(r"$\psi$ (rad)")
        a.set_xlim(-np.pi, np.pi)
        a.set_ylim(-np.pi, np.pi)
    fig.suptitle(f"Alanine dipeptide ground truth ({len(traj)} frames shown, "
                 f"stride {stride})", y=1.03)
    _save(fig, outdir, "fig1_alanine_rama")


def make_all(results_csv="results/alanine_sweep_100ns.csv",
             outdir="figures_alanine", dcd=None, top=None):
    if dcd and top:
        print("[figures_alanine] ground truth")
        fig1_alanine_rama(dcd, top, outdir)
    else:
        print("[figures_alanine] no --dcd/--top given; skipping Ramachandran panel")

    if not os.path.exists(results_csv):
        raise SystemExit(f"no results at {results_csv}")
    df = pd.read_csv(results_csv)
    print(f"[figures_alanine] {len(df)} conditions from {results_csv}")
    fig3_state_inflation(df, outdir, "bic")
    fig3_state_inflation(df, outdir, "icl")
    fig4_criteria(df, outdir)
    fig5_recovery(df, outdir)
    fig6_coverage(df, outdir)
    fig7_tica_lag(df, outdir)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/alanine_sweep_100ns.csv")
    ap.add_argument("--outdir", default="figures_alanine")
    ap.add_argument("--dcd", default=None, help="100 ns trajectory (optional)")
    ap.add_argument("--top", default="data/alanine_dipeptide.pdb")
    a = ap.parse_args()
    make_all(a.results, a.outdir, a.dcd, a.top)
