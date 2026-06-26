# source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh
# -*- coding: utf-8 -*-
import os, sys, re, glob, math
import shutil

if sys.version_info >= (3, 12):
    alt_python = shutil.which("python3.11") or shutil.which("python3.10")
    if alt_python and os.path.abspath(sys.executable) != os.path.abspath(alt_python):
        os.execv(alt_python, [alt_python, *sys.argv])

from array import array
from pathlib import Path
import subprocess


def _ensure_root_loaded():
    """Attempt to import ROOT, sourcing thisroot.sh if necessary."""
    try:
        import ROOT  # noqa: F401
        return
    except (ModuleNotFoundError, ImportError):
        if (
            sys.version_info[:2] != (3, 11)
            and os.environ.get("ASE_HISTOGRAMS_REEXEC") != "1"
        ):
            alt_python = shutil.which("python3.11")
            if alt_python and os.path.abspath(sys.executable) != os.path.abspath(alt_python):
                os.environ["ASE_HISTOGRAMS_REEXEC"] = "1"
                os.execv(alt_python, [alt_python, *sys.argv])
        pass

    # Prefer a user-provided ROOT setup, falling back to the repo default.
    repo_root = Path(__file__).resolve().parent.parent
    default_thisroot = repo_root / "Analysis/root/root/bin/thisroot.sh"
    # If a newer build is present, prefer that.
    newer_thisroot = repo_root / "Analysis/root/root-new/bin/thisroot.sh"
    thisroot = newer_thisroot if newer_thisroot.exists() else default_thisroot
    if not thisroot.exists():
        raise

    try:
        env_dump = subprocess.check_output(
            ["bash", "-lc", f"source {thisroot} >/dev/null 2>&1 && env"],
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # noqa: BLE001
        raise ModuleNotFoundError(
            "ROOT module not found and failed to source thisroot.sh"
        ) from exc

    for line in env_dump.splitlines():
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key] = value
        if key in {"PYTHONPATH", "PATH"}:
            for entry in value.split(":"):
                if entry and entry not in sys.path:
                    sys.path.insert(0, entry)

    import ROOT  # noqa: F401


_ensure_root_loaded()

import ROOT  # noqa: E402
from ROOT import (  # noqa: E402
    TFile,
    TCanvas,
    THStack,
    TLegend,
    TLatex,
    TGraph,
    TMultiGraph,
    gROOT,
    gStyle,
)

# Disable statistics boxes globally for all histograms drawn by this script.
gStyle.SetOptStat(0)
# Keep histograms detached from input TFiles unless explicitly attached.
# This avoids lifetime/ownership issues when canvases are serialized.
ROOT.TH1.AddDirectory(False)

# =============================================================================
# Helpers anti-crash: apertura, escalado y normalización seguros
# =============================================================================

def open_if_exists(path):
    """Devuelve TFile abierto si existe y es legible; si no, None."""
    if not os.path.exists(path):
        print(f"[INFO] No existe: {path}")
        return None
    try:
        f = TFile.Open(path, "read")
    except Exception:
        print(f"[WARN] No pude abrir: {path}")
        return None
    if not f or f.IsZombie():
        print(f"[WARN] No pude abrir: {path}")
        return None
    return f

def _center_of_max(h):
    if not h or h.GetNbinsX() == 0:
        return 0.0
    b = h.GetMaximumBin()
    return float(h.GetXaxis().GetBinCenter(b))

def get_xs_nsim_from_file(tf):
    """Lee Cross_Section y no_sim del TFile tf (por centro del bin del máximo)."""
    xs_h = tf.Get('Cross_Section')
    n_h  = tf.Get('no_sim')
    xs   = _center_of_max(xs_h)
    nsim = _center_of_max(n_h)
    return xs, nsim

def get_xs_nsim_from_groot():
    """Lee Cross_Section y no_sim del directorio actual con gROOT.FindObject."""
    xs_h = gROOT.FindObject('Cross_Section')
    n_h  = gROOT.FindObject('no_sim')
    xs   = _center_of_max(xs_h)
    nsim = _center_of_max(n_h)
    return xs, nsim

def scale_sigmaL_over_N(h, xs, nsim, L, factor=1.0, who=""):
    """
    Aplica seguro: h.Scale(factor * L * xs * 1e-12 / nsim)
    Devuelve True si escaló, False si no (y deja h tal cual).
    """
    if h is None:
        return False
    if xs <= 0 or nsim <= 0:
        print(f"[WARN] {who} no escalable (xs={xs}, N={nsim}). Se salta el escalado.")
        return False
    h.Scale((factor * L * xs * 1e-12) / nsim)
    return True

def norm_to_unity(h, rebin=None, who=""):
    """Normaliza seguro: h.Scale(1/Integral). Devuelve True si normalizó."""
    if h is None:
        return False
    if rebin and rebin > 1:
        safe_rebin(h, rebin, who=who)
    integ = h.Integral()
    if integ <= 0:
        print(f"[WARN] {who} no normalizable (integral={integ}).")
        return False
    h.Scale(1.0 / integ)
    return True

