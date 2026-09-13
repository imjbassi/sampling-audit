import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "src"))

from iid_equilibrium_control import equilibrium_grid
from potentials import Prinz1D, MullerBrown


def test_equilibrium_grids_are_normalized_and_finite():
    for potential in (Prinz1D(), MullerBrown()):
        points, weights = equilibrium_grid(
            potential, points_1d=1001, points_2d=40
        )
        assert points.shape[1] == potential.dim
        assert weights.ndim == 1
        assert len(weights) == len(points)
        assert np.all(np.isfinite(weights))
        assert np.all(weights >= 0)
        assert np.isclose(weights.sum(), 1.0)
