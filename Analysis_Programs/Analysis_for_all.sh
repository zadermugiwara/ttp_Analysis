#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$here/common.sh"

source_env_script "$HERWIG_ENV" || true

bash "$here/Analysis.sh" bkgsm
bash "$here/Analysis.sh" ttbarra
bash "$here/Analysis.sh" Tt1M