def safe_rebin(hist, rebin, who=""):
    """Rebin protegido: solo aplica si rebin divide al número de bins."""
    if hist is None or not rebin or rebin <= 1:
        return False
    nbins = hist.GetNbinsX()
    if nbins < rebin or nbins % rebin != 0:
        if who:
            print(f"[INFO] {who}: se omite rebin ({rebin}) porque nbins={nbins}.")
        return False
    try:
        hist.Rebin(rebin)
        return True
    except Exception:
        print(f"[WARN] {who}: error al rebin-{rebin}.")
        return False

def _safe_rebin_axis(hist, axis, factors, who=""):
    """Intenta rebin en el eje indicado usando factores en cascada."""
    if hist is None or not factors:
        return False
    if axis == 'X':
        nbins = hist.GetNbinsX()
        rebin_method = hist.RebinX
    else:
        nbins = hist.GetNbinsY()
        rebin_method = hist.RebinY
    for factor in factors:
        if factor and factor > 1 and nbins >= factor and nbins % factor == 0:
            try:
                rebin_method(factor)
                return True
            except Exception:
                print(f"[WARN] {who}: error al rebin{axis}-{factor}.")
                return False
    if who:
        print(f"[INFO] {who}: se omite rebin {axis} (factores {factors}) porque nbins={nbins}.")
    return False

def safe_rebin_2d(hist, factors_x=None, factors_y=None, who=""):
    """Rebin protegido para histogramas 2D."""
    applied = False
    if factors_x:
        applied |= _safe_rebin_axis(hist, 'X', factors_x, who=who)
    if factors_y:
        applied |= _safe_rebin_axis(hist, 'Y', factors_y, who=who)
    return applied

# =============================================================================
# Descubrimiento de masas + Colores consistentes por masa
# =============================================================================

_MASS_COLOR_CACHE = {}  # mass(str) -> ROOT color index

def _canonical_mass_key(mass_str):
    """Normaliza la masa para cachear consistentemente (e.g. 1200 y 1200.0)."""
    try:
        return str(int(float(mass_str)))
    except Exception:
        return str(mass_str).strip()

def _stable_text_hash(text):
    """Hash simple y estable entre ejecuciones para claves no numéricas."""
    return sum((idx + 1) * ord(ch) for idx, ch in enumerate(str(text)))

def _mass_to_color_index(mass_str):
    """
    Color estable por masa:
    - Para masas conocidas (1200/1600/2000/2400), usa un mapa fijo.
    - Para el resto, usa un índice determinista sobre SIGNAL_COLOR_POOL.
    - Independiente del orden de descubrimiento de archivos.
    """
    mass_key = _canonical_mass_key(mass_str)
    if mass_key in _MASS_COLOR_CACHE:
        return _MASS_COLOR_CACHE[mass_key]

    try:
        mass_int = int(mass_key)
    except Exception:
        mass_int = None

    color_idx = None
    if mass_int is not None:
        color_idx = SIGNAL_MASS_COLOR_MAP.get(mass_int)

    if color_idx is None:
        # Fallback determinista para cualquier masa no ancla, sin depender del orden.
        # Evita reciclar colores ancla cuando hay más masas.
        seed = mass_int if mass_int is not None else _stable_text_hash(mass_key)
        pool = SIGNAL_FALLBACK_COLOR_POOL if SIGNAL_FALLBACK_COLOR_POOL else SIGNAL_COLOR_POOL
        pool_size = len(pool)
        for shift in range(pool_size):
            idx = ((seed * 2654435761) + 97 * shift) % pool_size
            candidate = pool[idx]
            if candidate not in FORBIDDEN_SIGNAL_COLORS:
                color_idx = candidate
                break

    if color_idx is None:
        color_idx = ROOT.kRed + 1

    _MASS_COLOR_CACHE[mass_key] = color_idx
    return color_idx

def discover_signal_files(tag_name, directory="root"):
    """
    Busca archivos 'root/{tag_name}*.root' y extrae la primera secuencia numérica
    DESPUÉS del prefijo tag_name como masa. Ejemplos válidos:
      - Tt1M1200.root         -> 1200
      - Tt1M1800kappa0p10.root -> 1800
      - Tt1M2400_something.root -> 2400
    Devuelve lista ordenada por masa ascendente: [(mass_str, TFile), ...]
    """
    pattern = os.path.join(directory, f"{tag_name}*.root")
    files = glob.glob(pattern)
    out = []
    rx = re.compile(rf"^{re.escape(tag_name)}(\d+)")
    for fp in files:
        base = os.path.basename(fp)
        m = None
        mobj = rx.search(base)
        if mobj:
            m = mobj.group(1)
        else:
            # como fallback, toma el último bloque numérico antes de '.root'
            mobj2 = re.search(r"(\d+)(?=\.root$)", base)
            if mobj2:
                m = mobj2.group(1)
        if not m:
            continue
        out.append((m, fp))
    out.sort(key=lambda t: float(t[0]))
    if out:
        print(f"[OK] Señales encontradas para tag '{tag_name}': " + ", ".join(m for m,_ in out))
    else:
        print(f"[ERROR] No hay archivos de señal para tag '{tag_name}' en {directory}.")
    return out

