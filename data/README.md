# Data provenance and archival status

The committed CSV files in `results/` are the analysis-level data used for the
manuscript figures and tables. `data/alanine_dipeptide.pdb` is the starting
structure for the molecular-dynamics protocol implemented in `src/alanine.py`.
The IID equilibrium control is generated analytically from the synthetic
potentials and therefore requires no additional raw trajectory.

The two exact 100 ns production trajectories used for the reported alanine
results have been recovered and validated for a versioned data deposit. They
are intentionally excluded from Git because each DCD is about 28.8 MB. The
seed-0 trajectory was recovered from the original WSL analysis workspace at
`~/sampling-audit/data/alanine/traj_seed0.dcd`; the archived Claude transcript
records the completed sweep reading that exact path. The seed-1 trajectory was
recovered from the original analysis task's scratch space. Each DCD contains
100,000 frames and 22 atoms at a 1 ps saved-frame interval. Re-running the
script reproduces the stated protocol but should not be described as bitwise
reproduction of trajectories across different OpenMM, driver, or hardware
stacks. The versioned data deposit should contain both DCD files, the exact
topology, production logs, package environment, and SHA-256 checksums; add its
DOI to the manuscript Data Availability section before journal submission.

The tracked `data/alanine/log_seed0.txt` and `log_seed1.txt` files are the
complete 100 ns production logs, each ending at 50,000,000 integration steps.
The earlier seed-0 log that originally occupied `log_seed0.txt` ended at
2,500,000 steps and belongs to the superseded 5 ns pilot; it is retained under
the explicit name `log_seed0_5ns_pilot.txt`.

Recovery checksums for the raw trajectories are:

- seed 0: `f861a2853d7b810c462c95a1e46090818d60f3085d6f152f677d2c25c9ba1f28`
- seed 1: `c7eefa469ab5617c96746cc02234c497c54804f9a8f564b48a9b9c1c64a15542`

A local `traj_seed99.dcd` found during the publication-readiness audit was not
used: it is neither of the two reported production seeds and therefore cannot
replace their missing raw-data provenance.
