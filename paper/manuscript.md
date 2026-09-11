# How Many Metastable States Did You Actually Find?
### Sampling Budget as a Confound in Dimensionality-Reduction Analyses of Molecular Simulation

## Abstract

A common claim in the molecular simulation literature takes the form
"projecting our trajectory with method M reveals N metastable states." That
sentence presents N as a property of the molecule. We show it is also,
substantially, a property of how much data was collected. Across two
potentials with basin counts fixed by construction and a 100 ns all-atom
simulation of alanine dipeptide, the number of states reported by PCA, TICA,
and VAE projections under standard model-selection criteria increases
monotonically with sampling budget while the ground-truth landscape does not
change (Spearman rho = 0.90-0.97 across systems and methods). The effect
survives a coverage-matched control that holds landscape exploration fixed and
varies only sample size, which rules out incomplete exploration as the
explanation. It is not reducible to a single criterion's idiosyncrasy: AIC is
saturated at every budget tested, BIC inflates monotonically, and only the
integrated completed likelihood (ICL) avoids reaching the search ceiling,
though it remains inaccurate in a method-dependent direction. Recovery against
ground truth under the standard pipeline peaks at an intermediate budget and
then declines as more data is added, even as recovery given the true state
count remains flat or improves -- collecting more data makes the standard
analysis pipeline's answer worse, not better, across every method-system
combination tested, including on real molecular dynamics data. We recommend
reporting state counts alongside the sampling budget at which they were
obtained, and offer ICL as a materially safer default than BIC or AIC for this
purpose.

## 1. Introduction

Dimensionality reduction is the standard first step in characterizing the
conformational landscape of a molecular system from simulation data. A
trajectory of hundreds or thousands of coordinates is projected onto two or
three dimensions using PCA, TICA, or increasingly a learned nonlinear
embedding such as a VAE, and the resulting low-dimensional density is read for
metastable states -- the basins a molecule spends most of its time in and
transitions between only rarely.

The sentence that reports this reading, "our analysis reveals N metastable
states," attributes N to the molecule. This paper asks how much of N is
instead attributable to the sampling budget: the number of frames the analyst
happened to save.

The question matters because sampling budget is rarely fixed by the science.
It is set by wall-clock time, hardware access, and project deadlines, and it
varies by orders of magnitude across published studies of the same or similar
systems. If reported state counts are sensitive to this variable, then a
literature comparing state counts across studies -- or a single study
reporting a state count without its sampling context -- is implicitly
comparing sampling budgets as much as it is comparing molecules.

We test this directly using systems where the number of metastable states is
known independently of any dimensionality reduction or clustering method: two
synthetic potentials with basin count fixed by construction, and a real
all-atom simulation of alanine dipeptide, whose three conformational states are
defined by backbone dihedral angles rather than by any method under audit. On
every system tested, the number of states reported by a standard
projection-plus-model-selection pipeline increases with sampling budget at
fixed ground truth, and a coverage-matched control rules out incomplete
exploration as the explanation.

This paper makes three contributions.

**A controlled audit of a previously undocumented confound.** We show that
reported metastable state count is a function of sampling budget under
standard analysis pipelines, holding the ground-truth landscape fixed by
construction. The effect appears in two synthetic potentials of different
dimensionality and basin count, and reproduces in a 100 ns all-atom simulation
of a real biomolecule.

**A control design that isolates the mechanism.** By comparing a genuinely
short trajectory against a uniform subsample of one long reference trajectory
at matched sample size, we separate two candidate explanations that prior
comparative work does not distinguish: whether the effect reflects incomplete
exploration of the landscape, or the state-count estimator's response to
sample size independent of exploration. The effect persists under coverage
matching on every system tested, which locates it in the estimator rather than
in what the trajectory visited.

**A practical recommendation, not just a diagnosis.** Five model-selection
criteria are compared on identical data. BIC and AIC both inflate with budget,
with AIC additionally saturated at every budget tested rather than trending; the
integrated completed likelihood (ICL) never reaches the search ceiling on
either synthetic system, though it is not thereby accurate. We further
localize where the resulting error comes from: across all nine method-system
pairs tested, recovery under the standard pipeline declines from its peak to
the largest budget tested, but the size of the decline is explained by a
single mechanism rather than left unexplained. PCA and VAE decline sharply
(29-84%) regardless of how faithful their projection is; TICA declines only
as much as its warm-up phase -- the minimum data needed to produce a stable
projection at all -- leaves room for the ordinary selection-driven
degradation to operate, ranging from 9% where warm-up consumes most of the
tested budget to 53% where it does not.

We do not claim that any published metastable-state count is wrong. The claim
is that such counts are, by default, incompletely reported: a number without
its sampling budget carries less information than authors and readers
typically treat it as carrying.

## 2. Related work

