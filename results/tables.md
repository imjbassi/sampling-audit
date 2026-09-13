# Generated tables

Source: `results/sweep.csv`  
Conditions: 960  |  seeds: 20  |  budgets: [np.int64(250), np.int64(500), np.int64(1000), np.int64(2000), np.int64(4000), np.int64(8000), np.int64(16000), np.int64(32000)]

## Table 1 — Budget trend in reported state count

| criterion   | mode      | method   | rho [95% CI]         |   n_seeds |   n_obs |
|:------------|:----------|:---------|:---------------------|----------:|--------:|
| bic         | short     | pca      | +0.88 [+0.85, +0.91] |        20 |     160 |
| bic         | short     | tica     | +0.94 [+0.93, +0.96] |        20 |     160 |
| bic         | short     | vae      | +0.92 [+0.91, +0.94] |        20 |     160 |
| bic         | subsample | pca      | +0.88 [+0.85, +0.91] |        20 |     160 |
| bic         | subsample | tica     | +0.96 [+0.95, +0.97] |        20 |     160 |
| bic         | subsample | vae      | +0.93 [+0.92, +0.94] |        20 |     160 |
| aic         | short     | pca      | +0.61 [+0.52, +0.70] |        20 |     160 |
| aic         | short     | tica     | +0.71 [+0.60, +0.81] |        20 |     160 |
| aic         | short     | vae      | +0.75 [+0.67, +0.82] |        20 |     160 |
| aic         | subsample | pca      | +0.31 [+0.20, +0.43] |        20 |     160 |
| aic         | subsample | tica     | +0.67 [+0.55, +0.78] |        20 |     160 |
| aic         | subsample | vae      | +0.64 [+0.53, +0.73] |        20 |     160 |
| icl         | short     | pca      | +0.58 [+0.43, +0.72] |        20 |     160 |
| icl         | short     | tica     | +0.74 [+0.67, +0.82] |        20 |     160 |
| icl         | short     | vae      | +0.41 [+0.27, +0.55] |        20 |     160 |
| icl         | subsample | pca      | +0.34 [+0.16, +0.52] |        20 |     160 |
| icl         | subsample | tica     | +0.92 [+0.89, +0.94] |        20 |     160 |
| icl         | subsample | vae      | +0.28 [+0.12, +0.45] |        20 |     160 |
| silhouette  | short     | pca      | -0.26 [-0.36, -0.14] |        20 |     160 |
| silhouette  | short     | tica     | +0.14 [-0.02, +0.31] |        20 |     160 |
| silhouette  | short     | vae      | -0.52 [-0.62, -0.42] |        20 |     160 |
| silhouette  | subsample | pca      | +nan [+nan, +nan]    |        20 |     160 |
| silhouette  | subsample | tica     | +0.30 [+0.11, +0.48] |        20 |     160 |
| silhouette  | subsample | vae      | +0.03 [-0.10, +0.14] |        20 |     160 |
| elbow_gap   | short     | pca      | +0.03 [-0.09, +0.16] |        20 |     160 |
| elbow_gap   | short     | tica     | +0.37 [+0.28, +0.46] |        20 |     160 |
| elbow_gap   | short     | vae      | +0.46 [+0.31, +0.60] |        20 |     160 |
| elbow_gap   | subsample | pca      | +0.00 [+0.00, +0.00] |        20 |     160 |
| elbow_gap   | subsample | tica     | +0.54 [+0.44, +0.63] |        20 |     160 |
| elbow_gap   | subsample | vae      | -0.03 [-0.18, +0.11] |        20 |     160 |

## Table 2 — Reported k at budget endpoints (BIC)

