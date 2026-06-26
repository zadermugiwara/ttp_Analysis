#!/usr/bin/env python3
"""Extract top-partner widths from MadGraph param cards into CSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


DECAY_RE = re.compile(
    r"^\s*DECAY\s+6000006\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
    re.MULTILINE,
)
MASS_RE = re.compile(r"^Tt(\d+)", re.IGNORECASE)
KAPPA_RE = re.compile(r"kappa\s*0[ \t._-]*([0-9]+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--madgraph-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/widths.csv"))
    return parser.parse_args()


def find_param_card(directory: Path) -> Path | None:
    for candidate in (directory / "Cards/param_card.dat", directory / "param_card.dat"):
        if candidate.is_file():
            return candidate
    return None


def main() -> None:
    args = parse_args()
    rows: list[dict[str, object]] = []
    for directory in sorted(args.madgraph_root.iterdir()):
        if not directory.is_dir():
            continue
        mass_match = MASS_RE.search(directory.name)
        card = find_param_card(directory)
        if not mass_match or not card:
            continue
        width_match = DECAY_RE.search(card.read_text(errors="ignore"))
        if not width_match:
            continue
        kappa_match = KAPPA_RE.search(directory.name)
        rows.append(
            {
                "sample": directory.name,
                "mass_GeV": int(mass_match.group(1)),
                "kappa": int(kappa_match.group(1)) / 100.0 if kappa_match else 0.20,
                "width_GeV": float(width_match.group(1)),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample", "mass_GeV", "kappa", "width_GeV"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} widths to {args.output}")


if __name__ == "__main__":
    main()
