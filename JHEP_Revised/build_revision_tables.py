#!/usr/bin/env python3
"""Generate LaTeX tables used by the JHEP revision manuscript.

The script intentionally reads the existing CSV/width inputs rather than
hard-coding the values into the paper.  It does not run event generation.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TABLES = ROOT / "tables"
TABLES.mkdir(exist_ok=True)


SCENARIOS = {
    "baseline": DATA / "kappa_baseline.csv",
    "ISR+80": DATA / "kappa_plus80ISR.csv",
    "ISR-80": DATA / "kappa_minus80ISR.csv",
}


def cowan_counting_z(s: float, b: float) -> float:
    if s <= 0:
        return 0.0
    if b <= 0:
        return math.sqrt(2.0 * s)
    return math.sqrt(max(0.0, 2.0 * ((s + b) * math.log(1.0 + s / b) - s)))


def cowan_counting_z_bkg_unc(s: float, b: float, sigma_b: float) -> float:
    if s <= 0:
        return 0.0
    if b <= 0 or sigma_b <= 0:
        return cowan_counting_z(s, b)
    sigma2 = sigma_b * sigma_b
    first = ((s + b) * (b + sigma2)) / (b * b + (s + b) * sigma2)
    second = 1.0 + sigma2 * s / (b * (b + sigma2))
    return math.sqrt(max(0.0, 2.0 * ((s + b) * math.log(first) - (b * b / sigma2) * math.log(second))))


def systematic_z(s: float, b: float, rel_b: float, rel_s: float = 0.0) -> float:
    return cowan_counting_z_bkg_unc(max(0.0, s * (1.0 - rel_s)), b, rel_b * b)


def read_scan(path: Path) -> dict[tuple[float, int], dict[str, float]]:
    out: dict[tuple[float, int], dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (float(row["kappa"]), int(row["mass_GeV"]))
            out[key] = {
                "S": float(row["S"]),
                "B": float(row["B"]),
                "Z": float(row["Z"]),
            }
    return out


def read_widths(path: Path) -> dict[int, dict[float, float]]:
    text = path.read_text(encoding="utf-8")
    widths: dict[int, dict[float, float]] = {}
    for block in re.finditer(
        r"Tt(?P<mass>\d+)\} samples with \$\\kappa\$.*?\\midrule(?P<body>.*?)\\bottomrule",
        text,
        re.S,
    ):
        mass = int(block.group("mass"))
        widths[mass] = {}
        for kappa, width in re.findall(r"\$(\d+\.\d+)\$\s*&\s*([0-9.]+)", block.group("body")):
            widths[mass][float(kappa)] = float(width)
    return widths


def tex_escape(text: str) -> str:
    return text.replace("%", r"\%")


def write_benchmark_table(scans: dict[str, dict[tuple[float, int], dict[str, float]]]) -> None:
    masses = [1200, 1600, 2000, 2400]
    rows = []
    for mass in masses:
        for label in ["baseline", "ISR+80", "ISR-80"]:
            values = scans[label][(0.2, mass)]
            rows.append(
                "    "
                + " & ".join(
                    [
                        f"{mass/1000:.1f}",
                        tex_escape(label),
                        f"{values['S']:.1f}",
                        f"{values['B']:.0f}",
                        f"{values['Z']:.2f}",
                        f"{cowan_counting_z(values['S'], values['B']):.2f}",
                        f"{systematic_z(values['S'], values['B'], 0.05):.2f}",
                        f"{systematic_z(values['S'], values['B'], 0.10, 0.05):.2f}",
                    ]
                )
                + r" \\"
            )
    content = r"""\begin{table}[t]
\centering
\caption{Benchmark yields and significance cross-checks at $\kappa_T=0.20$.
The headline discovery test in the revised text uses the binned profile-likelihood workflow; the
last three columns provide transparent counting cross-checks with no nuisance parameters, a
$5\%$ background-normalization nuisance, and a conservative $10\%$ background plus $5\%$
signal-efficiency scenario.}
\label{tab:benchmark-yields}
\begin{tabular}{llrrrrrr}
\toprule
$m_T$ [TeV] & Scenario & $S$ & $B$ & $S/\sqrt{S+B}$ & $Z_A$ & $Z_A(5\%B)$ & $Z_A(10\%B,5\%S)$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "benchmark_yields.tex").write_text(content, encoding="utf-8")