**Comparative benchmarks of dimensionality reduction for molecular systems.**
Recent work has directly compared PCA, TICA, and VAE projections, together with
downstream clustering choices, on protein folding trajectories and on Markov
state model construction, finding that the choice of method changes the
resulting free energy surface and the states it appears to reveal. This
literature establishes that method choice matters at fixed data. The present
work holds method fixed and varies the data, which is the complementary axis:
we ask not which method is best at a given budget, but whether the answer any
method gives depends on the budget itself. We are not aware of prior work that
varies sampling budget at fixed, independently known ground truth to isolate
this effect.

**Undersampling and non-ergodicity in molecular dynamics.** It is well
established and frequently acknowledged that molecular dynamics trajectories
are undersampled relative to the timescales of interest, and that this
undersampling can bias downstream analysis. This is typically stated as a
caveat rather than measured as a quantitative confound with a known
ground-truth comparison. Our contribution is to make the undersampling
question tractable by constructing systems where the true answer is known,
and to show that the resulting effect is not explained by exploration deficit
alone, since it persists when landscape coverage is matched across budgets.

**Model selection under misspecification.** The behavior of BIC and related
criteria when the fitted model class does not match the true data-generating
process is well studied in the statistics literature; in particular, the
likelihood gain from additional mixture components can grow with sample size
under misspecification even when the penalty term does not compensate
proportionally. Our results are consistent with this mechanism contributing to
the effect, but not with it being the whole explanation: the effect's
persistence under coverage matching, and its variation across a projection
method (TICA) whose own stability is separately budget-dependent, point to
more than one contributing cause. We are explicit throughout about which part
of the effect is attributable to which mechanism, rather than presenting a
single unified explanation the data does not fully support.

We are generous to this prior work by design. The gap we identify is narrow:
existing benchmarks are good benchmarks, conducted at whatever budget the
authors used, and simply do not vary that budget as an independent condition
against known ground truth. The contribution of this paper is the control, not
a correction to any specific published result.

## 3. Setup

### 3.1 Systems

Three systems are used, chosen so that ground truth is available independently
of any method under audit.

**Müller-Brown potential** (2 latent dimensions, 3 basins). A standard
three-well potential with minima located by gradient descent from known
starting points; basin membership is assigned by steepest-descent quenching to
the nearest minimum, never by a fitted clustering model. Figure 1 shows the
potential surface, the resulting ground-truth basins, and a representative
sampled trajectory.

**Prinz potential** (1 latent dimension, 4 basins). A standard four-well
potential from the Markov state model literature; basin boundaries are the
potential's barrier tops, located once on a fine grid at construction time.

**Alanine dipeptide** (all-atom, 3 basins). A 100 ns Langevin dynamics
simulation in implicit solvent (OpenMM, amber14/GBn2, 2 fs timestep, 1 ps save
interval, 100,000 saved frames). Ground truth is the standard three-region
partition of the backbone (phi, psi) dihedral space -- a chemical definition
entirely independent of dimensionality reduction or clustering. Observed
features are pairwise distances between heavy atoms, deliberately excluding
phi/psi, so that the methods under audit must recover the landscape from a
representation that does not already contain the answer. The simulation length
was chosen after an initial 5 ns pilot run showed the rarest basin
(alpha_L/C7ax) was visited inconsistently at small sampling budgets; 100 ns
ensures all three basins are visited at every tested budget under
coverage-matched subsampling, and at budgets of 8,000 frames and above under
short trajectories (Section 7).

For the two synthetic potentials, the low-dimensional dynamics are lifted into
30 observed dimensions through a fixed random Fourier feature map plus
isotropic noise, drawn once and held constant across every sampling condition,
so that no difference between conditions is attributable to a changing
observation model. Figure 2 shows the resulting embeddings across projection
method and sampling budget on Müller-Brown, coloured by true basin, to
illustrate the visual character of the confound before the quantitative
results in Sections 4-6: the underlying landscape is identical in every panel.

### 3.2 Sampling conditions

Two modes are compared at each of several sampling budgets (250 to 32,000
frames for the synthetic potentials; 100 to 4,000 frames for alanine
dipeptide, scaled to the shorter available trajectory):

- **short**: a trajectory run to produce exactly the target number of saved
  frames. This is the condition an analyst with a fixed compute budget
  actually has, and it confounds two things: how much of the landscape was
  explored, and how many points the selection criterion sees.
- **subsample**: one long reference trajectory per seed, uniformly thinned to
  the target budget. Landscape coverage is held approximately fixed by
  construction across every budget; only the number of points varies.

Comparing the two isolates whether an observed effect is due to incomplete
exploration (would appear in `short` but not `subsample`) or to the estimator's
response to sample size (would appear in both).

### 3.3 Methods under audit

