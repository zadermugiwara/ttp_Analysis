#!/usr/bin/env bash
# smart_histograms.sh — run Histograms.py for any configs consistently
set -Eeuo pipefail
IFS=$'\n\t'
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

python_bin="$(resolve_python_bin || true)"
if [[ -z "$python_bin" ]]; then
  echo "[ERROR] Could not find a compatible Python interpreter."
  exit 1
fi

# Suggested presets for UI discovery:
# ARGS: ideal
# ARGS: ISR
# ARGS: +80
# ARGS: -80
# ARGS: ISR+80
# ARGS: ISR-80
# ARGS: kappa010
# ARGS: kappa015
# ARGS: kappa020
# ARGS: ideal ISR +80

configs=("${@}")
if [[ ${#configs[@]} -eq 0 ]]; then
  configs=(ideal ISR +80 -80 ISR+80 ISR-80 kappa010 kappa015 kappa020 kappa025 kappa030 kappa035 kappa040 kappa045 kappa050 kappa055 kappa060 kappa065)
fi

for cfg in "${configs[@]}"; do
  dir="$(cfg_dir "$cfg")"
  if [[ ! -d "$dir" ]]; then
    echo "[WARN] Skip $cfg (no dir $dir)"
    continue
  fi
  echo "[HIST] $cfg → $dir"
  pushd "$dir" >/dev/null
  source_env_script "$ROOT_SETUP" || true
  background_dirs="$(background_dirs_for_cfg "$cfg")"
  export ASE_BACKGROUND_DIRS="$background_dirs"
  if [[ -n "$background_dirs" ]]; then
    echo "[CFG] background roots: $background_dirs"
  fi
  "$python_bin" "$PY_HISTO"
  popd >/dev/null
  unset ASE_BACKGROUND_DIRS
done
echo "[DONE] smart_histograms complete."
