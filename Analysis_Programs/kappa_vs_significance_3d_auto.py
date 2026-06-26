# -*- coding: utf-8 -*-
"""
Produce per-kappa significance tables and minimal plots.

- Robust to ROOT memory growth: one fresh worker per kappa (maxtasksperchild=1)
- Per-kappa outputs: <out_dir>/kappa_<label>.root
- Summary: TH2D (mass vs kappa, Z=S/sqrt(S+B)) stored in <out_dir>/<summary_root>
- Plots (points only) saved under <out_dir> when requested.
- CSV with all rows is written to <out_dir>/<csv_name>
"""

import argparse
import csv
import glob
import math
import multiprocessing as mp
import os
import re
from array import array as carray

# ------------------ CONFIG ------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
DEFAULT_SH_PATH = os.path.join(SCRIPT_DIR, "Histograms.sh")
DEFAULT_OUT_DIR = os.path.join(DEFAULT_ASE_DIR, "results")

DEFAULT_MASSES      = [1200, 1600, 2000, 2400]
DEFAULT_SIGNAL_TMPL = "Tt1M{mass}.root"
DEFAULT_BACKGROUNDS = ["ttz", "w+w-z", "tth", "ttbarra"]

DEFAULT_VAR       = "mrecoil_isolated_toplikes_rec_missE_cut"
DEFAULT_LUMI      = 5e18

DEFAULT_SUMMARY_ROOT  = "kappa_mass_significance_grid.root"
DEFAULT_CSV_NAME      = "kappa_mass_significance.csv"
DEFAULT_MAKE_PLOTS    = True   # final small points-only plots
# --------------------------------------------

def ensure_dir(p): os.makedirs(p, exist_ok=True); return p

def as_root_dir(path):
    if not path:
        return None
    expanded = os.path.expanduser(os.path.expandvars(path))
    if os.path.isdir(os.path.join(expanded, "root")):
        return os.path.join(expanded, "root")
    return expanded

def as_root_dirs(path_spec):
    root_dirs = []
    if not path_spec:
        return root_dirs
    for raw in str(path_spec).split(os.pathsep):
        root_dir = as_root_dir(raw.strip())
        if root_dir and root_dir not in root_dirs:
            root_dirs.append(root_dir)
    return root_dirs

def kappa_from_label(lbl):
    m = re.match(r'kappa(\d+)$', lbl)
    return (int(m.group(1))/100.0) if m else None

def parse_kappa_dirs(sh_path, label_regex):
    pairs = []
    if not os.path.exists(sh_path): return pairs
    label_re = re.compile(label_regex)
    lines = open(sh_path, "r", encoding="utf-8", errors="ignore").read().splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r'\b(?:elif|if)\s*\[\s*\$1\s*==\s*"([^"]+)"\s*\]', lines[i])
        if not m: i += 1; continue
        lbl = m.group(1); j = i+1; d = None
        if label_re.pattern and not label_re.match(lbl):
            i += 1
            continue
        while j < len(lines):
            if re.search(r'\b(?:elif|if)\s*\[\s*\$1\s*==', lines[j]) or lines[j].strip()=="fi": break
            mcd = re.search(r'^\s*cd\s+([^\n;#]+)', lines[j])
            if mcd: d = mcd.group(1).strip(); break
            j += 1
        if d: pairs.append((lbl, d))
        i = j if j>i else i+1
    return pairs

def discover_kappa_dirs_from_tree(label_regex, ase_dir=DEFAULT_ASE_DIR):
    pairs = []
    label_re = re.compile(label_regex)
    prefix = "ttp_Analysis_"
    for path in sorted(glob.glob(os.path.join(ase_dir, f"{prefix}*"))):
        if not os.path.isdir(path):
            continue
        name = os.path.basename(path.rstrip("/"))
        if not name.startswith(prefix):
            continue
        lbl = name[len(prefix):]
        if not label_re.match(lbl):
            continue
        pairs.append((lbl, path))
    return pairs

def unique_existing_dirs(paths):
    out = []
    for path in paths:
        root_dir = as_root_dir(path)
        if root_dir and os.path.isdir(root_dir) and root_dir not in out:
            out.append(root_dir)
    return out

