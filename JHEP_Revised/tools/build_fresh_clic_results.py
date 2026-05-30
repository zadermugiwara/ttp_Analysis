#!/usr/bin/env python3
"""Build derived tables from the fresh CLIC luminosity-spectrum production.

The inputs are the reconstructed cutflow CSVs and sqrt(s') diagnostic CSVs
produced by the local queue tools.  No event-generation numbers are hard-coded
here; all manuscript-facing tables are regenerated from the CSV artifacts.
"""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
TABLES = ROOT / "tables"
FIGS = ROOT / "figs"

ISR_CUTFLOWS = LOGS / "reconstruction_cutflows.csv"
CLIC_CUTFLOWS = LOGS / "reconstruction_cutflows_clic3000ll_fresh.csv"
CLIC_OVERLAY_CUTFLOWS = LOGS / "reconstruction_cutflows_clic3000ll_fresh_overlay.csv"
SQRTS_SUMMARY = ROOT / "data" / "sqrt_s_prime_clic3000ll_fresh_nev10000" / "sqrt_s_prime_summary.csv"
PROFILE_SUMMARY = ROOT / "validation" / "profile_clic_unpol_rebin100_summary.csv"

MASS_TO_BDT = {1200: "BDT 1200", 1600: "BDT 1600", 2000: "BDT 2000", 2400: "BDT 2400"}
BACKGROUNDS = ["ttbar", "ttz", "tth", "w_w-z"]
POLS = ["minus80", "unpol", "plus80"]
POL_LABEL = {"minus80": r"$P_{e^-}=-80\%$", "unpol": "unpol.", "plus80": r"$P_{e^-}=+80\%$"}


def cowan_counting_z(s: float, b: float) -> float:
    if s <= 0.0:
        return 0.0
    if b <= 0.0:
        return math.sqrt(2.0 * s)
    return math.sqrt(max(0.0, 2.0 * ((s + b) * math.log(1.0 + s / b) - s)))


def cowan_counting_z_bkg_unc(s: float, b: float, sigma_b: float) -> float:
    if s <= 0.0:
        return 0.0
    if b <= 0.0 or sigma_b <= 0.0:
        return cowan_counting_z(s, b)
    sigma2 = sigma_b * sigma_b
    first = ((s + b) * (b + sigma2)) / (b * b + (s + b) * sigma2)
    second = 1.0 + sigma2 * s / (b * (b + sigma2))
    return math.sqrt(max(0.0, 2.0 * ((s + b) * math.log(first) - (b * b / sigma2) * math.log(second))))


def systematic_z(s: float, b: float, rel_b: float, rel_s: float = 0.0) -> float:
    return cowan_counting_z_bkg_unc(max(0.0, s * (1.0 - rel_s)), b, rel_b * b)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def strip_suffix(sample: str) -> tuple[str, str, bool]:
    suffixes = [
        ("_clic3000ll_nev10000_fresh_ggbx1", "clic3000ll", True),
        ("_clic3000ll_nev10000_fresh", "clic3000ll", False),
        ("_isronlyll_nev10000_ggbx1", "isronlyll", True),
        ("_isronlyll_nev10000", "isronlyll", False),
    ]
    for suffix, scenario, overlay in suffixes:
        if sample.endswith(suffix):
            return sample[: -len(suffix)], scenario, overlay
    return sample, "unknown", False


def parse_base(base: str) -> tuple[str, int | None, str] | None:
    signal = re.fullmatch(r"Tt(?P<mass>\d+)(?P<pol>-80ISR|_80ISR|ISR)", base)
    if signal:
        return "Tt", int(signal.group("mass")), parse_pol(signal.group("pol"))

    background = re.fullmatch(r"(?P<proc>ttbar|ttz|tth|w_w-z)(?P<pol>-80ISR|_80ISR|ISR)", base)
    if background:
        return background.group("proc"), None, parse_pol(background.group("pol"))
    return None


def parse_pol(tag: str) -> str:
    if tag == "-80ISR":
        return "minus80"
    if tag == "_80ISR":
        return "plus80"
    if tag == "ISR":
        return "unpol"
    raise ValueError(f"unknown polarization tag {tag}")


def index_cutflows(path: Path) -> dict[tuple[str, str, bool, str, int | None, str, str], float]:
    index: dict[tuple[str, str, bool, str, int | None, str, str], float] = {}
    for row in read_csv(path):
        base, scenario, overlay = strip_suffix(row["sample"])
        parsed = parse_base(base)
        if parsed is None:
            continue
        process, mass, pol = parsed
        mode = "overlay" if overlay else "clean"
        key = (scenario, mode, overlay, process, mass, pol, row["cut"])
        index[key] = float(row["weighted_yield"])
    return index