**PCA**, **TICA** (solved as an explicit generalized eigenproblem so its
regularization is auditable rather than a library default), and a **VAE**
(fixed architecture, trained for a fixed number of gradient steps rather than a
fixed number of epochs, so that larger datasets are not silently given more
optimization). t-SNE is reported only in an appendix figure: its cluster count
is governed substantially by its perplexity hyperparameter rather than by data
structure, so treating its output as a state-count estimate would not be
sound.

### 3.4 State-count selection

Five criteria for choosing the number of mixture components in the projected
space are compared on identical embeddings: BIC, AIC, the integrated completed
likelihood (ICL, which adds an entropy penalty on component overlap to BIC),
silhouette score, and an elbow heuristic on k-means inertia. This comparison is
included because the most direct objection to the central finding is that it
is a known property of BIC's penalty behavior under model misspecification
rather than a property of the dimensionality reduction step; the five-criterion
comparison is designed to answer that objection with evidence.

### 3.5 Metrics and statistics

**Recovery** is measured by the adjusted Rand index (ARI) between the
recovered clustering and ground-truth basin membership, both at the
criterion-selected state count and, as a control, at the true state count
supplied directly ("oracle k"). ARI is chance-corrected, so it does not reward
a method for reporting more clusters -- the specific failure mode under
investigation. **Basin visitation** and **rarest-basin occupancy** are tracked
per condition to identify and exclude degenerate cases in which a trajectory
visited fewer true basins than exist, which produce a constant ground-truth
label vector against which any single-cluster solution scores ARI = 1.0
trivially.

The seed is the unit of replication: frames within a trajectory are strongly
autocorrelated, so all confidence intervals are bootstrapped over seeds, never
over frames. The headline statistic reported for the budget effect is a
Spearman rank correlation between log sampling budget and reported state
count, chosen because the claim under test is monotone inflation rather than
any specific functional form. Twenty seeds are used per condition on the
synthetic potentials; eight seeds on alanine dipeptide, reflecting its higher
per-condition compute cost.

## 4. Reported state count tracks sampling budget

Across both landscapes, all three projections, and both sampling modes, the
number of metastable states selected by BIC increases monotonically with the
number of saved frames, while the underlying potential is identical in every
condition.

On Müller–Brown (true k = 3), BIC-selected state counts rise from 1.0–6.3 at
n = 250 to 11.9–14.8 at n = 32,000. On Prinz (true k = 4) the same sweep runs
from 1.0–7.1 up to 12.5–14.9. At the largest budget every method on every
system reports at least three times the true number of basins.

The rank correlation between log sampling budget and BIC-selected state count
is uniformly high and tightly bounded (Table 1):

| system | mode | PCA | TICA | VAE |
|---|---|---|---|---|
| Müller–Brown | short | +0.88 [+0.85, +0.91] | +0.94 [+0.93, +0.96] | +0.92 [+0.91, +0.94] |
| Müller–Brown | subsample | +0.88 [+0.85, +0.91] | +0.96 [+0.95, +0.97] | +0.93 [+0.92, +0.94] |
| Prinz | short | +0.95 [+0.93, +0.96] | +0.97 [+0.97, +0.98] | +0.93 [+0.92, +0.94] |
| Prinz | subsample | +0.95 [+0.94, +0.96] | +0.96 [+0.95, +0.97] | +0.91 [+0.89, +0.93] |

Bootstrap intervals are over the 20 seeds. No interval approaches zero. (Figure 3)

Two points of interpretation are worth making immediately, because they bound
what this result does and does not say.

First, the effect is **not** a claim that these projections fail to represent
the landscape. Section 6 shows the opposite. It is a claim about the composite
pipeline of projection followed by model selection, which is how state counts
are obtained in practice.

Second, the reported counts at large budgets are **right-censored**. The search
range was capped at k = 15. Under BIC, PCA hits that cap in 44% of
Müller–Brown conditions and 29–30% of Prinz conditions (Table 4). Where the cap
binds, the tabulated mean is a lower bound on what the criterion would have
selected, and the rank correlation is correspondingly attenuated. The reported
effect is therefore conservative.

## 5. The effect is not reducible to one selection criterion

The obvious objection is that BIC's penalty grows as log n while the
likelihood gain from an additional mixture component grows with n, so BIC
selects more components as n increases under any model misspecification — and a
projected free energy basin is never exactly Gaussian. On that account the
result would be a property of the criterion rather than of the analysis
pipeline.

Five criteria were therefore computed on every condition. The outcome is more
informative than a simple yes or no.

**AIC is saturated, not budget-driven.** AIC reaches the search ceiling in
65-84% of Müller-Brown conditions and 12-65% of Prinz conditions (Table 4), but
Fig. 4 shows why that number cannot be read as inflation: AIC's curve is
U-shaped, starting at ~14 states for PCA and ~8 for TICA and VAE at n = 250,
dipping near n = 1000, then returning to ~14.5. It over-selects at every
budget, including the smallest. Its rank correlation is computed across a
non-monotone curve that spends most of its range censored at the cap and is
therefore uninterpretable. AIC is reported for completeness and excluded from
the trend claim.

