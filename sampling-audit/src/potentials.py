"""
Ground-truth potentials with analytically known metastable states.

The whole point of this project is that we need a system where the true number
of basins, their locations, and their relative populations are known by
construction -- not inferred by the same class of method we are auditing.

Two systems:
  Prinz1D   -- the standard 4-well 1D potential from Prinz et al. (2011),
               used throughout the MSM literature as a validation system.
  MullerBrown -- the standard 2D 3-basin potential.

Both expose:
  potential(x)      -> energy
  gradient(x)       -> dV/dx
  assign_basin(x)   -> integer basin label (ground truth)
  n_states          -> true number of metastable states
"""

import numpy as np


class Potential:
    """Base class. Subclasses define potential/gradient/assign_basin."""

    name = "base"
    dim = 1
    n_states = 0

    def potential(self, x):
        raise NotImplementedError

    def gradient(self, x):
        raise NotImplementedError

    def assign_basin(self, x):
        raise NotImplementedError

    def grid(self, n=200):
        """Return a mesh covering the domain, for plotting free energy surfaces."""
        raise NotImplementedError


class Prinz1D(Potential):
    """
    Prinz four-well potential:
        V(x) = 4 * (x^8 + 0.8*exp(-80 x^2) + 0.2*exp(-80 (x-0.5)^2)
                    + 0.5*exp(-40 (x+0.5)^2))

    Four metastable basins on x in [-1, 1]. Basin boundaries are the barrier
    tops, located numerically once at construction so that ground-truth labels
    never depend on any fitted model.
    """

    name = "prinz1d"
    dim = 1
    n_states = 4
    domain = (-1.0, 1.0)

    def __init__(self):
        self._boundaries = self._find_boundaries()

    def potential(self, x):
        x = np.asarray(x, dtype=float)
        return 4.0 * (
            x ** 8
            + 0.8 * np.exp(-80.0 * x ** 2)
            + 0.2 * np.exp(-80.0 * (x - 0.5) ** 2)
            + 0.5 * np.exp(-40.0 * (x + 0.5) ** 2)
        )

    def gradient(self, x):
        x = np.asarray(x, dtype=float)
        return 4.0 * (
            8.0 * x ** 7
            + 0.8 * (-160.0 * x) * np.exp(-80.0 * x ** 2)
            + 0.2 * (-160.0 * (x - 0.5)) * np.exp(-80.0 * (x - 0.5) ** 2)
            + 0.5 * (-80.0 * (x + 0.5)) * np.exp(-40.0 * (x + 0.5) ** 2)
        )

    def _find_boundaries(self):
        """Locate barrier tops (local maxima) on a fine grid -> basin edges."""
        xs = np.linspace(self.domain[0], self.domain[1], 20001)
        v = self.potential(xs)
        # local maxima of V are the dividing surfaces between basins
        is_max = (v[1:-1] > v[:-2]) & (v[1:-1] > v[2:])
        maxima = xs[1:-1][is_max]
        return np.sort(maxima)

    def assign_basin(self, x):
        """Label each point by which barrier-delimited well it sits in."""
        x = np.asarray(x, dtype=float).ravel()
        return np.searchsorted(self._boundaries, x)

    def grid(self, n=400):
        return np.linspace(self.domain[0], self.domain[1], n).reshape(-1, 1)


class MullerBrown(Potential):
    """
    Müller-Brown potential, scaled. Three metastable basins.

    Ground-truth basin assignment is done by steepest-descent quenching:
    each sampled point is relaxed downhill to its nearest local minimum, and
    labelled by which of the three known minima it lands in. This is a
    physically defined assignment that does not depend on clustering.
    """

    name = "mueller_brown"
    dim = 2
    n_states = 3
    domain = ((-1.7, 1.3), (-0.4, 2.3))

    _A = np.array([-200.0, -100.0, -170.0, 15.0])
    _a = np.array([-1.0, -1.0, -6.5, 0.7])
    _b = np.array([0.0, 0.0, 11.0, 0.6])
    _c = np.array([-10.0, -10.0, -6.5, 0.7])
    _x0 = np.array([1.0, 0.0, -0.5, -1.0])
    _y0 = np.array([0.0, 0.5, 1.5, 1.0])

    # scale factor keeps barriers crossable at the temperatures we simulate
    scale = 0.05

    def __init__(self):
        self._minima = self._find_minima()

    def potential(self, xy):
        xy = np.atleast_2d(np.asarray(xy, dtype=float))
        x = xy[:, 0][:, None]
        y = xy[:, 1][:, None]
        dx = x - self._x0[None, :]
        dy = y - self._y0[None, :]
        terms = self._A[None, :] * np.exp(
            self._a[None, :] * dx ** 2
            + self._b[None, :] * dx * dy
            + self._c[None, :] * dy ** 2
        )
        return self.scale * terms.sum(axis=1)

    def gradient(self, xy):
        xy = np.atleast_2d(np.asarray(xy, dtype=float))
        x = xy[:, 0][:, None]
        y = xy[:, 1][:, None]
        dx = x - self._x0[None, :]
        dy = y - self._y0[None, :]
        e = self._A[None, :] * np.exp(
            self._a[None, :] * dx ** 2
            + self._b[None, :] * dx * dy
            + self._c[None, :] * dy ** 2
        )
        gx = (e * (2.0 * self._a[None, :] * dx + self._b[None, :] * dy)).sum(axis=1)
        gy = (e * (self._b[None, :] * dx + 2.0 * self._c[None, :] * dy)).sum(axis=1)
        return self.scale * np.stack([gx, gy], axis=1)

    def _find_minima(self):
        """Known Müller-Brown minima, refined by gradient descent."""
        seeds = np.array([[-0.558, 1.442], [0.623, 0.028], [-0.050, 0.467]])
        refined = []
        for s in seeds:
            p = s.copy().reshape(1, 2)
            for _ in range(5000):
                g = self.gradient(p)
                p = p - 1e-4 * g
            refined.append(p.ravel())
        return np.array(refined)

    def _quench(self, xy, steps=400, lr=1e-4):
        """Steepest descent to nearest local minimum."""
        p = np.array(xy, dtype=float, copy=True)
        for _ in range(steps):
            p = p - lr * self.gradient(p)
        return p

    def assign_basin(self, xy):
        xy = np.atleast_2d(np.asarray(xy, dtype=float))
        quenched = self._quench(xy)
        d = np.linalg.norm(
            quenched[:, None, :] - self._minima[None, :, :], axis=2
        )
        return np.argmin(d, axis=1)

    def grid(self, n=200):
        gx = np.linspace(self.domain[0][0], self.domain[0][1], n)
        gy = np.linspace(self.domain[1][0], self.domain[1][1], n)
        X, Y = np.meshgrid(gx, gy)
        return np.stack([X.ravel(), Y.ravel()], axis=1), X.shape


POTENTIALS = {
    "prinz1d": Prinz1D,
    "mueller_brown": MullerBrown,
}


def get_potential(name):
    if name not in POTENTIALS:
        raise KeyError(f"unknown potential {name!r}; have {list(POTENTIALS)}")
    return POTENTIALS[name]()