def infer_background_root_dirs(signal_root_dir):
    candidates = []
    if signal_root_dir:
        candidates.append(signal_root_dir)

    scan_dir = os.path.dirname(signal_root_dir.rstrip("/")) if signal_root_dir else ""
    scan_name = os.path.basename(scan_dir)
    if "ISR" in scan_name and "+80" in scan_name:
        fallback = "ttp_Analysis+80ISR"
    elif "ISR" in scan_name and "-80" in scan_name:
        fallback = "ttp_Analysis-80ISR"
    elif "ISR" in scan_name:
        fallback = "ttp_AnalysisISR"
    elif "+80" in scan_name:
        fallback = "ttp_Analysis+80"
    elif "-80" in scan_name:
        fallback = "ttp_Analysis-80"
    else:
        fallback = "ttp_Analysis"

    candidates.append(os.path.join(DEFAULT_ASE_DIR, fallback))
    candidates.append(os.path.join(DEFAULT_ASE_DIR, "ttp_Analysis"))
    return unique_existing_dirs(candidates)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Build per-kappa significance ROOT files, summary histogram, and optional plots."
    )
    parser.add_argument("--sh-path", default=DEFAULT_SH_PATH,
                        help="Shell dispatcher listing available analyses (default: %(default)s)")
    parser.add_argument("--label-regex", default=r"kappa(\d+)$",
                        help="Regex to select labels from the shell script (default: %(default)s)")
    parser.add_argument("--dir-suffix", default="",
                        help="Suffix appended to each directory discovered in the shell script")
    parser.add_argument("--limit-labels", nargs="+", default=None,
                        help="Optional explicit list of labels to run (after regex filtering)")
    parser.add_argument("--background-dir", default=None,
                        help="Directory (or its root subdir) providing background ROOT files; "
                             "defaults to each signal directory if omitted")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                        help="Output directory for ROOT/CSV/plots (default: %(default)s)")
    parser.add_argument("--summary-root", default=None,
                        help=f"Summary ROOT filename (default: {DEFAULT_SUMMARY_ROOT})")
    parser.add_argument("--csv", default=None,
                        help=f"CSV filename (default: {DEFAULT_CSV_NAME})")
    parser.add_argument("--masses", nargs="+", type=float, default=None,
                        help=f"Signal masses to process (default: {' '.join(map(str, DEFAULT_MASSES))})")
    parser.add_argument("--signal-template", default=DEFAULT_SIGNAL_TMPL,
                        help="Signal ROOT file template (default: %(default)s)")
    parser.add_argument("--backgrounds", nargs="+", default=None,
                        help=f"List of background prefixes (default: {' '.join(DEFAULT_BACKGROUNDS)})")
    parser.add_argument("--var", default=DEFAULT_VAR,
                        help="Histogram name for yield extraction (default: %(default)s)")
    parser.add_argument("--lumi", type=float, default=DEFAULT_LUMI,
                        help="Integrated luminosity in ab^{-1}? (default: %(default)s)")
    parser.add_argument("--processes", type=int, default=1,
                        help="Concurrent worker processes; use 0 to force single-process mode (default: %(default)s)")
    parser.add_argument("--make-plots", dest="make_plots", action="store_true",
                        help="Enable final plots (default behaviour)")
    parser.add_argument("--no-plots", dest="make_plots", action="store_false",
                        help="Disable final plots")
    parser.set_defaults(make_plots=DEFAULT_MAKE_PLOTS)
    parser.add_argument("--dry-run", action="store_true",
                        help="Only list the directories that would be processed")
    return parser.parse_args()

