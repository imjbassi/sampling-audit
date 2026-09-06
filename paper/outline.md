# Paper outline

**Working title:** How Many Metastable States Did You Actually Find? Sampling
Budget as a Confound in Dimensionality-Reduction Analyses of Molecular
Simulation

**Format target:** 8 pages + appendix (archival), with a 4-page compression for
a workshop submission. Same two-draft strategy that worked before.

---

## 1. Introduction (~0.75 pp)

Open with the sentence pattern the paper is about: *"projecting our trajectory
with method M reveals N metastable basins."* That sentence attributes N to the
molecule. Ask whether it is also a statement about the sampling budget.

Three contributions, stated plainly:

1. A controlled audit showing that the number of metastable states reported by
   standard DR + model-selection pipelines increases monotonically with
   sampling budget while the underlying landscape is held fixed by
   construction.
2. A coverage-matched control separating the two candidate mechanisms —
   exploration deficit versus estimator response to sample size — which prior
   comparative studies do not distinguish because they compare methods at fixed
   data rather than varying data at fixed ground truth.
3. A practical recommendation: report state counts with the budget they were
   obtained at, and prefer selection criteria that resist the effect.

Do **not** claim any published result is wrong. The claim is that a reporting
convention is incomplete. That distinction is what keeps the paper defensible
and keeps reviewers from becoming defensive.

## 2. Related work (~0.75 pp)

Three strands, each acknowledged for what it did do:

- **Method comparisons.** Recent benchmarks compare PCA/TICA/VAE projections
  and clustering algorithms on folding trajectories and on MSM construction.
  These establish that method choice changes the answer. They hold the data
  fixed and vary the method; this paper does the reverse.
- **Sampling and ergodicity.** It is well known and frequently stated that MD
  data are undersampled and non-ergodic. This is usually a caveat in prose.
  The contribution here is to measure the consequence for reported state count
  under controlled conditions.
- **Model selection for mixtures.** BIC's behaviour under misspecification is
  known in statistics. Section 5 shows the effect is not reducible to it.

Be explicit and generous here. The nearest prior work is good work; the gap is
narrow and real, and overclaiming it is the fastest way to lose a reviewer.

## 3. Setup (~1.5 pp)

- **Systems.** Müller-Brown (k=3) and Prinz (k=4). Ground truth by
  construction; basin assignment by steepest-descent quenching / barrier-top
  partition, never by a fitted model. → **Fig. 1**
- **Observation model.** Fixed random Fourier lift R^d → R^30 plus isotropic
  noise, drawn once and held constant across every condition, so no difference
  between conditions can be attributed to a changed observable.
- **Methods under audit.** PCA, TICA (explicit generalised eigenproblem), VAE
  (fixed architecture, fixed gradient-step budget). t-SNE appears in the
  appendix only, with an explicit note that its cluster count is governed by
  perplexity and is therefore not a meaningful estimate of state count.
- **Selection criteria.** BIC, AIC, ICL, silhouette, elbow gap.
- **Metrics.** Reported k; ARI against ground truth at selected k and at oracle
  k; basin-population L1 error; ceiling-hit rate.
- **Statistics.** Seed is the replicate; all CIs bootstrap over seeds. Headline
  statistic is Spearman ρ(log n_frames, reported k).

## 4. Main result (~2 pp)

- **Fig. 2** — embedding grid, method × budget, coloured by true basin. The
  visual hook: identical landscape in every panel.
- **Fig. 3** — reported k versus budget, with bootstrap CIs, true k as a
  reference line. The main plot.
- **Table 1** — Spearman ρ per (mode, method, criterion).
- **Table 2** — reported k at smallest versus largest budget.

State the effect size in the abstract as a rank correlation with a CI, not as a
single dramatic ratio.

## 5. Is it just BIC? (~1 pp)

The section that decides whether the paper survives review.

- **Fig. 4** — same trend under five criteria.
- Report honestly which criteria resist it. Preliminary runs suggest ICL is
  substantially more robust than BIC; if that holds, it is a *constructive*
  finding and should be promoted, not buried — a paper that says "here is the
  problem and here is what to use instead" is much stronger than one that only
  says "here is the problem."
- **Table 4** — ceiling-hit rate. Where reported k is censored at kmax, say so
  and note the inflation is understated.

## 6. Is it just undersampling? (~1 pp)

- **Fig. 6** — the coverage-matched control. Budget trend under `short` versus
  `subsample`.
- If the effect persists under coverage matching, the mechanism is the
  estimator, not exploration. If it attenuates, quantify by how much and say
  so.
- **Fig. 5** — selected-k versus oracle-k recovery, which localises the damage:
  if oracle-k ARI is high while selected-k ARI is low, the projection is fine
  and the state-count choice is doing the harm. That is a much more actionable
  message than "DR methods are unreliable."

## 7. Real system: alanine dipeptide (~1 pp)

Ground truth from backbone dihedrals — chemistry, not clustering. Features are
heavy-atom pairwise distances, deliberately not φ/ψ. Show the same budget sweep
reproduces the toy-system trend, or report the extent to which it does not.

This section is what upgrades the paper from "synthetic study" to something a
simulation audience will act on. It is also the section most likely to
complicate the story — plan for that rather than hoping.

## 8. Recommendations (~0.5 pp)

Concrete and short:

1. Report the sampling budget alongside any claimed state count.
2. Show the state count as a function of budget, not at one budget.
3. Prefer selection criteria that penalise component overlap.
4. Where a reference or reduced-budget condition exists, report the
   budget-matched comparison.

## 9. Limitations (~0.5 pp)

See `threats.md`. Write this section before the results section, not after —
it constrains what the results section is allowed to claim.

---

## Figure/table inventory

| ID | Content | Source |
|---|---|---|
| Fig 1 | Ground-truth landscape, basins, trajectory | `figures.fig1_landscape` |
| Fig 2 | Embedding grid, method × budget | `figures.fig2_embedding_grid` |
| Fig 3 | Reported k vs budget (main result) | `figures.fig3_state_inflation` |
| Fig 4 | Five selection criteria | `figures.fig4_criteria` |
| Fig 5 | Selected-k vs oracle-k recovery | `figures.fig5_recovery` |
| Fig 6 | Coverage-matched control | `figures.fig6_coverage` |
| Tab 1–4 | Trends, endpoints, recovery, ceiling | `report.py` |

## Remaining work

- [ ] Full sweep at 20 seeds, both potentials (`run_all.sh`)
- [ ] Alanine dipeptide simulation and sweep
- [ ] Decide archival venue; compress to 4 pages for a workshop
- [ ] Anonymise; AI-disclosure statement
- [ ] Make repo public on submission
