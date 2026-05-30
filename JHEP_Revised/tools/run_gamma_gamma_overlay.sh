#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ASE_DIR="${ASE_DIR:-/home/higinio/Documentos/ASE}"
HERWIG_ENV="${HERWIG_ENV:-$ASE_DIR/HERWIG/bin/activate}"
CONFIG="${CONFIG:-$ASE_DIR/JHEP_Revised/config/herwig_clic_gamma_gamma_overlay.in}"
OUT="$ASE_DIR/JHEP_Revised/data/overlay/gamma_gamma_hadrons_3tev.hepmc"
LIST="$ASE_DIR/JHEP_Revised/data/overlay/gamma_gamma_overlay_files.txt"
NEVENTS="${NEVENTS:-1000}"
SEED="${SEED:-12345}"

if [[ ! -f "$HERWIG_ENV" ]]; then
  echo "[ERROR] Missing Herwig environment: $HERWIG_ENV" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

set +u
# shellcheck disable=SC1090
source "$HERWIG_ENV"
set -u

pushd "$ASE_DIR" >/dev/null
rm -f "$OUT" CLICGammaGammaOverlay.run
Herwig read "$CONFIG"
Herwig run CLICGammaGammaOverlay.run -N "$NEVENTS" -s "$SEED"
printf "%s\n" "$OUT" > "$LIST"
popd >/dev/null

echo "[OK] overlay HepMC: $OUT"
echo "[OK] overlay list:  $LIST"
echo "Use with:"
echo "  ASE_GG_OVERLAY_LIST=$LIST ASE_GG_OVERLAY_BX=1 Analysis_Programs/ttp_Analysis Tt1M1200"