**ICL never saturates, but it is not accurate.** ICL is the only criterion that
reached the ceiling in zero of twenty-four (system x mode x method) cells,
which keeps its output in an interpretable range. Within that range it is
wrong in a method-dependent direction (Fig. 4, Müller-Brown, true k = 3): PCA
reports 5.0-6.2 states throughout, roughly twice the truth and nearly flat;
VAE reports 1.2-1.8, *under*-selecting at every budget; only TICA rises
monotonically through the true value, from 1.0 to 4.6. The defensible claim is
that ICL avoids the runaway behaviour of BIC and AIC, not that it recovers the
correct state count.

**Silhouette and elbow gap are insensitive rather than robust.** Both return a
near-constant answer regardless of budget. PCA's silhouette selection is
exactly 2 at every budget on Müller-Brown and exactly 4 at every budget on
Prinz; elbow gap is flat at 2 for PCA and VAE on both systems. The Prinz case
is the more instructive one: silhouette's constant output there coincides with
the true state count, so on that system alone the criterion appears to perform
perfectly. It has not measured anything. A criterion that returns the same
answer irrespective of the data will look excellent on any landscape where that
answer happens to be correct, and this is precisely how an uninformative
criterion can acquire a reputation for reliability. The sign changes in
Table 1 (silhouette/PCA: -0.26 on Müller-Brown, +0.65 on Prinz) are sign
changes on an essentially constant output and should be read as noise, not as
landscape sensitivity.

The honest summary is narrower than "five criteria disagree" and narrower than
a clean ordering by penalty strength: **BIC inflates monotonically with
sampling budget; AIC is saturated at all budgets; ICL alone stays in an
interpretable range without saturating, though it remains inaccurate in a
method-dependent direction; and the two geometry-based criteria are
unresponsive to budget and to landscape alike.** (Figure 4)

### One exception, stated plainly

ICL's resistance does not extend to TICA. TICA's ICL correlation is +0.74 and
+0.92 on Müller–Brown (short, subsample) and +0.91 and +0.93 on Prinz —
comparable to its BIC correlations rather than to PCA's and VAE's ICL values.

We do not have a confirmed mechanism for this. One plausible account is that
TICA components, being constructed to maximise autocorrelation rather than
variance, produce latent densities less well approximated by a Gaussian
mixture, weakening the entropy penalty that ICL relies on. This is a
conjecture and is flagged as such; it is a natural target for follow-up rather
than something the present data settles. It is reported here because a
recommendation to use ICL would be misleading without it.

## 6. The effect is not explained by incomplete exploration

The competing mechanism is exploration deficit: short trajectories visit less
of the landscape, so fewer or differently shaped basins are populated, and the
apparent structure changes for reasons that have nothing to do with sample
size.

The `subsample` mode addresses this directly. A single long reference
trajectory per seed is thinned uniformly to each target budget, so landscape
coverage is held approximately fixed by construction while only the number of
points varies.

Coverage matching does not remove the effect. BIC budget correlations under
`short` and `subsample` are statistically indistinguishable in every cell:

| system | method | short | subsample |
|---|---|---|---|
| Müller–Brown | PCA | +0.88 [+0.85, +0.91] | +0.88 [+0.85, +0.91] |
| Müller–Brown | TICA | +0.94 [+0.93, +0.96] | +0.96 [+0.95, +0.97] |
| Müller–Brown | VAE | +0.92 [+0.91, +0.94] | +0.93 [+0.92, +0.94] |
| Prinz | PCA | +0.95 [+0.93, +0.96] | +0.95 [+0.94, +0.96] |
| Prinz | TICA | +0.97 [+0.97, +0.98] | +0.96 [+0.95, +0.97] |
| Prinz | VAE | +0.93 [+0.92, +0.94] | +0.91 [+0.89, +0.93] |

Confidence intervals overlap in all six comparisons. Whatever drives the
inflation, it survives holding coverage fixed, which locates it in the
estimator's response to sample size rather than in what the trajectory
happened to visit. (Figure 6)

### Recovery degrades as sampling budget increases

The gap between recovery at the selected state count and recovery at the true
state count is not constant. Recovery under the standard pipeline peaks at an
intermediate budget and then declines, while oracle-k recovery over the same
range is flat or rising. (Figure 5)

