"""
Apply the coverage-artifact filter to Fig. 5.

Adds a `drop_degenerate` option to fig5_recovery so the plotted curve matches
the cleaned numbers in the results text. Without this the figure still shows
conditions in which fewer basins were visited than exist -- rows whose ARI is
not interpretable -- while the prose reports the cleaned values, and a referee
comparing the two would find them inconsistent.

Run from the repository root:
    python patch_fig5.py
    python src/figures.py --results results/sweep.csv --outdir figures
    python src/figures.py --results results/sweep_prinz.csv \\
        --outdir figures_prinz --potential prinz1d
"""

import os
import re

TARGET = os.path.join("src", "figures.py")

OLD_SIG = 'def fig5_recovery(df, outdir="figures", criterion="bic"):'

NEW_FUNC = '''def fig5_recovery(df, outdir="figures", criterion="bic",
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
'''


def main():
    if not os.path.exists(TARGET):
        raise SystemExit(
            f"{TARGET} not found. Run this from the repository root "
            "(the folder containing src/ and results/)."
        )

    src = open(TARGET, encoding="utf-8").read()

    if "drop_degenerate" in src:
        print("[patch] already applied, nothing to do")
        return
    if OLD_SIG not in src:
        raise SystemExit(
            "[patch] could not find fig5_recovery signature; the file may "
            "already have been edited. Patch manually."
        )

    start = src.index(OLD_SIG)
    nxt = src.index("def fig6_coverage", start)
    patched = src[:start] + NEW_FUNC + "\n\n" + src[nxt:]

    open(TARGET + ".bak", "w", encoding="utf-8").write(src)
    open(TARGET, "w", encoding="utf-8").write(patched)
    print(f"[patch] fig5_recovery updated; original saved to {TARGET}.bak")
    print("[patch] now re-run src/figures.py for both result files")


if __name__ == "__main__":
    main()
