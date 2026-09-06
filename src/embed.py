"""
The dimensionality reduction methods under audit.

All embedders share one interface:
    embedder.fit_transform(X, lag=...) -> Z of shape (n, n_components)

PCA   -- variance-maximising linear projection (sklearn).
TICA  -- time-lagged independent component analysis; the field's default
         "principled" choice because it targets slow processes rather than
         large-amplitude ones. Implemented here directly so its regularisation
         is explicit and auditable rather than buried in a library default.
VAE   -- small MLP variational autoencoder in torch, the representative
         nonlinear/deep method.

Note on t-SNE/UMAP: deliberately NOT part of the core claim. Their apparent
cluster count is governed largely by perplexity / n_neighbors rather than by
data structure, so treating recovered cluster count as a property of the data
would be unsound. They are included only in the descriptive appendix figure.
"""

import numpy as np
from sklearn.decomposition import PCA as _SkPCA
import scipy.linalg


class PCAEmbedder:
    name = "pca"
    needs_time = False

    def __init__(self, n_components=2, seed=0):
        self.n_components = n_components
        self.seed = seed

    def fit_transform(self, X, lag=None):
        n_comp = min(self.n_components, X.shape[1], X.shape[0])
        model = _SkPCA(n_components=n_comp, random_state=self.seed)
        return model.fit_transform(X)


class TICAEmbedder:
    """
    Solve the generalised eigenproblem  C_tau v = lambda C_0 v
    with C_0 the instantaneous covariance and C_tau the symmetrised
    time-lagged covariance at lag tau.
    """

    name = "tica"
    needs_time = True

    def __init__(self, n_components=2, lag=10, reg=1e-6, seed=0):
        self.n_components = n_components
        self.lag = lag
        self.reg = reg
        self.seed = seed

    def fit_transform(self, X, lag=None):
        tau = int(lag if lag is not None else self.lag)
        n = X.shape[0]
        if n <= tau + 2:
            # not enough frames to form a lagged pair set at this lag
            return np.full((n, self.n_components), np.nan)

        Xm = X - X.mean(axis=0, keepdims=True)
        A = Xm[:-tau]
        B = Xm[tau:]
        m = A.shape[0]

        C0 = (A.T @ A + B.T @ B) / (2.0 * m)
        Ctau = (A.T @ B + B.T @ A) / (2.0 * m)

        C0 = C0 + self.reg * np.eye(C0.shape[0])

        try:
            vals, vecs = scipy.linalg.eigh(Ctau, C0)
        except np.linalg.LinAlgError:
            return np.full((n, self.n_components), np.nan)

        order = np.argsort(vals)[::-1]
        vecs = vecs[:, order][:, : self.n_components]
        return Xm @ vecs


class VAEEmbedder:
    """
    Small MLP VAE. Latent mean is used as the embedding.

    Architecture and training budget are held fixed across every sampling
    condition. That is a deliberate design choice: if we tuned epochs or
    capacity per condition we would confound the sampling-budget effect we are
    trying to isolate with a model-capacity effect.
    """

    name = "vae"
    needs_time = False

    def __init__(self, n_components=2, hidden=64, epochs=200, batch_size=256,
                 lr=1e-3, seed=0, beta=1.0, device=None, fixed_steps=None):
        self.n_components = n_components
        self.hidden = hidden
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.seed = seed
        self.beta = beta
        self.device = device
        # If set, train for a FIXED number of gradient steps regardless of
        # dataset size. Without this, a fixed epoch count silently gives large
        # datasets more optimisation than small ones, which would confound
        # "more data" with "more training" -- the exact kind of nuisance
        # variable this paper is about.
        self.fixed_steps = fixed_steps
        self.history = []

    def fit_transform(self, X, lag=None):
        import torch
        import torch.nn as nn

        dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        Xn = (X - X.mean(axis=0, keepdims=True)) / (X.std(axis=0, keepdims=True) + 1e-8)
        Xt = torch.tensor(Xn, dtype=torch.float32, device=dev)
        D = Xt.shape[1]
        L = self.n_components

        # kept flat rather than wrapped in a Module subclass so that every
        # layer and the exact loss are visible to a reviewer at a glance
        enc = nn.Sequential(
            nn.Linear(D, self.hidden), nn.ReLU(),
            nn.Linear(self.hidden, self.hidden), nn.ReLU(),
        ).to(dev)
        to_mu = nn.Linear(self.hidden, L).to(dev)
        to_logvar = nn.Linear(self.hidden, L).to(dev)
        dec = nn.Sequential(
            nn.Linear(L, self.hidden), nn.ReLU(),
            nn.Linear(self.hidden, self.hidden), nn.ReLU(),
            nn.Linear(self.hidden, D),
        ).to(dev)

        params = (list(enc.parameters()) + list(to_mu.parameters())
                  + list(to_logvar.parameters()) + list(dec.parameters()))
        opt = torch.optim.Adam(params, lr=self.lr)

        n = Xt.shape[0]
        bs = min(self.batch_size, n)
        self.history = []

        steps_per_epoch = max(1, int(np.ceil(n / bs)))
        n_epochs = (int(np.ceil(self.fixed_steps / steps_per_epoch))
                    if self.fixed_steps else self.epochs)

        for ep in range(n_epochs):
            perm = torch.randperm(n, device=dev)
            tot = 0.0
            for i in range(0, n, bs):
                idx = perm[i:i + bs]
                xb = Xt[idx]
                h = enc(xb)
                mu = to_mu(h)
                logvar = to_logvar(h).clamp(-10, 10)
                std = torch.exp(0.5 * logvar)
                z = mu + std * torch.randn_like(std)
                xr = dec(z)
                rec = ((xr - xb) ** 2).sum(dim=1).mean()
                kld = (-0.5 * (1 + logvar - mu ** 2 - logvar.exp()).sum(dim=1)).mean()
                loss = rec + self.beta * kld
                opt.zero_grad()
                loss.backward()
                opt.step()
                tot += float(loss.detach()) * xb.shape[0]
            self.history.append(tot / n)

        with torch.no_grad():
            Z = to_mu(enc(Xt)).cpu().numpy()
        return Z


class TSNEEmbedder:
    """Descriptive only -- see module docstring. Not part of the core claim."""

    name = "tsne"
    needs_time = False

    def __init__(self, n_components=2, perplexity=30, seed=0):
        self.n_components = n_components
        self.perplexity = perplexity
        self.seed = seed

    def fit_transform(self, X, lag=None):
        from sklearn.manifold import TSNE
        perp = min(self.perplexity, max(5, (X.shape[0] - 1) // 3))
        model = TSNE(n_components=self.n_components, perplexity=perp,
                     random_state=self.seed, init="pca")
        return model.fit_transform(X)


EMBEDDERS = {
    "pca": PCAEmbedder,
    "tica": TICAEmbedder,
    "vae": VAEEmbedder,
    "tsne": TSNEEmbedder,
}


def get_embedder(name, **kwargs):
    if name not in EMBEDDERS:
        raise KeyError(f"unknown embedder {name!r}; have {list(EMBEDDERS)}")
    return EMBEDDERS[name](**kwargs)