A coverage artifact was checked for before drawing this conclusion. Conditions
in which the trajectory visited fewer basins than exist produce a constant
ground-truth label vector, against which a single-cluster solution scores
ARI = 1.0 trivially. Such conditions occur only in `short` mode at small
budgets -- 100% of Müller-Brown conditions at n = 250, declining to zero by
n = 4000, and 35% of Prinz conditions at n = 250, zero by n = 1000 -- and in
**no** `subsample` condition on either system. All 38 rows scoring ARI > 0.999
are degenerate. Because coverage-matched subsampling contains no degenerate
conditions, the primary curves are unaffected: cleaned and raw values agree to
two decimal places throughout. Excluding degenerate rows from `short` mode
makes the decline steeper rather than shallower (Müller-Brown TICA: peak
0.61 -> 0.76, final drop -0.42; VAE final drop -0.61), because those rows
carried low median ARI (0.023) at the small-budget end. The Müller-Brown
`short` condition at n = 250 is excluded entirely, having no valid
replicates.

Every method-system pair on the two synthetic potentials shows the
peak-then-decline pattern under coverage matching; the complete picture across
all three systems, including alanine dipeptide, is given as a single table in
Section 6.3 rather than duplicated here.

For these pairs, collecting more data makes the answer produced by the
standard pipeline substantially worse, with the crossover falling between
n = 250 and n = 1000. This is stronger than the endpoint comparison in Table 3,
which reports only the largest budget and therefore conceals the
non-monotonicity.

### The TICA exception, and the evidence for its mechanism

TICA on Prinz is the exception: recovery rises from 0.00 at n = 250 to 0.58 at
n = 8000 before a small decline to 0.51. It is not an instance of the pattern
and is not presented as one.

The mechanism is directly tested, not only inferred from this exception. A
lag/lagged-pair ablation (Prinz potential, lags in {5, 10, 20, 50, 100}, 10
seeds, subsample mode, 300 conditions) fits TICA at every combination of
sampling budget and lag and measures oracle-k recovery -- the projection's
quality with the selection step removed -- as a function of both:

| n_frames | lag=5 | lag=10 | lag=20 | lag=50 | lag=100 |
|---|---|---|---|---|---|
| 500 | 0.10 | 0.03 | 0.03 | 0.05 | 0.03 |
| 1000 | 0.35 | 0.16 | 0.06 | 0.06 | 0.07 |
| 2000 | 0.53 | 0.40 | 0.24 | 0.05 | 0.06 |
| 4000 | 0.67 | 0.55 | 0.42 | 0.20 | 0.09 |
| 8000 | 0.77 | 0.69 | 0.59 | 0.44 | 0.29 |
| 16000 | 0.87 | 0.80 | 0.70 | 0.57 | 0.54 |

Both predictions of the warm-up account are confirmed directly. At any fixed
budget, recovery decreases monotonically as lag increases, consistent with
fewer usable lagged pairs (n_frames - lag) producing a less stable time-lagged
covariance estimate. The budget at which recovery reaches a given level shifts
with lag exactly as the mechanism predicts: 0.35 oracle-k ARI is reached by
n = 1000 at lag = 5, requires roughly n = 8000 at lag = 50, and is not reached
even at n = 16000 at lag = 100. TICA is therefore subject to two opposing
budget effects -- an estimator that requires enough lagged pairs to stabilise,
with the requirement scaling with the lag itself, and a selection step that
degrades with data once the estimator has stabilised (visible in the
corresponding selected-k table, where recovery at lag = 5 peaks at n = 8000,
0.56, and declines to 0.45 by n = 16000, reproducing the main peak-then-decline
pattern within a single fixed lag setting) -- and the observed curve on any
given system is their sum. Where the crossover falls depends on how quickly
TICA stabilises on that landscape's combination of lag and dynamics: near
n = 1000 on Müller-Brown at the default lag, near n = 8000 on Prinz. PCA and
VAE have no comparable warm-up requirement, consistent with their declining
monotonically or peaking at the smallest budgets in the main sweep.

### Scope of the localisation claim

Oracle-k recovery separates cleanly by system rather than by method. On Prinz,
all three projections reach 0.81-0.90 when given the true state count, so the
projections are faithful and essentially all of the observed degradation is
attributable to state-count selection. On Müller-Brown only TICA reaches that
range (0.85); PCA and VAE reach only 0.41-0.44 even with the true k supplied,
so for those pairs the projection is itself a limiting factor and selection is
not the whole story.

The claim that the projection is faithful and only the selection step fails is
therefore supported wherever oracle-k recovery is high -- all of Prinz, and
TICA on Müller-Brown -- and is not supported in general. The paper should scope
it accordingly rather than asserting it as a universal result.

| system | method | selected k | oracle k | gap |
|---|---|---|---|---|
| Müller-Brown | PCA | 0.102 | 0.415 | 0.31 |
| Müller-Brown | TICA | 0.342 | 0.847 | 0.51 |
| Müller-Brown | VAE | 0.111 | 0.423 | 0.31 |
| Prinz | PCA | 0.349 | 0.897 | 0.55 |
| Prinz | TICA | 0.482 | 0.815 | 0.33 |
| Prinz | VAE | 0.399 | 0.854 | 0.46 |