def write_validity_tables(widths: dict[int, dict[float, float]]) -> None:
    summary_rows = []
    detail_rows = []
    for mass in sorted(widths):
        valid = [(k, w) for k, w in sorted(widths[mass].items()) if w / mass <= 0.10]
        invalid = [(k, w) for k, w in sorted(widths[mass].items()) if w / mass > 0.10]
        max_valid = valid[-1][0] if valid else float("nan")
        first_invalid = invalid[0][0] if invalid else float("nan")
        summary_rows.append(
            f"    {mass/1000:.1f} & {max_valid:.2f} & {first_invalid:.2f} "
            + rf"& $\Gamma_T/m_T \le 10\%$ \\"
        )
        for kappa, width in sorted(widths[mass].items()):
            detail_rows.append(
                f"    {mass/1000:.1f} & {kappa:.2f} & {width:.3f} & {100.0*width/mass:.1f} "
                + ("& kept" if width / mass <= 0.10 else "& outside")
                + r" \\"
            )

    summary = r"""\begin{table}[t]
\centering
\caption{Nominal validity domain used for the main $(m_T,\kappa_T)$ interpretation.
Points above $\Gamma_T/m_T=10\%$ are not interpreted as narrow-resonance reach points.}
\label{tab:width-validity-summary}
\begin{tabular}{cccl}
\toprule
$m_T$ [TeV] & Largest kept $\kappa_T$ & First omitted $\kappa_T$ & Criterion \\
\midrule
""" + "\n".join(summary_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "width_validity_summary.tex").write_text(summary, encoding="utf-8")

    detail = r"""\begin{table}[p]
\centering
\caption{Width ratios used to define the scan validity domain.}
\label{tab:width-ratios}
\begin{tabular}{ccrcl}
\toprule
$m_T$ [TeV] & $\kappa_T$ & $\Gamma_T$ [GeV] & $\Gamma_T/m_T$ [\%] & Main-scan status \\
\midrule
""" + "\n".join(detail_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "width_ratios.tex").write_text(detail, encoding="utf-8")


def write_background_table() -> None:
    content = r"""\begin{table}[t]
\centering
\caption{Background treatment in the revision.  The fresh CLIC production now
includes the original four generated background classes with ISR, luminosity
spectrum, and a parametric one-bunch $\gamma\gamma\to$hadrons overlay stress
test.  Additional electroweak and high-mass inclusive backgrounds remain
required before claiming a final detector-level CLIC reach.}
\label{tab:background-status}
\small
\begin{tabular}{@{}p{0.34\linewidth}p{0.24\linewidth}p{0.32\linewidth}@{}}
\toprule
Class & Status & Revision use \\
\midrule
$t\bar t$, $t\bar t Z$, $t\bar t H$, $W^+W^-Z$ & Fresh CLIC rerun complete & Used in Tables~\ref{tab:fresh-clic-reach}--\ref{tab:fresh-clic-vs-isr} \\
$\gamma\gamma\to$ hadrons overlay & Parametric stress test complete & One-bunch overlay impact reported in Table~\ref{tab:fresh-clic-overlay} \\
$t\bar t\nu\bar\nu$, $W^+W^-\nu\bar\nu$, $H\nu\bar\nu$, $ZZ$, $HZ$, $W^+W^-$ & Present in local analysis tree or queued as auxiliary inputs & Add to expanded-background rerun before final reach claim \\
W-fusion single top and high-mass $V+$jets & Not yet generated & Require generation or data-driven upper bound \\
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "background_status.tex").write_text(content, encoding="utf-8")


def write_response_matrix() -> None:
    rows = [
        ("Meaning of fully simulated", "Secs. \\ref{sec:samples}, \\ref{sec:realism}", "Term removed; detector treatment stated as fast/parametric unless GEANT4/CLICdet is added."),
        ("Top/b-tag efficiencies and mistags", "Sec. \\ref{sec:selection}, App. \\ref{app:response}", "Object definitions fixed; performance table is an explicit required validation item."),
        ("Isolation-veto definition", "Sec. \\ref{sec:selection}", "Cone, thresholds, nearby-activity veto, and relative-$H_T$ logic documented."),
        ("Polarization choice", "Sec. \\ref{sec:realism}", "Both $+80\\%$ and $-80\\%$ samples are shown; luminosity sharing is not assumed until a CLIC run plan is selected."),
        ("Background completeness", "Table \\ref{tab:background-status}", "Included, locally available, and missing background classes separated."),
        ("Cutflow and normalization", "Tables \\ref{tab:reproducibility}, \\ref{tab:benchmark-yields}", "Yields trace back to ROOT histogram entries, cross sections, simulated events, and luminosity."),
        ("Finite widths/interference", "Sec. \\ref{sec:kappa}, Table \\ref{tab:width-validity-summary}", "Main scan restricted to $\\Gamma_T/m_T\\le10\\%$; one full-matrix-element stress test listed as required."),
        ("Likelihood and systematics", "Sec. \\ref{sec:statistics}, Table \\ref{tab:benchmark-yields}", "Binned profile-likelihood workflow repaired; counting nuisance cross-checks included."),
        ("Modern taggers/ML", "Sec. \\ref{sec:outlook}", "Presented as next analysis step; no unvalidated ML gain claimed."),
        ("Forced decay modes", "App. \\ref{app:response}", "Validation matrix specified for $Wb$, $Zt$, and $Ht$ at 1.2 and 2.0 TeV."),
    ]
    body = "\n".join(
        f"    {idx} & {item} & {where} & {action} \\\\"
        for idx, (item, where, action) in enumerate(rows, start=1)
    )
    content = r"""\begin{table}[p]
\centering
\caption{Reviewer-response matrix implemented in the revised manuscript.}
\label{tab:response-matrix}
\small
\begin{tabular}{r p{0.23\linewidth} p{0.24\linewidth} p{0.38\linewidth}}
\toprule
\# & Review issue & Where addressed & Action \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "response_matrix.tex").write_text(content, encoding="utf-8")


def main() -> None:
    scans = {name: read_scan(path) for name, path in SCENARIOS.items()}
    widths = read_widths(ROOT.parent / "Paper" / "Tt_widths_table.tex")
    write_benchmark_table(scans)
    write_validity_tables(widths)
    write_background_table()
    write_response_matrix()


if __name__ == "__main__":
    main()