def _collect_background_dirs():
    """Return ordered list of directories to search for background ROOT files."""
    dirs = []
    local_root = Path.cwd() / "root"
    if local_root.is_dir():
        dirs.append(local_root)

    extra = os.environ.get("ASE_BACKGROUND_DIRS")
    if extra:
        for raw in extra.split(os.pathsep):
            raw = raw.strip()
            if not raw:
                continue
            candidate = Path(raw).expanduser()
            if candidate.is_dir() and candidate not in dirs:
                dirs.append(candidate)

    if not dirs:
        dirs.append(local_root)
    return dirs

BACKGROUND_SEARCH_DIRS = _collect_background_dirs()
if len(BACKGROUND_SEARCH_DIRS) > 1:
    print("[INFO] Background search order: " + ", ".join(str(p) for p in BACKGROUND_SEARCH_DIRS))
elif BACKGROUND_SEARCH_DIRS:
    print(f"[INFO] Background directory: {BACKGROUND_SEARCH_DIRS[0]}")

def resolve_background_file(name):
    """
    Resolve background ROOT file name against configured search directories.
    Returns string path (even if file missing, prefers first search dir).
    """
    for directory in BACKGROUND_SEARCH_DIRS:
        candidate = directory / name
        if candidate.exists():
            return str(candidate)
    if BACKGROUND_SEARCH_DIRS:
        return str(BACKGROUND_SEARCH_DIRS[0] / name)
    return str(Path("root") / name)

# =============================================================================
# Config
# =============================================================================

nombres = ['deltaRjet',"deltaRlepton","m_recoil","mass","mass_post","mass_lead","Ht",
           "fatjetHt","fatjet2Ht","fatjetpostHt","mass_post2","m_recoil2","fatjetpostHt2",
           "pt_fatjetpost","pt_fatjetpost2","goodFJ","m_recoil0.5","m_recoil0","masstoplike",
           "mrecoil toplikes","No_FJ","No_top_FJ","mrecoil_isolated_toplikes_rec_cut","m_recoilcut",
           "topHt","m_recoil_isolated_toplikes","TPmass","topmass","topdecmass","truth_recoil",
           "truth_deltaR_jet_TP","truth_deltaR_jet_top","truth_deltaR_jet_topdec","truth_deltaR_leptons_TP",
           "truth_deltaR_leptons_top","truth_deltaR_leptons_topdec","truth_deltaR_fatjet_TP",
           "truth_deltaR_fatjet_top","truth_deltaR_fatjet_topdec","good_deltaRjet","good_deltaRlepton",
           "good_m_recoil","good_m_fatjet","good_pt_fatjet","good_E_fatjet","good_Ht_fatjet","bad_deltaRjet",
           "bad_deltaRlepton","bad_m_recoil","bad_m_fatjet","bad_pt_fatjet","bad_E_fatjet","bad_Ht_fatjet",
           'Miss_Energy','mrecoil_isolated_toplikes_rec_missE_cut']

BACKGROUND_SOURCES = [
    ('ttz', 't#bar{t} Z'),
    ('w+w-z', 'W^{+} W^{-} Z'),
    ('tth', 't#bar{t} H'),
]
BASE_BACKGROUND = ('ttbarra', 't#bar{t}')

bkgcompare = ['mrecoil_isolated_toplikes_rec_cut', 'Miss_Energy','No_FJ', 'No_top_FJ','Ht',
              'fatjetpostHt', 'mrecoil_isolated_toplikes_rec_missE_cut',
              'mrecoil_BDT1200_cut', 'mrecoil_BDT_ttbar', 'mrecoil_BDT2400_cut']

bkgstack = ['mrecoil_isolated_toplikes_rec_cut', 'mrecoil_isolated_toplikes_rec_missE_cut',
            'mrecoil_BDT1200_cut', 'mrecoil_BDT_ttbar', 'mrecoil_BDT1600_cut',
            'mrecoil_BDT2000_cut','mrecoil_BDT2400_cut']

# Colores de fondo (estables por nombre y persistentes al reabrir .root).
# Evitamos TColor custom en bkg porque los índices RGB no son portables entre sesiones.
BACKGROUND_COLOR_MAP = {
    'ttbarra': ROOT.kGray + 1,
    'ttz': ROOT.kGreen - 6,
    'w+w-z': ROOT.kAzure - 8,
    'tth': ROOT.kOrange - 3,
}
BACKGROUND_COLOR_FALLBACK_POOL = [
    ROOT.kTeal - 7,
    ROOT.kCyan - 6,
    ROOT.kSpring - 7,
    ROOT.kViolet - 8,
    ROOT.kMagenta - 10,
    ROOT.kYellow - 7,
]

