#!/usr/bin/env bash
# Full synthetic reproduction. Expect several hours on CPU.
set -euo pipefail
OUTDIR="${OUTDIR:-reproduction_results}"
FIGDIR="${FIGDIR:-reproduction_figures}"
mkdir -p "$OUTDIR" "$FIGDIR"

echo "=== Mueller-Brown (primary) ==="
python src/sweep.py --potential mueller_brown \
  --methods pca tica vae \
  --budgets 250 500 1000 2000 4000 8000 16000 32000 \
  --seeds 20 --modes short subsample \
  --out "$OUTDIR/sweep.csv"

echo "=== Prinz 1D (generality check) ==="
python src/sweep.py --potential prinz1d \
  --methods pca tica vae \
  --budgets 250 500 1000 2000 4000 8000 16000 32000 \
  --seeds 20 --modes short subsample \
  --out "$OUTDIR/sweep_prinz.csv"

echo "=== TICA lag ablation (Prinz) ==="
python src/tica_lag_ablation.py --out "$OUTDIR/tica_lag_ablation.csv"

echo "=== Embedding-dimension ablation (Prinz) ==="
python src/dim_ablation.py --out "$OUTDIR/dim_ablation.csv"

echo "=== IID equilibrium control (exact latent coordinates) ==="
python src/iid_equilibrium_control.py --out "$OUTDIR/iid_equilibrium_control.csv"

echo "=== Figures ==="
python src/figures.py --results "$OUTDIR/sweep.csv" --outdir "$FIGDIR/mueller_brown"
python src/figures.py --results "$OUTDIR/sweep_prinz.csv" \
  --outdir "$FIGDIR/prinz" --potential prinz1d

echo "=== Tables ==="
python src/report.py --results "$OUTDIR/sweep.csv" --out "$OUTDIR/tables.md"
python src/report.py --results "$OUTDIR/sweep_prinz.csv" --out "$OUTDIR/tables_prinz.md"
