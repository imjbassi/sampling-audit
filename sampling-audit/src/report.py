"""
Generate the paper's tables directly from the sweep output.

Nothing in the paper should be a number typed by hand. Every table here is
regenerated from results/sweep.csv, so a re-run with more seeds updates the
manuscript rather than silently disagreeing with it.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze import budget_trend, summarize, ceiling_report  # noqa: E402
from selection import CRITERIA                               # noqa: E402


def table_budget_trend(df):
    """Table 1: does reported state count track sampling budget?"""
    parts = []
    for crit in CRITERIA:
        col = f"k_{crit}"
        if col not in df.columns:
            continue
        t = budget_trend(df, col)
        if t.empty:
            continue
        t["criterion"] = crit
        parts.append(t)
    if not parts:
        return pd.DataFrame()
    t = pd.concat(parts, ignore_index=True)
    t["rho [95% CI]"] = t.apply(
        lambda r: f"{r.spearman_rho:+.2f} [{r.rho_ci_lo:+.2f}, {r.rho_ci_hi:+.2f}]",
        axis=1,
    )
    return t[["criterion", "mode", "method", "rho [95% CI]", "p_value",
              "n_seeds", "n_obs"]]


def table_endpoints(df, criterion="bic"):
    """Table 2: reported k at the smallest vs largest budget."""
    lo, hi = df["n_frames"].min(), df["n_frames"].max()
    s = summarize(df, f"k_{criterion}")
    a = s[s["n_frames"] == lo].set_index(["mode", "method"])
    b = s[s["n_frames"] == hi].set_index(["mode", "method"])
    out = pd.DataFrame({
        f"k @ n={lo}": a.apply(
            lambda r: f"{r['mean']:.1f} [{r['ci_lo']:.1f}, {r['ci_hi']:.1f}]",
            axis=1),
        f"k @ n={hi}": b.apply(
            lambda r: f"{r['mean']:.1f} [{r['ci_lo']:.1f}, {r['ci_hi']:.1f}]",
            axis=1),
        "k_true": int(df["k_true"].iloc[0]),
    })
    return out.reset_index()


def table_recovery(df, criterion="bic"):
    """Table 3: cost of selecting k, isolated from the projection itself."""
    rows = []
    for (mode, method), g in df.groupby(["mode", "method"]):
        hi = g[g["n_frames"] == g["n_frames"].max()]
        rows.append({
            "mode": mode, "method": method,
            "ARI (selected k)": f"{hi[f'ari_{criterion}'].mean():.3f}",
            "ARI (oracle k)": f"{hi['ari_oracle_k'].mean():.3f}",
            "gap": f"{hi['ari_oracle_k'].mean() - hi[f'ari_{criterion}'].mean():+.3f}",
            "n_seeds": hi["seed"].nunique(),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/sweep.csv")
    ap.add_argument("--out", default="results/tables.md")
    ap.add_argument("--kmax", type=int, default=15)
    args = ap.parse_args()

    df = pd.read_csv(args.results)
    lines = ["# Generated tables", "",
             f"Source: `{args.results}`  ",
             f"Conditions: {len(df)}  |  seeds: {df['seed'].nunique()}  |  "
             f"budgets: {sorted(df['n_frames'].unique())}", ""]

    lines += ["## Table 1 — Budget trend in reported state count", "",
              table_budget_trend(df).to_markdown(index=False), ""]
    lines += ["## Table 2 — Reported k at budget endpoints (BIC)", "",
              table_endpoints(df).to_markdown(index=False), ""]
    lines += ["## Table 3 — Recovery: selected k vs oracle k", "",
              table_recovery(df).to_markdown(index=False), ""]

    cr = ceiling_report(df, kmax=args.kmax)
    lines += ["## Table 4 — Search-ceiling hit rate (disclosure)", "",
              "A non-zero rate means reported k is right-censored at kmax and "
              "the inflation is *understated*.", "",
              cr.to_markdown(index=False), ""]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(lines))
    print(f"[report] wrote {args.out}")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