def _background_color_for(process_name, idx_hint=0):
    """Color consistente por proceso de fondo, independiente del orden en listas."""
    if process_name in BACKGROUND_COLOR_MAP:
        return BACKGROUND_COLOR_MAP[process_name]
    return BACKGROUND_COLOR_FALLBACK_POOL[idx_hint % len(BACKGROUND_COLOR_FALLBACK_POOL)]

histo2D = ['EFJvsmrecoil', 'm_FJvspt_FJ', 'EFJvsmass', 'EFJvspt', 'massvspt', 'mrecoilvspt',
           'EvsHt', 'ptvsHt', 'mrecoilvsHt', 'ptfatvsHt',
           'truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec','METvsmrecoil']

Luminosity = 5*(10**18)

# Etiquetas de señal (prefijos de archivo en ./root). Puedes pasar una o varias por CLI:
#   python script.py Tt1M
#   python script.py Tt1M Tt2M
kappa = ['Tt1M']
if len(sys.argv) >= 2:
    # Permite separar por comas en un solo arg, o múltiples args.
    cli_tags = []
    for arg in sys.argv[1:]:
        cli_tags.extend([t for t in arg.split(",") if t])
    if cli_tags:
        kappa = cli_tags
        print("[CLI] Tags de señal:", kappa)

# Directorio de salidas gráficas directas (PDF/PNG)
OUT_DIR = os.path.join(os.getcwd(), "Resultados")
os.makedirs(OUT_DIR, exist_ok=True)

# Escalas opcionales por masa para las señales (por defecto 1.0)
# Si quieres el antiguo "x10" en 2400, descomenta esta línea:
# SIGNAL_SCALE = {"2400": 10.0}
SIGNAL_SCALE = {}

# Paleta base para señales (colores brillantes, distintos de fondo)
SIGNAL_COLOR_POOL = [
    ROOT.kRed + 1,
    ROOT.kAzure - 3,
    ROOT.kGreen + 2,
    ROOT.kMagenta + 2,
    ROOT.kOrange + 7,
    ROOT.kPink + 7,
    ROOT.kSpring + 5,
    ROOT.kTeal + 2,
    ROOT.kViolet + 5,
    ROOT.kBlue - 7,
    ROOT.kCyan + 2,
    ROOT.kYellow + 3,
    ROOT.kBlue + 3,
    ROOT.kMagenta - 9,
    ROOT.kOrange - 3,
]
# Mapeo fijo por masa para consistencia con Paper/figs/recoil_comparison.py
SIGNAL_MASS_COLOR_MAP = {
    1200: ROOT.kRed + 1,
    1600: ROOT.kAzure - 3,
    2000: ROOT.kGreen + 2,
    2400: ROOT.kMagenta + 2,
}
FORBIDDEN_SIGNAL_COLORS = {ROOT.kWhite, ROOT.kBlack, 0}
SIGNAL_FALLBACK_COLOR_POOL = [
    c for c in SIGNAL_COLOR_POOL
    if c not in SIGNAL_MASS_COLOR_MAP.values() and c not in FORBIDDEN_SIGNAL_COLORS
]

# =============================================================================
# Representación de muestras ROOT (fondos / señales)
# =============================================================================

class RootSample:
    """Pequeña envoltura para manejar TFile, escala y carga de histogramas."""

    def __init__(self, file_path, label, color=None, extra_scale=1.0):
        self.file_path = file_path
        self.label = label
        self.color = color
        self.extra_scale = extra_scale
        self.file = open_if_exists(file_path)
        self.xs = 0.0
        self.nsim = 0.0
        if self.file:
            self.xs, self.nsim = get_xs_nsim_from_file(self.file)
            if self.xs <= 0 or self.nsim <= 0:
                print(f"[WARN] {label}: xs={self.xs}, N={self.nsim}.")

    def is_ready(self):
        return bool(self.file)

    def load_hist(self, hist_name):
        if not self.file:
            return None
        hist = self.file.Get(hist_name)
        if not hist:
            print(f"[WARN] {self.label}: histograma '{hist_name}' ausente en {self.file_path}.")
            return None
        clone = hist.Clone(f"{hist_name}_{self.label}")
        # Ensure cloned histograms are independent from the source TFile.
        if hasattr(clone, "SetDirectory"):
            clone.SetDirectory(0)
        return clone

    def scale_to_lumi(self, hist, luminosity, rebin=None, who=None):
        """Escala por luminosidad (sigma*L/N) aplicando optional rebin."""
        if hist is None:
            return None
        who = who or self.label
        if not scale_sigmaL_over_N(hist, self.xs, self.nsim, L=luminosity,
                                   factor=self.extra_scale, who=who):
            return None
        if rebin and rebin > 1:
            safe_rebin(hist, rebin, who=who)
        return hist

    def normalize(self, hist, rebin=None, who=None):
        """Normaliza a unidad aplicando optional rebin."""
        if hist is None:
            return None
        who = who or self.label
        return hist if norm_to_unity(hist, rebin=rebin, who=who) else None

    def close(self):
        if self.file:
            self.file.Close()
            self.file = None

