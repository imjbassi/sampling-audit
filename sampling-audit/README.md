# Sampling-Budget Audit of Dimensionality Reduction for Conformational Landscapes

Auditing whether the metastable states that PCA, TICA, and VAE projections
"reveal" in molecular simulation data are properties of the free energy
landscape, or partly artifacts of how much data was collected.

## The question

A very common claim in the molecular simulation literature has the form:

> Projecting our trajectory with method M reveals N metastable basins.

That sentence presents N as a property of the molecule. This repository tests
whether it is also, substantially, a property of the sampling budget — the
number of frames the analyst happened to save.

The test is only meaningful if the true answer is known independently of the
method being audited. So the primary systems are potentials where the number,
location, and population of basins are fixed **by construction** (Müller-Brown,
3 basins; Prinz, 4 basins), with the low-dimensional dynamics lifted through a
fixed random nonlinear map into 30 observed dimensions so that dimensionality
reduction is a non-trivial task. Ground-truth labels always come from the
latent coordinate, never from a fitted model.

## The control that makes it defensible

Two sampling modes are run over the identical landscape:

| mode | what varies | what it isolates |
|---|---|---|
| `short` | a genuinely short trajectory | exploration deficit **and** sample size, confounded |
| `subsample` | uniform thinning of one long trajectory | sample size alone, coverage held fixed |

If the effect survives `subsample`, "short simulations explore less" does not
explain it, and the inflation lives in the estimator. If it vanishes, it is an
exploration deficit. Running only `short` and asserting either one would not be
a result.

A second control guards the other obvious objection — that BIC selects more
Gaussian components as *n* grows under model misspecification, independent of
any real structure. Five selection criteria are computed on every condition
(BIC, AIC, ICL, silhouette, elbow gap). ICL and silhouette share almost none of
BIC's assumptions, so the claim is only made to the extent it survives them.

A third control fixes VAE training at a constant number of gradient steps
rather than a constant number of epochs, so "more data" is never silently
confounded with "more optimisation".

## Layout

```
src/
  potentials.py   Müller-Brown and Prinz potentials; ground-truth basin assignment
  simulate.py     overdamped Langevin integrator; nonlinear lift to R^30
  embed.py        PCA, TICA (explicit generalised eigenproblem), VAE, t-SNE
  selection.py    five model-selection criteria for "how many states?"
  cluster.py      clustering + chance-corrected recovery metrics
  sweep.py        the experiment driver
  analyze.py      bootstrap CIs over seeds; Spearman budget-trend tests
  figures.py      all publication figures
  alanine.py      real-system validation (alanine dipeptide, optional)
paper/
  outline.md      section-by-section plan mapped to figures
  threats.md      threats to validity and how each is addressed
```

## Reproducing

```bash
pip install -r requirements.txt

# main sweep: ~3-6 hours on CPU at these settings
python src/sweep.py \
  --methods pca tica vae \
  --budgets 250 500 1000 2000 4000 8000 16000 32000 \
  --seeds 20 --modes short subsample \
  --out results/sweep.csv

# second landscape, for generality
python src/sweep.py --potential prinz1d --seeds 20 \
  --out results/sweep_prinz.csv

# figures
python src/figures.py --results results/sweep.csv
```

`--resume` skips conditions already written, so a long run can be interrupted
and restarted safely.

### Optional real-system validation

```bash
pip install -r requirements-md.txt
python src/alanine.py simulate --ns 100
python src/alanine.py sweep --dcd data/alanine/traj_seed0.dcd \
                            --top data/alanine_dipeptide.pdb
```

## Statistical conventions

- The **seed is the replicate.** Frames within a trajectory are heavily
  autocorrelated, so all confidence intervals bootstrap over seeds, never over
  frames.
- The headline statistic is a **Spearman rank correlation** between
  `log(n_frames)` and reported state count, because the claim is monotone
  inflation rather than any particular functional form.
- **ARI** is the recovery metric because it is chance-corrected: it does not
  reward a method merely for producing more clusters, which is precisely the
  failure mode under investigation.
- Ceiling hits (`k_selected == kmax`) are reported explicitly. Where the rate is
  non-negligible, the inflation is right-censored and therefore understated.

## Status

Toy-system pipeline implemented and running. Alanine dipeptide validation is
scaffolded but not yet run. See `paper/outline.md` for what remains.
