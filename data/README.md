# Data provenance and archival status

The committed CSV files in `results/` are the analysis-level data used for the
manuscript figures and tables. `data/alanine_dipeptide.pdb` is the starting
structure for the molecular-dynamics protocol implemented in `src/alanine.py`.
The IID equilibrium control is generated analytically from the synthetic
potentials and therefore requires no additional raw trajectory.

The two exact 100 ns production trajectories used for the reported alanine
results are not currently in this Git repository. The exact seed-1 DCD has
been recovered from the original analysis task and validated for the planned
data deposit, but the exact seed-0 DCD remains unavailable. Re-running the script
reproduces the stated protocol but should not be described as bitwise
reproduction of those trajectories across different OpenMM, driver, or
hardware stacks. Before journal submission, archive both DCD files, the exact
topology, run logs, package environment, and SHA-256 checksums in a versioned
data repository and add its DOI to the manuscript Data Availability section.

The tracked `data/alanine/log_seed1.txt` is the complete 100 ns seed-1
production log (50,000,000 integration steps). The seed-0 log originally
tracked as `log_seed0.txt` ends at 2,500,000 steps and belongs to the
superseded 5 ns pilot; it is retained under the explicit name
`log_seed0_5ns_pilot.txt` and must not be represented as the missing 100 ns
seed-0 production log.

A local `traj_seed99.dcd` found during the publication-readiness audit was not
used: it is neither of the two reported production seeds and therefore cannot
replace their missing raw-data provenance.