# =============================================================================
# MAIN
# =============================================================================

STACK_REBIN = 40
COMPARE_REBIN = 20
SIGNAL_COMPARE_REBIN = 20
H2_REBIN_X_FACTORS = [100, 50, 25, 20, 10, 5, 2]
H2_REBIN_Y_FACTORS = [100, 50, 25, 20, 10, 5, 2]

def _axis_hints(histograms):
    valid = [h for h in histograms if h]
    if not valid:
        return 1.0, 1.0
    ref = valid[0]
    sizex = ref.GetXaxis().GetBinCenter(ref.GetNbinsX())
    sizey = max(h.GetMaximum() for h in valid)
    if sizex <= 0:
        sizex = 1.0
    if sizey <= 0:
        sizey = 1.0
    return math.ceil(sizex), sizey

def _guess_xaxis_title(hist_name, hist=None):
    """Infer a readable X-axis title when the ROOT input does not provide one."""
    if hist:
        existing = hist.GetXaxis().GetTitle()
        if existing and existing.strip():
            return existing

    lower = hist_name.lower()
    if "mrecoil" in lower or "m_recoil" in lower:
        return "#it{m}_{recoil} [GeV]"
    if "miss_energy" in lower or lower.startswith("met"):
        return "Missing energy [GeV]"
    if "deltar" in lower:
        return "#DeltaR"
    if "ht" in lower:
        return "#it{H}_{T} [GeV]"
    if lower.startswith("pt") or "_pt_" in lower or "pt_" in lower:
        return "#it{p}_{T} [GeV]"
    if "mass" in lower:
        return "Mass [GeV]"
    if lower in {"goodfj", "no_fj", "no_top_fj"}:
        return "Multiplicity"

    return hist_name.replace("_", " ")

def _style_axis(axis, title_size=0.046, label_size=0.042, title_offset=None):
    """Apply a consistent readable axis style."""
    if not axis:
        return
    axis.SetTitleFont(42)
    axis.SetLabelFont(42)
    axis.SetTitleSize(title_size)
    axis.SetLabelSize(label_size)
    if title_offset is not None:
        axis.SetTitleOffset(title_offset)

def _set_hist_axis_titles(hist, hist_name, y_title):
    """Apply consistent axis titles for 1D histograms."""
    if not hist:
        return
    xaxis = hist.GetXaxis()
    yaxis = hist.GetYaxis()
    xaxis.SetTitle(_guess_xaxis_title(hist_name, hist=hist))
    yaxis.SetTitle(y_title)
    _style_axis(xaxis, title_offset=1.05)
    _style_axis(yaxis, title_offset=1.15)
    lower = hist_name.lower()
    if "mrecoil" in lower or "m_recoil" in lower:
        xaxis.SetRangeUser(800, 3000)

def _style_legend(legend, text_size=0.032):
    """Apply a compact legend style."""
    if not legend:
        return
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetTextFont(42)
    legend.SetTextSize(text_size)

def _draw_latex_annotations(sizex, sizey, right_text="#sqrt{s} = 3 TeV"):
    pad = ROOT.gPad
    if not pad:
        return
    txt = TLatex()
    txt.SetTextFont(42)
    txt.SetTextSize(0.05)
    txt.SetTextAlign(11)
    top_y = min(0.99, 1.0 - pad.GetTopMargin() + 0.006)
    txt.DrawLatexNDC(pad.GetLeftMargin(), top_y, "e^{+}e^{-} collider")
    txt2 = TLatex()
    txt2.SetTextFont(42)
    txt2.SetTextSize(0.05)
    txt2.SetTextAlign(31)
    txt2.DrawLatexNDC(1.0 - pad.GetRightMargin(), top_y, right_text)

def _axis_hints_2d(hist):
    if not hist:
        return 1.0, 1.0
    x = hist.GetXaxis().GetBinCenter(hist.GetNbinsX())
    y = hist.GetYaxis().GetBinCenter(hist.GetNbinsY())
    if x <= 0:
        x = hist.GetXaxis().GetXmax()
    if y <= 0:
        y = hist.GetYaxis().GetXmax()
    if x <= 0:
        x = 1.0
    if y <= 0:
        y = 1.0
    return x, y

def _draw_latex_annotations_2d(x_extent, y_extent, extra=""):
    pad = ROOT.gPad
    if not pad:
        return
    txt = TLatex()
    txt.SetTextFont(42)
    txt.SetTextSize(0.05)
    txt.SetTextAlign(11)
    top_y = min(0.99, 1.0 - pad.GetTopMargin() + 0.006)
    txt.DrawLatexNDC(pad.GetLeftMargin(), top_y, "e^{+}e^{-} collider")
    txt2 = TLatex()
    txt2.SetTextFont(42)
    txt2.SetTextSize(0.05)
    txt2.SetTextAlign(31)
    txt2.DrawLatexNDC(1.0 - pad.GetRightMargin(), top_y, "#sqrt{s} = 3 TeV")
    if extra:
        txt3 = TLatex()
        txt3.SetTextFont(42)
        txt3.SetTextSize(0.05)
        txt3.SetTextAlign(21)
        txt3.DrawLatexNDC(0.5, min(0.99, top_y + 0.035), extra)

