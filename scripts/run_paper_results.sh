#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$RESULTS_DIR/paper"

"$PYTHON_BIN" "$ROOT_DIR/plotting/signals_after_cuts.py" \
  --output "$RESULTS_DIR/paper/signals_after_cuts.pdf"

"$PYTHON_BIN" "$ROOT_DIR/plotting/recoil_baseline.py" \
  --mass 1200 --outdir "$RESULTS_DIR/paper" --formats pdf

"$PYTHON_BIN" "$ROOT_DIR/plotting/recoil_comparison.py" \
  --masses 1200 1600 2000 2400 \
  --scenarios base minus80 \
  --outdir "$RESULTS_DIR/paper" --formats pdf

"$PYTHON_BIN" "$ROOT_DIR/Analysis_Programs/kappa_vs_significance_3d_auto.py" \
  --out-dir "$RESULTS_DIR/kappa_baseline"
cp "$RESULTS_DIR/kappa_baseline/kappa_mass_significance_heat_points.png" \
  "$RESULTS_DIR/paper/kappa_scan_baseline.png"

"$PYTHON_BIN" "$ROOT_DIR/Analysis_Programs/kappa_vs_significance_3d_auto.py" \
  --dir-suffix=-80ISR \
  --out-dir "$RESULTS_DIR/kappa_minus80ISR"
cp "$RESULTS_DIR/kappa_minus80ISR/kappa_mass_significance_heat_points.png" \
  "$RESULTS_DIR/paper/kappa_scan_minus80ISR.png"

echo "Paper result assets written to $RESULTS_DIR/paper"
