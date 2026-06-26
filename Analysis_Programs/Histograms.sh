#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  Histograms.sh CONFIG

Examples:
  Histograms.sh ideal
  Histograms.sh ISR
  Histograms.sh +80
  Histograms.sh -80
  Histograms.sh ISR+80
  Histograms.sh ISR-80
  Histograms.sh kappa010
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

cfg="$1"
dir="$(cfg_dir "$cfg")"
if [[ ! -d "$dir" ]]; then
  echo "[ERROR] Invalid config '$cfg' (directory not found: $dir)." >&2
  exit 1
fi

python_bin="$(resolve_python_bin || true)"
if [[ -z "$python_bin" ]]; then
  echo "[ERROR] Could not find a compatible Python interpreter." >&2
  exit 1
fi

echo "[HIST] $cfg -> $dir"
pushd "$dir" >/dev/null
source_env_script "$ROOT_SETUP" || true
background_dirs="$(background_dirs_for_cfg "$cfg")"
export ASE_BACKGROUND_DIRS="$background_dirs"
"$python_bin" "$PY_HISTO"
unset ASE_BACKGROUND_DIRS
popd >/dev/null