for tag in kappa:
    print(f"[INFO] Procesando tag de señal '{tag}'")
    signal_info = discover_signal_files(tag, directory="root")
    if not signal_info:
        continue

    signal_samples = []
    for mass_str, file_path in signal_info:
        label = f"m_{{T}}={mass_str} GeV"
        color = _mass_to_color_index(mass_str)
        scale_factor = SIGNAL_SCALE.get(str(mass_str), 1.0)
        sample = RootSample(file_path, label, color=color, extra_scale=scale_factor)
        sample.mass = mass_str
        if sample.is_ready():
            signal_samples.append(sample)
    if not signal_samples:
        print(f"[WARN] No hay señales válidas para '{tag}'.")
        continue

    base_bkg_path = resolve_background_file(f"{BASE_BACKGROUND[0]}.root")
    base_background = RootSample(
        base_bkg_path,
        BASE_BACKGROUND[1],
        color=_background_color_for(BASE_BACKGROUND[0]),
    )

    background_samples = []
    for idx, (short_name, display) in enumerate(BACKGROUND_SOURCES):
        color = _background_color_for(short_name, idx)
        bkg_path = resolve_background_file(f"{short_name}.root")
        sample = RootSample(bkg_path, display, color=color)
        if sample.is_ready():
            background_samples.append(sample)

    output_path = f"{tag}output.root"
    output_file = TFile(output_path, "RECREATE")
    if not output_file or output_file.IsZombie():
        print(f"[ERROR] No pude crear '{output_path}'.")
        for sample in signal_samples:
            sample.close()
        for sample in background_samples:
            sample.close()
        base_background.close()
        continue

    print(f"[INFO] Se generará la salida en {output_path}")

    # --------------------------- (A) STACKS ---------------------------
    for hist_name in bkgstack:
        for idx, signal in enumerate(signal_samples, start=1):
            plot = TCanvas(f"c_plot_{hist_name}_{signal.mass}", f"{hist_name}_{signal.mass}", 1800, 1200)
            stack_canvas = TCanvas(f"c_stack_{hist_name}_{signal.mass}", f"stack_{hist_name}_{signal.mass}", 1800, 1200)
            legend_entries = []
            drawn_hists = []
            stack = THStack(f"{hist_name}_stack_{signal.mass}", "")

            plot.cd()

            base_hist = None
            if base_background.is_ready():
                base_hist = base_background.load_hist(hist_name)
                base_hist = base_background.scale_to_lumi(
                    base_hist, Luminosity, rebin=STACK_REBIN,
                    who=f"{base_background.label} {hist_name}"
                )
            if base_hist:
                base_hist.SetLineColor(base_background.color or ROOT.kBlack)
                base_hist.SetFillColor(0)
                base_hist.SetFillStyle(0)
                base_hist.SetMarkerColor(base_background.color or ROOT.kBlack)
                base_hist.SetLineWidth(2)
                base_hist.SetStats(0)
                _set_hist_axis_titles(base_hist, hist_name, "Number of Events")
                base_hist.Draw("HIST")
                legend_entries.append((base_hist, base_background.label, "l"))
                stack.Add(base_hist)
                drawn_hists.append(base_hist)

            for bkg_sample in background_samples:
                hist = bkg_sample.load_hist(hist_name)
                hist = bkg_sample.scale_to_lumi(
                    hist, Luminosity, rebin=STACK_REBIN,
                    who=f"{bkg_sample.label} {hist_name}"
                )
                if not hist:
                    continue
                hist.SetLineColor(bkg_sample.color if bkg_sample.color else ROOT.kBlack)
                hist.SetFillColor(0)
                hist.SetFillStyle(0)
                hist.SetMarkerColor(bkg_sample.color if bkg_sample.color else ROOT.kBlack)
                hist.SetLineWidth(2)
                _set_hist_axis_titles(hist, hist_name, "Number of Events")
                draw_opt = "HIST SAME" if drawn_hists else "HIST"
                hist.Draw(draw_opt)
                legend_entries.append((hist, bkg_sample.label, "l"))
                stack.Add(hist)
                drawn_hists.append(hist)

            sig_hist = signal.load_hist(hist_name)
            sig_hist = signal.scale_to_lumi(
                sig_hist, Luminosity, rebin=STACK_REBIN,
                who=f"{signal.label} {hist_name}"
            )
            if sig_hist:
                sig_hist.SetLineColor(signal.color if signal.color else ROOT.kRed + 1)
                sig_hist.SetFillColor(0)
                sig_hist.SetFillStyle(0)
                sig_hist.SetMarkerColor(signal.color if signal.color else ROOT.kRed + 1)
                sig_hist.SetLineWidth(3)
                _set_hist_axis_titles(sig_hist, hist_name, "Number of Events")
                draw_opt = "HIST SAME" if drawn_hists else "HIST"
                sig_hist.Draw(draw_opt)
                legend_entries.append((sig_hist, signal.label, "l"))
                stack.Add(sig_hist)
                drawn_hists.append(sig_hist)
            else:
                print(f"[WARN] Sin histograma '{hist_name}' para {signal.label}")

            if drawn_hists:
                sizex, sizey = _axis_hints(drawn_hists)
                legend_plot = TLegend(.73, .32, .97, .53)
                _style_legend(legend_plot)
                for hist, label, opt in legend_entries:
                    legend_plot.AddEntry(hist, label, opt)
                legend_plot.Draw()
                _draw_latex_annotations(sizex, sizey)
                plot.Update()
                output_file.WriteObject(plot, f"{hist_name}_{signal.mass}_CrossSection")

                stack_canvas.cd()
                stack.Draw("HIST")
                stack.GetXaxis().SetTitle(_guess_xaxis_title(hist_name))
                stack.GetYaxis().SetTitle("Number of Events")
                _style_axis(stack.GetXaxis())
                _style_axis(stack.GetYaxis())
                if "mrecoil" in hist_name.lower() or "m_recoil" in hist_name.lower():
                    stack.GetXaxis().SetLimits(800, 3000)
                legend_stack = TLegend(.73, .32, .97, .53)
                _style_legend(legend_stack)
                for hist, label, opt in legend_entries:
                    legend_stack.AddEntry(hist, label, opt)
                legend_stack.Draw()
                stack_hist = stack.GetHistogram()
                if stack_hist:
                    stack_sizex = math.ceil(stack_hist.GetXaxis().GetBinCenter(stack_hist.GetNbinsX()))
                else:
                    stack_sizex, _ = _axis_hints(drawn_hists)
                stack_sizey = stack.GetMaximum()
                if stack_sizey <= 0:
                    stack_sizey = sizey
                stack_header = "#sqrt{s} = 3 TeV"
                if "mrecoil" in hist_name.lower():
                    stack_header = "L = 5 ab^{-1}; #sqrt{s} = 3 TeV"
                _draw_latex_annotations(stack_sizex, stack_sizey, right_text=stack_header)
                stack_canvas.Update()
                output_file.WriteObject(stack_canvas, f"stack_{hist_name}_{signal.mass}_CrossSection")
            else:
                print(f"[WARN] No se pudo dibujar '{hist_name}' con {signal.label}")

    # ----------------- (B) Comparación de formas normalizadas -----------------
    for hist_name in bkgcompare:
        for idx, signal in enumerate(signal_samples, start=1):
            canvas = TCanvas(f"c_cmp_{hist_name}_{signal.mass}", f"{hist_name}_{signal.mass}", 1800, 1200)
            legend_entries = []
            drawn_hists = []

            canvas.cd()

            base_hist = None
            if base_background.is_ready():
                base_hist = base_background.load_hist(hist_name)
                base_hist = base_background.normalize(
                    base_hist, rebin=COMPARE_REBIN,
                    who=f"{base_background.label} {hist_name}"
                )
            if not base_hist:
                print(f"[WARN] Base '{hist_name}' no disponible para normalización.")
                del canvas
                continue
            base_hist.SetLineColor(base_background.color or ROOT.kBlack)
            base_hist.SetFillColor(0)
            base_hist.SetMarkerColor(base_background.color or ROOT.kBlack)
            base_hist.SetLineWidth(2)
            base_hist.SetStats(0)
            _set_hist_axis_titles(base_hist, hist_name, "Arbitrary Units")
            base_hist.Draw("HIST")
            legend_entries.append((base_hist, base_background.label, "l"))
            drawn_hists.append(base_hist)

            for bkg_sample in background_samples:
                hist = bkg_sample.load_hist(hist_name)
                hist = bkg_sample.normalize(
                    hist, rebin=COMPARE_REBIN,
                    who=f"{bkg_sample.label} {hist_name}"
                )
                if not hist:
                    continue
                hist.SetLineColor(bkg_sample.color if bkg_sample.color else ROOT.kBlack)
                hist.SetFillColor(0)
                hist.SetMarkerColor(bkg_sample.color if bkg_sample.color else ROOT.kBlack)
                hist.SetLineWidth(2)
                _set_hist_axis_titles(hist, hist_name, "Arbitrary Units")
                hist.Draw("HIST SAME")
                legend_entries.append((hist, bkg_sample.label, "l"))
                drawn_hists.append(hist)

            sig_hist = signal.load_hist(hist_name)
            sig_hist = signal.normalize(
                sig_hist, rebin=COMPARE_REBIN,
                who=f"{signal.label} {hist_name}"
            )
            if not sig_hist:
                print(f"[WARN] Señal '{signal.label}' sin histograma normalizable '{hist_name}'.")
                del canvas
                continue
            sig_hist.SetLineColor(signal.color if signal.color else ROOT.kRed + 1)
            sig_hist.SetFillStyle(0)
            sig_hist.SetMarkerColor(signal.color if signal.color else ROOT.kRed + 1)
            sig_hist.SetLineWidth(3)
            _set_hist_axis_titles(sig_hist, hist_name, "Arbitrary Units")
            sig_hist.Draw("HIST SAME")
            legend_entries.append((sig_hist, signal.label, "l"))
            drawn_hists.append(sig_hist)

            legend_cmp = TLegend(.73, .32, .97, .53)
            _style_legend(legend_cmp)
            for hist, label, opt in legend_entries:
                legend_cmp.AddEntry(hist, label, opt)
            legend_cmp.Draw()

            sizex, sizey = _axis_hints(drawn_hists)
            _draw_latex_annotations(sizex, sizey)
            canvas.Update()
            output_file.WriteObject(canvas, f"{hist_name}_{signal.mass}_Normalized")

    # ----------------- (C) Comparación entre señales (normalizadas) -----------------
    for hist_name in nombres:
        canvas = TCanvas(f"c_sig_{hist_name}", f"{hist_name}_signals", 1800, 1200)
        canvas.SetLeftMargin(0.16)
        canvas.SetBottomMargin(0.12)
        canvas.SetTopMargin(0.08)
        legend = TLegend(.73, .32, .97, .53)
        _style_legend(legend)
        drawn_hists = []

        for signal in signal_samples:
            hist = signal.load_hist(hist_name)
            hist = signal.normalize(
                hist, rebin=SIGNAL_COMPARE_REBIN,
                who=f"{signal.label} {hist_name}"
            )
            if not hist:
                continue
            color = signal.color if signal.color else ROOT.kRed + 1
            if color in (0, ROOT.kWhite):
                color = ROOT.kRed + 1
            hist.SetLineColor(color)
            hist.SetMarkerColor(color)
            hist.SetFillStyle(0)
            hist.SetStats(0)
            hist.SetLineWidth(3)
            _set_hist_axis_titles(hist, hist_name, "Arbitrary Units")
            draw_opt = "HIST SAME" if drawn_hists else "HIST"
            hist.Draw(draw_opt)
            legend.AddEntry(hist, signal.label, "l")
            drawn_hists.append(hist)

        if drawn_hists:
            sizex, sizey = _axis_hints(drawn_hists)
            _draw_latex_annotations(sizex, sizey)
            legend.Draw()
            canvas.Update()
            output_file.WriteObject(canvas, f"{hist_name}_SignalsOverlay")
        else:
            print(f"[WARN] Ninguna señal disponible para '{hist_name}'.")
        del canvas

    # ----------------- (D) Histogramas 2D -----------------
    two_d_backgrounds = list(background_samples)
    if base_background.is_ready():
        two_d_backgrounds.append(base_background)

    for hist_name in histo2D:
        for signal in signal_samples:
            canvas = TCanvas(f"c_sig2d_{hist_name}_{signal.mass}", f"{hist_name}_{signal.mass}_2D", 1800, 1200)
            hist = signal.load_hist(hist_name)
            if not hist:
                del canvas
                continue
            if signal.color in (0, ROOT.kWhite, None):
                hist.SetLineColor(ROOT.kRed + 1)
                hist.SetMarkerColor(ROOT.kRed + 1)
            else:
                hist.SetLineColor(signal.color)
                hist.SetMarkerColor(signal.color)
            safe_rebin_2d(hist, H2_REBIN_X_FACTORS, H2_REBIN_Y_FACTORS,
                          who=f"{signal.label} {hist_name}")
            hist.SetStats(0)
            hist.SetDirectory(0)
            hist.Draw("COLZ")
            x_hint, y_hint = _axis_hints_2d(hist)
            _draw_latex_annotations_2d(x_hint, y_hint, signal.label)
            canvas.Update()
            output_file.WriteObject(canvas, f"{hist_name}_{signal.mass}_Signal2D")
            del canvas

        for bkg_sample in two_d_backgrounds:
            canvas = TCanvas(f"c_bkg2d_{hist_name}_{bkg_sample.label}", f"{hist_name}_{bkg_sample.label}_2D", 1800, 1200)
            hist = bkg_sample.load_hist(hist_name)
            if not hist:
                del canvas
                continue
            color = bkg_sample.color if getattr(bkg_sample, "color", None) not in (None, 0) else ROOT.kBlue + 1
            hist.SetLineColor(color)
            hist.SetMarkerColor(color)
            safe_rebin_2d(hist, H2_REBIN_X_FACTORS, H2_REBIN_Y_FACTORS,
                          who=f"{bkg_sample.label} {hist_name}")
            hist.SetStats(0)
            hist.SetDirectory(0)
            hist.Draw("COLZ")
            x_hint, y_hint = _axis_hints_2d(hist)
            _draw_latex_annotations_2d(x_hint, y_hint, bkg_sample.label)
            canvas.Update()
            output_file.WriteObject(canvas, f"{hist_name}_{bkg_sample.label}_Background2D")
            del canvas

    output_file.Close()
    for sample in signal_samples:
        sample.close()
    for sample in background_samples:
        sample.close()
    base_background.close()