# ---------------- Worker (fresh process per kappa) ----------------
def worker_one_kappa(args):
    import ROOT, os
    from ROOT import TFile, TH1F, TTree, gROOT
    gROOT.SetBatch(True)
    ROOT.TH1.AddDirectory(False)
    try:
        ROOT.DisableImplicitMT()
    except Exception:
        pass
    try:
        ROOT.gStyle.SetCanvasPreferGL(False)
        ROOT.gEnv.SetValue("OpenGL.CanvasPreferGL", "0")
        os.environ["ROOT_DISABLE_OPENGL"] = "1"
    except Exception:
        pass

    lbl, signal_root_dir, background_root_dirs, MASSES, SIGNAL_TMPL, BACKGROUNDS, VAR, LUMI, OUT_DIR = args
    k = kappa_from_label(lbl)
    if k is None:
        return (lbl, None, [], 0.0)

    def open_if_exists(path):
        path = os.path.expanduser(os.path.expandvars(path.strip().strip('"').strip("'")))
        if not os.path.exists(path): return None
        f = TFile.Open(path, "READ")
        if not f or f.IsZombie(): return None
        return f

    def close_root(f):
        try:
            if f:
                f.Close()
        except Exception:
            pass

    def center_of_max(h):
        if not h or h.GetNbinsX()==0: return 0.0
        return float(h.GetXaxis().GetBinCenter(h.GetMaximumBin()))

    def get_xs_nsim(tf):
        return center_of_max(tf.Get("Cross_Section")), center_of_max(tf.Get("no_sim"))

    def expected(tf, hist):
        h = tf.Get(hist)
        if not h: return 0.0
        xs, ns = get_xs_nsim(tf)
        if xs <= 0 or ns <= 0: return 0.0
        val = float(h.GetEntries()) * (LUMI * xs * 1e-12) / ns
        try:
            del h
        except Exception:
            pass
        return val

    def background_path(name):
        for root_dir in background_root_dirs or []:
            path = os.path.join(root_dir, f"{name}.root")
            if os.path.exists(path):
                return path
        return None

    def signal_path(name):
        if not signal_root_dir:
            return None
        return os.path.join(signal_root_dir, name)

    # Sum B once per run
    B = 0.0
    for b in BACKGROUNDS:
        fb = open_if_exists(background_path(b))
        if not fb: continue
        B += expected(fb, VAR)
        close_root(fb)

    rows = []
    # Tiny per-kappa ROOT
    kroot = os.path.join(OUT_DIR, f"kappa_{lbl}.root")
    fk = TFile(kroot, "RECREATE")
    ZTree = TTree("ZTree", "Per-kappa significance")
    mass_a  = carray('d', [0.0])
    kappa_a = carray('d', [k if k is not None else 0.0])
    S_a     = carray('d', [0.0])
    B_a     = carray('d', [B])
    Z_a     = carray('d', [0.0])
    ZTree.Branch("mass",  mass_a,  "mass/D")
    ZTree.Branch("kappa", kappa_a, "kappa/D")
    ZTree.Branch("S",     S_a,     "S/D")
    ZTree.Branch("B",     B_a,     "B/D")
    ZTree.Branch("Z",     Z_a,     "Z/D")

    hZmass = TH1F(f"hZ_mass_{lbl}", f"Z per mass (kappa={k:.2f});m_T index;Z",
                  len(MASSES), 0.5, len(MASSES)+0.5)

    for i, m in enumerate(MASSES, start=1):
        fs = open_if_exists(signal_path(SIGNAL_TMPL.format(mass=int(m))))
        if not fs: 
            continue
        S = expected(fs, VAR)
        close_root(fs)
        Z = S / math.sqrt(max(1e-12, S + B))
        rows.append((float(m), float(S), float(B), float(Z)))
        mass_a[0] = float(m); S_a[0] = S; Z_a[0] = Z
        ZTree.Fill()
        hZmass.SetBinContent(i, Z)

    fk.WriteObject(ZTree, "ZTree")
    fk.WriteObject(hZmass, hZmass.GetName())
    close_root(fk)
    try:
        import gc; gc.collect()
    except Exception:
        pass
    return (lbl, k, rows, B)

