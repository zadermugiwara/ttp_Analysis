#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  Analysis.sh Tt1M|ttbarra|bkgsm
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

analyzer_bin="$ANALYZER"
if [[ -f "./ttp_Analysis" && -x "./ttp_Analysis" ]]; then
  analyzer_bin="./ttp_Analysis"
fi

run_histograms() {
  local python_bin
  python_bin="$(resolve_python_bin || true)"
  if [[ -z "$python_bin" ]]; then
    echo "[ERROR] Could not find a compatible Python interpreter."
    return 1
  fi
  source_env_script "$ROOT_SETUP" || true
  "$python_bin" "$PY_HISTO"
}

source_env_script "$HERWIG_ENV" || true
source_env_script "$ROOT_SETUP" || true

case "$1" in
  Tt1M)
    for sample in Tt1M1200 Tt1M1500 Tt1M1600 Tt1M1700 Tt1M1800 Tt1M1900 Tt1M2000 Tt1M2100 Tt1M2200 Tt1M2300 Tt1M2400; do
      "$analyzer_bin" "$sample"
    done
    run_histograms
    ;;
  ttbarra)
    "$analyzer_bin" ttbarra
    ;;
  bkgsm)
    for sample in w+w-veve ttveve ttz w+w-z tth w+w- hveve zz hz; do
      "$analyzer_bin" "$sample"
    done
    ;;
  *)
    echo "invalid argument: $1" >&2
    usage
    exit 1
    ;;
esac
