#!/usr/bin/env bash
# common.sh — shared helpers & config
set -Eeuo pipefail
IFS=$'\n\t'
trap 'echo "[ERROR] ${BASH_SOURCE[0]} failed at line $LINENO" >&2' ERR

# ====== User-configurable roots (override via env) ======
DEFAULT_ASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASE_DIR="${ASE_DIR:-$DEFAULT_ASE_DIR}"
PROG_DIR="${PROG_DIR:-$ASE_DIR/Analysis_Programs}"
BUILD_DIR="${BUILD_DIR:-$PROG_DIR}"
ANALYZER="${ANALYZER:-$PROG_DIR/ttp_Analysis}"
PY_HISTO="${PY_HISTO:-$PROG_DIR/Histograms.py}"
ROOT_SETUP="${ROOT_SETUP:-}"
if [[ -z "$ROOT_SETUP" ]]; then
  if [[ -f "$ASE_DIR/Analysis/root/root-new/bin/thisroot.sh" ]]; then
    ROOT_SETUP="$ASE_DIR/Analysis/root/root-new/bin/thisroot.sh"
  else
    ROOT_SETUP="$ASE_DIR/Analysis/root/root/bin/thisroot.sh"
  fi
fi
HERWIG_ENV="${HERWIG_ENV:-$ASE_DIR/HERWIG/bin/activate}"

# Source env scripts (e.g. HERWIG activate) safely when set -u is enabled.
source_env_script() {
  local script="$1"
  [[ -f "$script" ]] || return 0

  local had_nounset=0
  if [[ $- == *u* ]]; then
    had_nounset=1
    set +u
  fi

  # shellcheck disable=SC1090
  source "$script"
  local status=$?

  if (( had_nounset )); then
    set -u
  fi
  return "$status"
}

root_expected_python_minor() {
  local setup="$1"
  local root_prefix cfg version
  root_prefix="$(cd "$(dirname "$setup")/.." && pwd)"
  cfg="$root_prefix/share/root/cmake/ROOTConfig.cmake"
  [[ -f "$cfg" ]] || return 1

  version="$(sed -nE 's/.*ROOT_PYTHON_VERSION[[:space:]]+([0-9]+\.[0-9]+)(\.[0-9]+)?.*/\1/p' "$cfg" | head -n 1)"
  [[ -n "$version" ]] || return 1
  printf "%s" "$version"
}

resolve_python_bin() {
  local candidate

  if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN:-}" ]]; then
    printf "%s" "$PYTHON_BIN"
    return 0
  fi

  if [[ -n "${ROOT_SETUP:-}" && -f "${ROOT_SETUP:-}" ]]; then
    local root_prefix py_minor
    root_prefix="$(cd "$(dirname "$ROOT_SETUP")/.." && pwd)"
    candidate="$root_prefix/bin/python"
    if [[ -x "$candidate" ]]; then
      printf "%s" "$candidate"
      return 0
    fi

    py_minor="$(root_expected_python_minor "$ROOT_SETUP" || true)"
    if [[ -n "$py_minor" ]]; then
      candidate="$(command -v "python${py_minor}" || true)"
      if [[ -n "$candidate" ]]; then
        printf "%s" "$candidate"
        return 0
      fi
    fi
  fi

  for candidate in python3.11 python3.10 python3 /bin/python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

# Map a config token to its analysis directory
cfg_dir() {
  case "$1" in
    ideal)    printf "%s/ttp_Analysis" "$ASE_DIR" ;;
    ISR)      printf "%s/ttp_AnalysisISR" "$ASE_DIR" ;;
    +80)      printf "%s/ttp_Analysis+80" "$ASE_DIR" ;;
    -80)      printf "%s/ttp_Analysis-80" "$ASE_DIR" ;;
    ISR+80)   printf "%s/ttp_Analysis+80ISR" "$ASE_DIR" ;;
    ISR-80)   printf "%s/ttp_Analysis-80ISR" "$ASE_DIR" ;;
    kappa*)   printf "%s/ttp_Analysis_%s" "$ASE_DIR" "$1" ;;
    *)        printf "%s/%s" "$ASE_DIR" "$1" ;;
  esac
}

# Build ttp_Analysis if missing or stale
ensure_build() {
  local cc="$PROG_DIR/ttp_Analysis.cc"
  local mk="$PROG_DIR/Makefile"
  if [[ ! -x "$ANALYZER" || "$ANALYZER" -ot "$cc" || "$ANALYZER" -ot "$mk" ]]; then
    echo "[BUILD] Compiling ttp_Analysis in $PROG_DIR"
    # Try to enable user envs if they exist; don't fail if not present
    [[ -f "$HERWIG_ENV" ]] && source "$HERWIG_ENV" || true
    make -C "$PROG_DIR" -j"$(nproc)"
  fi
}

discover_datasets() {
  # Echo dataset names by inspecting files/list_all_files_* (no hardcoded lists)
  # Strips prefix and extension: list_all_files_XXXXXXXX(.txt|.dat|whatever)
  local ptn="files/list_all_files_"
  if compgen -G "$ptn*" > /dev/null; then
    ls $ptn* 2>/dev/null | sed -E 's@.*/list_all_files_@@; s@\.[^.]+$@@' | sort -u
  elif [[ -f datasets.txt ]]; then
    # Optional fallback curated list, one per line
    cat datasets.txt | sed '/^\s*#/d;/^\s*$/d' | sort -u
  else
    return 1
  fi
}

background_dirs_for_cfg() {
  local cfg="$1"
  local dir
  dir="$(cfg_dir "$cfg")"
  local local_root="$dir/root"

  local -a candidates=()
  if [[ -d "$local_root" ]]; then
    candidates+=("$local_root")
  fi

  local pol=""
  if [[ "$cfg" == *"+80"* ]]; then
    pol="+80"
  elif [[ "$cfg" == *"-80"* ]]; then
    pol="-80"
  fi

  local token="ideal"
  if [[ "$cfg" == *"ISR"* ]]; then
    token="ISR"
    if [[ -n "$pol" ]]; then
      token="ISR${pol}"
    fi
  elif [[ -n "$pol" ]]; then
    token="$pol"
  fi

  local fallback
  fallback="$(cfg_dir "$token")/root"
  if [[ -d "$fallback" ]]; then
    candidates+=("$fallback")
  fi

  local base
  base="$(cfg_dir ideal)/root"
  if [[ -d "$base" ]]; then
    candidates+=("$base")
  fi

  declare -A seen=()
  local -a ordered=()
  local have_realpath=0
  if command -v realpath >/dev/null 2>&1; then
    have_realpath=1
  fi

  local path resolved
  for path in "${candidates[@]}"; do
    [[ -z "$path" ]] && continue
    if [[ ! -d "$path" ]]; then
      continue
    fi
    resolved="$path"
    if (( have_realpath )); then
      resolved="$(realpath "$path" 2>/dev/null || echo "$path")"
    fi
    if [[ -z "${seen[$resolved]:-}" ]]; then
      ordered+=("$resolved")
      seen[$resolved]=1
    fi
  done

  if [[ ${#ordered[@]} -eq 0 ]]; then
    ordered+=("$local_root")
  fi

  (IFS=':'; printf "%s" "${ordered[*]}")
}
