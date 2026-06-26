#!/usr/bin/env python3
"""Create the reusable MadGraph process template used by the workflow."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "generation/models/VLQ_UFO"
CARDS = ROOT / "generation/cards"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mg5", default=shutil.which("mg5_aMC"), help="Path to mg5_aMC.")
    parser.add_argument("--output", type=Path, required=True, help="MadGraph process directory.")
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.mg5:
        raise SystemExit("mg5_aMC was not found; pass --mg5 /path/to/mg5_aMC")
    if args.output.exists():
        if not args.force:
            raise SystemExit(f"{args.output} already exists; pass --force to replace it")
        shutil.rmtree(args.output)

    commands = f"""import model {MODEL}
define myt = t t~
define mytp = tp tp~
generate e+ e- > myt mytp
output {args.output.resolve()}
"""
    with tempfile.NamedTemporaryFile("w", suffix=".mg5", delete=False) as handle:
        handle.write(commands)
        command_file = Path(handle.name)
    try:
        subprocess.run([args.mg5, str(command_file)], check=True)
    finally:
        command_file.unlink(missing_ok=True)

    target_cards = args.output / "Cards"
    for name in ("run_card.dat", "param_card.dat", "madspin_card.dat", "pythia8_card.dat"):
        shutil.copy2(CARDS / name, target_cards / name)
    print(f"Created process template: {args.output}")


if __name__ == "__main__":
    main()
