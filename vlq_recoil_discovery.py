#!/usr/bin/env python3
"""
Profile-likelihood discovery analysis for VLQ(t) recoil-mass searches.

Implements a binned, extended RooFit/RooStats workflow with optional ROI scans,
cross-section re-scaling, asymptotic discovery tests, and frequentist toy checks.
"""

import argparse
import logging
import math
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

def _reexec_with_compatible_python() -> None:
    if (
        sys.version_info[:2] != (3, 11)
        and os.environ.get("ASE_DISCOVERY_REEXEC") != "1"
    ):
        alt_python = shutil.which("python3.11") or shutil.which("python3.10")
        if alt_python and os.path.abspath(sys.executable) != os.path.abspath(alt_python):
            os.environ["ASE_DISCOVERY_REEXEC"] = "1"
            os.execv(alt_python, [alt_python, *sys.argv])


def _bootstrap_root_env() -> None:
    repo_root = Path(__file__).resolve().parent
    candidates: List[Path] = []

    root_setup_env = os.environ.get("ROOT_SETUP")
    if root_setup_env:
        candidates.append(Path(root_setup_env).expanduser())

    candidates.extend(
        [
            repo_root / "Analysis/root/root-new/bin/thisroot.sh",
            repo_root / "Analysis/root/root/bin/thisroot.sh",
        ]
    )

    for setup_path in candidates:
        if not setup_path.exists():
            continue
        try:
            env_dump = subprocess.check_output(
                ["bash", "-lc", f"source {shlex.quote(str(setup_path))} >/dev/null 2>&1 && env"],
                text=True,
            )
        except subprocess.CalledProcessError:
            continue

        for line in env_dump.splitlines():
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ[key] = value
            if key == "PYTHONPATH":
                for entry in value.split(":"):
                    if entry and entry not in sys.path:
                        sys.path.insert(0, entry)
        return


_reexec_with_compatible_python()
try:
    import ROOT
except (ModuleNotFoundError, ImportError):
    _reexec_with_compatible_python()
    _bootstrap_root_env()
    import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)