def merge_indexes(*indexes: dict[tuple[str, str, bool, str, int | None, str, str], float]) -> dict[tuple[str, str, bool, str, int | None, str, str], float]:
    merged: dict[tuple[str, str, bool, str, int | None, str, str], float] = {}
    for index in indexes:
        merged.update(index)
    return merged


def yield_for(
    index: dict[tuple[str, str, bool, str, int | None, str, str], float],
    scenario: str,
    overlay: bool,
    process: str,
    mass: int | None,
    pol: str,
    cut: str,
) -> float:
    mode = "overlay" if overlay else "clean"
    return index.get((scenario, mode, overlay, process, mass, pol, cut), 0.0)


def background_sum(
    index: dict[tuple[str, str, bool, str, int | None, str, str], float],
    scenario: str,
    overlay: bool,
    pol: str,
    cut: str,
) -> float:
    return sum(yield_for(index, scenario, overlay, proc, None, pol, cut) for proc in BACKGROUNDS)


def build_reach(index: dict[tuple[str, str, bool, str, int | None, str, str], float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in ["isronlyll", "clic3000ll"]:
        for overlay in ([False, True] if scenario == "clic3000ll" else [False, True]):
            for mass, cut in MASS_TO_BDT.items():
                for pol in POLS:
                    s = yield_for(index, scenario, overlay, "Tt", mass, pol, cut)
                    b = background_sum(index, scenario, overlay, pol, cut)
                    if s <= 0.0 and b <= 0.0:
                        continue
                    rows.append(
                        {
                            "scenario": scenario,
                            "overlay": overlay,
                            "mass_GeV": mass,
                            "polarization": pol,
                            "cut": cut,
                            "S": s,
                            "B": b,
                            "S_over_sqrt_SB": s / math.sqrt(s + b) if s + b > 0.0 else 0.0,
                            "Z_A": cowan_counting_z(s, b),
                            "Z_A_5pctB": systematic_z(s, b, 0.05),
                            "Z_A_10pctB_5pctS": systematic_z(s, b, 0.10, 0.05),
                        }
                    )
    return rows


def write_dict_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(x: object, digits: int = 2) -> str:
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def write_reach_table(rows: list[dict[str, object]]) -> None:
    selected = [
        row
        for row in rows
        if row["scenario"] == "clic3000ll" and not row["overlay"] and row["polarization"] in {"unpol", "plus80", "minus80"}
    ]
    selected.sort(key=lambda r: (int(r["mass_GeV"]), POLS.index(str(r["polarization"]))))
    body = "\n".join(
        "    "
        + " & ".join(
            [
                f"{int(row['mass_GeV']) / 1000.0:.1f}",
                POL_LABEL[str(row["polarization"])],
                fmt(row["S"], 1),
                fmt(row["B"], 1),
                fmt(row["S_over_sqrt_SB"], 2),
                fmt(row["Z_A"], 2),
                fmt(row["Z_A_5pctB"], 2),
                fmt(row["Z_A_10pctB_5pctS"], 2),
            ]
        )
        + r" \\"
        for row in selected
    )
    content = r"""\begin{table}[t]
\centering
\caption{Fresh CLIC luminosity-spectrum counting cross-checks at $\kappa_T=0.20$,
using the mass-matched BDT selection for each signal point and the four generated
background classes.  These numbers include ISR plus the CLIC luminosity-spectrum
sampling used in the fresh production, but not the overlay stress-test variant.}
\label{tab:fresh-clic-reach}
\small
\begin{tabular}{llrrrrrr}
\toprule
$m_T$ [TeV] & Beam & $S$ & $B$ & $S/\sqrt{S+B}$ & $Z_A$ & $Z_A(5\%B)$ & $Z_A(10\%B,5\%S)$ \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "fresh_clic_reach_counting.tex").write_text(content, encoding="utf-8")


def build_overlay_impact(index: dict[tuple[str, str, bool, str, int | None, str, str], float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for mass, cut in MASS_TO_BDT.items():
        for pol in POLS:
            clean_s = yield_for(index, "clic3000ll", False, "Tt", mass, pol, cut)
            over_s = yield_for(index, "clic3000ll", True, "Tt", mass, pol, cut)
            clean_b = background_sum(index, "clic3000ll", False, pol, cut)
            over_b = background_sum(index, "clic3000ll", True, pol, cut)
            rows.append(
                {
                    "mass_GeV": mass,
                    "polarization": pol,
                    "cut": cut,
                    "S_clean": clean_s,
                    "S_overlay": over_s,
                    "S_ratio_overlay_clean": over_s / clean_s if clean_s > 0.0 else 0.0,
                    "B_clean": clean_b,
                    "B_overlay": over_b,
                    "B_ratio_overlay_clean": over_b / clean_b if clean_b > 0.0 else 0.0,
                    "Z_clean": cowan_counting_z(clean_s, clean_b),
                    "Z_overlay": cowan_counting_z(over_s, over_b),
                    "Z_ratio_overlay_clean": cowan_counting_z(over_s, over_b) / cowan_counting_z(clean_s, clean_b)
                    if cowan_counting_z(clean_s, clean_b) > 0.0
                    else 0.0,
                }
            )
    return rows


def write_overlay_table(rows: list[dict[str, object]]) -> None:
    selected = [row for row in rows if row["polarization"] == "unpol"]
    selected.sort(key=lambda r: int(r["mass_GeV"]))
    body = "\n".join(
        "    "
        + " & ".join(
            [
                f"{int(row['mass_GeV']) / 1000.0:.1f}",
                fmt(row["S_clean"], 1),
                fmt(row["S_overlay"], 1),
                fmt(row["S_ratio_overlay_clean"], 3),
                fmt(row["B_clean"], 1),
                fmt(row["B_overlay"], 1),
                fmt(row["B_ratio_overlay_clean"], 3),
                fmt(row["Z_ratio_overlay_clean"], 3),
            ]
        )
        + r" \\"
        for row in selected
    )
    content = r"""\begin{table}[t]
\centering
\caption{Parametric $\gamma\gamma\to$hadrons overlay stress test for the
unpolarized fresh CLIC samples.  Ratios are overlay divided by the corresponding
clean luminosity-spectrum reconstruction after the mass-matched BDT selection.}
\label{tab:fresh-clic-overlay}
\small
\begin{tabular}{lrrrrrrr}
\toprule
$m_T$ [TeV] & $S_{\rm clean}$ & $S_{\rm ov}$ & $S_{\rm ov}/S_{\rm clean}$
& $B_{\rm clean}$ & $B_{\rm ov}$ & $B_{\rm ov}/B_{\rm clean}$ & $Z_{\rm ov}/Z_{\rm clean}$ \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "fresh_clic_overlay_impact.tex").write_text(content, encoding="utf-8")


def build_isr_comparison(index: dict[tuple[str, str, bool, str, int | None, str, str], float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for mass, cut in MASS_TO_BDT.items():
        for pol in POLS:
            isr_s = yield_for(index, "isronlyll", False, "Tt", mass, pol, cut)
            clic_s = yield_for(index, "clic3000ll", False, "Tt", mass, pol, cut)
            isr_b = background_sum(index, "isronlyll", False, pol, cut)
            clic_b = background_sum(index, "clic3000ll", False, pol, cut)
            rows.append(
                {
                    "mass_GeV": mass,
                    "polarization": pol,
                    "cut": cut,
                    "S_isr_only": isr_s,
                    "S_clic_spectrum": clic_s,
                    "S_ratio_clic_isr": clic_s / isr_s if isr_s > 0.0 else 0.0,
                    "B_isr_only": isr_b,
                    "B_clic_spectrum": clic_b,
                    "B_ratio_clic_isr": clic_b / isr_b if isr_b > 0.0 else 0.0,
                    "Z_isr_only": cowan_counting_z(isr_s, isr_b),
                    "Z_clic_spectrum": cowan_counting_z(clic_s, clic_b),
                    "Z_ratio_clic_isr": cowan_counting_z(clic_s, clic_b) / cowan_counting_z(isr_s, isr_b)
                    if cowan_counting_z(isr_s, isr_b) > 0.0
                    else 0.0,
                }
            )
    return rows


def write_isr_comparison_table(rows: list[dict[str, object]]) -> None:
    selected = [row for row in rows if row["polarization"] == "unpol"]
    selected.sort(key=lambda r: int(r["mass_GeV"]))
    body = "\n".join(
        "    "
        + " & ".join(
            [
                f"{int(row['mass_GeV']) / 1000.0:.1f}",
                fmt(row["S_ratio_clic_isr"], 3),
                fmt(row["B_ratio_clic_isr"], 3),
                fmt(row["Z_isr_only"], 2),
                fmt(row["Z_clic_spectrum"], 2),
                fmt(row["Z_ratio_clic_isr"], 3),
            ]
        )
        + r" \\"
        for row in selected
    )
    content = r"""\begin{table}[t]
\centering
\caption{Impact of replacing the ISR-only lepton beams by the fresh CLIC
luminosity-spectrum setup for unpolarized samples.  Ratios compare the
mass-matched BDT yields from the fresh CLIC run to the older ISR-only run.}
\label{tab:fresh-clic-vs-isr}
\small
\begin{tabular}{lrrrrr}
\toprule
$m_T$ [TeV] & $S_{\rm CLIC}/S_{\rm ISR}$ & $B_{\rm CLIC}/B_{\rm ISR}$
& $Z_{\rm ISR}$ & $Z_{\rm CLIC}$ & $Z_{\rm CLIC}/Z_{\rm ISR}$ \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "fresh_clic_vs_isr.tex").write_text(content, encoding="utf-8")


def write_sqrts_table(path: Path) -> None:
    rows = read_csv(path)
    selected: list[dict[str, str]] = []
    for row in rows:
        base, _, _ = strip_suffix(row["sample"])
        parsed = parse_base(base)
        if parsed is None:
            continue
        process, mass, pol = parsed
        if process == "Tt" and pol == "unpol":
            selected.append(row | {"mass_GeV": str(mass)})
    selected.sort(key=lambda r: int(r["mass_GeV"]))
    body = "\n".join(
        "    "
        + " & ".join(
            [
                f"{int(row['mass_GeV']) / 1000.0:.1f}",
                f"{float(row['mean_sqrt_s_prime_GeV']):.0f}",
                f"{float(row['q05_sqrt_s_prime_GeV']):.0f}",
                f"{float(row['q50_sqrt_s_prime_GeV']):.0f}",
                f"{float(row['frac_sprime_below_0p95']):.3f}",
                f"{float(row['mean_abs_beta_z']):.3f}",
                f"{float(row['q95_abs_recoil_shift_GeV']):.0f}",
            ]
        )
        + r" \\"
        for row in selected
    )
    content = r"""\begin{table}[t]
\centering
\caption{Fresh CLIC luminosity-spectrum diagnostic for unpolarized signal
samples.  The table reports the generated effective collision energy
$\sqrt{s'}$, the longitudinal boost, and the 95th percentile of the recoil-mass
shift induced by using the nominal $\sqrt{s}=\SI{3}{TeV}$ in the recoil formula.}
\label{tab:fresh-clic-sqrts}
\small
\begin{tabular}{lrrrrrr}
\toprule
$m_T$ [TeV] & $\langle\sqrt{s'}\rangle$ [GeV] & $q_{5}$ [GeV] & $q_{50}$ [GeV]
& $f(\sqrt{s'}<0.95\sqrt{s})$ & $\langle|\beta_z|\rangle$ & $q_{95}(|\Delta m_{\rm rec}|)$ [GeV] \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "fresh_clic_sqrts_summary.tex").write_text(content, encoding="utf-8")


def write_profile_table(path: Path) -> None:
    if not path.exists():
        return
    rows = read_csv(path)
    rows.sort(key=lambda r: int(r["mass_GeV"]))
    body = "\n".join(
        "    "
        + " & ".join(
            [
                f"{int(row['mass_GeV']) / 1000.0:.1f}",
                f"{float(row['S_exp']):.1f}",
                f"{float(row['B_exp']):.1f}",
                f"{float(row['Z_Cowan_counting']):.2f}",
                f"{float(row['Z_Cowan_binned']):.2f}",
                f"{float(row['Z_profile_Asimov']):.2f}",
                f"{float(row['Z_systematic_5pctB']):.2f}",
            ]
        )
        + r" \\"
        for row in rows
    )
    content = r"""\begin{table}[t]
\centering
\caption{Binned profile-likelihood closure for the unpolarized fresh CLIC
samples.  The recoil histograms use the mass-matched BDT selections and are
rebinned to $\SI{100}{GeV}$ bins to avoid empty-background template bins.  The
agreement between $Z_{\rm binned}$ and $Z_{\rm PLR}^{\rm Asimov}$ validates the
manual profile-likelihood implementation for these inputs.}
\label{tab:fresh-clic-profile}
\small
\begin{tabular}{lrrrrrr}
\toprule
$m_T$ [TeV] & $S$ & $B$ & $Z_A^{\rm count}$ & $Z_A^{\rm binned}$ & $Z_{\rm PLR}^{\rm Asimov}$ & $Z(5\%B)$ \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    (TABLES / "fresh_clic_profile_closure.tex").write_text(content, encoding="utf-8")


def write_svg_bar(path: Path, title: str, labels: list[str], values: list[float], ylabel: str) -> None:
    width, height = 760, 420
    margin_l, margin_b, margin_t, margin_r = 80, 70, 60, 30
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    vmax = max(values) if values else 1.0
    vmax = vmax * 1.15 if vmax > 0 else 1.0
    bar_w = plot_w / max(1, len(values)) * 0.68
    gap = plot_w / max(1, len(values))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2:.1f}" y="30" text-anchor="middle" font-family="Arial" font-size="18">{title}</text>',
        f'<line x1="{margin_l}" y1="{height-margin_b}" x2="{width-margin_r}" y2="{height-margin_b}" stroke="#222"/>',
        f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{height-margin_b}" stroke="#222"/>',
        f'<text x="20" y="{height/2:.1f}" transform="rotate(-90 20 {height/2:.1f})" text-anchor="middle" font-family="Arial" font-size="13">{ylabel}</text>',
    ]
    for i in range(6):
        yval = vmax * i / 5
        y = height - margin_b - plot_h * yval / vmax
        parts.append(f'<line x1="{margin_l-5}" y1="{y:.1f}" x2="{width-margin_r}" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{margin_l-10}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{yval:.1f}</text>')
    for idx, (label, value) in enumerate(zip(labels, values)):
        x = margin_l + idx * gap + (gap - bar_w) / 2
        h = plot_h * value / vmax
        y = height - margin_b - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="#386cb0"/>')
        parts.append(f'<text x="{x+bar_w/2:.1f}" y="{height-margin_b+20}" text-anchor="middle" font-family="Arial" font-size="11">{label}</text>')
        parts.append(f'<text x="{x+bar_w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Arial" font-size="11">{value:.2f}</text>')
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_figures(reach_rows: list[dict[str, object]], overlay_rows: list[dict[str, object]]) -> None:
    FIGS.mkdir(exist_ok=True)
    unpol = [row for row in reach_rows if row["scenario"] == "clic3000ll" and not row["overlay"] and row["polarization"] == "unpol"]
    unpol.sort(key=lambda r: int(r["mass_GeV"]))
    write_svg_bar(
        FIGS / "fresh_clic_unpol_counting_Z.svg",
        "Fresh CLIC unpolarized counting Z_A",
        [f"{int(row['mass_GeV'])/1000.0:.1f}" for row in unpol],
        [float(row["Z_A"]) for row in unpol],
        "Z_A",
    )
    overlay = [row for row in overlay_rows if row["polarization"] == "unpol"]
    overlay.sort(key=lambda r: int(r["mass_GeV"]))
    write_svg_bar(
        FIGS / "fresh_clic_overlay_Z_ratio.svg",
        "Overlay stress-test impact on unpolarized Z_A",
        [f"{int(row['mass_GeV'])/1000.0:.1f}" for row in overlay],
        [float(row["Z_ratio_overlay_clean"]) for row in overlay],
        "Z overlay / Z clean",
    )


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    index = merge_indexes(index_cutflows(ISR_CUTFLOWS), index_cutflows(CLIC_CUTFLOWS), index_cutflows(CLIC_OVERLAY_CUTFLOWS))

    reach_rows = build_reach(index)
    overlay_rows = build_overlay_impact(index)
    isr_comparison_rows = build_isr_comparison(index)

    write_dict_csv(LOGS / "fresh_clic_reach_counting.csv", reach_rows)
    write_dict_csv(LOGS / "fresh_clic_overlay_impact.csv", overlay_rows)
    write_dict_csv(LOGS / "fresh_clic_vs_isr.csv", isr_comparison_rows)

    write_reach_table(reach_rows)
    write_overlay_table(overlay_rows)
    write_isr_comparison_table(isr_comparison_rows)
    write_sqrts_table(SQRTS_SUMMARY)
    write_profile_table(PROFILE_SUMMARY)
    write_figures(reach_rows, overlay_rows)

    print(f"wrote {LOGS / 'fresh_clic_reach_counting.csv'}")
    print(f"wrote {LOGS / 'fresh_clic_overlay_impact.csv'}")
    print(f"wrote {LOGS / 'fresh_clic_vs_isr.csv'}")
    print(f"wrote tables in {TABLES}")


if __name__ == "__main__":
    main()
