#source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh

# -*- coding: utf-8 -*-
"""
compare_mases.py — overlay 1D y mosaico 2x2 para 2D, con 4 masas.
Antisegfault:
  - TH1.AddDirectory(False) y SetDirectory(0)
  - Captura SIEMPRE el retorno de Rebin/RebinX/RebinY
  - Chequea tipo (TH1 vs TH2) antes de dibujar
  - Mantiene referencias vivas hasta guardar (keep_alive)
  - Sanea nombres (sin espacios) al escribir en ROOT
Salidas: /home/higinio/Documentos/ASE/Resultados
"""

import os, re
import ROOT
from ROOT import TFile, TCanvas, TLegend, TLatex, gROOT

gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

# ---------- Config ----------
TAG     = "Tt1M"
MASSES  = ["1200", "1600", "2000", "2400"]

VARS = [
    "m_recoil", "Ht", "mrecoil toplikes", "mrecoil_isolated_toplikes",
    "mrecoilvspt", "EvsHt", "ptvsHt", "mrecoilvsHt",
    "mrecoil_isolated_toplikes_rec_cut", "mrecoil_isolated_toplikes_subestructure_cut",
    "mrecoil_isolated_toplikes_rec_missE_cut", "good_m_recoil", "bad_m_recoil",
]

# intenta también variantes sin/Con espacios/guiones bajos
ALT_NAME_FUN = lambda s: list(dict.fromkeys([s, s.replace(" ", "_"), s.replace("_", " ")]))

VARS_2D = {"mrecoilvspt", "EvsHt", "ptvsHt", "mrecoilvsHt"}

NORMALIZE_1D = True
REBIN_1D     = 20
REBIN2D_X    = 100
REBIN2D_Y_LOW, REBIN2D_Y_HIGH = 2, 100

OUT_DIR  = "/home/higinio/Documentos/ASE/Resultados"
OUT_ROOT = "compare_masses.root"

COLORS = [ROOT.kBlack, ROOT.kRed+1, ROOT.kGreen+2, ROOT.kBlue+1]
# ---------------------------

def ensure_outdir(p):
    os.makedirs(p, exist_ok=True); return p

_safe_re = re.compile(r'[^A-Za-z0-9_]+')
def safe_key(s): return _safe_re.sub("_", s.strip())

def open_if_exists(path):
    if not os.path.exists(path):
        print(f"[INFO] No existe: {path}"); return None
    f = TFile.Open(path, "read")
    if not f or f.IsZombie():
        print(f"[WARN] No pude abrir: {path}"); return None
    return f

def fetch_hist_any_name(tf, base):
    """Intenta varios alias (espacio<->underscore)."""
    for candidate in ALT_NAME_FUN(base):
        h = tf.Get(candidate)
        if h: return h, candidate
    return None, None

def clone_detached(h, name):
    hc = h.Clone(safe_key(name))
    hc.SetDirectory(0)
    return hc

def rebin_1d_capture(h, ng):
    if not h or ng<=1: return h
    try:
        h2 = h.Rebin(ng)
        if h2: 
            h2.SetDirectory(0)
            return h2
        return h
    except Exception:
        return h

def rebin2d_capture(h2, nx=0, ny_sel=(2,100)):
    if not h2: return h2
    try:
        if nx and nx>1:
            h2x = h2.RebinX(nx)
            if h2x: h2 = h2x
        if h2.GetNbinsY() < 1000:
            h2y = h2.RebinY(ny_sel[0])
        else:
            h2y = h2.RebinY(ny_sel[1])
        if h2y: h2 = h2y
    except Exception:
        pass
    h2.SetDirectory(0)
    return h2

def normalize_to_unity(h):
    integ = h.Integral() if h else 0.0
    if integ>0.0: h.Scale(1.0/integ)

