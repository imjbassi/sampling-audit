# Data provenance and archival status

The committed CSV files in `results/` are the analysis-level data used for the
manuscript figures and tables. `data/alanine/alanine.pdb` is the starting
structure for the molecular-dynamics protocol implemented in `src/alanine.py`.
The IID equilibrium control is generated analytically from the synthetic
potentials and therefore requires no additional raw trajectory.

The two exact 100 ns production trajectories used for the reported alanine
results are not currently in this Git repository. Re-running the script
reproduces the stated protocol but should not be described as bitwise
reproduction of those trajectories across different OpenMM, driver, or
hardware stacks. Before journal submission, archive both DCD files, the exact
topology, run logs, package environment, and SHA-256 checksums in a versioned
data repository and add its DOI to the manuscript Data Availability section.

A local `traj_seed99.dcd` found during the publication-readiness audit was not
used: it is neither of the two reported production seeds and therefore cannot
replace their missing raw-data provenance.
