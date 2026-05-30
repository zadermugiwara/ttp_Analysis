#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for cfg in \
  ideal ISR +80 -80 ISR+80 ISR-80 \
  kappa010 kappa015 kappa020 kappa025 kappa030 kappa035 \
  kappa040 kappa045 kappa050 kappa055 kappa060 kappa065
do
  bash "$here/Histograms.sh" "$cfg"
done
