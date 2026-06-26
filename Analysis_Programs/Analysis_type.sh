#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  Analysis_type.sh CONFIG

Examples:
  Analysis_type.sh ideal
  Analysis_type.sh ISR
  Analysis_type.sh +80
  Analysis_type.sh -80
  Analysis_type.sh ISR+80
  Analysis_type.sh ISR-80
  Analysis_type.sh kappa010
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

pushd "$dir" >/dev/null
if [[ "$cfg" == kappa* ]]; then
  bash "$here/Analysis.sh" Tt1M
else
  bash "$here/Analysis_for_all.sh"
fi
popd >/dev/null