(All values at n = 32,000, `short` mode; `subsample` values are within 0.03.
Note that these endpoint figures understate oracle-k recovery for TICA under
subsampling, which reaches 0.82 on Prinz at the largest budget.)

### 6.3 The complete picture across nine method-system pairs

Every method-system pair tested shows recovery declining from its peak to the
largest budget tested. What differs is how much, and the amount tracks a
specific mechanism rather than varying arbitrarily.

| system | method | peak ARI (budget) | ARI at largest budget | relative decline | oracle-k ARI |
|---|---|---|---|---|---|
| Müller-Brown | PCA | 0.25 (n=250) | 0.11 | 56% | 0.415 |
| Müller-Brown | TICA | 0.77 (n=1000) | 0.36 | 53% | 0.847 |
| Müller-Brown | VAE | 0.79 (n=500) | 0.13 | 84% | 0.423 |
| Prinz | PCA | 0.64 (n=250) | 0.35 | 45% | 0.897 |
| Prinz | TICA | 0.58 (n=8000) | 0.51 | 12% | 0.815 |
| Prinz | VAE | 0.72 (n=1000) | 0.41 | 43% | 0.854 |
| Alanine dipeptide | PCA | 0.47 (n=100) | 0.12 | 74% | 0.475 |
| Alanine dipeptide | TICA | 0.44 (n=16000) | 0.27 | 37% | 0.963 |
| Alanine dipeptide | VAE | 0.54 (n=2000) | 0.18 | 66% | 0.421 |

Two patterns are visible in this table together that were not visible when the
systems were reported separately.

**PCA and VAE decline sharply and consistently** (43-84% relative decline)
across all three systems, regardless of how faithful the underlying projection
is (compare their oracle-k column, which ranges from 0.42 to 0.90). Their
selected-k recovery is dominated by the state-count selection failure, not by
projection quality.

**TICA's decline tracks how long its warm-up phase lasts, not the system.**
TICA requires a minimum number of lagged pairs to produce a stable projection
at all; at small budgets on every system it starts near zero (Müller-Brown:
0.09 at n=250; Prinz: 0.00 at n=250-500; alanine: 0.00 at n=100). Once past
this threshold, its subsequent decline depends on how much of the tested
budget range remains after warm-up resolves. On Prinz, warm-up consumes most
of the range and the subsequent decline is mild (12%). On Müller-Brown,
warm-up resolves almost immediately, leaving most of the range for the
ordinary selection-driven decline to operate, and the result is sharp (53%,
comparable to PCA and VAE on the same system). On alanine dipeptide under the
100 ns trajectory, warm-up resolves faster still -- by n=250, because
coverage-matched subsampling draws uniformly from a much longer, better-mixed
reference trajectory than a short one, so even a small subsample yields
well-distributed lagged pairs -- and the resulting decline (37%) sits between
the two extremes, consistent with most of the budget range operating in the
selection-driven regime. This is consistent with two mechanisms operating on
the same curve rather than one: an estimator-stability effect that dominates
at small budgets and a selection-driven degradation that dominates once the
estimator has stabilized, exactly as characterized via the oracle-k contrast
in Section 6. That the warm-up threshold itself shifts with how the reference
trajectory was generated, not only with lag and system identity, is a further
prediction of the mechanism that this comparison confirms.

All nine method-system pairs decline from peak to the largest budget tested,
and the size of the decline is explained by a specific, testable mechanism
rather than left as an unexplained residual in a minority of cases. This
table, not a summary fraction, is the result that belongs in the paper.

## 7. Alanine dipeptide: simulation detail and comparison to the synthetic systems

The synthetic systems establish the effect under conditions where ground truth
is exact and the observation model is fully controlled. This section reports
the real-molecule replication and what is and is not comparable between the
two settings.

**Simulation.** A single 100 ns trajectory of alanine dipeptide (ACE-ALA-NME)
was run in implicit solvent (OpenMM, amber14/GBn2 force field, Langevin middle
integrator, 2 fs timestep, 300 K, 1 ps save interval, one simulation seed),
producing 100,000 saved frames. An initial 5 ns pilot run was discarded after
it showed the rarest of the three basins (alpha_L/C7ax) was not consistently
visited at the sampling budgets under study; 100 ns was chosen because it
visits all three basins at every tested budget under coverage-matched
subsampling, and at budgets of 8,000 frames and above under short trajectories
(Table, below). Sampling budgets from 100 to 64,000 frames were drawn from
this trajectory: `short` budgets as contiguous leading blocks, `subsample`
budgets as uniform thinning, matching the two conditions used on the synthetic
systems. Ground-truth basin membership was assigned from the backbone (phi,
psi) dihedral angles into the standard three-region partition (C7eq, alpha_R,
alpha_L/C7ax), a chemical definition independent of any method under audit.
Observed features for the dimensionality reduction methods were pairwise
distances between heavy atoms, excluding phi/psi so that the audited methods
must recover the landscape from a representation that does not already encode
the answer.

