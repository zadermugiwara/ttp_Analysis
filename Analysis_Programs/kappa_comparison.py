#source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh

# -*- coding: utf-8 -*-
"""
kappa_vs_significance_auto.py

Lee los directorios kappa desde tu Histograms.sh y grafica:
    kappa  vs  S/sqrt(S+B)
usando la variable:
    "mrecoil_isolated_toplikes_rec_missE_cut"

NO requiere argumentos. Ajusta rutas/constantes abajo si cambian.
"""

import os, re, math, csv
from array import array
import ROOT
from ROOT import TFile, TCanvas, TGraph, TLatex, gROOT

gROOT.SetBatch(True)

# ==================== PARÁMETROS EMBEBIDOS ====================
# Ruta a tu script de despacho (según tus capturas)
SH_PATH = "/home/higinio/Documentos/ASE/Analysis_Programs/Histograms.sh"

# Dentro de CADA directorio kappa, se espera un subdir 'root/' con:
SIGNAL_FILE = "Tt1M1200.root"                 # señal
BACKGROUNDS = ["ttz", "w+w-z", "tth", "ttbarra"]  # fondos

# Histograma de la selección final para contar S y B:
VAR = "mrecoil_isolated_toplikes_rec_missE_cut"

# Luminosidad en tu convención (5 ab^-1 -> 5e18 con el 1e-12 en el scale)
LUMI = 5e18

# ==== Directorio de salida solicitado ====
OUT_DIR = "/home/higinio/Documentos/ASE/Resultados"

# Nombres de archivo (se guardan dentro de OUT_DIR)
OUT_ROOT   = "kappa_scan.root"
OUT_PDF    = "kappa_vs_significance.pdf"
OUT_PNG    = "kappa_vs_significance.png"
OUT_CSV    = "kappa_vs_significance.csv"
# ===============================================================


# ==================== HELPERS ROBUSTOS ====================
def ensure_outdir(path):
    path = os.path.expanduser(os.path.expandvars(path))
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] No pude crear {path}: {e}")
    return path

def open_if_exists(path):
    """Abre un TFile solo si existe y es válido."""
    path = os.path.expanduser(os.path.expandvars(path.strip().strip('"').strip("'")))
    if not os.path.exists(path):
        print(f"[INFO] No existe: {path}")
        return None
    f = TFile.Open(path, "read")
    if not f or f.IsZombie():
        print(f"[WARN] No pude abrir: {path}")
        return None
    return f

def _center_of_max(h):
    if not h or h.GetNbinsX()==0:
        return 0.0
    b = h.GetMaximumBin()
    return float(h.GetXaxis().GetBinCenter(b))

def get_xs_nsim_from_file(tf):
    """Lee Cross_Section y no_sim del archivo ROOT (por centro del bin del máximo)."""
    xs_h = tf.Get("Cross_Section")
    n_h  = tf.Get("no_sim")
    xs   = _center_of_max(xs_h)
    nsim = _center_of_max(n_h)
    return xs, nsim

def expected_yield_from_entries(tf, hist_name, lumi=LUMI):
    """
    Yield esperado = Entries * (lumi * xs * 1e-12 / nsim)  (seguro).
    Si xs/nsim inválidos -> 0.
    """
    h = tf.Get(hist_name)
    if not h:
        return 0.0
    xs, nsim = get_xs_nsim_from_file(tf)
    if xs <= 0 or nsim <= 0:
        print(f"[WARN] xs/nsim inválidos en {tf.GetName()} (xs={xs}, N={nsim})")
        return 0.0
    scale = (lumi * xs * 1e-12) / nsim
    return float(h.GetEntries()) * scale

def sum_background_yield(dir_path, hist_name, lumi=LUMI):
    """Suma yields de fondos en un directorio kappa dado."""
    total = 0.0
    for b in BACKGROUNDS:
        fb = open_if_exists(os.path.join(dir_path, "root", f"{b}.root"))
        if not fb:
            continue
        total += expected_yield_from_entries(fb, hist_name, lumi=lumi)
        fb.Close()
    return total

def kappa_value_from_label(label):
    """
    Convierte 'kappa010' -> 0.10, 'kappa065' -> 0.65, etc.
    Regla: tomar TODOS los dígitos tras 'kappa' como entero y dividir por 100.
    """
    m = re.match(r'kappa(\d+)$', label)
    if not m:
        return None
    digits = m.group(1)
    try:
        return int(digits) / 100.0
    except Exception:
        return None

