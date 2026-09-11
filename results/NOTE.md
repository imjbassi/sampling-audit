# Note on the results in this directory

All sweeps in this directory are complete. An earlier revision of this file
warned that `sweep.csv` was partial after two killed runs in the build
container; that is no longer the case and the warning has been removed.

| file | conditions | grid |
|---|---|---|
| `sweep.csv` | 960 | Müller-Brown, 2 modes x 3 methods x 8 budgets (250-32,000) x 20 seeds |
| `sweep_prinz.csv` | 960 | Prinz, 2 modes x 3 methods x 8 budgets (250-32,000) x 20 seeds |
| `alanine_sweep_100ns.csv` | 480 | alanine dipeptide, 100 ns trajectory, 2 modes x 3 methods x 10 budgets (100-64,000) x 8 seeds |
| `alanine_sweep.csv` | 288 | superseded 5 ns pilot, seed 0 — retained for provenance only |
| `alanine_sweep_seed1.csv` | 288 | superseded 5 ns pilot, seed 1 — retained for provenance only |
| `dim_ablation.csv` | 540 | Prinz, n_components in {2,3,5} x 3 methods x 6 budgets x 10 seeds |
| `tica_lag_ablation.csv` | 300 | Prinz, lag in {5,10,20,50,100} x 6 budgets x 10 seeds |

## Which alanine file the paper uses

`alanine_sweep_100ns.csv` is the authoritative alanine result and is the file
every alanine number in the manuscript is drawn from. The two 5 ns files are
the discarded pilot described in Section 7: at that trajectory length the
rarest basin (alpha_L/C7ax) was visited inconsistently at the sampling budgets
under study. They are kept in the repository so the pilot-versus-production
comparison in Section 9 can be checked, and should not be used for any other
purpose.

## Reproducing

Run `./run_all.sh` on your own machine. At 20 seeds across both potentials
expect several hours; use `--resume` freely, it skips completed conditions.