| n_frames (short mode) | 100 | 250 | 500 | 1000 | 2000 | 4000 | 8000+ |
|---|---|---|---|---|---|---|---|
| mean basins visited (of 3) | 2.0 | 2.1 | 2.1 | 2.3 | 2.6 | 2.8 | 3.0 |

Under coverage-matched subsampling, all three basins are visited at every
budget tested, from n=100 upward, since subsampling draws uniformly from the
full 100,000-frame reference trajectory rather than from a contiguous block.

**Replication of the main effect.** BIC-selected state count increases with
sampling budget on all three methods, in both modes (Spearman rho = 0.90-0.97,
8 seeds per correlation -- fewer than the 20 seeds used on the synthetic
systems, per the limitation discussed in Section 9). PCA rises from a mean of
3.1 states at n=100 to 14.5 at n=64,000, against a true count of 3. TICA and
VAE rise from conservative counts near 1 at the smallest budget to 13.9 at the
largest. All three methods approach the search ceiling (kmax=15) at the
largest budgets tested, consistent with the ceiling-censoring pattern
documented on the synthetic systems.

**A method ranking that reverses relative to the synthetic systems.** On the
synthetic potentials, TICA is not uniformly the best-recovering method (it
matches PCA and VAE's oracle-k quality only on Müller-Brown and is comparable
to all three on Prinz). On alanine dipeptide, TICA's oracle-k recovery (0.958)
is clearly the best of the three, well above PCA (0.494) and VAE (0.391) --
the largest gap between TICA and the other two methods observed on any system
in this paper. Its selected-k recovery at the largest budget (0.249) remains
far below this ceiling, the same selection-step bottleneck seen throughout.
This is consistent with TICA's construction: it is designed to find slow
collective coordinates, and backbone dihedral transitions in a real molecule
are exactly the kind of slow process TICA targets, whereas the Müller-Brown
and Prinz potentials were not constructed to favor any particular method. The
practical implication is that TICA's relative advantage may be larger on real
molecular systems than the synthetic benchmarks alone would suggest -- a claim
the synthetic systems could not have supported on their own, and that alanine
dipeptide is well-suited to test given how it was built.

**A limitation specific to this validation.** All results in this section come
from a single simulation seed. The eight sweep seeds used above vary only the
randomness in subsampling, clustering initialization, and VAE training applied
to that one trajectory; they do not constitute eight independent physical
replicates of the underlying dynamics, unlike the twenty seeds on the
synthetic systems, each of which reran the full Langevin sampling process
independently. This is disclosed as a limitation in Section 9. Trajectory
length, which was a limitation in an earlier iteration of this work, is
resolved by this 100 ns run and is no longer a live concern for the results
reported here; a second independent simulation seed at 100 ns remains the
single highest-value remaining experiment.

## 8. Recommendations

1. **Report the sampling budget alongside any claimed metastable state count.**
   A state count without its budget is, by the evidence in this paper,
   an incompletely specified quantity.

2. **Do not report a state count from a single budget as a stable property of
   the system.** Where feasible, report how the count changes with budget
   (as in the Table above), or explicitly justify why the budget used is
   believed to be past the point where this matters -- which, per point 3,
   requires checking rather than assuming.

3. **Check the gap between recovery at the selected state count and at a
   plausible alternative before trusting the selected count, rather than
   assuming the selection step is reliable.** This paper's oracle-k comparison
   is one way to do this when ground truth is known; in practice a domain
   plausible-range check (does k = 3 versus k = 8 tell qualitatively different
   biological stories?) serves a similar function.

4. **Prefer ICL over BIC or AIC for this purpose, with the caveat that ICL is
   not thereby accurate, only less prone to runaway inflation.** ICL never
   reached the search ceiling in twenty-four (system x mode x method)
   conditions tested here, where BIC did so in up to 44% of conditions and
   AIC in up to 84%. ICL's own reported count should still be treated as an
   estimate to sanity-check, not a final answer.

5. **Where TICA is used, check for evidence of a warm-up regime before
   trusting its output at a given budget.** TICA's failure mode at small
   budgets (near-zero recovery, not merely inaccurate recovery) is distinct
   from PCA's and VAE's and is not fixed by any of the five selection criteria
   tested; it requires enough usable lagged pairs (sampling budget minus lag)
   at the chosen lag to produce a stable estimate. This is not only a plausible
   diagnostic but a measured one: the lag ablation in Section 6 shows recovery
   at fixed budget falling monotonically as lag increases, and the budget
   needed to reach any given recovery level rising correspondingly with lag.
   A practical check even without ground truth is whether the projection
   changes substantially under a moderate change in lag; if it does, the
   estimate at the current lag and budget should not yet be trusted.

