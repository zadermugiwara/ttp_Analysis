#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

source_env_script "$HERWIG_ENV" || true

make -C "$PROG_DIR"

for target in \
  "$ASE_DIR/ttp_Analysis/" \
  "$ASE_DIR/ttp_AnalysisISR/" \
  "$ASE_DIR/ttp_Analysis+80/" \
  "$ASE_DIR/ttp_Analysis-80/" \
  "$ASE_DIR/ttp_Analysis+80ISR/" \
  "$ASE_DIR/ttp_Analysis-80ISR/"
do
  cp "$PROG_DIR/ttp_Analysis" "$target"
done

for cfg in \
  ideal ISR +80 -80 ISR+80 ISR-80 \
  kappa010 kappa015 kappa020 kappa025 kappa030 kappa035 \
  kappa040 kappa045 kappa050 kappa055 kappa060 kappa065
do
  bash "$here/Analysis_type.sh" "$cfg"
done

