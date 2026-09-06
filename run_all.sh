#!/usr/bin/env bash
# Full reproduction. Expect several hours on CPU.
set -euo pipefail
mkdir -p results figures

echo "=== Mueller-Brown (primary) ==="
python src/sweep.py --potential mueller_brown \
  --methods pca tica vae \
  --budgets 250 500 1000 2000 4000 8000 16000 32000 \
  --seeds 20 --modes short subsample \
  --out results/sweep.csv --resume

echo "=== Prinz 1D (generality check) ==="
python src/sweep.py --potential prinz1d \
  --methods pca tica vae \
  --budgets 250 500 1000 2000 4000 8000 16000 32000 \
  --seeds 20 --modes short subsample \
  --out results/sweep_prinz.csv --resume

echo "=== Figures ==="
python src/figures.py --results results/sweep.csv --outdir figures
python src/figures.py --results results/sweep_prinz.csv \
  --outdir figures_prinz --potential prinz1d

echo "=== Tables ==="
python src/report.py --results results/sweep.csv --out results/tables.md
