import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))

from analyze import paired_mode_difference


def test_paired_mode_difference_recovers_direction():
    rows = []
    budgets = [100, 200, 400, 800]
    for seed in range(6):
        for mode in ("short", "subsample"):
            for i, n in enumerate(budgets):
                # short rises, subsample falls; the paired delta must be negative
                value = i if mode == "short" else -i
                rows.append({"seed": seed, "mode": mode, "method": "pca",
                             "n_frames": n, "k_bic": value})
    out = paired_mode_difference(pd.DataFrame(rows), n_boot=200, seed=7)
    assert len(out) == 1
    assert np.isclose(out.loc[0, "delta_rho"], -2.0)
    assert out.loc[0, "delta_ci_hi"] < 0


def test_paired_mode_difference_requires_both_modes():
    df = pd.DataFrame({
        "seed": [0, 1, 2], "mode": ["short"] * 3,
        "method": ["pca"] * 3, "n_frames": [100, 200, 400],
        "k_bic": [1, 2, 3],
    })
    assert paired_mode_difference(df, n_boot=20).empty
