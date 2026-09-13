# Generated tables

Source: `results/sweep_prinz.csv`  
Conditions: 960  |  seeds: 20  |  budgets: [np.int64(250), np.int64(500), np.int64(1000), np.int64(2000), np.int64(4000), np.int64(8000), np.int64(16000), np.int64(32000)]

## Table 1 — Budget trend in reported state count

| criterion   | mode      | method   | rho [95% CI]         |   n_seeds |   n_obs |
|:------------|:----------|:---------|:---------------------|----------:|--------:|
| bic         | short     | pca      | +0.95 [+0.93, +0.96] |        20 |     160 |
| bic         | short     | tica     | +0.97 [+0.97, +0.98] |        20 |     160 |
| bic         | short     | vae      | +0.93 [+0.92, +0.94] |        20 |     160 |
| bic         | subsample | pca      | +0.95 [+0.94, +0.96] |        20 |     160 |
| bic         | subsample | tica     | +0.96 [+0.95, +0.97] |        20 |     160 |
| bic         | subsample | vae      | +0.91 [+0.89, +0.93] |        20 |     160 |
| aic         | short     | pca      | +0.67 [+0.58, +0.75] |        20 |     160 |
| aic         | short     | tica     | +0.82 [+0.71, +0.90] |        20 |     160 |
| aic         | short     | vae      | +0.77 [+0.69, +0.84] |        20 |     160 |
| aic         | subsample | pca      | +0.66 [+0.58, +0.75] |        20 |     160 |
| aic         | subsample | tica     | +0.85 [+0.75, +0.93] |        20 |     160 |
| aic         | subsample | vae      | +0.74 [+0.68, +0.80] |        20 |     160 |
| icl         | short     | pca      | +0.48 [+0.32, +0.62] |        20 |     160 |
| icl         | short     | tica     | +0.91 [+0.89, +0.93] |        20 |     160 |
| icl         | short     | vae      | +0.46 [+0.35, +0.56] |        20 |     160 |
| icl         | subsample | pca      | +0.36 [+0.24, +0.48] |        20 |     160 |
| icl         | subsample | tica     | +0.93 [+0.93, +0.94] |        20 |     160 |
| icl         | subsample | vae      | +0.24 [+0.12, +0.38] |        20 |     160 |
| silhouette  | short     | pca      | +0.65 [+0.57, +0.73] |        20 |     160 |
| silhouette  | short     | tica     | +0.26 [+0.09, +0.42] |        20 |     160 |
| silhouette  | short     | vae      | +0.41 [+0.28, +0.54] |        20 |     160 |
| silhouette  | subsample | pca      | +0.12 [+0.12, +0.24] |        20 |     160 |
| silhouette  | subsample | tica     | -0.22 [-0.32, -0.11] |        20 |     160 |
| silhouette  | subsample | vae      | +0.12 [-0.07, +0.30] |        20 |     160 |
| elbow_gap   | short     | pca      | -0.48 [-0.57, -0.38] |        20 |     160 |
| elbow_gap   | short     | tica     | +0.28 [+0.16, +0.40] |        20 |     160 |
| elbow_gap   | short     | vae      | -0.05 [-0.18, +0.05] |        20 |     160 |
| elbow_gap   | subsample | pca      | -0.12 [-0.24, -0.12] |        20 |     160 |
| elbow_gap   | subsample | tica     | +0.09 [-0.01, +0.21] |        20 |     160 |
| elbow_gap   | subsample | vae      | -0.13 [-0.25, -0.01] |        20 |     160 |

## Table 2 — Reported k at budget endpoints (BIC)

| mode      | method   | k @ n=250      | k @ n=32000       |   k_true |
|:----------|:---------|:---------------|:------------------|---------:|
| short     | pca      | 6.3 [5.8, 6.8] | 14.9 [14.8, 15.0] |        4 |
| short     | tica     | 2.2 [1.9, 2.6] | 12.6 [12.2, 12.9] |        4 |
| short     | vae      | 1.6 [1.2, 1.9] | 14.1 [13.6, 14.6] |        4 |
| subsample | pca      | 7.1 [6.8, 7.5] | 14.9 [14.8, 15.0] |        4 |
| subsample | tica     | 1.0 [1.0, 1.0] | 12.5 [12.1, 12.9] |        4 |
| subsample | vae      | 2.6 [2.0, 3.3] | 13.8 [13.3, 14.3] |        4 |

## Table 3 — Recovery: selected k vs oracle k

| mode      | method   |   ARI (selected k) |   ARI (oracle k) |   gap |   n_seeds |
|:----------|:---------|-------------------:|-----------------:|------:|----------:|
| short     | pca      |              0.349 |            0.897 | 0.547 |        20 |
| short     | tica     |              0.482 |            0.815 | 0.333 |        20 |
| short     | vae      |              0.399 |            0.854 | 0.455 |        20 |
| subsample | pca      |              0.35  |            0.898 | 0.548 |        20 |
| subsample | tica     |              0.507 |            0.826 | 0.319 |        20 |
| subsample | vae      |              0.406 |            0.858 | 0.452 |        20 |

## Table 4 — Search-ceiling hit rate (disclosure)

A non-zero rate means reported k is right-censored at kmax and the inflation is *understated*.

| criterion   | mode      | method   |   ceiling_rate |   n |
|:------------|:----------|:---------|---------------:|----:|
| bic         | short     | pca      |        0.29375 | 160 |
| bic         | short     | tica     |        0       | 160 |
| bic         | short     | vae      |        0.09375 | 160 |
| bic         | subsample | pca      |        0.3     | 160 |
| bic         | subsample | tica     |        0       | 160 |
| bic         | subsample | vae      |        0.075   | 160 |
| aic         | short     | pca      |        0.61875 | 160 |
| aic         | short     | tica     |        0.19375 | 160 |
| aic         | short     | vae      |        0.36875 | 160 |
| aic         | subsample | pca      |        0.65    | 160 |
| aic         | subsample | tica     |        0.11875 | 160 |
| aic         | subsample | vae      |        0.3625  | 160 |
| icl         | short     | pca      |        0       | 160 |
| icl         | short     | tica     |        0       | 160 |
| icl         | short     | vae      |        0       | 160 |
| icl         | subsample | pca      |        0       | 160 |
| icl         | subsample | tica     |        0       | 160 |
| icl         | subsample | vae      |        0       | 160 |
| silhouette  | short     | pca      |        0       | 160 |
| silhouette  | short     | tica     |        0       | 160 |
| silhouette  | short     | vae      |        0       | 160 |
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
| pca      | k_bic    |  0.00446145 |    -0.0111476 |   0.0202222   |        20 |
| tica     | k_bic    | -0.0138667  |    -0.0235144 |  -0.00477031  |        20 |
| vae      | k_bic    | -0.0219983  |    -0.0462125 |   0.000317745 |        20 |