# ---------------------------------------------------------------------------
# Argument parsing and configuration
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Binned profile-likelihood discovery test for VLQ(t) recoil mass.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--signal", nargs="+", required=True, help="Signal ROOT file(s).")
    parser.add_argument("--background", nargs="+", required=True, help="Background ROOT file(s).")
    parser.add_argument("--hist", required=True, help="Histogram name common to all ROOT files.")
    parser.add_argument("--obs", help="ROOT file providing observed data histogram.")
    parser.add_argument("--var", default="m_recoil", help="RooRealVar name.")
    parser.add_argument("--xmin", type=float, help="Lower edge of analysis window.")
    parser.add_argument("--xmax", type=float, help="Upper edge of analysis window.")
    parser.add_argument("--rebin", type=int, help="Optional rebin factor (>1).")
    parser.add_argument(
        "--scan-bins",
        type=int,
        help="Divide [xmin,xmax] into this many equal windows and evaluate expected Z.",
    )
    parser.add_argument(
        "--scan-keep",
        type=int,
        default=1,
        help="Keep the best N scan windows (union) ranked by expected Z.",
    )
    parser.add_argument(
        "--scale-from-xsec",
        action="store_true",
        help="Scale histograms using cross sections and luminosity.",
    )
    parser.add_argument("--lumi", type=float, help="Integrated luminosity in pb^-1.")
    parser.add_argument(
        "--signal-xsec",
        type=float,
        nargs="+",
        help="Signal cross section(s) in pb (one value or one per --signal file).",
    )
    parser.add_argument(
        "--background-xsec",
        type=float,
        nargs="+",
        help="Background cross section(s) in pb (match number of --background files or give a total).",
    )
    parser.add_argument(
        "--background-norm-unc",
        type=float,
        default=0.0,
        help="Relative background-normalization uncertainty for the counting cross-check.",
    )
    parser.add_argument(
        "--signal-eff-unc",
        type=float,
        default=0.0,
        help="Relative signal-efficiency uncertainty for the conservative counting cross-check.",
    )
    parser.add_argument(
        "--run-roostats-asymptotic",
        action="store_true",
        help=(
            "Also run RooStats AsymptoticCalculator as a diagnostic.  The manual "
            "profile-likelihood closure is used by default because the local ROOT "
            "build can return p0=0.5 for zero-nuisance discovery models."
        ),
    )
    parser.add_argument("--toys", type=int, default=0, help="Number of B-only toys for cross-check.")
    parser.add_argument("--outdir", default="./out", help="Output directory.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# Histogram utilities
# ---------------------------------------------------------------------------

def load_and_sum_hists(
    paths: Sequence[str],
    hist_name: str,
    per_file_targets: Optional[Sequence[Optional[float]]] = None,
) -> ROOT.TH1D:
    """Load histograms from ROOT files, detach them, and return their sum."""
    total: Optional[ROOT.TH1] = None
    if per_file_targets is not None and len(per_file_targets) != len(paths):
        raise ValueError("per_file_targets length must match number of paths.")
    for idx, path in enumerate(paths):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing ROOT file: {path}")
        f = ROOT.TFile.Open(path)
        if not f or f.IsZombie():
            raise OSError(f"Unable to open ROOT file: {path}")
        hist = f.Get(hist_name)
        if not hist:
            f.Close()
            raise KeyError(f"Histogram '{hist_name}' not found in {path}")
        if not isinstance(hist, ROOT.TH1):
            f.Close()
            raise TypeError(f"Object '{hist_name}' in {path} is not a TH1.")
        clone = hist.Clone(f"{hist_name}_{os.path.basename(path)}")
        clone.SetDirectory(0)
        clone.Sumw2()
        if per_file_targets is not None:
            target = per_file_targets[idx]
            if target is not None:
                scale_histogram_to_yield(clone, target, os.path.basename(path))
        f.Close()
        if total is None:
            total = clone.Clone(f"{hist_name}_sum")
            total.SetDirectory(0)
            total.Sumw2()
        else:
            total.Add(clone)
    if total is None:
        raise RuntimeError(f"No histograms were loaded for '{hist_name}'.")
    return total


def apply_range_and_rebin(
    hist: ROOT.TH1,
    xmin: Optional[float],
    xmax: Optional[float],
    rebin: Optional[int],
) -> ROOT.TH1:
    """Restrict histogram range to physical bins and optionally rebin."""
    out = hist.Clone(f"{hist.GetName()}_proc")
    out.SetDirectory(0)
    out.Sumw2()
    if xmin is not None or xmax is not None:
        xaxis = out.GetXaxis()
        lower = xaxis.GetXmin() if xmin is None else xmin
        upper = xaxis.GetXmax() if xmax is None else xmax
        if lower >= upper:
            raise ValueError(f"Invalid histogram range [{lower}, {upper}].")

        first_bin = xaxis.FindFixBin(lower + 1e-9)
        last_bin = xaxis.FindFixBin(upper - 1e-9)
        first_bin = max(1, min(first_bin, out.GetNbinsX()))
        last_bin = max(1, min(last_bin, out.GetNbinsX()))
        if first_bin > last_bin:
            raise ValueError(f"Requested range [{lower}, {upper}] contains no histogram bins.")

        nbins = last_bin - first_bin + 1
        low_edge = xaxis.GetBinLowEdge(first_bin)
        high_edge = xaxis.GetBinUpEdge(last_bin)
        ranged = ROOT.TH1D(f"{out.GetName()}_range", out.GetTitle(), nbins, low_edge, high_edge)
        ranged.SetDirectory(0)
        ranged.Sumw2()
        for src_bin in range(first_bin, last_bin + 1):
            dst_bin = src_bin - first_bin + 1
            ranged.SetBinContent(dst_bin, out.GetBinContent(src_bin))
            ranged.SetBinError(dst_bin, out.GetBinError(src_bin))
        out = ranged
    if rebin is not None:
        if rebin <= 1:
            logging.warning("Ignoring non-positive rebin factor %s.", rebin)
        else:
            if out.GetNbinsX() % rebin != 0:
                logging.warning(
                    "Rebin factor %s does not divide %s bins evenly for %s.",
                    rebin,
                    out.GetNbinsX(),
                    out.GetName(),
                )
            out = out.Rebin(rebin, f"{out.GetName()}_rebin")
            out.SetDirectory(0)
            out.Sumw2()
    return out


def scale_histogram_to_yield(hist: ROOT.TH1, target_yield: float, label: str) -> None:
    """Scale histogram so its integral equals target_yield."""
    current = hist.Integral()
    if current <= 0:
        raise RuntimeError(f"Cannot scale {label} histogram with non-positive integral ({current}).")
    if target_yield <= 0:
        raise ValueError(f"Target yield for {label} must be positive (got {target_yield}).")
    scale = target_yield / current
    hist.Scale(scale)
    logging.debug("Scaled %s histogram by factor %.6f to reach yield %.3f.", label, scale, target_yield)


def prepare_scale_targets(
    paths: Sequence[str],
    xsecs: Optional[Sequence[float]],
    lumi: Optional[float],
    label: str,
) -> Tuple[List[Optional[float]], Optional[float]]:
    """Prepare per-file targets (if provided) and total desired yield."""
    if xsecs is None:
        return [None] * len(paths), None
    if lumi is None or lumi <= 0:
        raise ValueError(f"--lumi must be provided and positive when scaling {label} histograms.")
    if any(val <= 0 for val in xsecs):
        raise ValueError(f"{label.capitalize()} cross sections must be positive.")
    if len(xsecs) == 1:
        total = xsecs[0] * lumi
        return [None] * len(paths), total
    if len(xsecs) != len(paths):
        raise ValueError(
            f"Provide either one {label} cross section or one per input file "
            f"(expected {len(paths)}, got {len(xsecs)})."
        )
    per_file = [xs * lumi for xs in xsecs]
    return per_file, sum(per_file)


def clone_with_mask(orig: ROOT.TH1, mask: List[bool], name: str) -> ROOT.TH1:
    """Return a clone retaining only bins with mask=True."""
    out = orig.Clone(name)
    out.SetDirectory(0)
    for ibin in range(1, orig.GetNbinsX() + 1):
        if not mask[ibin - 1]:
            out.SetBinContent(ibin, 0.0)
            out.SetBinError(ibin, 0.0)
    return out


# ---------------------------------------------------------------------------
# Significance utilities
# ---------------------------------------------------------------------------

def asimov_counting_Z(s: float, b: float) -> float:
    """Cowan-Asimov significance for counting experiments."""
    if s <= 0:
        return 0.0
    if b <= 0:
        return math.sqrt(2.0 * s)
    term = (s + b) * math.log(1.0 + s / b) - s
    return math.sqrt(max(0.0, 2.0 * term))


def asimov_binned_Z(hs: ROOT.TH1, hb: ROOT.TH1) -> float:
    """Cowan-Asimov significance summed over histogram bins."""
    if hs.GetNbinsX() != hb.GetNbinsX():
        raise ValueError("Signal/background histograms must share binning.")
    total = 0.0
    for ibin in range(1, hs.GetNbinsX() + 1):
        s = hs.GetBinContent(ibin)
        b = hb.GetBinContent(ibin)
        if s <= 0 and b <= 0:
            continue
        if b <= 0:
            total += 2.0 * s
        else:
            total += 2.0 * ((s + b) * math.log(1.0 + s / b) - s)
    return math.sqrt(max(0.0, total))


def poisson_template_nll(mu_value: float, h_sig: ROOT.TH1, h_bkg: ROOT.TH1, h_data: ROOT.TH1) -> float:
    """Binned Poisson NLL, dropping data-only factorial constants."""
    if h_sig.GetNbinsX() != h_bkg.GetNbinsX() or h_sig.GetNbinsX() != h_data.GetNbinsX():
        raise ValueError("Signal, background, and data histograms must share binning.")
    total = 0.0
    for ibin in range(1, h_sig.GetNbinsX() + 1):
        observed = h_data.GetBinContent(ibin)
        expected = h_bkg.GetBinContent(ibin) + mu_value * h_sig.GetBinContent(ibin)
        expected = max(expected, 1e-12)
        total += expected - observed * math.log(expected)
    return total


def minimize_mu_1d(
    h_sig: ROOT.TH1,
    h_bkg: ROOT.TH1,
    h_data: ROOT.TH1,
    mu_min: float = 0.0,
    mu_max: float = 10.0,
    tol: float = 1e-5,
) -> Tuple[float, float]:
    """Minimize the one-parameter binned template NLL with a bounded search."""
    inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
    inv_phi2 = (3.0 - math.sqrt(5.0)) / 2.0
    lo, hi = mu_min, mu_max
    h = hi - lo
    c = lo + inv_phi2 * h
    d = lo + inv_phi * h
    fc = poisson_template_nll(c, h_sig, h_bkg, h_data)
    fd = poisson_template_nll(d, h_sig, h_bkg, h_data)
    while hi - lo > tol:
        if fc < fd:
            hi = d
            d = c
            fd = fc
            h = hi - lo
            c = lo + inv_phi2 * h
            fc = poisson_template_nll(c, h_sig, h_bkg, h_data)
        else:
            lo = c
            c = d
            fc = fd
            h = hi - lo
            d = lo + inv_phi * h
            fd = poisson_template_nll(d, h_sig, h_bkg, h_data)

    candidates = [
        (mu_min, poisson_template_nll(mu_min, h_sig, h_bkg, h_data)),
        (mu_max, poisson_template_nll(mu_max, h_sig, h_bkg, h_data)),
        ((lo + hi) / 2.0, poisson_template_nll((lo + hi) / 2.0, h_sig, h_bkg, h_data)),
    ]
    return min(candidates, key=lambda item: item[1])


def manual_binned_profile_likelihood(h_sig: ROOT.TH1, h_bkg: ROOT.TH1, h_data: ROOT.TH1) -> Dict[str, float]:
    """Compute q0 for the binned signal-plus-background template model."""
    mu_hat, nll_hat = minimize_mu_1d(h_sig, h_bkg, h_data)
    nll_b = poisson_template_nll(0.0, h_sig, h_bkg, h_data)
    q0 = 0.0 if mu_hat <= 0.0 else max(0.0, 2.0 * (nll_b - nll_hat))
    return {
        "mu_hat": mu_hat,
        "q0": q0,
        "Z": math.sqrt(q0),
        "nll_sb": nll_hat,
        "nll_b": nll_b,
    }


def asimov_counting_Z_with_bkg_uncertainty(s: float, b: float, sigma_b: float) -> float:
    """Cowan-Asimov discovery significance with a Gaussian background constraint."""
    if s <= 0:
        return 0.0
    if b <= 0 or sigma_b <= 0:
        return asimov_counting_Z(s, b)
    sigma2 = sigma_b * sigma_b
    first_num = (s + b) * (b + sigma2)
    first_den = b * b + (s + b) * sigma2
    second_arg = 1.0 + (sigma2 * s) / (b * (b + sigma2))
    if first_num <= 0 or first_den <= 0 or second_arg <= 0:
        return 0.0
    term = (s + b) * math.log(first_num / first_den) - (b * b / sigma2) * math.log(second_arg)
    return math.sqrt(max(0.0, 2.0 * term))


def p_value_from_Z(z_value: float) -> float:
    """One-sided Gaussian tail probability for a discovery significance."""
    if z_value <= 0:
        return 0.5
    return 0.5 * math.erfc(z_value / math.sqrt(2.0))


def conservative_counting_Z_with_systematics(
    s: float,
    b: float,
    rel_bkg_unc: float,
    rel_sig_unc: float,
) -> float:
    """Counting cross-check using a one-sigma downward signal efficiency shift."""
    s_eff = max(0.0, s * (1.0 - max(0.0, rel_sig_unc)))
    sigma_b = max(0.0, rel_bkg_unc) * b
    return asimov_counting_Z_with_bkg_uncertainty(s_eff, b, sigma_b)


# ---------------------------------------------------------------------------
# ROI scanning
# ---------------------------------------------------------------------------

def perform_roi_scan(
    h_sig: ROOT.TH1,
    h_bkg: ROOT.TH1,
    scan_bins: int,
    scan_keep: int,
    mu_true: float,
) -> Tuple[ROOT.TH1, ROOT.TH1, Dict[str, List[Dict[str, float]]]]:
    """Evaluate sliding windows and retain union of best scan_keep windows."""
    if scan_bins <= 0:
        raise ValueError("--scan-bins must be positive.")
    scan_keep = max(1, scan_keep)

    axis = h_sig.GetXaxis()
    xmin = axis.GetBinLowEdge(1)
    xmax = axis.GetBinUpEdge(h_sig.GetNbinsX())
    window_width = (xmax - xmin) / scan_bins

    windows: List[Dict[str, float]] = []
    mask = [False] * h_sig.GetNbinsX()

    for idx in range(scan_bins):
        wmin = xmin + idx * window_width
        wmax = xmin + (idx + 1) * window_width
        start = axis.FindFixBin(wmin + 1e-9)
        end = axis.FindFixBin(wmax - 1e-9)
        if start > end:
            continue
        sig_slice = clone_with_mask(h_sig, [(start <= i <= end) for i in range(1, h_sig.GetNbinsX() + 1)], f"sig_scan_{idx}")
        bkg_slice = clone_with_mask(h_bkg, [(start <= i <= end) for i in range(1, h_bkg.GetNbinsX() + 1)], f"bkg_scan_{idx}")
        z_bin = asimov_binned_Z(sig_slice, bkg_slice)
        windows.append(
            {
                "idx": idx,
                "xmin": axis.GetBinLowEdge(start),
                "xmax": axis.GetBinUpEdge(end),
                "width": axis.GetBinUpEdge(end) - axis.GetBinLowEdge(start),
                "Z": z_bin,
                "S": mu_true * sig_slice.Integral(),
                "B": bkg_slice.Integral(),
                "start": start,
                "end": end,
            }
        )

    if not windows:
        raise RuntimeError("Sliding-window scan produced no valid windows.")

    windows.sort(key=lambda item: item["Z"], reverse=True)
    selected = windows[:scan_keep]
    for win in selected:
        for ibin in range(win["start"], win["end"] + 1):
            mask[ibin - 1] = True

    sig_roi = clone_with_mask(h_sig, mask, f"{h_sig.GetName()}_roi")
    bkg_roi = clone_with_mask(h_bkg, mask, f"{h_bkg.GetName()}_roi")

    info = {
        "windows": selected,
        "width": window_width,
    }
    return sig_roi, bkg_roi, info


# ---------------------------------------------------------------------------
# RooFit helpers
# ---------------------------------------------------------------------------

def make_asimov_hist(h_sig: ROOT.TH1, h_bkg: ROOT.TH1, mu_value: float, name: str) -> ROOT.TH1:
    """Construct an Asimov histogram for the given signal strength."""
    hist = h_bkg.Clone(name)
    hist.SetDirectory(0)
    for ibin in range(1, hist.GetNbinsX() + 1):
        expected = h_bkg.GetBinContent(ibin) + mu_value * h_sig.GetBinContent(ibin)
        hist.SetBinContent(ibin, expected)
        hist.SetBinError(ibin, math.sqrt(expected) if expected > 0 else 0.0)
    return hist


def make_data_hist(hist: ROOT.TH1, xvar: ROOT.RooRealVar, name: str) -> ROOT.RooDataHist:
    """Wrap a TH1 into a RooDataHist."""
    return ROOT.RooDataHist(name, name, ROOT.RooArgList(xvar), hist)


def build_workspace(
    xvar: ROOT.RooRealVar,
    sig_pdf: ROOT.RooHistPdf,
    bkg_pdf: ROOT.RooHistPdf,
    sb_pdf: ROOT.RooAddPdf,
    mu: ROOT.RooRealVar,
    s_tot: ROOT.RooRealVar,
    b_tot: ROOT.RooRealVar,
) -> Tuple[ROOT.RooWorkspace, ROOT.RooStats.ModelConfig, ROOT.RooStats.ModelConfig]:
    """Create a workspace hosting the PDFs and ModelConfigs."""
    w = ROOT.RooWorkspace("w", True)

    for obj in (xvar, sig_pdf, bkg_pdf, sb_pdf, mu, s_tot, b_tot):
        getattr(w, "import")(obj, ROOT.RooFit.RecycleConflictNodes())

    w.defineSet("poi", ROOT.RooArgSet(w.var("mu")))
    w.defineSet("obs", ROOT.RooArgSet(w.var(xvar.GetName())))
    w.defineSet("nuis", ROOT.RooArgSet())

    w.var("mu").setVal(1.0)
    w.var("mu").setConstant(False)

    sb_model = ROOT.RooStats.ModelConfig("SplusB", w)
    sb_model.SetPdf(w.pdf("sbPdf"))
    sb_model.SetParametersOfInterest(w.set("poi"))
    sb_model.SetObservables(w.set("obs"))
    sb_model.SetSnapshot(ROOT.RooArgSet(w.var("mu")))

    mu_b_only = w.var("mu")
    mu_b_only.setVal(0.0)
    mu_b_only.setConstant(True)

    b_model = ROOT.RooStats.ModelConfig("Bonly", w)
    b_model.SetPdf(w.pdf("sbPdf"))
    b_model.SetParametersOfInterest(w.set("poi"))
    b_model.SetObservables(w.set("obs"))
    b_model.SetSnapshot(ROOT.RooArgSet(w.var("mu")))

    mu_b_only.setConstant(False)
    mu_b_only.setVal(1.0)

    getattr(w, "import")(sb_model)
    getattr(w, "import")(b_model)

    return w, sb_model, b_model


def _fit_with_fallback(
    pdf: ROOT.RooAbsPdf,
    data: ROOT.RooAbsData,
    mu: ROOT.RooRealVar,
    mu_value: Optional[float],
    const: bool,
) -> Tuple[float, Dict[str, object]]:
    """Run fitTo; if it fails, fall back to RooMinimizer on the explicit NLL."""
    keep: Dict[str, object] = {}
    if mu_value is not None:
        mu.setVal(mu_value)
    mu.setConstant(const)
    result = pdf.fitTo(
        data,
        ROOT.RooFit.Save(True),
        ROOT.RooFit.PrintLevel(-1),
        ROOT.RooFit.Strategy(1),
        ROOT.RooFit.Extended(True),
    )
    if result:
        nll_val = result.minNll()
        keep["fit_result"] = result
    else:
        logging.warning("fitTo failed; falling back to explicit NLL minimisation.")
        nll = pdf.createNLL(data, ROOT.RooFit.Extended(True), ROOT.RooFit.Offset(True))
        minim = ROOT.RooMinimizer(nll)
        minim.setPrintLevel(-1)
        minim.setStrategy(1)
        status = minim.minimize("Minuit2", "migrad")
        if status != 0:
            logging.warning("Fallback migrad status = %s", status)
        minim.minimize("Minuit2", "hesse")
        nll_val = nll.getVal()
        keep["nll"] = nll
        keep["minim"] = minim
    mu.setConstant(False)
    return nll_val, keep


def manual_profile_likelihood(
    sb_pdf: ROOT.RooAbsPdf,
    data: ROOT.RooAbsData,
    mu: ROOT.RooRealVar,
) -> Dict[str, float]:
    """Compute q0 manually via extended NLL fits (free μ and μ=0)."""
    nll_sb, keep_sb = _fit_with_fallback(sb_pdf, data, mu, None, False)
    mu_hat = max(mu.getVal(), 0.0)
    mu.setVal(mu_hat)

    nll_b, keep_b = _fit_with_fallback(sb_pdf, data, mu, 0.0, True)
    mu.setVal(mu_hat)

    q0 = max(0.0, 2.0 * (nll_b - nll_sb))
    z_plr = math.sqrt(q0) if q0 > 0 else 0.0

    result: Dict[str, float] = {
        "mu_hat": mu_hat,
        "nll_sb": nll_sb,
        "nll_b": nll_b,
        "q0": q0,
        "Z": z_plr,
    }
    # retain references to keep objects alive
    result["_keep_sb"] = keep_sb
    result["_keep_b"] = keep_b
    return result


def configure_one_sided(calculator: ROOT.RooStats.AsymptoticCalculator) -> None:
    """Attempt to configure the calculator for one-sided discovery tests."""
    if hasattr(calculator, "SetOneSidedDiscovery"):
        calculator.SetOneSidedDiscovery(True)
        logging.debug("Configured AsymptoticCalculator with SetOneSidedDiscovery(True).")
    elif hasattr(calculator, "SetOneSided"):
        calculator.SetOneSided(True)
        logging.debug("Configured AsymptoticCalculator with SetOneSided(True).")
    else:
        logging.warning("AsymptoticCalculator lacks one-sided configuration APIs.")


def run_asymptotic_test(
    data: ROOT.RooAbsData,
    sb_model: ROOT.RooStats.ModelConfig,
    b_model: ROOT.RooStats.ModelConfig,
) -> Optional[Dict[str, float]]:
    """Run the AsymptoticCalculator discovery test."""
    # RooStats constructors take the alternate (S+B) model before the null
    # (B-only) model.  Reversing this order returns the uninformative p0=0.5
    # failure mode that this script used to show in Asimov closure tests.
    ac = ROOT.RooStats.AsymptoticCalculator(data, sb_model, b_model)
    configure_one_sided(ac)
    test_stat = ROOT.RooStats.ProfileLikelihoodTestStat(sb_model.GetPdf())
    if hasattr(test_stat, "SetOneSidedDiscovery"):
        test_stat.SetOneSidedDiscovery(True)
    elif hasattr(test_stat, "SetOneSided"):
        test_stat.SetOneSided(True)
    if hasattr(ac, "SetTestStatistic"):
        ac.SetTestStatistic(test_stat)
    result = ac.GetHypoTest()
    if not result:
        logging.warning("AsymptoticCalculator returned no result.")
        return None
    p0 = result.NullPValue() if hasattr(result, "NullPValue") else result.GetNullPValue()
    z = result.Significance() if hasattr(result, "Significance") else result.GetSignificance()
    return {"p0": p0, "Z": z, "source": "RooStats AsymptoticCalculator"}


def manual_asymptotic_from_plr(plr: Dict[str, float]) -> Dict[str, float]:
    """Convert the manual profile-likelihood q0 result into asymptotic p0 and Z."""
    return {
        "p0": p_value_from_Z(plr["Z"]),
        "Z": plr["Z"],
        "source": "Manual profile-likelihood asymptotic",
    }


def configure_test_stat() -> ROOT.RooStats.ProfileLikelihoodTestStat:
    """Construct a one-sided profile likelihood test statistic."""
    ts = ROOT.RooStats.ProfileLikelihoodTestStat()
    if hasattr(ts, "SetOneSidedDiscovery"):
        ts.SetOneSidedDiscovery(True)
    elif hasattr(ts, "SetOneSided"):
        ts.SetOneSided(True)
    return ts


def run_toy_test(
    data: ROOT.RooAbsData,
    sb_model: ROOT.RooStats.ModelConfig,
    b_model: ROOT.RooStats.ModelConfig,
    ntoys: int,
) -> Optional[Dict[str, float]]:
    """Execute a B-only toy cross-check."""
    if ntoys <= 0:
        return None
    fc = ROOT.RooStats.FrequentistCalculator(data, sb_model, b_model)
    fc.SetToys(ntoys, 0)
    sampler = fc.GetTestStatSampler()
    ts = ROOT.RooStats.ProfileLikelihoodTestStat(sb_model.GetPdf())
    if hasattr(ts, "SetOneSidedDiscovery"):
        ts.SetOneSidedDiscovery(True)
    elif hasattr(ts, "SetOneSided"):
        ts.SetOneSided(True)
    sampler.SetTestStatistic(ts)
    sampler.SetGenerateBinned(True)
    result = fc.GetHypoTest()
    if not result:
        logging.warning("FrequentistCalculator returned no result.")
        return None
    p0 = result.NullPValue() if hasattr(result, "NullPValue") else result.GetNullPValue()
    if hasattr(ROOT.RooStats, "PValueToSignificance"):
        z = ROOT.RooStats.PValueToSignificance(p0)
    else:
        z = ROOT.Math.normal_quantile_c(p0, 1.0)
    return {"p0": p0, "Z": z, "ntoys": ntoys}


# ---------------------------------------------------------------------------
# Plotting utilities
# ---------------------------------------------------------------------------

def plot_histograms(
    outdir: str,
    xvar: ROOT.RooRealVar,
    h_sig: ROOT.TH1,
    h_bkg: ROOT.TH1,
    h_data: ROOT.TH1,
    mu_scale: float,
) -> None:
    """Create data vs model and residual plots."""
    canvas = ROOT.TCanvas("c_data", "c_data", 800, 800)
    canvas.Divide(1, 2)
    pad1 = canvas.cd(1)
    pad1.SetPad(0, 0.3, 1, 1)
    pad1.SetBottomMargin(0.02)
    pad2 = canvas.cd(2)
    pad2.SetPad(0, 0, 1, 0.3)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.3)

    pad1.cd()
    stack = ROOT.THStack("stack", "")
    h_bkg_draw = h_bkg.Clone("h_bkg_draw")
    h_bkg_draw.SetDirectory(0)
    h_bkg_draw.SetFillColor(ROOT.kAzure - 9)
    h_bkg_draw.SetLineColor(ROOT.kAzure + 2)
    stack.Add(h_bkg_draw, "HIST")

    h_sig_draw = h_sig.Clone("h_sig_draw")
    h_sig_draw.SetDirectory(0)
    h_sig_draw.Scale(mu_scale)
    h_sig_draw.SetFillColor(ROOT.kRed - 4)
    h_sig_draw.SetLineColor(ROOT.kRed + 1)
    stack.Add(h_sig_draw, "HIST")
    stack.Draw("HIST")
    stack.GetYaxis().SetTitle("Events / bin")
    stack.GetXaxis().SetLabelSize(0)

    h_exp = make_asimov_hist(h_sig, h_bkg, mu_scale, "expectation_for_plot")
    h_expect_draw = h_exp.Clone("h_expect_draw")
    h_expect_draw.SetDirectory(0)
    h_expect_draw.SetLineColor(ROOT.kBlack)
    h_expect_draw.SetLineWidth(2)
    h_expect_draw.SetFillStyle(0)
    h_expect_draw.Draw("HIST SAME")

    h_data_draw = h_data.Clone("h_data_draw")
    h_data_draw.SetDirectory(0)
    h_data_draw.SetMarkerStyle(20)
    h_data_draw.SetMarkerSize(1.0)
    h_data_draw.SetLineColor(ROOT.kBlack)
    h_data_draw.Draw("E1 SAME")

    legend = ROOT.TLegend(0.6, 0.65, 0.88, 0.88)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.AddEntry(h_data_draw, "Observed / Asimov data", "lep")
    legend.AddEntry(h_bkg_draw, "Background", "f")
    legend.AddEntry(h_sig_draw, f"Signal (mu={mu_scale:.2f})", "f")
    legend.AddEntry(h_expect_draw, "S+B expectation", "l")
    legend.Draw()

    pad2.cd()
    pulls = h_data.Clone("pulls")
    pulls.SetDirectory(0)
    for ibin in range(1, pulls.GetNbinsX() + 1):
        obs = h_data.GetBinContent(ibin)
        exp = h_exp.GetBinContent(ibin)
        if exp > 0:
            pulls.SetBinContent(ibin, (obs - exp) / math.sqrt(exp))
        else:
            pulls.SetBinContent(ibin, 0.0)
        pulls.SetBinError(ibin, 0.0)
    pulls.SetTitle("")
    pulls.GetYaxis().SetTitle("(Data-Exp)/#sqrt{Exp}")
    pulls.GetYaxis().SetNdivisions(505)
    pulls.GetYaxis().SetTitleSize(0.12)
    pulls.GetYaxis().SetTitleOffset(0.5)
    pulls.GetYaxis().SetLabelSize(0.1)
    pulls.GetXaxis().SetLabelSize(0.1)
    pulls.GetXaxis().SetTitleSize(0.12)
    pulls.GetXaxis().SetTitle(xvar.GetTitle())
    pulls.Draw("P")
    zline = ROOT.TLine(xvar.getMin(), 0, xvar.getMax(), 0)
    zline.SetLineStyle(2)
    zline.Draw()

    canvas.SaveAs(os.path.join(outdir, "data_vs_model.pdf"))


