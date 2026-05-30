#!/usr/bin/env python3
"""Run a resumable queue of MG5 command files.

Each command file is executed in order, with stdout/stderr captured to an
individual log.  A CSV status file is updated after every job so the queue can
be restarted without repeating successful jobs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
from pathlib import Path


MG5 = Path("/home/higinio/Documentos/ASE/HERWIG/opt/MG5_aMC_v3_5_1/bin/mg5_aMC")
ERROR_PATTERNS = (
    "Traceback (most recent call last)",
    "Command \"import ",
    " interrupted with error:",
    " interrupted in sub-command:",
    "Input/output error",
    "InvalidCmd :",
    "ERROR DETECTED",
    "No such file or directory",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commands", nargs="*", type=Path, help="MG5 command files to run.")
    parser.add_argument("--glob", default="", help="Glob for command files, e.g. 'JHEP_Revised/config/madgraph_runs/*_nev10000.mg5'.")
    parser.add_argument("--mg5", type=Path, default=MG5)
    parser.add_argument("--log-dir", type=Path, default=Path("JHEP_Revised/logs/mg5_queue"))
    parser.add_argument("--status", type=Path, default=Path("JHEP_Revised/logs/mg5_queue_status.csv"))
    parser.add_argument("--rerun-failed", action="store_true", help="Rerun failed jobs instead of skipping them.")
    parser.add_argument("--limit", type=int, default=0, help="Run at most this many pending jobs.")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue the queue after a failed job.")
    parser.add_argument(
        "--require-path",
        action="append",
        default=[],
        type=Path,
        help="Path that must exist before each job, e.g. a mounted external drive.",
    )
    return parser.parse_args()


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def read_status(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["command"]: row for row in csv.DictReader(handle)}


def write_status(path: Path, rows: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["command", "status", "returncode", "start", "end", "log"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow(rows[key])


def log_has_error(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(pattern in text for pattern in ERROR_PATTERNS)


def command_files(args: argparse.Namespace) -> list[Path]:
    files = list(args.commands)
    if args.glob:
        files.extend(sorted(Path().glob(args.glob)))
    seen = set()
    out = []
    for path in files:
        resolved = str(path)
        if resolved not in seen:
            out.append(path)
            seen.add(resolved)
    return out


def main() -> None:
    args = parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)
    status = read_status(args.status)
    files = command_files(args)
    if not files:
        raise SystemExit("no command files selected")

    ran = 0
    for command in files:
        key = str(command)
        previous = status.get(key, {})
        if previous.get("status") == "ok":
            print(f"[skip ok] {command}")
            continue
        if previous.get("status") == "failed" and not args.rerun_failed:
            print(f"[skip failed] {command}")
            continue
        if args.limit and ran >= args.limit:
            break
        missing = [str(path) for path in args.require_path if not path.exists()]
        if missing:
            print(f"[abort] required path missing before {command}: {', '.join(missing)}")
            break

        log = args.log_dir / f"{command.stem}.log"
        row = {
            "command": key,
            "status": "running",
            "returncode": "",
            "start": now(),
            "end": "",
            "log": str(log),
        }
        status[key] = row
        write_status(args.status, status)
        print(f"[run] {command}")
        with log.open("w", encoding="utf-8", errors="replace") as handle:
            proc = subprocess.run([str(args.mg5), str(command)], stdout=handle, stderr=subprocess.STDOUT)
        has_error = log_has_error(log)
        row["returncode"] = str(proc.returncode)
        row["end"] = now()
        row["status"] = "ok" if proc.returncode == 0 and not has_error else "failed"
        write_status(args.status, status)
        print(f"[{row['status']}] {command} -> {log}")
        ran += 1
        if row["status"] != "ok" and not args.continue_on_failure:
            print(f"[abort] stopping after failed job: {command}")
            break

    print(f"queue status: {args.status}")


if __name__ == "__main__":
    main()