def axis_titles(var):
    mapping = {
        "m_recoil": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "Ht": ("H_{T} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoil toplikes": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoil_isolated_toplikes": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoil_isolated_toplikes_rec_cut": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoil_isolated_toplikes_subestructure_cut": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoil_isolated_toplikes_rec_missE_cut": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "good_m_recoil": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "bad_m_recoil": ("m_{recoil} [GeV]", "Arbitrary Units" if NORMALIZE_1D else "Events"),
        "mrecoilvspt": ("p_{T} [GeV]", "m_{recoil} [GeV]"),
        "EvsHt": ("H_{T} [GeV]", "E [GeV]"),
        "ptvsHt": ("H_{T} [GeV]", "p_{T} [GeV]"),
        "mrecoilvsHt": ("H_{T} [GeV]", "m_{recoil} [GeV]"),
    }
    return mapping.get(var, ("", ""))

def draw_latex_header(xmax, ymax, is2d=False):
    """Place collider labels above the frame to avoid overlap."""
    y_ndc = 0.93 if not is2d else 0.92
    tx = TLatex()
    tx.SetNDC()
    tx.SetTextFont(42)
    tx.SetTextSize(0.045)
    tx.SetTextAlign(13)  # left-aligned, top anchored
    ty = TLatex()
    ty.SetNDC()
    ty.SetTextFont(42)
    ty.SetTextSize(0.045)
    ty.SetTextAlign(33)  # right-aligned, top anchored
    tx.DrawLatex(0.18, y_ndc, "e^{+}e^{-} collider")
    ty.DrawLatex(0.88, y_ndc, "#sqrt{s} = 3 TeV")

def main():
    ensure_outdir(OUT_DIR)
    out_root_path = os.path.join(OUT_DIR, OUT_ROOT)
    fout = TFile(out_root_path, "RECREATE")

    # Abre señales
    sig_files = []
    for m in MASSES:
        f = open_if_exists(os.path.join("root", f"{TAG}{m}.root"))
        if f: sig_files.append((m, f))
    if not sig_files:
        print("[ERROR] No hay ROOT de señal."); return
    print("[OK] Señales encontradas:", ", ".join(m for m,_ in sig_files))

    keep_alive = []  # <- evita que Python destruya objetos aún usados por el canvas

    for var in VARS:
        is2d = var in VARS_2D
        print(f"[INFO] Dibujando {var} ({'2D' if is2d else '1D'})")

        if not is2d:
            # ---------- 1D overlay ----------
            cname = safe_key(f"c_{var}_overlay")
            c = TCanvas(cname, f"{var} — overlay", 1200, 900)
            leg = TLegend(.62, .60, .88, .86)
            leg.SetBorderSize(0)
            leg.SetFillColor(0)
            leg.SetTextFont(42)
            leg.SetTextAlign(12)
            drawn = False; ymax = 0.0; xmax = 1.0

            for idx, (mass, f) in enumerate(sig_files):
                h, used_name = fetch_hist_any_name(f, var)
                if not h:
                    print(f"[WARN] {f.GetName()} no tiene '{var}'"); continue
                if not (h.InheritsFrom("TH1")):
                    print(f"[WARN] '{used_name}' no es TH1: clase={h.ClassName()}"); continue

                hc = clone_detached(h, f"{var}_{mass}_clone")
                hc = rebin_1d_capture(hc, REBIN_1D)
                if NORMALIZE_1D: normalize_to_unity(hc)

                col = COLORS[idx % len(COLORS)]
                hc.SetLineColor(col); hc.SetMarkerColor(col); hc.SetLineWidth(2); hc.SetStats(0)

                xt, yt = axis_titles(var)
                if xt: hc.GetXaxis().SetTitle(xt)
                if yt: hc.GetYaxis().SetTitle(yt)

                opt = "HIST" if not drawn else "HIST SAME"
                hc.Draw(opt); drawn = True

                ymax = max(ymax, hc.GetMaximum())
                xmax = hc.GetXaxis().GetBinCenter(max(1, hc.GetNbinsX()))
                leg.AddEntry(hc, f"m_{{T}}={mass} GeV", "l")

                keep_alive.append(hc)

            if drawn:
                leg.Draw(); keep_alive.append(leg)
                draw_latex_header(xmax, ymax, is2d=False)
                fout.cd(); c.Write(cname)
                c.SaveAs(os.path.join(OUT_DIR, f"{cname}.png"))
                c.SaveAs(os.path.join(OUT_DIR, f"{cname}.pdf"))
                c.Update()
            else:
                print(f"[WARN] Nada para {var}")

        else:
            # ---------- 2D 2x2 ----------
            cname = safe_key(f"c_{var}_2D_2x2")
            c = TCanvas(cname, f"{var} — 2D (2x2)", 1600, 1200)
            c.Divide(2, 2)

            pad_idx = 1; drew_any = False
            xt, yt = axis_titles(var)

            for idx, (mass, f) in enumerate(sig_files):
                h2, used_name = fetch_hist_any_name(f, var)
                if not h2:
                    print(f"[WARN] {f.GetName()} no tiene '{var}'"); continue
                if not (h2.InheritsFrom("TH2")):
                    print(f"[WARN] '{used_name}' no es TH2: clase={h2.ClassName()}"); continue

                hc2 = clone_detached(h2, f"{var}_{mass}_2Dclone")
                hc2 = rebin2d_capture(hc2, nx=REBIN2D_X, ny_sel=(REBIN2D_Y_LOW, REBIN2D_Y_HIGH))

                c.cd(pad_idx); pad_idx += 1
                ROOT.gPad.SetRightMargin(0.12); ROOT.gPad.SetLeftMargin(0.12); ROOT.gPad.SetBottomMargin(0.12)
                hc2.SetStats(0)
                if xt: hc2.GetXaxis().SetTitle(xt)
                if yt: hc2.GetYaxis().SetTitle(yt)
                hc2.Draw("COLZ")

                xend = hc2.GetXaxis().GetBinCenter(max(1, hc2.GetNbinsX()))
                yend = hc2.GetYaxis().GetBinCenter(max(1, hc2.GetNbinsY()))
                tx = TLatex(); tx.SetTextFont(42); tx.SetTextSize(0.045)
                ty = TLatex(); ty.SetTextFont(42); ty.SetTextSize(0.045)
                tm = TLatex(); tm.SetTextFont(42); tm.SetTextSize(0.045)
                tx.DrawLatex(0.02*xend, 1.01*yend, "e^{+}e^{-} collider")
                ty.DrawLatex(0.80*xend, 1.01*yend, "#sqrt{s} = 3 TeV")
                tm.DrawLatex(0.40*xend, 1.04*yend, f"m_{{T}} = {mass} GeV")
                keep_alive += [hc2, tx, ty, tm]
                drew_any = True

            if drew_any:
                fout.cd(); c.Write(cname)
                c.SaveAs(os.path.join(OUT_DIR, f"{cname}.png"))
                c.SaveAs(os.path.join(OUT_DIR, f"{cname}.pdf"))
                c.Update()
            else:
                print(f"[WARN] Nada para {var}")

    # cerrar
    fout.Close()
    for _, f in sig_files: f.Close()
    print(f"[DONE] Canvases en: {out_root_path}\nPNG/PDF en: {OUT_DIR}")

if __name__ == "__main__":
    main()
