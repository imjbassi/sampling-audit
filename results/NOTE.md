# Note on the results in this directory

`sweep.csv` is PARTIAL. The sweep was launched twice in the build container and
was killed both times before completion (memory contention). Roughly 10-17 of
120 conditions finished, all in the `short` / `pca` corner of the grid.

**Do not cite any number from this file.** It exists only to show the output
schema is correct and the pipeline runs end to end.

The two figures that ARE complete and trustworthy (`figures/fig1_landscape`,
`figures/fig2_embedding_grid`) do not depend on the sweep — they are generated
directly from the potentials and the embedders.

To produce real results, run `./run_all.sh` on your own machine. At 20 seeds
across both potentials expect several hours; use `--resume` freely, it skips
completed conditions.