def plot_profile_scan(
    outdir: str,
    h_sig: ROOT.TH1,
    h_bkg: ROOT.TH1,
    h_data: ROOT.TH1,
    nll_best: float,
    mu_hat: float,
    q0: float,
) -> None:
    """Plot -2 ln lambda(mu) profile."""
    canvas = ROOT.TCanvas("c_profile", "c_profile", 700, 600)
    graph = ROOT.TGraph()
    mu_min = 0.0
    mu_max = max(3.0, 3.0 * mu_hat if mu_hat > 0 else 3.0)
    steps = 80
    for idx in range(steps):
        value = mu_min + (mu_max - mu_min) * idx / (steps - 1)
        nll = poisson_template_nll(value, h_sig, h_bkg, h_data)
        delta = max(0.0, 2.0 * (nll - nll_best))
        graph.SetPoint(idx, value, delta)

    graph.SetLineColor(ROOT.kBlue + 1)
    graph.SetLineWidth(2)
    graph.SetTitle(";#mu; -2ln#lambda(#mu)")
    graph.Draw("AL")
    ymax = max(5.0, graph.GetHistogram().GetMaximum() * 1.2)
    graph.GetYaxis().SetRangeUser(0, ymax)

    line_hat = ROOT.TLine(mu_hat, 0, mu_hat, ymax)
    line_hat.SetLineColor(ROOT.kRed + 1)
    line_hat.SetLineStyle(2)
    line_hat.Draw()
    line_zero = ROOT.TLine(0, 0, 0, ymax)
    line_zero.SetLineColor(ROOT.kGray + 2)
    line_zero.SetLineStyle(3)
    line_zero.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC(True)
    latex.SetTextSize(0.035)
    latex.DrawLatex(0.55, 0.85, f"#hat{{#mu}} = {mu_hat:.3f}")
    latex.DrawLatex(0.55, 0.80, f"q_{{0}} = {q0:.3f},  Z = {math.sqrt(q0):.3f}")

    canvas.SaveAs(os.path.join(outdir, "profile_scan.pdf"))


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def write_report(
    outdir: str,
    totals: Dict[str, float],
    counting_Z: float,
    binned_Z: float,
    plr_obs: Dict[str, float],
    plr_exp: Dict[str, float],
    asymptotic_obs: Optional[Dict[str, float]],
    asymptotic_exp: Optional[Dict[str, float]],
    toy_result: Optional[Dict[str, float]],
    syst_Z: Optional[Dict[str, float]],
) -> None:
    """Persist analysis summary to results.txt."""
    path = os.path.join(outdir, "results.txt")
    lines: List[str] = []
    lines.append("VLQ(t) recoil-mass discovery analysis summary\n")
    lines.append(f"S_exp = {totals['S']:.6f}\n")
    lines.append(f"B_exp = {totals['B']:.6f}\n")
    lines.append(f"S/sqrt(S+B) = {totals['S_over_sqrtSB']:.6f}\n")
    lines.append(f"Z_Cowan_counting = {counting_Z:.6f}\n")
    lines.append(f"Z_Cowan_binned   = {binned_Z:.6f}\n")
    lines.append(f"Analysis window  = [{totals['xmin']:.3f}, {totals['xmax']:.3f}]\n")
    if "roi_windows" in totals:
        lines.append("Selected ROI windows (by expected Z):\n")
        for idx, window in enumerate(totals["roi_windows"], start=1):
            lines.append(
                f"  {idx}) [{window['xmin']:.3f}, {window['xmax']:.3f}]  "
                f"width={window['width']:.3f}  Z={window['Z']:.3f}  "
                f"S={window['S']:.3f}  B={window['B']:.3f}\n"
            )
    lines.append("\nManual profile-likelihood results:\n")
    lines.append(f"  mu_hat = {plr_obs['mu_hat']:.6f}\n")
    lines.append(f"  q0(obs) = {plr_obs['q0']:.6f}\n")
    lines.append(f"  Z(obs)  = {plr_obs['Z']:.6f}\n")
    lines.append(f"  q0(exp) = {plr_exp['q0']:.6f}\n")
    lines.append(f"  Z(exp)  = {plr_exp['Z']:.6f}\n")

    if asymptotic_obs:
        lines.append(f"\n{asymptotic_obs.get('source', 'Asymptotic result')} (observed):\n")
        lines.append(f"  p0 = {asymptotic_obs['p0']:.6e}\n")
        lines.append(f"  Z  = {asymptotic_obs['Z']:.6f}\n")
    if asymptotic_exp:
        lines.append(f"\n{asymptotic_exp.get('source', 'Asymptotic result')} (Asimov S+B):\n")
        lines.append(f"  p0 = {asymptotic_exp['p0']:.6e}\n")
        lines.append(f"  Z  = {asymptotic_exp['Z']:.6f}\n")

    if toy_result:
        lines.append("\nFrequentist toys (B-only):\n")
        lines.append(f"  N_toys = {toy_result['ntoys']}\n")
        lines.append(f"  p0     = {toy_result['p0']:.6e}\n")
        lines.append(f"  Z      = {toy_result['Z']:.6f}\n")

    if syst_Z:
        lines.append("\nCounting cross-check with normalization systematics:\n")
        lines.append(f"  rel_background_unc = {syst_Z['rel_bkg_unc']:.6f}\n")
        lines.append(f"  rel_signal_eff_unc = {syst_Z['rel_sig_unc']:.6f}\n")
        lines.append(f"  Z_systematic       = {syst_Z['Z']:.6f}\n")

    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)


