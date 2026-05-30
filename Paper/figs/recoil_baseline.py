#!/usr/bin/env python3
"""
Rebuild the recoil_baseline figure (background total + signal) for one mass.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import ROOT
from mass_color_map import baseline_color_for_mass

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)


def build_baseline_hists(source_path: pathlib.Path, mass: int) -> tuple[ROOT.TH1, ROOT.TH1]:
    """Extract background total and signal histograms from the mass stack canvas."""
    if not source_path.exists():
        raise FileNotFoundError(f"Missing ROOT file: {source_path}")

    canvas_name = f"stack_mrecoil_isolated_toplikes_rec_missE_cut_{mass}_CrossSection"
    stack_name = f"mrecoil_isolated_toplikes_rec_missE_cut_stack_{mass}"
    signal_token = f"m_{{T}}={mass}"

    source_file = ROOT.TFile.Open(str(source_path))
    if not source_file or source_file.IsZombie():
        raise OSError(f"Unable to open ROOT file: {source_path}")

    canvas = source_file.Get(canvas_name)
    if not canvas:
        source_file.Close()
        raise KeyError(f"Canvas '{canvas_name}' not found in {source_path}")

    stack = canvas.FindObject(stack_name)
    if not stack:
        source_file.Close()
        raise KeyError(f"Stack '{stack_name}' not found in canvas '{canvas_name}'")

    hists = stack.GetHists()
    if not hists or hists.GetSize() == 0:
        source_file.Close()
        raise RuntimeError(f"No histograms found in stack '{stack_name}'")

    background_hists = []
    signal_hist = None
    for idx in range(hists.GetSize()):
        hist = hists.At(idx)
        clone = hist.Clone(f"clone_{mass}_{idx}")
        if hasattr(clone, "SetDirectory"):
            clone.SetDirectory(0)
        if signal_token in hist.GetName():
            signal_hist = clone
        else:
            background_hists.append(clone)

    source_file.Close()

    if not signal_hist or not background_hists:
        raise RuntimeError(f"Could not find signal/background for mass {mass} GeV.")

    background = background_hists[0].Clone(f"background_total_{mass}")
    if hasattr(background, "SetDirectory"):
        background.SetDirectory(0)
    for hist in background_hists[1:]:
        background.Add(hist)
    return background, signal_hist


def style_hists(background: ROOT.TH1, signal_hist: ROOT.TH1, mass: int) -> None:
    """Apply plot style and mass-consistent signal color."""
    max_y = max(background.GetMaximum(), signal_hist.GetMaximum())
    background.SetMaximum(max_y * 1.25)

    background.SetFillColor(ROOT.kBlack)
    background.SetFillStyle(1001)
    background.SetLineColor(ROOT.kBlack)
    background.SetLineWidth(2)
    background.GetXaxis().SetTitle("#it{m}_{recoil} [GeV]")
    background.GetYaxis().SetTitle("Number of events")
    for axis in (background.GetXaxis(), background.GetYaxis()):
        axis.SetTitleFont(42)
        axis.SetLabelFont(42)
        axis.SetTitleSize(0.045)
        axis.SetLabelSize(0.042)

    signal_hist.SetLineColor(baseline_color_for_mass(mass))
    signal_hist.SetLineWidth(3)
    signal_hist.SetFillStyle(0)
    signal_hist.SetMarkerStyle(0)
    for axis in (signal_hist.GetXaxis(), signal_hist.GetYaxis()):
        axis.SetTitleFont(42)
        axis.SetLabelFont(42)


def make_plot(source_path: pathlib.Path, mass: int, outdir: pathlib.Path, formats: list[str]) -> None:
    """Build and save the baseline plot for one mass."""
    background, signal_hist = build_baseline_hists(source_path, mass)
    style_hists(background, signal_hist, mass)

    canvas = ROOT.TCanvas(f"c_recoil_baseline_{mass}", f"c_recoil_baseline_{mass}", 1200, 850)
    canvas.SetMargin(0.12, 0.05, 0.12, 0.08)
    background.Draw("HIST")
    signal_hist.Draw("HIST SAME")

    legend = ROOT.TLegend(0.60, 0.68, 0.89, 0.86)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.04)
    legend.AddEntry(background, "Background total", "f")
    legend.AddEntry(signal_hist, f"Signal m_{{T}}={mass} GeV", "l")
    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetTextFont(42)
    latex.SetTextSize(0.045)
    latex.SetTextAlign(13)
    latex.DrawLatexNDC(0.12, 0.97, "e^{+}e^{-} collider")
    latex.SetTextAlign(33)
    latex.DrawLatexNDC(0.88, 0.97, "L = 5 ab^{-1}; #sqrt{s} = 3 TeV")

    outdir.mkdir(parents=True, exist_ok=True)
    for ext in formats:
        canvas.SaveAs(str(outdir / f"recoil_baseline_{mass}.{ext}"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild recoil baseline figure for one mass.")
    parser.add_argument("--mass", type=int, default=1200, help="Mass hypothesis (GeV).")
    parser.add_argument(
        "--input",
        type=pathlib.Path,
        default=pathlib.Path("/home/higinio/Documentos/ASE/ttp_Analysis/Tt1Moutput.root"),
        help="ROOT file for the unpolarised baseline sample.",
    )
    parser.add_argument(
        "--outdir",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent,
        help="Output directory for the generated figure.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "png"],
        default=["pdf"],
        help="Output formats (default: pdf).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        make_plot(args.input, args.mass, args.outdir, args.formats)
    except Exception as exc:  # pragma: no cover - runtime error reporting
        sys.stderr.write(f"[ERROR] {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
