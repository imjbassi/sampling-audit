"""
Aggregation and inference over the sweep output.

Design notes that matter for defensibility:

* Everything is reported with bootstrap confidence intervals over SEEDS, not
  over frames. Frames within a trajectory are strongly autocorrelated, so a
  bootstrap over frames would produce intervals that are far too narrow. The
  seed is the independent replicate.

* The headline effect is quantified as a Spearman rank correlation between
  log(n_frames) and k_selected, computed per (mode, method, criterion). Rank
  correlation rather than a slope because we are claiming monotone inflation,
  not a particular functional form.

* Seed count is reported alongside every estimate. A result that only appears
  at low seed count and dissolves under seed expansion is not a result -- that
  lesson is applied here by default rather than discovered later.
"""

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_ci(values, n_boot=10000, alpha=0.05, seed=0, stat=np.mean):
    v = np.asarray([x for x in values if x == x], dtype=float)
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    if len(v) == 1:
        return float(v[0]), np.nan, np.nan
    rng = np.random.default_rng(seed)
    boots = stat(rng.choice(v, size=(n_boot, len(v)), replace=True), axis=1)
    return float(stat(v)), float(np.percentile(boots, 100 * alpha / 2)), float(
        np.percentile(boots, 100 * (1 - alpha / 2))
    )


def summarize(df, value_col, group_cols=("mode", "method", "n_frames"),
              n_boot=10000, seed=0):
    """Mean + bootstrap CI of `value_col` within each group."""
    out = []
    for keys, g in df.groupby(list(group_cols)):
        if not isinstance(keys, tuple):
            keys = (keys,)
        m, lo, hi = bootstrap_ci(g[value_col].values, n_boot=n_boot, seed=seed)
        rec = dict(zip(group_cols, keys))
        rec.update({
            "mean": m, "ci_lo": lo, "ci_hi": hi,
            "n_seeds": int(g[value_col].notna().sum()),
        })
        out.append(rec)
    return pd.DataFrame(out).sort_values(list(group_cols)).reset_index(drop=True)


def budget_trend(df, value_col, group_cols=("mode", "method")):
    """
    Spearman correlation between log(n_frames) and `value_col`.

    This is the number the abstract quotes. Positive rho with a CI excluding
    zero means: the pipeline reports more states as you give it more data,
    while the underlying landscape never changed.
    """
    rows = []
    for keys, g in df.groupby(list(group_cols)):
        if not isinstance(keys, tuple):
            keys = (keys,)
        g = g.dropna(subset=[value_col, "n_frames"])
        if len(g) < 6 or g["n_frames"].nunique() < 3:
            continue
        rho, p = stats.spearmanr(np.log(g["n_frames"]), g[value_col])

        # bootstrap the correlation over seeds so the CI respects the
        # replicate structure rather than treating every row as independent
        seeds = g["seed"].unique()
        rng = np.random.default_rng(0)
        boots = []
        for _ in range(2000):
            pick = rng.choice(seeds, size=len(seeds), replace=True)
            sub = pd.concat([g[g.seed == s] for s in pick])
            if sub["n_frames"].nunique() < 3:
                continue
            r, _ = stats.spearmanr(np.log(sub["n_frames"]), sub[value_col])
            if r == r:
                boots.append(r)

        rec = dict(zip(group_cols, keys))
        rec.update({
            "metric": value_col,
            "spearman_rho": float(rho),
            "p_value": float(p),
            "rho_ci_lo": float(np.percentile(boots, 2.5)) if boots else np.nan,
            "rho_ci_hi": float(np.percentile(boots, 97.5)) if boots else np.nan,
            "n_obs": int(len(g)),
            "n_seeds": int(g["seed"].nunique()),
        })
        rows.append(rec)
    return pd.DataFrame(rows)


def coverage_control(df, value_col="k_bic"):
    """
    The key contrast: does the budget trend survive when landscape coverage is
    held fixed?

    Returns one row per method with the trend under each mode side by side.
    If `subsample` rho is close to `short` rho, exploration deficit is not the
    explanation and the effect lives in the estimator.
    """
    t = budget_trend(df, value_col)
    if t.empty:
        return t
    piv = t.pivot_table(index="method", columns="mode",
                        values=["spearman_rho", "rho_ci_lo", "rho_ci_hi"])
    piv.columns = ["_".join(c) for c in piv.columns]
    return piv.reset_index()


def ceiling_report(df, kmax=15):
    """
    How often did the selection criterion hit the search ceiling?

    A high rate means k_selected is right-censored and the true inflation is
    UNDERSTATED. This has to be disclosed, not buried -- it is the difference
    between "selects 15 states" and "selects at least 15 states".
    """
    rows = []
    for crit in ["bic", "aic", "icl", "silhouette", "elbow_gap"]:
        col = f"k_{crit}"
        if col not in df:
            continue
        for keys, g in df.groupby(["mode", "method"]):
            rate = float((g[col] >= kmax).mean())
            rows.append({"criterion": crit, "mode": keys[0], "method": keys[1],
                         "ceiling_rate": rate, "n": len(g)})
    return pd.DataFrame(rows)


def load(path):
    df = pd.read_csv(path)
    for c in df.columns:
        if c.startswith(("k_", "ari_", "nmi_")):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df
