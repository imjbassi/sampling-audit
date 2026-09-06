"""
Model-selection criteria for "how many metastable states are there?"

THIS MODULE EXISTS BECAUSE OF THE OBVIOUS REFEREE OBJECTION.

If we only used BIC, a referee would correctly say: "BIC's penalty grows like
log(n) while the likelihood gain from an extra Gaussian component grows like n,
so under model misspecification -- and a projected free energy basin is never
exactly Gaussian -- BIC selects more components as n grows. Your effect is a
known property of your criterion, not of dimensionality reduction."

That objection has to be answered with evidence, not prose. So every criterion
below is computed on every condition:

  bic        -- standard, and the one most practitioners use
  aic        -- weaker penalty; if the effect were purely a penalty-strength
                artifact, AIC and BIC should order the methods identically
  icl        -- integrated completed likelihood: BIC plus an entropy term that
                explicitly penalises overlapping components, so it is much more
                resistant to splitting one basin into two
  silhouette -- geometry-based, likelihood-free; shares no assumptions with the
                three above
  elbow_gap  -- largest relative drop in within-cluster dispersion (k-means),
                a crude but assumption-light stand-in for reading the plot by eye

The paper's claim is only as strong as its weakest criterion. If the trend
survives ICL and silhouette, it is not a BIC artifact.
"""

import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def _fit_gmms(Z, k_range, seed=0, n_init=5):
    fits = {}
    n = Z.shape[0]
    for k in k_range:
        if k >= n:
            continue
        try:
            gm = GaussianMixture(
                n_components=k, covariance_type="full",
                random_state=seed, n_init=n_init, reg_covar=1e-6,
            ).fit(Z)
        except Exception:
            continue
        fits[k] = gm
    return fits


def _icl(gm, Z):
    """BIC plus the mean-entropy penalty on the responsibility matrix."""
    resp = gm.predict_proba(Z)
    resp = np.clip(resp, 1e-12, 1.0)
    entropy = -np.sum(resp * np.log(resp))
    return gm.bic(Z) + 2.0 * entropy


def all_criteria(Z, k_range=range(1, 16), seed=0, n_init=5):
    """
    Returns (selections, labels, curves).

    selections : {criterion_name: k_selected}
    labels     : {criterion_name: cluster labels at that k}
    curves     : {criterion_name: {k: score}}
    """
    Z = np.asarray(Z, dtype=float)
    empty = ({}, {}, {})
    if Z.ndim != 2 or not np.all(np.isfinite(Z)) or Z.shape[0] < 4:
        return empty

    k_range = [k for k in k_range if k < Z.shape[0]]
    fits = _fit_gmms(Z, k_range, seed=seed, n_init=n_init)
    if not fits:
        return empty

    curves = {"bic": {}, "aic": {}, "icl": {}, "silhouette": {}, "elbow_gap": {}}
    labels_by_k = {}

    for k, gm in fits.items():
        lab = gm.predict(Z)
        labels_by_k[k] = lab
        curves["bic"][k] = float(gm.bic(Z))
        curves["aic"][k] = float(gm.aic(Z))
        curves["icl"][k] = float(_icl(gm, Z))
        if k >= 2 and len(np.unique(lab)) > 1:
            try:
                curves["silhouette"][k] = float(silhouette_score(Z, lab))
            except Exception:
                pass

    # k-means inertia curve for the elbow heuristic
    inertias = {}
    for k in k_range:
        if k >= Z.shape[0]:
            continue
        try:
            km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(Z)
            inertias[k] = float(km.inertia_)
        except Exception:
            continue
    ks = sorted(inertias)
    for i in range(1, len(ks)):
        prev, cur = inertias[ks[i - 1]], inertias[ks[i]]
        curves["elbow_gap"][ks[i]] = (prev - cur) / prev if prev > 0 else 0.0

    selections, labels = {}, {}
    for crit in ("bic", "aic", "icl"):
        if curves[crit]:
            k = min(curves[crit], key=curves[crit].get)   # minimise
            selections[crit] = k
            labels[crit] = labels_by_k.get(k)
    for crit in ("silhouette", "elbow_gap"):
        if curves[crit]:
            k = max(curves[crit], key=curves[crit].get)   # maximise
            selections[crit] = k
            labels[crit] = labels_by_k.get(k)

    return selections, labels, curves


CRITERIA = ["bic", "aic", "icl", "silhouette", "elbow_gap"]
