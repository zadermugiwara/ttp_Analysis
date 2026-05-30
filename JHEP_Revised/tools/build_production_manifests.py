#!/usr/bin/env python3
"""Build reconstruction manifests from completed MG5 queue jobs.

The reconstruction code reads one text file per sample under
``ttp_AnalysisISR/files/list_all_files_<sample>``.  This tool turns the MG5
queue status into those list files and records the corresponding LHE/HepMC
locations in a CSV manifest.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=Path, default=Path("JHEP_Revised/logs/mg5_queue_status.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("JHEP_Revised/logs/production_manifest.csv"))
    parser.add_argument("--analysis-dir", type=Path, default=Path("ttp_AnalysisISR"))
    parser.add_argument("--require-ok", action="store_true", help="Only emit rows/list files for jobs with status=ok.")
    parser.add_argument("--decompress-hepmc", action="store_true", help="Create .hepmc files from .hepmc.gz when needed.")
    return parser.parse_args()


def read_status(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_command(path: Path) -> tuple[Path, str]:
    project_dir: Path | None = None
    run_name: str | None = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("launch "):
                parts = line.split()
                if len(parts) >= 2:
                    project_dir = Path(parts[1])
                if "-n" in parts:
                    idx = parts.index("-n")
                    if idx + 1 < len(parts):
                        run_name = parts[idx + 1]
            if project_dir is not None and run_name is not None:
                break
    if project_dir is None or run_name is None:
        raise ValueError(f"could not parse launch project/run from {path}")
    return project_dir, run_name


def sample_name(command: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", command.stem)


def file_state(path: Path) -> str:
    if path.exists() and path.stat().st_size > 0:
        return "ready"
    if path.exists():
        return "empty"
    return "missing"


def maybe_decompress(gz_path: Path, out_path: Path) -> None:
    if out_path.exists() and out_path.stat().st_size > 0:
        return
    if not (gz_path.exists() and gz_path.stat().st_size > 0):
        return
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with gzip.open(gz_path, "rb") as src, tmp_path.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    tmp_path.replace(out_path)


def main() -> None:
    args = parse_args()
    rows = read_status(args.status)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    list_dir = args.analysis_dir / "files"
    list_dir.mkdir(parents=True, exist_ok=True)

    out_rows: list[dict[str, str]] = []
    for row in rows:
        command = Path(row["command"])
        if args.require_ok and row.get("status") != "ok":
            continue
        try:
            project_dir, run_name = parse_command(command)
        except Exception as exc:
            out_rows.append(
                {
                    "sample": sample_name(command),
                    "command": str(command),
                    "status": row.get("status", ""),
                    "project": "",
                    "project_dir": "",
                    "run_name": "",
                    "hard_lhe": "",
                    "decayed_lhe": "",
                    "hepmc": "",
                    "hepmc_gz": "",
                    "hepmc_for_analysis": "",
                    "state": f"parse_error:{exc}",
                    "list_file": "",
                }
            )
            continue

        event_dir = project_dir / "Events" / f"{run_name}_decayed_1"
        hard_lhe = project_dir / "Events" / run_name / "unweighted_events.lhe.gz"
        decayed_lhe = event_dir / "unweighted_events.lhe.gz"
        hepmc = event_dir / "tag_1_pythia8_events.hepmc"
        hepmc_gz = event_dir / "tag_1_pythia8_events.hepmc.gz"
        if args.decompress_hepmc:
            maybe_decompress(hepmc_gz, hepmc)

        hepmc_for_analysis = hepmc if file_state(hepmc) == "ready" else Path("")
        state_bits = [
            f"hard_lhe={file_state(hard_lhe)}",
            f"decayed_lhe={file_state(decayed_lhe)}",
            f"hepmc={file_state(hepmc)}",
            f"hepmc_gz={file_state(hepmc_gz)}",
        ]
        list_file = ""
        if hepmc_for_analysis:
            list_path = list_dir / f"list_all_files_{sample_name(command)}"
            list_path.write_text(str(hepmc_for_analysis.resolve()) + "\n", encoding="utf-8")
            list_file = str(list_path)

        out_rows.append(
            {
                "sample": sample_name(command),
                "command": str(command),
                "status": row.get("status", ""),
                "project": project_dir.name,
                "project_dir": str(project_dir),
                "run_name": run_name,
                "hard_lhe": str(hard_lhe),
                "decayed_lhe": str(decayed_lhe),
                "hepmc": str(hepmc),
                "hepmc_gz": str(hepmc_gz),
                "hepmc_for_analysis": str(hepmc_for_analysis),
                "state": ";".join(state_bits),
                "list_file": list_file,
            }
        )

    fields = [
        "sample",
        "command",
        "status",
        "project",
        "project_dir",
        "run_name",
        "hard_lhe",
        "decayed_lhe",
        "hepmc",
        "hepmc_gz",
        "hepmc_for_analysis",
        "state",
        "list_file",
    ]
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    ready = sum(1 for row in out_rows if row["hepmc_for_analysis"])
    print(f"manifest: {args.manifest}")
    print(f"ready HepMC list files: {ready}/{len(out_rows)}")


if __name__ == "__main__":
    main()
