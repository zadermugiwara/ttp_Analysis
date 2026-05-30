#!/usr/bin/env python3
"""Run the sqrt(s') diagnostic for all completed manifest samples."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("JHEP_Revised/logs/production_manifest.csv"))
    parser.add_argument("--script", type=Path, default=Path("JHEP_Revised/tools/sqrt_s_prime_analysis.py"))
    parser.add_argument("--out-dir", type=Path, default=Path("JHEP_Revised/data/sqrt_s_prime_isronlyll_nev10000"))
    parser.add_argument("--fig-dir", type=Path, default=Path("JHEP_Revised/figs/sqrt_s_prime_isronlyll_nev10000"))
    parser.add_argument("--sample", action="append", default=[], help="Run only these manifest sample names.")
    parser.add_argument("--max-events", type=int, default=0)
    parser.add_argument("--write-events", action="store_true")
    return parser.parse_args()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    args = parse_args()
    wanted = set(args.sample)
    command = [
        sys.executable,
        str(args.script),
        "--out-dir",
        str(args.out_dir),
        "--fig-dir",
        str(args.fig_dir),
    ]
    if args.max_events:
        command.extend(["--max-events", str(args.max_events)])
    if args.write_events:
        command.append("--write-events")

    selected = 0
    for row in read_manifest(args.manifest):
        if row.get("status") != "ok":
            continue
        if wanted and row["sample"] not in wanted:
            continue
        decayed_lhe = Path(row.get("decayed_lhe", ""))
        if not (decayed_lhe.exists() and decayed_lhe.stat().st_size > 0):
            continue
        command.extend(["--sample", f"{row['sample']}={decayed_lhe}"])
        selected += 1

    if selected == 0:
        raise SystemExit("no completed LHE samples selected")

    print(f"running sqrt(s') for {selected} samples")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