| mode      | method   | k @ n=250      | k @ n=32000       |   k_true |
|:----------|:---------|:---------------|:------------------|---------:|
| short     | pca      | 2.6 [1.9, 3.5] | 14.8 [14.6, 14.9] |        3 |
| short     | tica     | 1.3 [1.1, 1.5] | 12.7 [12.1, 13.2] |        3 |
| short     | vae      | 1.0 [1.0, 1.0] | 12.6 [11.6, 13.4] |        3 |
| subsample | pca      | 6.3 [6.0, 6.6] | 14.8 [14.7, 15.0] |        3 |
| subsample | tica     | 1.3 [1.1, 1.5] | 13.2 [12.5, 13.8] |        3 |
| subsample | vae      | 1.8 [1.6, 1.9] | 11.9 [10.9, 12.9] |        3 |

## Table 3 — Recovery: selected k vs oracle k

| mode      | method   |   ARI (selected k) |   ARI (oracle k) |   gap |   n_seeds |
|:----------|:---------|-------------------:|-----------------:|------:|----------:|
| short     | pca      |              0.102 |            0.415 | 0.314 |        20 |
| short     | tica     |              0.342 |            0.847 | 0.505 |        20 |
| short     | vae      |              0.111 |            0.423 | 0.311 |        20 |
| subsample | pca      |              0.109 |            0.412 | 0.302 |        20 |
| subsample | tica     |              0.36  |            0.856 | 0.496 |        20 |
| subsample | vae      |              0.129 |            0.437 | 0.308 |        20 |

## Table 4 — Search-ceiling hit rate (disclosure)

A non-zero rate means reported k is right-censored at kmax and the inflation is *understated*.

| criterion   | mode      | method   |   ceiling_rate |   n |
|:------------|:----------|:---------|---------------:|----:|
| bic         | short     | pca      |        0.4375  | 160 |
| bic         | short     | tica     |        0.0125  | 160 |
| bic         | short     | vae      |        0.0375  | 160 |
| bic         | subsample | pca      |        0.41875 | 160 |
| bic         | subsample | tica     |        0.03125 | 160 |
| bic         | subsample | vae      |        0.025   | 160 |
| aic         | short     | pca      |        0.65625 | 160 |
| aic         | short     | tica     |        0.26875 | 160 |
| aic         | short     | vae      |        0.24375 | 160 |
| aic         | subsample | pca      |        0.8375  | 160 |
| aic         | subsample | tica     |        0.25    | 160 |
| aic         | subsample | vae      |        0.275   | 160 |
| icl         | short     | pca      |        0       | 160 |
| icl         | short     | tica     |        0       | 160 |
| icl         | short     | vae      |        0       | 160 |
| icl         | subsample | pca      |        0       | 160 |
| icl         | subsample | tica     |        0       | 160 |
| icl         | subsample | vae      |        0       | 160 |
| silhouette  | short     | pca      |        0       | 160 |
| silhouette  | short     | tica     |        0.00625 | 160 |
| silhouette  | short     | vae      |        0.01875 | 160 |
| silhouette  | subsample | pca      |        0       | 160 |
| silhouette  | subsample | tica     |        0.00625 | 160 |
| silhouette  | subsample | vae      |        0       | 160 |
| elbow_gap   | short     | pca      |        0       | 160 |
| elbow_gap   | short     | tica     |        0       | 160 |
| elbow_gap   | short     | vae      |        0       | 160 |
| elbow_gap   | subsample | pca      |        0       | 160 |
| elbow_gap   | subsample | tica     |        0       | 160 |
| elbow_gap   | subsample | vae      |        0       | 160 |

## Table 5 — Paired coverage-mode contrast

Delta is rho(subsample) minus rho(short), bootstrapped over matched seeds.

| method   | metric   |   delta_rho |   delta_ci_lo |   delta_ci_hi |   n_seeds |
|:---------|:---------|------------:|--------------:|--------------:|----------:|
| pca      | k_bic    |  0.00188444 |   -0.0370229  |     0.038683  |        20 |
| tica     | k_bic    |  0.0166173  |    0.00405419 |     0.030138  |        20 |
| vae      | k_bic    |  0.0069208  |   -0.0137876  |     0.0270798 |        20 |
