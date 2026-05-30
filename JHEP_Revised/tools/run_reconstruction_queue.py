#!/usr/bin/env python3
"""Run ``ttp_Analysis`` over a production manifest.

The queue is resumable through a CSV status file.  Use ``--overlay-bx`` or
``--overlay-mean-bx`` to enable the gamma-gamma overlay environment variables;
in that mode the sample name gets a suffix so ROOT/output files do not replace
the no-overlay reconstruction.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("JHEP_Revised/logs/production_manifest.csv"))
    parser.add_argument("--analysis-dir", type=Path, default=Path("ttp_AnalysisISR"))
    parser.add_argument("--analyzer", type=Path, default=Path("Analysis_Programs/ttp_Analysis"))
    parser.add_argument("--common-sh", type=Path, default=Path("Analysis_Programs/common.sh"))
    parser.add_argument("--status", type=Path, default=Path("JHEP_Revised/logs/reconstruction_queue_status.csv"))
    parser.add_argument("--log-dir", type=Path, default=Path("JHEP_Revised/logs/reconstruction_queue"))
    parser.add_argument("--sample", action="append", default=[], help="Run only these manifest sample names.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--rerun-failed", action="store_true")
    parser.add_argument("--overlay-list", type=Path, default=Path("JHEP_Revised/data/overlay/gamma_gamma_overlay_files.txt"))
    parser.add_argument("--overlay-bx", type=int, default=0)
    parser.add_argument("--overlay-mean-bx", type=float, default=0.0)
    parser.add_argument("--overlay-suffix", default="", help="Sample-name suffix. Defaults to _ggbxN or _ggmeanX when overlay is enabled.")
    return parser.parse_args()


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_status(path: Path) -> dict[str, dict[str, str]]:
    return {row["sample"]: row for row in read_csv(path)}


def write_status(path: Path, rows: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["sample", "base_sample", "status", "returncode", "start", "end", "log"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow(rows[key])


def overlay_suffix(args: argparse.Namespace) -> str:
    if args.overlay_suffix:
        return args.overlay_suffix
    if args.overlay_bx > 0:
        return f"_ggbx{args.overlay_bx}"
    if args.overlay_mean_bx > 0:
        return "_ggmean" + str(args.overlay_mean_bx).replace(".", "p")
    return ""


def ensure_overlay_list_file(analysis_dir: Path, sample: str, base_list_file: Path) -> None:
    target = analysis_dir / "files" / f"list_all_files_{sample}"
    if target.exists():
        return
    target.write_text(base_list_file.read_text(encoding="utf-8"), encoding="utf-8")


def shell_command(common_sh: Path, analyzer: Path, sample: str) -> str:
    return (
        "set -Eeuo pipefail; "
        f"source {common_sh.resolve()}; "
        "source_env_script \"$HERWIG_ENV\" || true; "
        "source_env_script \"$ROOT_SETUP\" || true; "
        f"{analyzer.resolve()} {sample}"
    )


def main() -> None:
    args = parse_args()
    manifest_rows = read_csv(args.manifest)
    wanted = set(args.sample)
    suffix = overlay_suffix(args)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    status = read_status(args.status)
    ran = 0

    for row in manifest_rows:
        if row.get("status") != "ok":
            continue
        if not row.get("hepmc_for_analysis"):
            continue
        base_sample = row["sample"]
        if wanted and base_sample not in wanted:
            continue
        sample = base_sample + suffix
        previous = status.get(sample, {})
        if previous.get("status") == "ok":
            print(f"[skip ok] {sample}")
            continue
        if previous.get("status") == "failed" and not args.rerun_failed:
            print(f"[skip failed] {sample}")
            continue
        if args.limit and ran >= args.limit:
            break

        base_list_file = Path(row["list_file"])
        if suffix:
            ensure_overlay_list_file(args.analysis_dir, sample, base_list_file)

        log = args.log_dir / f"{sample}.log"
        env = os.environ.copy()
        if args.overlay_bx > 0 or args.overlay_mean_bx > 0:
            env["ASE_GG_OVERLAY_LIST"] = str(args.overlay_list.resolve())
            env["ASE_GG_OVERLAY_BX"] = str(args.overlay_bx)
            env["ASE_GG_OVERLAY_MEAN_BX"] = str(args.overlay_mean_bx)

        status[sample] = {
            "sample": sample,
            "base_sample": base_sample,
            "status": "running",
            "returncode": "",
            "start": now(),
            "end": "",
            "log": str(log),
        }
        write_status(args.status, status)
        print(f"[run] {sample}")
        with log.open("w", encoding="utf-8", errors="replace") as handle:
            proc = subprocess.run(
                ["bash", "-lc", shell_command(args.common_sh, args.analyzer, sample)],
                cwd=args.analysis_dir,
                stdout=handle,
                stderr=subprocess.STDOUT,
                env=env,
            )
        status[sample]["returncode"] = str(proc.returncode)
        status[sample]["end"] = now()
        status[sample]["status"] = "ok" if proc.returncode == 0 else "failed"
        write_status(args.status, status)
        print(f"[{status[sample]['status']}] {sample} -> {log}")
        ran += 1

    print(f"queue status: {args.status}")


if __name__ == "__main__":
    main()
