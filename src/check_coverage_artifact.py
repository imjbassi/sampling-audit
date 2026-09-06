"""
Check for the degenerate-coverage artifact before trusting Fig. 5.

THE PROBLEM

When a trajectory visits only one true basin, the ground-truth label vector is
constant. Any clustering that returns a single cluster then scores ARI = 1.0 --
not because it recovered the landscape, but because there was only one thing to
recover. Those rows are meaningless and, if they sit at the small-budget end,
they inflate the left side of the recovery curve and make the
degradation-with-data effect look steeper than it is.

WHAT THIS PRINTS

  1. how many conditions have k_visited < k_true, broken down by budget
  2. mean ARI on those rows vs the rest, to size the distortion
  3. the recovery curve recomputed with degenerate rows dropped

If (3) still shows recovery falling with budget, the effect is real and the
artifact only affected its apparent magnitude. If (3) flattens the curve, the
headline claim has to be restated.

USAGE
    python src/check_coverage_artifact.py --results results/sweep.csv
    python src/check_coverage_artifact.py --results results/sweep_prinz.csv
"""

import argparse

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/sweep.csv")
    ap.add_argument("--criterion", default="bic")
    args = ap.parse_args()

    df = pd.read_csv(args.results)
    ari = f"ari_{args.criterion}"
    k_true = int(df["k_true"].iloc[0])

    df["degenerate"] = df["k_visited"] < k_true

    print(f"=== {args.results} (true k = {k_true}) ===\n")

    print("1. Degenerate conditions (fewer basins visited than exist)\n")
    tab = (df.groupby(["mode", "n_frames"])["degenerate"]
             .agg(["sum", "count"]))
    tab["rate"] = (tab["sum"] / tab["count"]).round(3)
    print(tab.to_string(), "\n")

    print("2. Do degenerate rows score spuriously high ARI?\n")
    cmp = df.groupby("degenerate")[ari].agg(["mean", "median", "count"]).round(3)
    print(cmp.to_string())
    n_perfect = int((df[ari] > 0.999).sum())
    n_perfect_deg = int(((df[ari] > 0.999) & df["degenerate"]).sum())
    print(f"\n   ARI > 0.999 rows: {n_perfect} total, "
          f"{n_perfect_deg} of them degenerate\n")

    print("3. Recovery curve with degenerate rows dropped\n")
    clean = df[~df["degenerate"]]
    for mode in sorted(df["mode"].unique()):
        print(f"   --- {mode} ---")
        for m in sorted(df["method"].unique()):
            raw = (df[(df["mode"] == mode) & (df["method"] == m)]
                   .groupby("n_frames")[ari].mean())
            cln = (clean[(clean["mode"] == mode) & (clean["method"] == m)]
                   .groupby("n_frames")[ari].mean())
            print(f"   {m:<5} raw  : "
                  + "  ".join(f"{n}:{v:.2f}" for n, v in raw.items()))
            print(f"   {m:<5} clean: "
                  + "  ".join(f"{n}:{v:.2f}" for n, v in cln.items()))
            if len(cln) >= 2:
                delta = cln.iloc[-1] - cln.max()
                print(f"   {m:<5} peak {cln.max():.2f} at n={cln.idxmax()}, "
                      f"final {cln.iloc[-1]:.2f}, drop {delta:+.2f}")
            print()

    print("4. Rarest-basin occupancy (how marginal is 'visited'?)\n")
    if "min_basin_frac" in df.columns:
        occ = (df.groupby(["mode", "n_frames"])["min_basin_frac"]
                 .mean().round(4))
        print(occ.to_string())
        thin = int((df["min_basin_frac"] < 0.01).sum())
        print(f"\n   conditions where rarest basin holds <1% of frames: "
              f"{thin} / {len(df)}")
        print("   (a basin present at 0.3% is 'visited' but cannot support a "
              "cluster;\n    consider a stricter occupancy threshold than "
              "k_visited alone)")


if __name__ == "__main__":
    main()
