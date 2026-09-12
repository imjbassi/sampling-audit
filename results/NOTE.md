# Note on the results in this directory

All sweeps in this directory are complete. An earlier revision of this file
warned that `sweep.csv` was partial after two killed runs in the build
container; that is no longer the case and the warning has been removed.

| file | conditions | grid |
|---|---|---|
| `sweep.csv` | 960 | Müller-Brown, 2 modes x 3 methods x 8 budgets (250-32,000) x 20 seeds |
| `sweep_prinz.csv` | 960 | Prinz, 2 modes x 3 methods x 8 budgets (250-32,000) x 20 seeds |
| `alanine_sweep_100ns.csv` | 480 | alanine dipeptide seed 0, 100 ns, 2 modes x 3 methods x 10 budgets (100-64,000) x 8 seeds |
| `alanine_sweep_100ns_seed1.csv` | 432 | alanine dipeptide seed 1, 100 ns, same grid truncated at 32,000 |
| `alanine_sweep.csv` | 288 | superseded 5 ns pilot, seed 0 — retained for provenance only |
| `alanine_sweep_seed1.csv` | 288 | superseded 5 ns pilot, seed 1 — retained for provenance only |
| `dim_ablation.csv` | 540 | Prinz, n_components in {2,3,5} x 3 methods x 6 budgets x 10 seeds |
| `tica_lag_ablation.csv` | 300 | Prinz, lag in {5,10,20,50,100} x 6 budgets x 10 seeds |

## Which alanine file the paper uses

`alanine_sweep_100ns.csv` (seed 0) is the primary alanine result and the file
every alanine number in the manuscript is drawn from unless stated otherwise.
`alanine_sweep_100ns_seed1.csv` is an independent physical replicate -- a
separate 100 ns Langevin run, not merely a re-seeded analysis of the same
trajectory -- and backs the cross-seed comparison in Section 7. It stops at
32,000 frames rather than 64,000: it exists to test seed-independence, not to
extend the budget range, and the top budget dominates the sweep's cost. The two 5 ns files are
the discarded pilot described in Section 7: at that trajectory length the
rarest basin (alpha_L/C7ax) was visited inconsistently at the sampling budgets
under study. They are kept in the repository so the pilot-versus-production
comparison in Section 9 can be checked, and should not be used for any other
purpose.

## Reproducing

Run `./run_all.sh` on your own machine. At 20 seeds across both potentials
expect several hours; use `--resume` freely, it skips completed conditions.