# ---------------- Parent / Driver ----------------
def main():
    # Keep allocator from hoarding arenas in the parent
    os.environ.setdefault("MALLOC_ARENA_MAX", "2")
    os.environ.setdefault("PYTHONMALLOC", "malloc")

    args = parse_args()
    out_dir = ensure_dir(os.path.expanduser(args.out_dir))
    csv_path = args.csv or os.path.join(out_dir, DEFAULT_CSV_NAME)
    summary_root = args.summary_root or DEFAULT_SUMMARY_ROOT
    if not os.path.isabs(summary_root):
        summary_root_path = os.path.join(out_dir, summary_root)
    else:
        summary_root_path = summary_root

    masses = list(DEFAULT_MASSES if args.masses is None else args.masses)
    masses = [int(m) if abs(m - int(m)) < 1e-9 else float(m) for m in masses]
    masses.sort()

    backgrounds = list(DEFAULT_BACKGROUNDS if args.backgrounds is None else args.backgrounds)

    sh_path = os.path.expanduser(os.path.expandvars(args.sh_path))
    pairs = parse_kappa_dirs(sh_path, args.label_regex)
    if not pairs:
        pairs = discover_kappa_dirs_from_tree(args.label_regex)
        if pairs:
            print(f"[INFO] Falling back to filesystem discovery under {DEFAULT_ASE_DIR}")
        else:
            print(f"[ERROR] No matching blocks found in {sh_path}")
            return

    label_limit = set(args.limit_labels) if args.limit_labels else None
    dir_suffix = args.dir_suffix or ""
    background_root_override = unique_existing_dirs(as_root_dirs(args.background_dir)) if args.background_dir else []

    work_items = []
    for lbl, base_dir in pairs:
        if label_limit and lbl not in label_limit:
            continue
        target_dir = (base_dir.rstrip("/") + dir_suffix) if dir_suffix else base_dir
        target_dir = os.path.expanduser(os.path.expandvars(target_dir))
        signal_root_dir = as_root_dir(target_dir)
        if not signal_root_dir or not os.path.isdir(signal_root_dir):
            print(f"[WARN] Skipping {lbl}: signal directory not found -> {target_dir}")
            continue
        background_root_dirs = list(background_root_override) if background_root_override else infer_background_root_dirs(signal_root_dir)
        if not background_root_dirs:
            background_root_dirs = [signal_root_dir]
        work_items.append((lbl, signal_root_dir, background_root_dirs))

    if args.dry_run:
        print("[DRY-RUN] Would process:")
        for lbl, sdir, bdirs in work_items:
            print(f"  {lbl}: signal={sdir} backgrounds={os.pathsep.join(bdirs)}")
        return

    if not work_items:
        print("[ERROR] Nothing to process after filtering.")
        return

    worker_args_list = [
        (
            lbl,
            signal_root_dir,
            background_root_dirs,
            masses,
            args.signal_template,
            backgrounds,
            args.var,
            args.lumi,
            out_dir,
        )
        for (lbl, signal_root_dir, background_root_dirs) in work_items
    ]

    def run_inline():
        out = []
        for wargs in worker_args_list:
            lbl, k, rows, B = worker_one_kappa(wargs)
            print(f"[KAPPA] {lbl} -> processed {len(rows)} masses (B={B:.4g})")
            out.append((lbl, k, rows))
        return out

    results = []
    # Use spawned workers by default to avoid memory pileup; even --processes 0
    # will be coerced to 1 so each kappa runs in its own fresh process.
    proc_count = args.processes
    if proc_count <= 0:
        proc_count = 1
    try:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=proc_count, maxtasksperchild=1) as pool:
            for lbl, k, rows, B in pool.imap(worker_one_kappa, worker_args_list):
                print(f"[KAPPA] {lbl} -> processed {len(rows)} masses (B={B:.4g})")
                results.append((lbl, k, rows))
    except (PermissionError, OSError) as exc:
        print(f"[WARN] multiprocessing failed ({exc}); falling back to single-process mode")
        results = run_inline()

    # Build tiny summary TH2D
    import ROOT
    from ROOT import TFile, TH2D, TCanvas, TLatex, gROOT
    gROOT.SetBatch(True); ROOT.TH1.AddDirectory(False)
    kappas = sorted({k for _,k,_ in results if k is not None})
    populated_masses = sorted({float(m) for _, _, rows in results for (m, _, _, _) in rows})
    populated_kappas = sorted({k for _, k, rows in results if k is not None and rows})

    def edges(v):
        v = sorted(set(v))
        if not v: return [0,1]
        out=[]
        for i,x in enumerate(v):
            if i==0:
                step=(v[1]-v[0]) if len(v)>1 else max(1.0,0.1*abs(v[0])); out.append(x-0.5*step)
            else:
                out.append(0.5*(v[i-1]+v[i]))
        step_last=(v[-1]-v[-2]) if len(v)>1 else max(1.0,0.1*abs(v[0])); out.append(v[-1]+0.5*step_last)
        return out

    hist_masses = populated_masses or [float(m) for m in masses]
    hist_kappas = populated_kappas or kappas
    hx = carray('d', edges(hist_masses)); hy = carray('d', edges(hist_kappas))
    hZ = TH2D("hZ_mass_kappa", "S/#sqrt{S+B};m_{T} [GeV];#kappa_{T}",
              len(hx)-1, hx, len(hy)-1, hy)
    hZ.SetStats(0)

    def occupied_axis_window(hist):
        x_first = x_last = None
        y_first = y_last = None
        for ix in range(1, hist.GetNbinsX() + 1):
            for iy in range(1, hist.GetNbinsY() + 1):
                if hist.GetBinContent(ix, iy) <= 0:
                    continue
                if x_first is None or ix < x_first:
                    x_first = ix
                if x_last is None or ix > x_last:
                    x_last = ix
                if y_first is None or iy < y_first:
                    y_first = iy
                if y_last is None or iy > y_last:
                    y_last = iy

        if x_first is None:
            return (
                hist.GetXaxis().GetXmin(),
                hist.GetXaxis().GetXmax(),
                hist.GetYaxis().GetXmin(),
                hist.GetYaxis().GetXmax(),
            )

        xaxis = hist.GetXaxis()
        yaxis = hist.GetYaxis()
        return (
            xaxis.GetBinLowEdge(x_first),
            xaxis.GetBinUpEdge(x_last),
            yaxis.GetBinLowEdge(y_first),
            yaxis.GetBinUpEdge(y_last),
        )

    def occupied_zmax(hist):
        zmax = 0.0
        for ix in range(1, hist.GetNbinsX() + 1):
            for iy in range(1, hist.GetNbinsY() + 1):
                zmax = max(zmax, hist.GetBinContent(ix, iy))
        return zmax

    # CSV + fill
    with open(csv_path, "w", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["kappa","mass_GeV","S","B","Z"])
        for lbl, k, rows in results:
            if k is None: continue
            for (m, S, B, Z) in rows:
                hZ.SetBinContent(hZ.GetXaxis().FindBin(m), hZ.GetYaxis().FindBin(k), Z)
                w.writerow([k, int(m), f"{S:.6g}", f"{B:.6g}", f"{Z:.6g}"])

    plot_xmin, plot_xmax, plot_ymin, plot_ymax = occupied_axis_window(hZ)
    plot_zmax = occupied_zmax(hZ)

    # Write tiny ROOT summary (hist only)
    tf = TFile(summary_root_path, "RECREATE")
    tf.WriteObject(hZ, hZ.GetName()); tf.Close()

    # --------- Final plots: points only (NO heatmap) ---------
    if args.make_plots:
        ROOT.gStyle.SetCanvasPreferGL(False); os.environ["ROOT_DISABLE_OPENGL"]="1"

        def configure_canvas(canvas):
            canvas.SetLeftMargin(0.16)
            canvas.SetRightMargin(0.10)
            canvas.SetBottomMargin(0.12)
            canvas.SetTopMargin(0.08)

        def draw_header():
            tx = ROOT.TLatex()
            tx.SetTextFont(42)
            tx.SetTextSize(0.045)
            tx.SetTextAlign(13)
            tx.DrawLatexNDC(0.12, 0.97, "e^{+}e^{-} collider")
            tx.SetTextAlign(33)
            tx.DrawLatexNDC(0.88, 0.97, "#sqrt{s} = 3 TeV")
            return tx

        # 1) Points-only (no background at all)
        c1 = TCanvas("c_points_only_clean", "Points only", 1180, 940)
        configure_canvas(c1)

        # Draw empty frame for axes
        frame = ROOT.TH2D("frame_points",
                          "S/#sqrt{S+B};m_{T} [GeV];#kappa_{T}",
                          hZ.GetXaxis().GetNbins(),
                          hZ.GetXaxis().GetXmin(),
                          hZ.GetXaxis().GetXmax(),
                          hZ.GetYaxis().GetNbins(),
                          hZ.GetYaxis().GetXmin(),
                          hZ.GetYaxis().GetXmax())
        frame.SetStats(0)
        frame.GetXaxis().SetTitleSize(0.050)
        frame.GetXaxis().SetLabelSize(0.040)
        frame.GetXaxis().SetTitleOffset(1.05)
        frame.GetYaxis().SetTitleSize(0.065)
        frame.GetYaxis().SetLabelSize(0.040)
        frame.GetYaxis().SetTitleOffset(1.10)
        frame.GetXaxis().SetRangeUser(plot_xmin, plot_xmax)
        frame.GetYaxis().SetRangeUser(plot_ymin, plot_ymax)
        frame.Draw()

        # Draw markers at bin centers (single style/color)
        hZ.SetMarkerStyle(20)     # ●
        hZ.SetMarkerSize(1.4)
        hZ.SetMarkerColor(ROOT.kBlack)
        hZ.Draw("P SAME")         # ONLY points; no COLZ, no boxes

        draw_header()
        c1.SaveAs(os.path.join(out_dir, "kappa_mass_significance_points_only_clean.png"))
        c1.SaveAs(os.path.join(out_dir, "kappa_mass_significance_points_only_clean.pdf"))
        del c1

        # 2) Points + Z number printed near each point (still no heatmap)
        c2 = TCanvas("c_points_with_text", "Points + Z text", 1180, 940)
        configure_canvas(c2)
        frame2 = frame.Clone("frame_points2")
        frame2.GetXaxis().SetRangeUser(plot_xmin, plot_xmax)
        frame2.GetYaxis().SetRangeUser(plot_ymin, plot_ymax)
        frame2.Draw()

        # Same markers
        hZ.SetMarkerStyle(20)
        hZ.SetMarkerSize(1.4)
        hZ.SetMarkerColor(ROOT.kBlack)
        hZ.Draw("P SAME")

        # Print Z at each occupied bin
        txt = ROOT.TLatex()
        txt.SetTextFont(42)
        txt.SetTextSize(0.030)
        txt.SetTextAlign(22)  # center
        for ix in range(1, hZ.GetNbinsX()+1):
            for iy in range(1, hZ.GetNbinsY()+1):
                z = hZ.GetBinContent(ix, iy)
                if z <= 0:
                    continue
                x = hZ.GetXaxis().GetBinCenter(ix)
                y = hZ.GetYaxis().GetBinCenter(iy)
                txt.DrawLatex(x, y, f"{z:.2f}")

        draw_header()
        c2.SaveAs(os.path.join(out_dir, "kappa_mass_significance_points_with_text.png"))
        c2.SaveAs(os.path.join(out_dir, "kappa_mass_significance_points_with_text.pdf"))
        del c2

        # 3) Heatmap + text (cropped to occupied bins)
        c3 = TCanvas("c_heat_points", "Heatmap + Z text", 1180, 940)
        configure_canvas(c3)
        c3.SetRightMargin(0.14)

        hZ_heat = hZ.Clone("hZ_mass_kappa_heat")
        hZ_heat.GetXaxis().SetRangeUser(plot_xmin, plot_xmax)
        hZ_heat.GetYaxis().SetRangeUser(plot_ymin, plot_ymax)
        hZ_heat.GetXaxis().SetTitleSize(0.050)
        hZ_heat.GetXaxis().SetLabelSize(0.040)
        hZ_heat.GetXaxis().SetTitleOffset(1.05)
        hZ_heat.GetYaxis().SetTitleSize(0.065)
        hZ_heat.GetYaxis().SetLabelSize(0.040)
        hZ_heat.GetYaxis().SetTitleOffset(1.10)
        hZ_heat.SetMinimum(0.0)
        hZ_heat.SetMaximum(plot_zmax if plot_zmax > 0 else 1.0)
        hZ_heat.SetMarkerColor(ROOT.kBlack)
        hZ_heat.Draw("COLZ TEXT")

        draw_header()
        c3.SaveAs(os.path.join(out_dir, "kappa_mass_significance_heat_points.png"))
        c3.SaveAs(os.path.join(out_dir, "kappa_mass_significance_heat_points.pdf"))
        del c3

    print("[DONE] Per-kappa ROOTs + summary saved under:", out_dir)

if __name__ == "__main__":
    main()