def parse_kappa_dirs(sh_path):
    """
    Busca pares (kappa_label, dir) en Histograms.sh.
    Patrón típico:
        elif [ $1 == "kappa010" ]; then
            cd /ruta/a/ttp_Analysis_kappa010
    Devuelve lista en el orden en que aparecen.
    """
    pairs = []
    if not os.path.exists(sh_path):
        print(f"[ERROR] No encuentro {sh_path}")
        return pairs

    with open(sh_path, "r", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.search(r'\b(?:elif|if)\s*\[\s*\$1\s*==\s*"(kappa\d+)"\s*\]', line)
        if m:
            label = m.group(1)
            dir_path = None
            # buscar la línea 'cd ...' más cercana
            j = i + 1
            while j < len(lines):
                # cortar si aparece otro elif/fi
                if re.search(r'\b(?:elif|if)\s*\[\s*\$1\s*==', lines[j]) or lines[j].strip() == "fi":
                    break
                mcd = re.search(r'^\s*cd\s+([^\n;#]+)', lines[j])
                if mcd:
                    dir_path = mcd.group(1).strip()
                    break
                j += 1
            if dir_path:
                pairs.append((label, dir_path))
            i = j if j>i else i+1
        else:
            i += 1
    return pairs
# ===========================================================


def main():
    # Asegurar carpeta de salida
    out_dir = ensure_outdir(OUT_DIR)
    out_root_path = os.path.join(out_dir, OUT_ROOT)
    out_pdf_path  = os.path.join(out_dir, OUT_PDF)
    out_png_path  = os.path.join(out_dir, OUT_PNG)
    out_csv_path  = os.path.join(out_dir, OUT_CSV)

    print(f"[INFO] Leyendo: {SH_PATH}")
    kp_dirs = parse_kappa_dirs(SH_PATH)
    if not kp_dirs:
        print("[ERROR] No encontré bloques kappa en Histograms.sh"); return

    print("[INFO] kappa → directorio encontrados:")
    for lbl, d in kp_dirs:
        print(f"  {lbl:>8}  ->  {d}")

    xs_vals, ys_vals = [], []  # (kappa, z)
    rows_csv = [("kappa_label", "kappa_val", "S", "B", "S/sqrt(S+B)", "dir")]

    for lbl, dir_path in kp_dirs:
        kappa = kappa_value_from_label(lbl)
        if kappa is None:
            print(f"[WARN] No pude interpretar {lbl}, se salta.")
            continue

        # Señal
        fs = open_if_exists(os.path.join(dir_path, "root", SIGNAL_FILE))
        if not fs:
            print(f"[WARN] Sin señal en {dir_path}, se salta.")
            continue
        S = expected_yield_from_entries(fs, VAR, LUMI)
        fs.Close()

        # Fondos
        B = sum_background_yield(dir_path, VAR, LUMI)

        z = S / math.sqrt(max(1e-12, S + B))
        xs_vals.append(kappa)
        ys_vals.append(z)
        rows_csv.append((lbl, f"{kappa:.4f}", f"{S:.6g}", f"{B:.6g}", f"{z:.6g}", dir_path))

        print(f"[OK] {lbl}: kappa={kappa:.3f}  S={S:.6g}  B={B:.6g}  S/sqrt(S+B)={z:.6g}")

    if not xs_vals:
        print("[ERROR] No hay puntos válidos."); return

    # Ordenar por kappa
    data = sorted(zip(xs_vals, ys_vals), key=lambda t: t[0])
    X = array('d', [p[0] for p in data])
    Y = array('d', [p[1] for p in data])

    # Plot
    gr = TGraph(len(X), X, Y)
    gr.SetName("gr_kappa_vs_signif")
    gr.SetTitle("#kappa vs S/#sqrt{S+B};#kappa;S/#sqrt{S+B}")
    gr.SetMarkerStyle(20); gr.SetMarkerSize(1.0)
    gr.SetLineWidth(2)

    c = TCanvas("c_kappa_vs_signif", "kappa vs S/sqrt(S+B)", 1100, 800)
    c.SetGrid()
    gr.Draw("ALP")

    xmax = max(X)
    ymax = max(Y) if len(Y)>0 else 1.0
    latex1 = TLatex(); latex1.SetTextFont(42); latex1.SetTextSize(0.045)
    latex1.DrawLatex(0.05*xmax, 1.05*ymax, "e^{+}e^{-} collider")
    latex2 = TLatex(); latex2.SetTextFont(42); latex2.SetTextSize(0.045)
    latex2.DrawLatex(0.75*xmax, 1.05*ymax, "#sqrt{s} = 3 TeV")

    # Guardar ROOT y figuras en OUT_DIR
    out = TFile(out_root_path, "RECREATE")
    out.WriteObject(gr, gr.GetName())
    out.WriteObject(c, c.GetName())
    out.Close()
    c.SaveAs(out_pdf_path)
    c.SaveAs(out_png_path)

    # CSV con los puntos
    try:
        with open(out_csv_path, "w", newline="") as fcsv:
            w = csv.writer(fcsv)
            w.writerows(rows_csv)
    except Exception as e:
        print(f"[WARN] No pude escribir CSV ({out_csv_path}): {e}")

    print(f"[DONE] Guardado en:\n  {out_root_path}\n  {out_pdf_path}\n  {out_png_path}\n  {out_csv_path}")

if __name__ == "__main__":
    main()