# ---------------------------------------------------------------------------
# Main analysis driver
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    os.makedirs(args.outdir, exist_ok=True)
    sig_per_targets: Optional[List[Optional[float]]] = None
    bkg_per_targets: Optional[List[Optional[float]]] = None
    sig_total_target: Optional[float] = None
    bkg_total_target: Optional[float] = None

    if args.scale_from_xsec:
        if args.signal_xsec is None or args.background_xsec is None:
            raise ValueError("Provide --signal-xsec and --background-xsec when using --scale-from-xsec.")
        if args.lumi is None or args.lumi <= 0:
            raise ValueError("--lumi must be positive when scaling from cross sections.")
        signal_xsecs = list(args.signal_xsec)
        background_xsecs = list(args.background_xsec)
        sig_per_targets, sig_total_target = prepare_scale_targets(args.signal, signal_xsecs, args.lumi, "signal")
        bkg_per_targets, bkg_total_target = prepare_scale_targets(args.background, background_xsecs, args.lumi, "background")
        logging.info(
            "Scaling enabled: signal xsecs=%s pb, background xsecs=%s pb, lumi=%.3e pb^-1.",
            ", ".join(f"{x:.6g}" for x in signal_xsecs),
            ", ".join(f"{x:.6g}" for x in background_xsecs),
            args.lumi,
        )

    logging.info("Loading histograms.")
    h_sig = load_and_sum_hists(args.signal, args.hist, sig_per_targets)
    h_bkg = load_and_sum_hists(args.background, args.hist, bkg_per_targets)

    h_sig = apply_range_and_rebin(h_sig, args.xmin, args.xmax, args.rebin)
    h_bkg = apply_range_and_rebin(h_bkg, args.xmin, args.xmax, args.rebin)

    roi_info: Optional[Dict[str, List[Dict[str, float]]]] = None
    if args.scan_bins is not None:
        logging.info("Performing ROI scan with %d windows (keeping %d).", args.scan_bins, args.scan_keep)
        h_sig, h_bkg, roi_info = perform_roi_scan(h_sig, h_bkg, args.scan_bins, args.scan_keep, mu_true=1.0)
        for rank, window in enumerate(roi_info["windows"], start=1):
            logging.info(
                "ROI rank %d: [%.3f, %.3f] (width %.3f) -> expected Z = %.3f (S=%.3f, B=%.3f)",
                rank,
                window["xmin"],
                window["xmax"],
                window["width"],
                window["Z"],
                window["S"],
                window["B"],
            )

    if args.scale_from_xsec:
        if sig_total_target is not None and all(t is None for t in sig_per_targets):
            logging.info("Scaling summed signal histogram to yield %.6f.", sig_total_target)
            scale_histogram_to_yield(h_sig, sig_total_target, "signal")
        if bkg_total_target is not None and all(t is None for t in bkg_per_targets):
            logging.info("Scaling summed background histogram to yield %.6f.", bkg_total_target)
            scale_histogram_to_yield(h_bkg, bkg_total_target, "background")

    if args.obs:
        logging.info("Loading observed histogram.")
        h_obs = load_and_sum_hists([args.obs], args.hist)
        h_obs = apply_range_and_rebin(h_obs, h_sig.GetXaxis().GetBinLowEdge(1), h_sig.GetXaxis().GetBinUpEdge(h_sig.GetNbinsX()), args.rebin)
        # Apply ROI mask if scanning was performed
        if roi_info is not None:
            mask = [False] * h_sig.GetNbinsX()
            for win in roi_info["windows"]:
                for ibin in range(win["start"], win["end"] + 1):
                    mask[ibin - 1] = True
            h_obs = clone_with_mask(h_obs, mask, f"{h_obs.GetName()}_roi")
    else:
        h_obs = None

    if h_sig.GetNbinsX() != h_bkg.GetNbinsX():
        raise ValueError("Signal and background histograms must share identical binning.")

    s_exp = h_sig.Integral()
    b_exp = h_bkg.Integral()
    if s_exp <= 0 or b_exp <= 0:
        raise RuntimeError("Signal and background yields must be positive after processing.")

    xmin_eff = h_sig.GetXaxis().GetBinLowEdge(1)
    xmax_eff = h_sig.GetXaxis().GetBinUpEdge(h_sig.GetNbinsX())

    logging.info("Final analysis window: [%.3f, %.3f]", xmin_eff, xmax_eff)
    logging.info("Yields: S = %.6f, B = %.6f, S/sqrt(S+B) = %.6f", s_exp, b_exp, s_exp / math.sqrt(s_exp + b_exp))

    count_Z = asimov_counting_Z(s_exp, b_exp)
    binned_Z = asimov_binned_Z(h_sig, h_bkg)
    logging.info("Cowan counting Z = %.6f, binned Z = %.6f", count_Z, binned_Z)
    syst_Z = None
    if args.background_norm_unc > 0 or args.signal_eff_unc > 0:
        if args.background_norm_unc < 0 or args.signal_eff_unc < 0:
            raise ValueError("Systematic uncertainties must be non-negative.")
        syst_Z = {
            "rel_bkg_unc": args.background_norm_unc,
            "rel_sig_unc": args.signal_eff_unc,
            "Z": conservative_counting_Z_with_systematics(
                s_exp,
                b_exp,
                args.background_norm_unc,
                args.signal_eff_unc,
            ),
        }
        logging.info(
            "Systematic counting cross-check Z = %.6f (bkg=%.3f, signal=%.3f).",
            syst_Z["Z"],
            args.background_norm_unc,
            args.signal_eff_unc,
        )

    xvar = ROOT.RooRealVar(args.var, args.var, xmin_eff, xmax_eff)
    xvar.setBins(h_sig.GetNbinsX())
    dh_sig = make_data_hist(h_sig, xvar, "dh_sig")
    dh_bkg = make_data_hist(h_bkg, xvar, "dh_bkg")
    sig_pdf = ROOT.RooHistPdf("sigPdf", "Signal PDF", ROOT.RooArgSet(xvar), dh_sig)
    bkg_pdf = ROOT.RooHistPdf("bkgPdf", "Background PDF", ROOT.RooArgSet(xvar), dh_bkg)
    mu = ROOT.RooRealVar("mu", "signal strength", 1.0, 0.0, 10.0)
    s_tot = ROOT.RooRealVar("S_tot", "signal total", s_exp)
    s_tot.setConstant(True)
    b_tot = ROOT.RooRealVar("B_tot", "background total", b_exp)
    b_tot.setConstant(True)
    n_sig = ROOT.RooFormulaVar("Nsig", "mu*S_tot", ROOT.RooArgList(mu, s_tot))
    n_bkg = ROOT.RooFormulaVar("Nbkg", "B_tot", ROOT.RooArgList(b_tot))
    sb_pdf = ROOT.RooAddPdf("sbPdf", "signal+background pdf", ROOT.RooArgList(sig_pdf, bkg_pdf), ROOT.RooArgList(n_sig, n_bkg))

    w, sb_model, b_model = build_workspace(xvar, sig_pdf, bkg_pdf, sb_pdf, mu, s_tot, b_tot)

    if h_obs:
        data_hist = h_obs.Clone("data_hist")
        data_hist.SetDirectory(0)
    else:
        data_hist = make_asimov_hist(h_sig, h_bkg, 1.0, "asimov_sb_hist")
    asimov_sb_hist = make_asimov_hist(h_sig, h_bkg, 1.0, "asimov_sb_hist_for_closure")
    asimov_b_hist = make_asimov_hist(h_sig, h_bkg, 0.0, "asimov_b_hist")

    data = make_data_hist(data_hist, xvar, "data_obs")
    asimov_sb = make_data_hist(asimov_sb_hist, xvar, "asimov_sb")
    asimov_b = make_data_hist(asimov_b_hist, xvar, "asimov_b")

    getattr(w, "import")(data, ROOT.RooFit.Rename("data_obs"))
    getattr(w, "import")(asimov_sb, ROOT.RooFit.Rename("asimov_sb"))
    getattr(w, "import")(asimov_b, ROOT.RooFit.Rename("asimov_b"))
    work_path = os.path.join(args.outdir, "analysis_workspace.root")
    w.writeToFile(work_path)
    logging.info("Workspace saved to %s", work_path)

    plr_obs = manual_binned_profile_likelihood(h_sig, h_bkg, data_hist)
    mu_hat = plr_obs["mu_hat"]

    plr_exp = manual_binned_profile_likelihood(h_sig, h_bkg, asimov_sb_hist)

    if args.run_roostats_asymptotic:
        mu.setVal(plr_obs["mu_hat"])
        mu.setConstant(False)
        asymptotic_obs = run_asymptotic_test(data, sb_model, b_model)
        mu.setVal(1.0)
        mu.setConstant(False)
        asymptotic_exp = run_asymptotic_test(asimov_sb, sb_model, b_model)
        if asymptotic_exp and asymptotic_exp["Z"] <= 0.0 and plr_exp["Z"] > 1e-6:
            logging.warning(
                "RooStats AsymptoticCalculator failed the Asimov closure "
                "(Z=%.6f while manual PLR Z=%.6f); using manual asymptotic output.",
                asymptotic_exp["Z"],
                plr_exp["Z"],
            )
            asymptotic_obs = manual_asymptotic_from_plr(plr_obs)
            asymptotic_exp = manual_asymptotic_from_plr(plr_exp)
    else:
        asymptotic_obs = manual_asymptotic_from_plr(plr_obs)
        asymptotic_exp = manual_asymptotic_from_plr(plr_exp)

    toy_result = run_toy_test(data, sb_model, b_model, args.toys) if args.toys > 0 else None

    # Cross-check warnings
    if plr_exp["Z"] + 1e-6 < s_exp / math.sqrt(s_exp + b_exp):
        logging.warning(
            "Manual PLR expected Z (%.3f) is below S/sqrt(S+B) (%.3f). "
            "Check binning, normalization, or test-statistic configuration.",
            plr_exp["Z"],
            s_exp / math.sqrt(s_exp + b_exp),
        )

    plot_histograms(args.outdir, xvar, h_sig, h_bkg, data_hist, mu_scale=1.0)
    plot_profile_scan(args.outdir, h_sig, h_bkg, data_hist, plr_obs["nll_sb"], mu_hat, plr_obs["q0"])

    if roi_info:
        roi_windows = roi_info["windows"]
    else:
        roi_windows = []

    totals = {
        "S": s_exp,
        "B": b_exp,
        "S_over_sqrtSB": s_exp / math.sqrt(s_exp + b_exp),
        "xmin": xmin_eff,
        "xmax": xmax_eff,
    }
    if roi_windows:
        totals["roi_windows"] = roi_windows
    if roi_info:
        totals["window_width"] = roi_info["width"]

    write_report(
        args.outdir,
        totals,
        count_Z,
        binned_Z,
        plr_obs,
        plr_exp,
        asymptotic_obs,
        asymptotic_exp,
        toy_result,
        syst_Z,
    )

    summary = [
        f"mu_hat={plr_obs['mu_hat']:.3f}",
        f"q0(obs)={plr_obs['q0']:.3f}",
        f"Z(obs)={plr_obs['Z']:.3f}",
        f"Z(exp)={plr_exp['Z']:.3f}",
        f"Z_Cowan_binned={binned_Z:.3f}",
    ]
    logging.info("Analysis complete: %s", ", ".join(summary))
    if toy_result:
        logging.info("Toy cross-check: Z=%.3f (p0=%.3e) with %d toys.", toy_result["Z"], toy_result["p0"], toy_result["ntoys"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - top-level safeguard
        logging.exception("Analysis failed: %s", exc)
        sys.exit(1)
