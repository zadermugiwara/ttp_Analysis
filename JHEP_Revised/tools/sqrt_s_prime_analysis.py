#!/usr/bin/env python3
"""Analyze the effective hard-scattering energy in LHE samples.

For each LHE event the script reads the two incoming beam particles, computes

    sqrt(s') = sqrt((p1 + p2)^2),  x_i = E_i / E_beam,

and, when an associated hard-process top is identifiable, compares the nominal
3 TeV recoil mass to the exact event-level recoil mass built with the incoming
four-vector.  This is a diagnostic for ISR/beamstrahlung samples; the nominal
3 TeV recoil remains the observable used by the reconstruction unless an
event-by-event beam-energy estimator is introduced.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


DEFAULT_SAMPLES = [
    "Tt1200_baseline=/media/higinio/Expansion1/Madgraph/Tt1200/Events/run_01_decayed_1/unweighted_events.lhe.gz",
    "Tt1200_ISR_clic3000ll=/media/higinio/Expansion1/Madgraph/Tt1200ISR/Events/run_01_decayed_1/unweighted_events.lhe.gz",
    "Tt1200_plus80_ISR_clic3000ll=/media/higinio/Expansion1/Madgraph/Tt1200+80ISR/Events/run_01_decayed_1/unweighted_events.lhe.gz",
    "Tt1200_minus80_ISR_clic3000ll=/media/higinio/Expansion1/Madgraph/Tt1200-80ISR/Events/run_02_decayed_1/unweighted_events.lhe.gz",
]


@dataclass
class Particle:
    pdgid: int
    status: int
    mother1: int
    mother2: int
    px: float
    py: float
    pz: float
    e: float
    mass: float


@dataclass
class EventResult:
    sample: str
    event: int
    x1: float
    x2: float
    sqrt_s_prime: float
    beta_z: float
    recoil_nominal: float | None
    recoil_event_level: float | None
    recoil_shift: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        action="append",
        default=[],
        help="Sample in label=/path/to/unweighted_events.lhe.gz form. Can be repeated.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("JHEP_Revised/data/sqrt_s_prime"),
        help="Directory for CSV outputs.",
    )
    parser.add_argument(
        "--fig-dir",
        type=Path,
        default=Path("JHEP_Revised/figs/sqrt_s_prime"),
        help="Directory for simple SVG histogram diagnostics.",
    )
    parser.add_argument("--ebeam", type=float, default=1500.0, help="Nominal single-beam energy in GeV.")
    parser.add_argument("--max-events", type=int, default=0, help="Optional cap per sample; 0 means all events.")
    parser.add_argument("--write-events", action="store_true", help="Write per-event diagnostics in addition to summaries.")
    return parser.parse_args()


def open_maybe_gzip(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def event_blocks(path: Path) -> Iterator[list[str]]:
    inside = False
    block: list[str] = []
    with open_maybe_gzip(path) as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == "<event>":
                inside = True
                block = []
                continue
            if stripped == "</event>":
                if block:
                    yield block
                inside = False
                continue
            if inside:
                block.append(line)


def parse_event(block: list[str]) -> list[Particle]:
    particles: list[Particle] = []
    for raw in block[1:]:
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("<"):
            continue
        parts = line.split()
        if len(parts) < 13:
            continue
        try:
            particles.append(
                Particle(
                    pdgid=int(parts[0]),
                    status=int(parts[1]),
                    mother1=int(parts[2]),
                    mother2=int(parts[3]),
                    px=float(parts[6]),
                    py=float(parts[7]),
                    pz=float(parts[8]),
                    e=float(parts[9]),
                    mass=float(parts[10]),
                )
            )
        except ValueError:
            continue
    return particles


def mass(px: float, py: float, pz: float, e: float) -> float:
    m2 = e * e - px * px - py * py - pz * pz
    if m2 >= 0:
        return math.sqrt(m2)
    return -math.sqrt(-m2)


def add(particles: Iterable[Particle]) -> tuple[float, float, float, float]:
    px = py = pz = e = 0.0
    for p in particles:
        px += p.px
        py += p.py
        pz += p.pz
        e += p.e
    return px, py, pz, e


def associated_top(particles: list[Particle]) -> Particle | None:
    hard_tops = [
        p
        for p in particles
        if abs(p.pdgid) == 6 and p.status in {2, 22} and p.mother1 == 1 and p.mother2 == 2
    ]
    if hard_tops:
        return hard_tops[0]
    tops = [p for p in particles if abs(p.pdgid) == 6 and p.status in {2, 22}]
    return tops[0] if tops else None


def analyze_sample(label: str, path: Path, ebeam: float, max_events: int) -> list[EventResult]:
    rows: list[EventResult] = []
    for idx, block in enumerate(event_blocks(path), start=1):
        if max_events and idx > max_events:
            break
        particles = parse_event(block)
        beams = [p for p in particles if p.status == -1]
        if len(beams) < 2:
            continue
        p_in = add(beams[:2])
        sqrt_s_prime = mass(*p_in)
        beta_z = p_in[2] / p_in[3] if p_in[3] else 0.0
        x1 = beams[0].e / ebeam
        x2 = beams[1].e / ebeam
        top = associated_top(particles)
        recoil_nominal = recoil_event = recoil_shift = None
        if top is not None:
            recoil_nominal = mass(-top.px, -top.py, -top.pz, 2.0 * ebeam - top.e)
            recoil_event = mass(
                p_in[0] - top.px,
                p_in[1] - top.py,
                p_in[2] - top.pz,
                p_in[3] - top.e,
            )
            recoil_shift = recoil_nominal - recoil_event
        rows.append(
            EventResult(
                sample=label,
                event=idx,
                x1=x1,
                x2=x2,
                sqrt_s_prime=sqrt_s_prime,
                beta_z=beta_z,
                recoil_nominal=recoil_nominal,
                recoil_event_level=recoil_event,
                recoil_shift=recoil_shift,
            )
        )
    return rows


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return float("nan")
    mu = mean(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def write_summary(path: Path, rows_by_sample: dict[str, list[EventResult]], ebeam: float) -> None:
    fields = [
        "sample",
        "events",
        "mean_sqrt_s_prime_GeV",
        "std_sqrt_s_prime_GeV",
        "q05_sqrt_s_prime_GeV",
        "q50_sqrt_s_prime_GeV",
        "q95_sqrt_s_prime_GeV",
        "frac_sprime_below_0p99",
        "frac_sprime_below_0p95",
        "mean_x1",
        "mean_x2",
        "mean_abs_beta_z",
        "mean_recoil_nominal_minus_event_GeV",
        "q95_abs_recoil_shift_GeV",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        nominal_sqrt_s = 2.0 * ebeam
        for label, rows in rows_by_sample.items():
            sprime = [r.sqrt_s_prime for r in rows]
            shifts = [r.recoil_shift for r in rows if r.recoil_shift is not None]
            writer.writerow(
                {
                    "sample": label,
                    "events": len(rows),
                    "mean_sqrt_s_prime_GeV": f"{mean(sprime):.6g}",
                    "std_sqrt_s_prime_GeV": f"{stdev(sprime):.6g}",
                    "q05_sqrt_s_prime_GeV": f"{quantile(sprime, 0.05):.6g}",
                    "q50_sqrt_s_prime_GeV": f"{quantile(sprime, 0.50):.6g}",
                    "q95_sqrt_s_prime_GeV": f"{quantile(sprime, 0.95):.6g}",
                    "frac_sprime_below_0p99": f"{sum(x < 0.99 * nominal_sqrt_s for x in sprime) / len(sprime):.6g}" if sprime else "nan",
                    "frac_sprime_below_0p95": f"{sum(x < 0.95 * nominal_sqrt_s for x in sprime) / len(sprime):.6g}" if sprime else "nan",
                    "mean_x1": f"{mean([r.x1 for r in rows]):.6g}",
                    "mean_x2": f"{mean([r.x2 for r in rows]):.6g}",
                    "mean_abs_beta_z": f"{mean([abs(r.beta_z) for r in rows]):.6g}",
                    "mean_recoil_nominal_minus_event_GeV": f"{mean(shifts):.6g}" if shifts else "nan",
                    "q95_abs_recoil_shift_GeV": f"{quantile([abs(x) for x in shifts], 0.95):.6g}" if shifts else "nan",
                }
            )


def write_event_rows(path: Path, rows: Iterable[EventResult]) -> None:
    fields = [
        "sample",
        "event",
        "x1",
        "x2",
        "sqrt_s_prime_GeV",
        "beta_z",
        "recoil_nominal_GeV",
        "recoil_event_level_GeV",
        "recoil_shift_GeV",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "sample": row.sample,
                    "event": row.event,
                    "x1": f"{row.x1:.8g}",
                    "x2": f"{row.x2:.8g}",
                    "sqrt_s_prime_GeV": f"{row.sqrt_s_prime:.8g}",
                    "beta_z": f"{row.beta_z:.8g}",
                    "recoil_nominal_GeV": "" if row.recoil_nominal is None else f"{row.recoil_nominal:.8g}",
                    "recoil_event_level_GeV": "" if row.recoil_event_level is None else f"{row.recoil_event_level:.8g}",
                    "recoil_shift_GeV": "" if row.recoil_shift is None else f"{row.recoil_shift:.8g}",
                }
            )


def histogram(values: list[float], bins: int, lo: float, hi: float) -> list[int]:
    counts = [0] * bins
    if hi <= lo:
        return counts
    width = (hi - lo) / bins
    for value in values:
        if value < lo or value > hi:
            continue
        idx = min(bins - 1, int((value - lo) / width))
        counts[idx] += 1
    return counts


def write_svg_hist(path: Path, title: str, rows_by_sample: dict[str, list[float]], lo: float, hi: float) -> None:
    colors = ["#1f77b4", "#b22222", "#228b22", "#6a3d9a", "#ff7f0e", "#4b5563"]
    width, height = 900, 520
    left, right, top, bottom = 70, 30, 55, 70
    bins = 60
    hists = {label: histogram(values, bins, lo, hi) for label, values in rows_by_sample.items()}
    ymax = max([max(counts) for counts in hists.values() if counts] + [1])
    plot_w = width - left - right
    plot_h = height - top - bottom
    bin_w = plot_w / bins
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="32" font-family="Arial" font-size="22">{title}</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="black"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="black"/>',
    ]
    for i in range(6):
        x = left + i * plot_w / 5
        value = lo + i * (hi - lo) / 5
        parts.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+5}" stroke="black"/>')
        parts.append(f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle" font-family="Arial" font-size="12">{value:.3g}</text>')
    for i in range(5):
        y = height - bottom - i * plot_h / 4
        value = i * ymax / 4
        parts.append(f'<line x1="{left-5}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="black"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="12">{value:.0f}</text>')
    for idx, (label, counts) in enumerate(hists.items()):
        color = colors[idx % len(colors)]
        points = []
        for bin_idx, count in enumerate(counts):
            x = left + (bin_idx + 0.5) * bin_w
            y = height - bottom - (count / ymax) * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(points)}"/>')
        legend_y = top + 18 * idx
        parts.append(f'<line x1="{width-260}" y1="{legend_y}" x2="{width-230}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{width-224}" y="{legend_y+4}" font-family="Arial" font-size="13">{label}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def sample_specs(raw_specs: list[str]) -> list[tuple[str, Path]]:
    specs = raw_specs or DEFAULT_SAMPLES
    out = []
    for raw in specs:
        if "=" not in raw:
            raise SystemExit(f"bad --sample value, expected label=path: {raw}")
        label, path = raw.split("=", 1)
        out.append((label, Path(path)))
    return out


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.fig_dir.mkdir(parents=True, exist_ok=True)
    rows_by_sample: dict[str, list[EventResult]] = {}
    for label, path in sample_specs(args.sample):
        if not path.exists():
            raise SystemExit(f"missing sample: {label} -> {path}")
        rows_by_sample[label] = analyze_sample(label, path, args.ebeam, args.max_events)
        print(f"{label}: {len(rows_by_sample[label])} events")

    write_summary(args.out_dir / "sqrt_s_prime_summary.csv", rows_by_sample, args.ebeam)
    if args.write_events:
        all_rows = [row for rows in rows_by_sample.values() for row in rows]
        write_event_rows(args.out_dir / "sqrt_s_prime_events.csv", all_rows)

    ratio_values = {
        label: [row.sqrt_s_prime / (2.0 * args.ebeam) for row in rows]
        for label, rows in rows_by_sample.items()
    }
    write_svg_hist(
        args.fig_dir / "sqrt_s_prime_ratio.svg",
        "Effective collision energy",
        ratio_values,
        lo=max(0.0, min(min(v) for v in ratio_values.values() if v) - 0.01),
        hi=1.005,
    )
    shift_values = {
        label: [row.recoil_shift for row in rows if row.recoil_shift is not None]
        for label, rows in rows_by_sample.items()
    }
    if any(shift_values.values()):
        lo = min(min(v) for v in shift_values.values() if v)
        hi = max(max(v) for v in shift_values.values() if v)
        pad = max(1.0, 0.05 * (hi - lo))
        write_svg_hist(
            args.fig_dir / "recoil_shift_nominal_minus_event.svg",
            "Nominal recoil minus event-level recoil [GeV]",
            shift_values,
            lo=lo - pad,
            hi=hi + pad,
        )
    print(f"summary: {args.out_dir / 'sqrt_s_prime_summary.csv'}")
    print(f"figures: {args.fig_dir}")


if __name__ == "__main__":
    main()
