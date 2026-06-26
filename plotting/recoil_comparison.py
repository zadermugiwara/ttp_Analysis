#!/usr/bin/env python3
"""
Rebuild the recoil comparison plot (Figure 2) with baseline vs ISR+polarised scenarios.

Inputs are the ROOT outputs of the three production configurations:
  - Unpolarised, no ISR:           ttp_Analysis/Tt1Moutput.root
  - ISR with P(e-) = +80%:         ttp_Analysis+80ISR/Tt1Moutput.root
  - ISR with P(e-) = -80%:         ttp_Analysis-80ISR/Tt1Moutput.root

The script extracts the recoil-mass stack for a given mass hypothesis, sums all
stack members to form total signal+background spectra, and overlays the three
configurations.  Update the ROOT paths or mass as needed.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Dict, List, Tuple

import ROOT
from mass_color_map import scenario_colors_for_mass

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
DEFAULT_MASSES = [1200, 1600, 2000, 2400]
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def build_total_hist(path: pathlib.Path, mass: int) -> ROOT.TH1:
    """Load the recoil-mass stack from a ROOT file and return the total (signal+background) histogram."""
    if not path.exists():
        raise FileNotFoundError(f"Missing ROOT file: {path}")

    canvas_name = f"stack_mrecoil_isolated_toplikes_rec_missE_cut_{mass}_CrossSection"
    stack_name = f"mrecoil_isolated_toplikes_rec_missE_cut_stack_{mass}"

    f = ROOT.TFile.Open(str(path))
    if not f or f.IsZombie():
        raise OSError(f"Unable to open ROOT file: {path}")

    canvas = f.Get(canvas_name)
    if not canvas:
        f.Close()
        raise KeyError(f"Canvas '{canvas_name}' not found in {path}")

    stack = canvas.FindObject(stack_name)
    if not stack:
        f.Close()
        raise KeyError(f"Stack '{stack_name}' not found in canvas '{canvas_name}' of {path}")

    hists = stack.GetHists()
    if not hists or hists.GetSize() == 0:
        f.Close()
        raise RuntimeError(f"No histograms found in stack '{stack_name}' of {path}")

    total = hists.At(0).Clone(f"total_{path.stem}_{mass}")
    total.SetDirectory(0)
    total.Sumw2()
    for idx in range(1, hists.GetSize()):
        total.Add(hists.At(idx))

    f.Close()
    return total


def style_hist(hist: ROOT.TH1, color: int, title: str) -> None:
    """Apply consistent styling to a histogram."""
    hist.SetLineColor(color)
    hist.SetLineWidth(3)
    hist.SetFillStyle(0)
    hist.SetMarkerStyle(0)
    # Keep legend label, but avoid drawing a canvas title at the top.
    hist.SetTitle("")
    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()
    xaxis.SetTitle("#it{m}_{recoil} [GeV]")
    xaxis.SetRangeUser(800, 3000)
    yaxis.SetTitle("Number of events")
    for axis in (xaxis, yaxis):
        axis.SetTitleFont(42)
        axis.SetLabelFont(42)
        axis.SetTitleSize(0.052)
        axis.SetLabelSize(0.046)


def make_plot(
    paths: Dict[str, pathlib.Path],
    mass: int,
    outdir: pathlib.Path,
    scenarios: List[str],
    formats: List[str],
    root_file: ROOT.TFile | None = None,
) -> ROOT.TCanvas:
    """Build and save the comparison plot."""
    mass_colors = scenario_colors_for_mass(mass)
    scenario_specs = {
        "base": ("Baseline S + B", mass_colors["base"]),
        "plus80": ("ISR + P_{e^{-}}=+80% S + B ", mass_colors["plus80"]),
        "minus80": ("ISR + P_{e^{-}}=-80% S + B ", mass_colors["minus80"]),
    }
    totals: Dict[str, Tuple[ROOT.TH1, int]] = {}
    for key in scenarios:
        label, color = scenario_specs[key]
        totals[label] = (build_total_hist(paths[key], mass), color)

    # Style and find global maximum
    max_y = 0.0
    for label, (hist, color) in totals.items():
        style_hist(hist, color, label)
        max_y = max(max_y, hist.GetMaximum())
    for hist, _ in totals.values():
        hist.SetMaximum(max_y * 1.25)

    # Draw
    canvas = ROOT.TCanvas(f"c_recoil_comparison_{mass}", f"c_recoil_comparison_{mass}", 1200, 850)
    canvas.SetMargin(0.12, 0.05, 0.12, 0.08)

    first = True
    legend = ROOT.TLegend(0.60, 0.68, 0.88, 0.84)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.034)

    for label, (hist, _) in totals.items():
        draw_opt = "HIST" if first else "HIST SAME"
        hist.Draw(draw_opt)
        legend.AddEntry(hist, label, "l")
        first = False

    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetTextFont(42)
    header_text_size = 0.045
    latex.SetTextSize(header_text_size)
    # Place header texts exactly on the frame top line.
    left_x = max(0.01, canvas.GetLeftMargin() - 0.004)
    right_x = min(0.99, 1.0 - canvas.GetRightMargin() + 0.004)
    center_x = 0.5 * (left_x + right_x)
    # Raise text above the frame line by an amount proportional to font size.
    top_y = min(0.99, 1.0 - canvas.GetTopMargin() + 0.12 * header_text_size)

    latex.SetTextAlign(11)  # left, bottom
    latex.DrawLatexNDC(left_x, top_y, "e^{+}e^{-} collider")
    latex.SetTextAlign(31)  # right, bottom
    latex.DrawLatexNDC(right_x, top_y, "L = 5 ab^{-1}; #sqrt{s} = 3 TeV")
    latex.SetTextAlign(21)  # center, bottom
    latex.DrawLatexNDC(center_x, top_y, f"m_{{T}} = {mass} GeV")

    # Ensure drawn primitives are finalized before serialization.
    canvas.Modified()
    canvas.Update()

    if root_file:
        root_file.cd()
        canvas.Write(f"recoil_comparison_{mass}")

    outdir.mkdir(parents=True, exist_ok=True)
    for ext in formats:
        canvas.SaveAs(str(outdir / f"recoil_comparison_{mass}.{ext}"))
    return canvas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild recoil comparison plot (baseline vs ISR ±80%).")
    parser.add_argument("--mass", type=int, default=None, help="Single mass hypothesis for the recoil stack naming (GeV).")
    parser.add_argument("--masses", nargs="+", type=int, help="Mass hypotheses to process in one run.")
    parser.add_argument(
        "--base",
        type=pathlib.Path,
        default=REPO_ROOT / "ttp_Analysis/Tt1Moutput.root",
        help="ROOT file for the unpolarised, no-ISR sample.",
    )
    parser.add_argument(
        "--plus80",
        type=pathlib.Path,
        default=REPO_ROOT / "ttp_Analysis+80ISR/Tt1Moutput.root",
        help="ROOT file for the ISR + P(e-) = +80% sample.",
    )
    parser.add_argument(
        "--minus80",
        type=pathlib.Path,
        default=REPO_ROOT / "ttp_Analysis-80ISR/Tt1Moutput.root",
        help="ROOT file for the ISR + P(e-) = -80% sample.",
    )
    parser.add_argument(
        "--outdir",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent,
        help="Output directory for the generated figure.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=["base", "plus80", "minus80"],
        default=["base", "plus80"],
        help="Scenarios to include in the overlay.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "png"],
        default=["pdf"],
        help="Output formats (default: pdf).",
    )
    parser.add_argument(
        "--root-output",
        type=pathlib.Path,
        default=None,
        help="Optional ROOT file path to store generated canvases (default: <outdir>/recoil_comparison.root).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {"base": args.base, "plus80": args.plus80, "minus80": args.minus80}
    args.outdir.mkdir(parents=True, exist_ok=True)
    root_output = args.root_output or (args.outdir / "recoil_comparison.root")
    if args.masses:
        masses = args.masses
    elif args.mass is not None:
        masses = [args.mass]
    else:
        masses = DEFAULT_MASSES
    root_file = ROOT.TFile(str(root_output), "RECREATE")
    if not root_file or root_file.IsZombie():
        sys.stderr.write(f"[ERROR] Could not create ROOT output file: {root_output}\n")
        sys.exit(1)
    try:
        for mass in masses:
            make_plot(paths, mass, args.outdir, args.scenarios, args.formats, root_file=root_file)
        root_file.Write()
        root_file.Close()
    except Exception as exc:  # pragma: no cover - runtime error reporting
        if root_file:
            root_file.Close()
        sys.stderr.write(f"[ERROR] {exc}\\n")
        sys.exit(1)
    # Workaround: some local ROOT/PyROOT combinations segfault on interpreter teardown
    # after successful plotting. Force a clean process exit after outputs are written.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
