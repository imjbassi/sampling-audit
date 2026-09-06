"""
Clustering of embeddings, with the number of states selected by the data
rather than fixed in advance.

This is the crux of the audit. In practice an analyst does not know the true
number of metastable states -- they read it off the projection, usually via a
model-selection criterion (BIC) or by eye. So the quantity we track is
`k_selected`: how many states the pipeline *claims* to find. If k_selected
grows with sampling budget while the true landscape is fixed, that is the
confound.

We also report metrics at k fixed to the true value, to separate "finds the
wrong number of states" from "draws the boundaries in the wrong place".
"""

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    silhouette_score,
)


def select_k_bic(Z, k_range=range(1, 11), seed=0, n_init=5):
    """
    Fit GMMs over a range of k and pick the BIC minimum.

    Returns (k_best, labels_best, bic_curve).
    """
    Z = np.asarray(Z, dtype=float)
    if not np.all(np.isfinite(Z)):
        return np.nan, None, {}

    bics = {}
    best = (np.inf, None, None)
    n = Z.shape[0]
    for k in k_range:
        if k >= n:
            continue
        try:
            gm = GaussianMixture(
                n_components=k,
                covariance_type="full",
                random_state=seed,
                n_init=n_init,
                reg_covar=1e-6,
            ).fit(Z)
        except Exception:
            continue
        b = gm.bic(Z)
        bics[k] = float(b)
        if b < best[0]:
            best = (b, k, gm.predict(Z))
    if best[1] is None:
        return np.nan, None, bics
    return best[1], best[2], bics


def cluster_fixed_k(Z, k, seed=0, method="gmm"):
    """Cluster at a prescribed k (used for the 'oracle k' control)."""
    Z = np.asarray(Z, dtype=float)
    if not np.all(np.isfinite(Z)) or Z.shape[0] <= k:
        return None
    if method == "gmm":
        gm = GaussianMixture(
            n_components=k, covariance_type="full", random_state=seed,
            n_init=5, reg_covar=1e-6,
        ).fit(Z)
        return gm.predict(Z)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(Z)
    return km.labels_


def recovery_metrics(true_labels, pred_labels, Z=None):
    """
    Agreement between recovered clustering and ground-truth basins.

    ARI is the headline: it is chance-corrected, so it does not reward a method
    simply for producing more clusters -- which matters here, because the
    failure mode we are hunting for is exactly "more clusters as data grows".
    """
    out = {"ari": np.nan, "nmi": np.nan, "silhouette": np.nan}
    if pred_labels is None:
        return out
    true_labels = np.asarray(true_labels).ravel()
    pred_labels = np.asarray(pred_labels).ravel()
    n = min(len(true_labels), len(pred_labels))
    t, p = true_labels[:n], pred_labels[:n]
    out["ari"] = float(adjusted_rand_score(t, p))
    out["nmi"] = float(normalized_mutual_info_score(t, p))
    if Z is not None and len(np.unique(p)) > 1 and np.all(np.isfinite(Z)):
        try:
            out["silhouette"] = float(silhouette_score(np.asarray(Z)[:n], p))
        except Exception:
            pass
    return out


def state_population_error(true_labels, pred_labels, n_true):
    """
    How badly are basin populations misestimated?

    Sorted-population L1 distance, so it is invariant to label permutation and
    defined even when k_pred != k_true.
    """
    if pred_labels is None:
        return np.nan
    t = np.asarray(true_labels).ravel()
    p = np.asarray(pred_labels).ravel()
    n = min(len(t), len(p))
    t, p = t[:n], p[:n]

    def pops(lab, k):
        c = np.bincount(lab, minlength=k).astype(float)
        return np.sort(c / c.sum())[::-1]

    kt = max(n_true, int(t.max()) + 1)
    kp = int(p.max()) + 1
    a = pops(t, kt)
    b = pops(p, kp)
    m = max(len(a), len(b))
    a = np.pad(a, (0, m - len(a)))
    b = np.pad(b, (0, m - len(b)))
    return float(np.abs(a - b).sum())
