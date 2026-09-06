"""
Publication figures.

Figure list (maps 1:1 onto the paper):
  fig1_landscape      -- ground truth: potential surface, basins, sample traj
  fig2_embedding_grid -- DR embeddings across methods x budgets (the visual hook)
  fig3_state_inflation-- k_selected vs budget with bootstrap CIs (main result)
  fig4_criteria       -- same trend under all five selection criteria
  fig5_recovery       -- ARI at selected k vs ARI at oracle k
  fig6_coverage       -- short vs subsample: the confound control

All figures are vector PDF plus PNG. Colours are colour-blind safe and every
panel carries its own axis labels so it survives being read out of context.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze import summarize, budget_trend            # noqa: E402
from potentials import get_potential                   # noqa: E402
from simulate import NonlinearLift, langevin           # noqa: E402
from embed import get_embedder                         # noqa: E402

PALETTE = {"pca": "#0072B2", "tica": "#D55E00", "vae": "#009E73",
           "tsne": "#CC79A7"}
MODE_LS = {"short": "-", "subsample": "--"}
LABEL = {"pca": "PCA", "tica": "TICA", "vae": "VAE", "tsne": "t-SNE"}

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 300, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
})


def _save(fig, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(outdir, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.pdf / .png")


def fig1_landscape(outdir="figures", potential="mueller_brown", seed=0):
    """Ground truth panel: energy surface, true basins, one trajectory."""
    pot = get_potential(potential)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))

    if pot.dim == 2:
        pts, shape = pot.grid(220)
        V = pot.potential(pts).reshape(shape)
        X = pts[:, 0].reshape(shape)
        Y = pts[:, 1].reshape(shape)
        vmax = np.percentile(V, 92)

        c = axes[0].contourf(X, Y, np.clip(V, None, vmax), levels=40,
                             cmap="viridis")
        axes[0].contour(X, Y, np.clip(V, None, vmax), levels=14,
                        colors="k", linewidths=0.3, alpha=0.4)
        plt.colorbar(c, ax=axes[0], label="V (arb. units)")
        axes[0].scatter(pot._minima[:, 0], pot._minima[:, 1], c="white",
                        edgecolors="k", s=70, marker="*", zorder=5,
                        label="minima")
        axes[0].set_title("(a) Potential energy surface")
        axes[0].legend(loc="upper right")

        lab = pot.assign_basin(pts).reshape(shape)
        axes[1].contourf(X, Y, lab, levels=[-0.5, 0.5, 1.5, 2.5],
                         colors=["#0072B2", "#D55E00", "#009E73"], alpha=0.55)
        axes[1].set_title(f"(b) Ground-truth basins (k={pot.n_states})")

        traj = langevin(pot, n_steps=400000, dt=1e-3, kT=1.0, seed=seed,
                        stride=40)
        tl = pot.assign_basin(traj)
        axes[2].scatter(traj[:, 0], traj[:, 1], c=tl, s=1.5, alpha=0.35,
                        cmap=matplotlib.colors.ListedColormap(
                            ["#0072B2", "#D55E00", "#009E73"]))
        axes[2].set_title(f"(c) Sampled trajectory (n={len(traj)})")
        for a in axes:
            a.set_xlabel("$z_1$")
            a.set_xlim(pot.domain[0])
            a.set_ylim(pot.domain[1])
        axes[0].set_ylabel("$z_2$")
    else:
        xs = pot.grid(800)
        axes[0].plot(xs.ravel(), pot.potential(xs.ravel()), lw=1.6, color="k")
        for b in pot._boundaries:
            axes[0].axvline(b, color="#D55E00", ls="--", lw=0.9)
        axes[0].set_title(f"(a) Potential, k={pot.n_states}")
        traj = langevin(pot, n_steps=400000, dt=1e-3, kT=1.0, seed=seed,
                        stride=40)
        axes[1].plot(traj.ravel()[:4000], lw=0.4)
        axes[1].set_title("(b) Trajectory")
        axes[2].hist(traj.ravel(), bins=120, color="#0072B2")
        axes[2].set_title("(c) Sampled density")

    fig.suptitle("Ground truth is known by construction, not inferred", y=1.04)
    _save(fig, outdir, "fig1_landscape")


def fig2_embedding_grid(outdir="figures", potential="mueller_brown",
                        methods=("pca", "tica", "vae"),
                        budgets=(500, 2000, 8000, 32000), seed=0,
                        obs_dim=30, stride=10, vae_steps=4000):
    """
    The visual hook: rows = method, cols = budget, colour = TRUE basin.

    A reader should be able to see structure appearing and fragmenting as the
    budget grows, even though the underlying landscape is identical in every
    panel.
    """
    pot = get_potential(potential)
    lift = NonlinearLift(latent_dim=pot.dim, obs_dim=obs_dim, seed=0)
    ref = langevin(pot, n_steps=max(budgets) * stride, dt=1e-3, kT=1.0,
                   seed=seed, stride=stride)

    fig, axes = plt.subplots(len(methods), len(budgets),
                             figsize=(2.5 * len(budgets), 2.4 * len(methods)),
                             squeeze=False)
    cmap = matplotlib.colors.ListedColormap(["#0072B2", "#D55E00", "#009E73",
                                             "#CC79A7"])
    for i, m in enumerate(methods):
        for j, nf in enumerate(budgets):
            idx = np.linspace(0, len(ref) - 1, min(nf, len(ref))).astype(int)
            z = ref[idx]
            lab = pot.assign_basin(z)
            X = lift(z, seed=seed)
            kw = {"n_components": 2, "seed": seed}
            if m == "tica":
                kw["lag"] = 10
            if m == "vae":
                kw["fixed_steps"] = vae_steps
            Z = get_embedder(m, **kw).fit_transform(X)
            ax = axes[i][j]
            if np.all(np.isfinite(Z)):
                ax.scatter(Z[:, 0], Z[:, 1], c=lab, s=2.5, alpha=0.5,
                           cmap=cmap, vmin=0, vmax=3)
            ax.set_xticks([])
            ax.set_yticks([])
            if i == 0:
                ax.set_title(f"n = {nf}")
            if j == 0:
                ax.set_ylabel(LABEL[m], fontsize=11)
    fig.suptitle("Embeddings coloured by TRUE basin; the landscape is identical "
                 "in every panel", y=1.0)
    _save(fig, outdir, "fig2_embedding_grid")


def fig3_state_inflation(df, outdir="figures", criterion="bic"):
    """Main result: reported state count vs sampling budget."""
    col = f"k_{criterion}"
    s = summarize(df, col)
    k_true = int(df["k_true"].iloc[0])

    modes = sorted(df["mode"].unique())
    fig, axes = plt.subplots(1, len(modes), figsize=(5.2 * len(modes), 3.6),
                             squeeze=False, sharey=True)
    for a, mode in zip(axes[0], modes):
        sub = s[s["mode"] == mode]
        for m in sorted(sub["method"].unique()):
            g = sub[sub["method"] == m].sort_values("n_frames")
            a.plot(g["n_frames"], g["mean"], "o-", color=PALETTE.get(m),
                   label=LABEL.get(m, m), ms=4)
            a.fill_between(g["n_frames"], g["ci_lo"], g["ci_hi"],
                           color=PALETTE.get(m), alpha=0.18, lw=0)
        a.axhline(k_true, color="k", ls=":", lw=1.4)
        a.text(0.02, 0.94, f"true k = {k_true}", transform=a.transAxes,
               fontsize=8, va="top")
        a.set_xscale("log")
        a.set_xlabel("sampling budget (saved frames)")
        a.set_title({"short": "short trajectories",
                     "subsample": "coverage-matched subsample"}.get(mode, mode))
    axes[0][0].set_ylabel(f"states reported ({criterion.upper()})")
    axes[0][-1].legend(title="projection")
    fig.suptitle("Reported number of metastable states grows with sampling "
                 "budget at fixed ground truth", y=1.03)
    _save(fig, outdir, f"fig3_state_inflation_{criterion}")


def fig4_criteria(df, outdir="figures",
                  criteria=("bic", "aic", "icl", "silhouette", "elbow_gap"),
                  mode="subsample"):
    """Is it a BIC artifact? Same trend under five selection criteria."""
    d = df[df["mode"] == mode] if mode in set(df["mode"]) else df
    k_true = int(df["k_true"].iloc[0])
    crits = [c for c in criteria if f"k_{c}" in d.columns]
    fig, axes = plt.subplots(1, len(crits), figsize=(2.7 * len(crits), 3.2),
                             squeeze=False, sharey=True)
    for a, c in zip(axes[0], crits):
        s = summarize(d, f"k_{c}")
        for m in sorted(s["method"].unique()):
            g = s[s["method"] == m].sort_values("n_frames")
            a.plot(g["n_frames"], g["mean"], "o-", color=PALETTE.get(m),
                   ms=3.5, label=LABEL.get(m, m))
            a.fill_between(g["n_frames"], g["ci_lo"], g["ci_hi"],
                           color=PALETTE.get(m), alpha=0.16, lw=0)
        a.axhline(k_true, color="k", ls=":", lw=1.2)
        a.set_xscale("log")
        a.set_title(c.upper() if len(c) <= 3 else c)
        a.set_xlabel("frames")
    axes[0][0].set_ylabel("states reported")
    axes[0][-1].legend()
    fig.suptitle(f"Trend under five selection criteria ({mode} mode)", y=1.04)
    _save(fig, outdir, "fig4_criteria")


def fig5_recovery(df, outdir="figures", criterion="bic",
                  drop_degenerate=True, min_basin_frac=None):
    """
    Selected-k recovery vs oracle-k recovery.

    drop_degenerate : exclude conditions where fewer true basins were visited
        than exist. In those conditions the ground-truth label vector is
        constant, so a single-cluster solution scores ARI = 1.0 trivially and
        the value is not interpretable. Budgets left with no valid replicates
        are dropped entirely rather than plotted from a partial sample.

    min_basin_frac : optionally also require the rarest true basin to hold at
        least this fraction of frames. A basin at 0.3% occupancy passes the
        k_visited test but cannot support a cluster.
    """
    n_before = len(df)
    if drop_degenerate and "k_visited" in df.columns:
        df = df[df["k_visited"] >= df["k_true"]]
    if min_basin_frac is not None and "min_basin_frac" in df.columns:
        df = df[df["min_basin_frac"] >= min_basin_frac]
    n_dropped = n_before - len(df)

    # drop budgets that lost all replicates, so no point is drawn from an
    # empty or near-empty sample
    keep = df.groupby(["mode", "n_frames"])["seed"].transform("count") >= 3
    df = df[keep]

    modes = sorted(df["mode"].unique())
    fig, axes = plt.subplots(1, len(modes), figsize=(5.2 * len(modes), 3.5),
                             squeeze=False, sharey=True)
    for a, mode in zip(axes[0], modes):
        d = df[df["mode"] == mode]
        for m in sorted(d["method"].unique()):
            for col, ls, lbl in ((f"ari_{criterion}", "-", "selected k"),
                                 ("ari_oracle_k", "--", "oracle k")):
                s = summarize(d[d["method"] == m], col)
                g = s.sort_values("n_frames")
                a.plot(g["n_frames"], g["mean"], ls, color=PALETTE.get(m),
                       ms=3.5, marker="o" if ls == "-" else "s",
                       label=f"{LABEL.get(m, m)} ({lbl})")
                a.fill_between(g["n_frames"], g["ci_lo"], g["ci_hi"],
                               color=PALETTE.get(m), alpha=0.12, lw=0)
        a.set_xscale("log")
        a.set_xlabel("sampling budget (saved frames)")
        a.set_title(mode)
        a.set_ylim(-0.05, 1.02)
    axes[0][0].set_ylabel("ARI vs ground-truth basins")
    axes[0][-1].legend(fontsize=7, ncol=2)

    note = ("degenerate conditions excluded" if drop_degenerate
            else "all conditions")
    fig.suptitle("Recovery peaks at an intermediate budget, then declines",
                 y=1.03)
    fig.text(0.5, -0.04, f"{note}: {n_dropped} of {n_before} rows removed",
             ha="center", fontsize=7, color="#555555")
    _save(fig, outdir, "fig5_recovery")
    print(f"  [fig5] dropped {n_dropped}/{n_before} degenerate rows")


def fig6_coverage(df, outdir="figures", criterion="bic"):
    """The control: budget trend with and without coverage matching."""
    t = budget_trend(df, f"k_{criterion}")
    if t.empty:
        print("  [skip] fig6: not enough conditions")
        return
    methods = sorted(t["method"].unique())
    modes = sorted(t["mode"].unique())
    x = np.arange(len(methods))
    w = 0.8 / max(1, len(modes))

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for i, mode in enumerate(modes):
        sub = t[t["mode"] == mode].set_index("method").reindex(methods)
        err = np.vstack([
            (sub["spearman_rho"] - sub["rho_ci_lo"]).values,
            (sub["rho_ci_hi"] - sub["spearman_rho"]).values,
        ])
        ax.bar(x + i * w - 0.4 + w / 2, sub["spearman_rho"].values, w,
               yerr=np.abs(err), capsize=3,
               label={"short": "short trajectories",
                      "subsample": "coverage-matched"}.get(mode, mode),
               color="#444444" if mode == "short" else "#999999")
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([LABEL.get(m, m) for m in methods])
    ax.set_ylabel(r"Spearman $\rho$(log frames, reported $k$)")
    ax.legend()
    ax.set_title("Does matching landscape coverage remove the effect?")
    _save(fig, outdir, "fig6_coverage")


def make_all(results_csv="results/sweep.csv", outdir="figures",
             potential="mueller_brown"):
    print("[figures] ground truth + embeddings")
    fig1_landscape(outdir, potential=potential)
    fig2_embedding_grid(outdir, potential=potential)
    if os.path.exists(results_csv):
        df = pd.read_csv(results_csv)
        print("[figures] results panels")
        fig3_state_inflation(df, outdir, "bic")
        fig3_state_inflation(df, outdir, "icl")
        fig4_criteria(df, outdir)
        fig5_recovery(df, outdir)
        fig6_coverage(df, outdir)
    else:
        print(f"[figures] no results at {results_csv}; ran ground-truth only")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/sweep.csv")
    ap.add_argument("--outdir", default="figures")
    ap.add_argument("--potential", default="mueller_brown")
    a = ap.parse_args()
    make_all(a.results, a.outdir, a.potential)
