#!/usr/bin/env python3
"""Export the normalized signal recoil overlay stored by Histograms.py."""

from __future__ import annotations

import argparse
from pathlib import Path

import ROOT


ROOT.gROOT.SetBatch(True)
REPO_ROOT = Path(__file__).resolve().parents[1]
CANVAS_NAME = "mrecoil_isolated_toplikes_rec_missE_cut_SignalsOverlay"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "ttp_Analysis/Tt1Moutput.root",
    )
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "results/paper/signals_after_cuts.pdf")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = ROOT.TFile.Open(str(args.input))
    if not source or source.IsZombie():
        raise SystemExit(f"Cannot open {args.input}")
    canvas = source.Get(CANVAS_NAME)
    if not canvas:
        raise SystemExit(f"Canvas {CANVAS_NAME!r} not found in {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.Draw()
    canvas.SaveAs(str(args.output))
    source.Close()


if __name__ == "__main__":
    main()