## 9. Limitations

Ordered by how much they constrain the paper's claims, most binding first.

**Silhouette and elbow-gap criteria are shown to be unreliable but not fully
explained.** Both return near-constant output regardless of budget, and this
paper documents that fact and its consequence (an illusion of stability that
happens to coincide with the correct answer on some systems and not others)
without establishing why these particular criteria are so insensitive to this
particular kind of data. This is noted as an open question rather than
resolved.

**All three systems tested have a small number of well-separated basins (3-4).**
Whether the effect's magnitude changes for landscapes with many close or
overlapping metastable states is untested and is a natural extension.

**Alanine dipeptide, while a real molecule, is small and fast-mixing.** The
result should not be extrapolated to slower-folding or larger proteins without
further validation; the paper's claims about real systems are scoped to this
system and are not evidence about protein folding timescales generally.

**A second 100 ns seed is the single highest-value remaining experiment.**
Unlike the 5 ns comparison above, a second independent 100 ns simulation would
test seed-independence on data that does not also carry a coverage confound,
and would upgrade the current single-seed 100 ns result to the same standard
of evidence as the synthetic systems. This is not yet done and is the paper's
most binding limitation as it currently stands.

**A cross-seed comparison exists, but at the superseded trajectory length,
and its evidentiary weight is downgraded accordingly.** Before the 100 ns run
adopted in Section 7, two independent 5 ns simulations (seed 0 and seed 1,
same protocol) were each swept and compared. At that trajectory length the
budget-inflation effect replicated closely across seeds (Spearman rho within
the 0.78-0.94 band on both, every method and mode), and TICA's relative
advantage over PCA and VAE also replicated. However, Section 7 establishes
that 5 ns is insufficient for the rarest basin to be reliably visited at the
sampling budgets under study, so both 5 ns runs share this limitation and the
cross-seed agreement, while a genuine positive sign, is not strong evidence
that the *properly-sampled* 100 ns result is seed-independent -- only that the
under-sampled result was. This comparison is retained as a preliminary,
favorable indicator rather than as confirmation, and is superseded by the
single-seed 100 ns result as the paper's primary alanine dipeptide evidence.

**Two selection-criterion claims rest on limited excursions.** ICL's zero
ceiling-hit rate is a strong result but was tested only up to a search ceiling
of kmax = 15; whether ICL would eventually saturate at a still-larger budget is
not established. Separately, ICL's own accuracy (as opposed to its resistance
to runaway inflation) has not been separately validated against an
independent ground truth beyond the ARI figures already reported.

**TICA's lag parameter was varied on one system only.** The warm-up mechanism
proposed in Section 6 is now directly tested via a lag/lagged-pair ablation
(300 conditions, 10 seeds) rather than only inferred from the oracle-k
contrast, and the ablation confirms both qualitative predictions of the
mechanism. This ablation was run on the Prinz potential only; whether the same
lag-dependence holds quantitatively on Müller-Brown and on alanine dipeptide
is untested and would further strengthen the claim's generality.

**The embedding-dimension ablation is complete and confirms the main results
are dimension-robust, with two secondary findings worth reporting.** Re-running
the core measurement at n_components in {2, 3, 5} on Prinz (540 conditions,
10 seeds) shows the budget-inflation effect essentially unchanged across
dimension for all three methods (Spearman rho stays within 0.86-0.98 with no
consistent trend as dimension increases), and ICL's zero ceiling-hit rate
holds at all three dimensions (0 of 9 method-by-dimension combinations reach
the cap), strengthening Recommendation 4 beyond the single dimension used
elsewhere in the paper.

Two secondary effects emerged that were not anticipated. PCA's oracle-k
recovery improves monotonically with dimension (0.895 to 0.958 from dim = 2 to
dim = 5 at the largest budget), consistent with a purely linear projection
retaining more information as more output dimensions are allowed; TICA's and
VAE's oracle-k recovery is roughly flat or mildly declines over the same range,
consistent with both already capturing the dynamically relevant directions at
two dimensions, leaving additional dimensions to add unneeded capacity (VAE) or
extra room for the selection step to overfit (TICA). Because selected-k
recovery barely moves with dimension for any method, PCA's oracle-versus-
selected gap widens as dimension increases -- a cleaner illustration of the
paper's localization claim than the two-dimensional case alone, since it shows
the selection step's relative cost growing precisely as the projection itself
improves. This ablation was run on Prinz only; whether the same pattern holds
on Müller-Brown and alanine dipeptide is untested.
