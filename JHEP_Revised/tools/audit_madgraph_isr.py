#!/usr/bin/env python3
"""Audit and optionally repair ISR-related MadGraph cards.

The script checks the generated project directories on the Expansion drive for
two reproducibility problems found during the revision:

* ISR Pythia cards missing explicit QED lepton-shower settings.
* Copied proc cards whose ``output`` line still names a different project.

It is intentionally conservative: physics run-card settings are only reported,
not changed, except for appending missing Pythia shower lines and fixing stale
proc-card output labels when ``--fix`` is passed.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


PYTHIA_LINES = [
    "SpaceShower:QEDshowerByL = on",
    "TimeShower:QEDshowerByL  = on",
    "SpaceShower:pTminChgL    = 0.1",
    "PDF:lepton             = on",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--madgraph-root",
        type=Path,
        default=Path("/media/higinio/Expansion1/Madgraph"),
        help="Directory containing generated MadGraph process folders.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("JHEP_Revised/logs/madgraph_isr_card_audit.csv"),
        help="CSV manifest to write.",
    )
    parser.add_argument("--fix", action="store_true", help="Apply safe card fixes.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def ensure_pythia_lines(path: Path, fix: bool) -> list[str]:
    if not path.exists():
        return ["missing_pythia_card"]

    text = read_text(path)
    missing = [line for line in PYTHIA_LINES if line.split("=")[0].strip() not in text]
    if missing and fix:
        block = "\n! Revision standardization: lepton ISR/QED shower settings\n"
        block += "\n".join(missing) + "\n"
        write_text(path, text.rstrip() + block)
    return [f"missing_pythia:{line}" for line in missing]


def ensure_proc_output(path: Path, project_name: str, fix: bool) -> list[str]:
    if not path.exists():
        return ["missing_proc_card"]

    text = read_text(path)
    match = re.search(r"(?m)^(\s*output\s+)(\S+)(.*)$", text)
    if not match:
        return ["missing_proc_output"]

    current = match.group(2)
    if current == project_name:
        return []

    if fix:
        fixed = text[: match.start()] + f"{match.group(1)}{project_name}{match.group(3)}" + text[match.end() :]
        write_text(path, fixed)
    return [f"stale_proc_output:{current}->{project_name}"]


def run_card_summary(path: Path) -> dict[str, str]:
    keys = {"lpp1", "lpp2", "ebeam1", "ebeam2", "polbeam1", "polbeam2", "pdlabel", "pdlabel1", "pdlabel2", "lhaid"}
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in read_text(path).splitlines():
        line = raw.split("!", 1)[0]
        if "=" not in line:
            continue
        value, key = [part.strip() for part in line.split("=", 1)]
        if key in keys:
            out[key] = value
    return out


def main() -> None:
    args = parse_args()
    rows: list[dict[str, str]] = []
    for project in sorted(args.madgraph_root.iterdir()):
        if not project.is_dir() or "ISR" not in project.name:
            continue
        cards = project / "Cards"
        actions: list[str] = []
        actions.extend(ensure_pythia_lines(cards / "pythia8_card.dat", args.fix))
        actions.extend(ensure_proc_output(cards / "proc_card_mg5.dat", project.name, args.fix))
        summary = run_card_summary(cards / "run_card.dat")
        rows.append(
            {
                "project": project.name,
                "actions": ";".join(actions) if actions else "ok",
                **summary,
            }
        )

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "project",
            "actions",
            "lpp1",
            "lpp2",
            "ebeam1",
            "ebeam2",
            "polbeam1",
            "polbeam2",
            "pdlabel",
            "pdlabel1",
            "pdlabel2",
            "lhaid",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    changed = [row for row in rows if row["actions"] != "ok"]
    mode = "fixed" if args.fix else "found"
    print(f"{mode} {len(changed)} projects with ISR-card issues")
    print(f"manifest: {args.manifest}")


if __name__ == "__main__":
    main()
