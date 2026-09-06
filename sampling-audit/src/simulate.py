"""
Overdamped Langevin sampling on a known potential, plus a nonlinear lift into
high dimension.

Why the lift: on a 1D or 2D potential, dimensionality reduction is trivial and
the audit would be vacuous. Real MD hands the analyst hundreds of coordinates
that are a noisy, redundant, nonlinear function of a few slow collective
variables. We reproduce that structure explicitly: sample the true low-D
dynamics, then map it through a fixed random smooth nonlinearity into D
observed dimensions and add isotropic observation noise.

The ground-truth basin label always comes from the *latent* coordinate, so it
is never contaminated by the lift or by any fitted model.
"""

import numpy as np


def langevin(potential, n_steps, dt=1e-3, kT=1.0, gamma=1.0, x0=None, seed=0,
             stride=1, burn_in=1000):
    """
    Integrate overdamped Langevin dynamics:
        x_{t+1} = x_t - (dt/gamma) grad V(x_t) + sqrt(2 dt kT / gamma) * xi

    Returns array of shape (n_steps // stride, dim).
    """
    rng = np.random.default_rng(seed)
    dim = potential.dim

    if x0 is None:
        x = _random_start(potential, rng)
    else:
        x = np.array(x0, dtype=float).reshape(1, dim)

    noise_scale = np.sqrt(2.0 * dt * kT / gamma)

    # burn in so the initial condition does not bias short trajectories
    for _ in range(burn_in):
        g = _grad(potential, x)
        x = x - (dt / gamma) * g + noise_scale * rng.standard_normal(x.shape)
        x = _reflect(potential, x)

    out = np.empty((n_steps // stride, dim), dtype=float)
    k = 0
    for t in range(n_steps):
        g = _grad(potential, x)
        x = x - (dt / gamma) * g + noise_scale * rng.standard_normal(x.shape)
        x = _reflect(potential, x)
        if t % stride == 0 and k < out.shape[0]:
            out[k] = x.ravel()
            k += 1
    return out[:k]


def _grad(potential, x):
    g = potential.gradient(x)
    return np.atleast_2d(np.asarray(g, dtype=float)).reshape(1, potential.dim)


def _reflect(potential, x):
    """Keep the walker inside the domain with reflecting boundaries."""
    dom = potential.domain
    if potential.dim == 1:
        lo, hi = dom
        x = np.where(x < lo, 2 * lo - x, x)
        x = np.where(x > hi, 2 * hi - x, x)
    else:
        for d in range(potential.dim):
            lo, hi = dom[d]
            col = x[:, d]
            col = np.where(col < lo, 2 * lo - col, col)
            col = np.where(col > hi, 2 * hi - col, col)
            x[:, d] = col
    return x


def _random_start(potential, rng):
    dom = potential.domain
    if potential.dim == 1:
        lo, hi = dom
        return rng.uniform(lo, hi, size=(1, 1))
    return np.array(
        [[rng.uniform(dom[d][0], dom[d][1]) for d in range(potential.dim)]]
    )


class NonlinearLift:
    """
    Fixed random smooth map R^d -> R^D.

    Each observed dimension is a random Fourier feature of the latent
    coordinate: cos(w . z + phi). This is smooth, invertible in principle from
    enough features, and mixes the latent coordinates the way internal
    coordinates mix collective variables in a real molecule.

    The lift is drawn ONCE per experiment (fixed seed) and held constant across
    every sampling-budget condition, so any difference in recovered structure
    cannot be attributed to a change in the observable.
    """

    def __init__(self, latent_dim, obs_dim=30, seed=0, freq_scale=2.0,
                 noise_std=0.05):
        rng = np.random.default_rng(seed)
        self.W = rng.normal(scale=freq_scale, size=(latent_dim, obs_dim))
        self.phi = rng.uniform(0, 2 * np.pi, size=obs_dim)
        self.noise_std = noise_std
        self.obs_dim = obs_dim
        self.latent_dim = latent_dim

    def __call__(self, z, seed=0):
        z = np.atleast_2d(np.asarray(z, dtype=float))
        rng = np.random.default_rng(seed + 99991)
        feats = np.cos(z @ self.W + self.phi[None, :])
        return feats + self.noise_std * rng.standard_normal(feats.shape)


def make_dataset(potential, lift, n_frames, stride=1, dt=1e-3, kT=1.0,
                 seed=0, n_trajs=1):
    """
    Produce (X, labels, latent) for a given sampling budget.

    n_frames is the number of SAVED frames, which is the quantity an analyst
    actually controls and reports. n_trajs > 1 splits the budget across
    independent short trajectories, which is the other axis we sweep.
    """
    per_traj = max(1, n_frames // n_trajs)
    latents = []
    for j in range(n_trajs):
        z = langevin(
            potential,
            n_steps=per_traj * stride,
            dt=dt,
            kT=kT,
            seed=seed * 1000 + j,
            stride=stride,
        )
        latents.append(z)
    latent = np.concatenate(latents, axis=0)[:n_frames]
    labels = potential.assign_basin(latent)
    X = lift(latent, seed=seed)
    return X, labels, latent
