#!/usr/bin/env python3
"""Collect ttp_Analysis cutflow summaries into a CSV file."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs", nargs="+", type=Path, help="out_<sample>.dat files")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", default="clean")
    return parser.parse_args()


def sample_from_path(path: Path) -> str:
    name = path.name
    if name.startswith("out_"):
        name = name[4:]
    if name.endswith(".dat"):
        name = name[:-4]
    return name


def parse_file(path: Path, mode: str) -> list[dict[str, str]]:
    sample = sample_from_path(path)
    rows: list[dict[str, str]] = []
    total_xs = ""
    in_cutflow = False
    cut_line = re.compile(r"^\s*(\d+)\s+(.+?)\s+([0-9]+)\s+([0-9.eE+-]+)\s*$")
    xs_line = re.compile(r"^Cross section \[pb\]:\s*([0-9.eE+-]+)")

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Cutflow summary" in raw:
            in_cutflow = True
            continue
        match = xs_line.search(raw.strip())
        if match:
            total_xs = match.group(1)
            continue
        if not in_cutflow:
            continue
        match = cut_line.match(raw)
        if not match:
            continue
        rows.append(
            {
                "sample": sample,
                "mode": mode,
                "step": match.group(1),
                "cut": match.group(2).strip(),
                "events": match.group(3),
                "weighted_yield": match.group(4),
                "total_cross_section_pb": total_xs,
                "source": str(path),
            }
        )
    for row in rows:
        row["total_cross_section_pb"] = total_xs
    return rows


def main() -> None:
    args = parse_args()
    all_rows: list[dict[str, str]] = []
    for path in args.outputs:
        if not path.exists():
            continue
        all_rows.extend(parse_file(path, args.mode))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["sample", "mode", "step", "cut", "events", "weighted_yield", "total_cross_section_pb", "source"]
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"wrote {len(all_rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
