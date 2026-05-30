#!/usr/bin/env bash
# smart_analysis.sh — one script to compile, run analyses in any config, optionally in parallel,
# and (optionally) build histograms.
set -Eeuo pipefail
IFS=$'\n\t'
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

usage() {
  cat <<'USAGE'
Usage:
  smart_analysis.sh [options]
Options:
  -c, --configs  Comma-separated list of configs (default: a sensible set)
                  Examples: "ideal,ISR,+80", "kappa010,kappa015,kappa020"
  -j, --jobs     Parallel jobs per config (default: 1). Requires GNU parallel or xargs.
      --include  Regex filter to include dataset names (applied after discovery)
      --exclude  Regex filter to exclude dataset names
      --histos   After running ttp_Analysis, also call Histograms.py in each config
  -h, --help     Show this help

Configs map → directories:
  ideal→ttp_Analysis, ISR→ttp_AnalysisISR, +80→ttp_Analysis+80, -80→ttp_Analysis-80,
  ISR+80→ttp_Analysis+80ISR, ISR-80→ttp_Analysis-80ISR, kappaXYZ→ttp_Analysis_kappaXYZ

Examples:
  # Run all defaults serially
  smart_analysis.sh
  # Run only ISR and +80 with 4-way parallelism
  smart_analysis.sh -c ISR,+80 -j 4
  # Only signals (by name pattern), any configs
  smart_analysis.sh --include '^Tt1M' -j 8
  # Everything and then histograms
  smart_analysis.sh --histos
# ARGS: --histos
# ARGS: -c ideal,ISR,+80
# ARGS: -c kappa010,kappa015,kappa020 -j 4
# ARGS: --include "^Tt1M"
# ARGS: --exclude "^ttbarra"
# ARGS: --jobs 4
USAGE
}

# ====== Defaults ======
# Build default configs dynamically from available directories
mapfile -t DEFAULT_CONFIGS < <(
  printf "ideal\n"
  find "$ASE_DIR" -maxdepth 1 -type d -name 'ttp_Analysis*' -printf '%f\n' \
    | sort \
    | while read -r base; do
        case "$base" in
          ttp_Analysis) echo ideal ;;
          ttp_Analysis+*) echo "${base#ttp_Analysis}" ;;
          ttp_Analysis-*) echo "${base#ttp_Analysis}" ;;
          ttp_Analysis_*) echo "${base#ttp_Analysis_}" ;;
          *) : ;;
        esac
      done \
    | grep -Ev '^ideal$'
)

# Deduplicate while preserving order
declare -A seen_cfg
configs=()
for cfg in "${DEFAULT_CONFIGS[@]}"; do
  [[ -z "$cfg" ]] && continue
  if [[ -z "${seen_cfg[$cfg]:-}" ]]; then
    configs+=("$cfg")
    seen_cfg[$cfg]=1
  fi
done

jobs=1
include=""
exclude=""
run_histos=0

# ====== Parse CLI ======
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--configs) IFS=',' read -r -a configs <<< "$2"; shift 2;;
    -j|--jobs) jobs="$2"; shift 2;;
    --include) include="$2"; shift 2;;
    --exclude) exclude="$2"; shift 2;;
    --histos) run_histos=1; shift ;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

python_bin="$(resolve_python_bin || true)"
if [[ -z "$python_bin" ]]; then
  echo "[ERROR] Could not find a compatible Python interpreter."
  exit 1
fi

ensure_build

run_one_cfg() {
  local cfg="$1"
  local dir
  dir="$(cfg_dir "$cfg")"
  if [[ ! -d "$dir" ]]; then
    echo "[WARN] Skip $cfg → directory not found: $dir"
    return
  fi

  echo "[CFG] $cfg → $dir"
  pushd "$dir" >/dev/null

  # Light env setup if available
  source_env_script "$HERWIG_ENV" || true
  source_env_script "$ROOT_SETUP" || true

  # Discover datasets dynamically
  mapfile -t names < <(discover_datasets || true)
  if [[ ${#names[@]} -eq 0 ]]; then
    echo "[WARN] No dataset lists found (files/list_all_files_* or datasets.txt)."
    popd >/dev/null
    return
  fi

  # Apply filters
  if [[ -n "$include" ]]; then
    mapfile -t names < <(printf "%s\n" "${names[@]}" | grep -E "$include" || true)
  fi
  if [[ -n "$exclude" ]]; then
    mapfile -t names < <(printf "%s\n" "${names[@]}" | grep -Ev "$exclude" || true)
  fi
  if [[ ${#names[@]} -eq 0 ]]; then
    echo "[INFO] Nothing to run in $cfg after filters."
    popd >/dev/null
    return
  fi

  echo "[RUN] $cfg: ${#names[@]} dataset(s)"

  local background_dirs
  background_dirs="$(background_dirs_for_cfg "$cfg")"
  export ASE_BACKGROUND_DIRS="$background_dirs"
  if [[ -n "$background_dirs" ]]; then
    echo "[CFG] background roots: $background_dirs"
  fi

  export ANALYZER
  _runner() {
    local cfg_name="$1"
    local n="$2"
    echo "[RUN] $cfg_name :: $n"
    set +e
    "$ANALYZER" "$n"
    local status=$?
    set -e
    if [[ $status -ne 0 ]]; then
      echo "[WARN] Analyzer failed for ${cfg_name} :: ${n} (status=$status). Skipping."
    fi
  }

  if command -v parallel >/dev/null 2>&1; then
    printf "%s\n" "${names[@]}" | parallel -j "$jobs" --halt soon,fail=1 --no-run-if-empty _runner "$cfg" {}
  else
    # Fallback: xargs parallelism
    export -f _runner
    printf "%s\n" "${names[@]}" | xargs -P "$jobs" -I{} bash -c '_runner "$@"' _ "$cfg" {}
  fi

  if (( run_histos )); then
    echo "[HIST] $cfg: running Histograms.py"
    "$python_bin" "$PY_HISTO"
  fi
  popd >/dev/null
  unset ASE_BACKGROUND_DIRS
}

for cfg in "${configs[@]}"; do
  run_one_cfg "$cfg"
done

echo "[DONE] smart_analysis complete."
