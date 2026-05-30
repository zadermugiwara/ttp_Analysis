#!/usr/bin/env python3
"""Repair macOS IntxLNK placeholder files in copied MadGraph projects.

Some project directories on the Expansion drive contain files whose content is
an ``IntxLNK`` record instead of a real POSIX symlink.  gfortran then tries to
compile the placeholder bytes and fails.  This tool converts those placeholders
back into symbolic links.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path


MAGIC = b"IntxLNK\x01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="*", type=Path, help="MadGraph project directories to repair.")
    parser.add_argument("--madgraph-root", type=Path, default=Path("/media/higinio/Expansion1/Madgraph"))
    parser.add_argument("--all-isr", action="store_true", help="Repair all *ISR* projects under --madgraph-root.")
    parser.add_argument(
        "--known-mg5-links",
        action="store_true",
        help="Only inspect standard MG5 link locations instead of recursively scanning every file.",
    )
    parser.add_argument("--manifest", type=Path, default=Path("JHEP_Revised/logs/madgraph_intxlnk_repair.csv"))
    parser.add_argument("--fix", action="store_true", help="Replace placeholders with symlinks.")
    return parser.parse_args()


def link_target(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data.startswith(MAGIC):
        return None
    raw = data[len(MAGIC) :]
    try:
        return raw.decode("utf-16le").rstrip("\x00")
    except UnicodeDecodeError:
        return None


def projects(args: argparse.Namespace) -> list[Path]:
    if args.all_isr:
        return sorted(path for path in args.madgraph_root.iterdir() if path.is_dir() and "ISR" in path.name)
    return args.project


def known_link_candidates(project: Path) -> list[Path]:
    """Return standard MG5 link paths likely to contain IntxLNK placeholders."""
    rels = [
        "Source/coupl.inc",
        "Source/leshouche.inc",
        "Source/maxamps.inc",
        "Source/nexternal.inc",
        "SubProcesses/coupl.inc",
        "SubProcesses/cuts.inc",
        "SubProcesses/genps.inc",
        "SubProcesses/lhe_event_infos.inc",
        "SubProcesses/maxconfigs.inc",
        "SubProcesses/maxparticles.inc",
        "SubProcesses/run.inc",
        "SubProcesses/run_config.inc",
    ]
    p_rels = [
        "reweight.f",
        "run.inc",
        "run_config.inc",
        "setcuts.f",
        "setscales.f",
        "sudakov.inc",
        "symmetry.f",
        "unwgt.f",
        "addmothers.f",
        "cluster.f",
        "cluster.inc",
        "idenparts.f",
        "initcluster.f",
        "lhe_event_infos.inc",
        "makefile",
        "maxconfigs.inc",
        "maxparticles.inc",
        "message.inc",
        "myamp.f",
        "genps.f",
        "genps.inc",
        "coupl.inc",
        "cuts.f",
        "cuts.inc",
        "dummy_fct.f",
    ]
    out = [project / rel for rel in rels]
    sub = project / "SubProcesses"
    if sub.exists():
        for pdir in sub.glob("P*"):
            if pdir.is_dir():
                out.extend(pdir / rel for rel in p_rels)
    return out


def main() -> None:
    args = parse_args()
    rows: list[dict[str, str]] = []
    for project in projects(args):
        if not project.exists():
            rows.append({"project": str(project), "file": "", "target": "", "action": "missing_project"})
            continue
        candidates = known_link_candidates(project) if args.known_mg5_links else project.rglob("*")
        for path in candidates:
            if not path.exists() or not path.is_file() or path.is_symlink():
                continue
            target = link_target(path)
            if target is None:
                continue
            action = "would_relink"
            if args.fix:
                path.unlink()
                os.symlink(target, path)
                action = "relinked"
            rows.append({"project": str(project), "file": str(path), "target": target, "action": action})

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["project", "file", "target", "action"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'fixed' if args.fix else 'found'} {len(rows)} IntxLNK placeholders")
    print(f"manifest: {args.manifest}")


if __name__ == "__main__":
    main()
