#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
from math import isclose
# === Hardcoded paths ===
ROOT_DIR = Path("/media/higinio/Expansion/Madgraph")
OUTPUT_TEX = Path("/home/higinio/Documentos/ASE/Resultados/Tt_widths_table.tex")

# Regex for "DECAY 6000006 <width>"
DECAY_RE = re.compile(r"^\s*DECAY\s+6000006\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", re.MULTILINE)
# Mass from folder name, e.g. Tt1200, Tt2400
MASS_RE = re.compile(r"^Tt(\d+)", re.IGNORECASE)
# Kappa token; handles variants like "kappa0 10", "kappa 0 10", "kappa0_10", "kappa0-10"
KAPPA_RE = re.compile(r"kappa\s*0[ \t._-]*([0-9]+)", re.IGNORECASE)

def find_param_card(d: Path) -> Path | None:
    """Locate param_card.dat inside a MadGraph output dir."""
    top = d / "param_card.dat"
    if top.is_file():
        return top
    cards = d / "Cards" / "param_card.dat"
    if cards.is_file():
        return cards
    return None

def extract_width(param_path: Path) -> float | None:
    text = param_path.read_text(errors="ignore")
    m = DECAY_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

def mass_from_name(name: str) -> int | None:
    m = MASS_RE.search(name)
    return int(m.group(1)) if m else None

def parse_kappa_from_name(name: str) -> float | None:
    """
    Extract κ from names like 'Tt2000kappa0 35' -> 0.35.
    Returns None if 'kappa' not present.
    """
    m = KAPPA_RE.search(name)
    if not m:
        return None
    digits = m.group(1)  # '35' -> 0.35; '5' -> 0.05
    try:
        return int(digits) / 100.0
    except Exception:
        return None

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", s)]

def latex_escape(s: str) -> str:
    return (s.replace("\\", r"\textbackslash{}")
             .replace("_", r"\_")
             .replace("&", r"\&")
             .replace("%", r"\%")
             .replace("#", r"\#")
             .replace("{", r"\{")
             .replace("}", r"\}")
             .replace("~", r"\textasciitilde{}"))

def make_kappa_table(rows, mass: int):
    """
    rows: list of (kappa, width, dirname) for a single mass.
    Returns LaTeX table string (booktabs).
    """
    lines = []
    if not rows:
        return ""
    rows = sorted(rows, key=lambda x: (x[0], x[1], natural_key(x[2])))
    lines.append(r"\begin{table}[H]")
    lines.append(r"\centering")
    lines.append(fr"\caption{{Widths $\Gamma(T)$ (PDG 6000006) for \texttt{{Tt{mass}}} samples with $\kappa$.}}")
    lines.append(fr"\label{{tab:Tt{mass}Kappa}}")
    lines.append(r"\begin{tabular}{lr}")
    lines.append(r"\toprule")
    lines.append(r"$\kappa$ & Width [GeV] \\")
    lines.append(r"\midrule")
    for kappa, width, _name in rows:
        # κ printed with two decimals, width with up to 6 significant digits
        lines.append(fr"${kappa:.2f}$ & {width:.6g} \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines)

def make_nokappa_table(groups):
    """
    groups: list of (width, [dirnames]) already grouped by (approx) equal width.
    Returns LaTeX table string (booktabs).
    """
    if not groups:
        return ""
    groups = sorted(groups, key=lambda x: x[0])  # by width
    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\caption{Widths $\Gamma(T)$ (PDG 6000006) for \texttt{Tt} samples without $\kappa$, grouped by identical width.}")
    lines.append(r"\label{tab:TtNoKappaGrouped}")
    # Using p{0.65\linewidth} so long name lists fit; requires array package (usually available).
    lines.append(r"\begin{tabular}{lp{0.65\linewidth}}")
    lines.append(r"\toprule")
    lines.append(r"Width [GeV] & Samples \\")
    lines.append(r"\midrule")
    for width, names in groups:
        names = sorted(names, key=natural_key)
        # Join with commas, escape LaTeX specials
        pretty = ", ".join(latex_escape(n) for n in names)
        lines.append(f"{width:.6g} & {pretty} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    return "\n".join(lines)

def group_equal_widths(rows, rel_tol=1e-10, abs_tol=1e-12):
    """
    rows: list of (dirname, width) for non-kappa.
    Groups entries whose widths are equal within tolerance.
    Returns list of (width_representative, [names]).
    """
    clusters: list[tuple[float, list[str]]] = []
    for name, w in rows:
        placed = False
        for i, (w0, names) in enumerate(clusters):
            if isclose(w, w0, rel_tol=rel_tol, abs_tol=abs_tol):
                names.append(name)
                placed = True
                break
        if not placed:
            clusters.append((w, [name]))
    # sort names within clusters
    for i, (w0, names) in enumerate(clusters):
        clusters[i] = (w0, sorted(names, key=natural_key))
    return clusters

def main():
    # Collect
    kappa_by_mass: dict[int, list[tuple[float, float, str]]] = {}
    nokappa_rows: list[tuple[str, float]] = []

    for child in ROOT_DIR.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("Tt"):
            continue

        pc = find_param_card(child)
        if not pc:
            continue

        width = extract_width(pc)
        if width is None:
            continue

        kappa = parse_kappa_from_name(name)
        if kappa is not None:
            m = mass_from_name(name)
            if m is None:
                # if somehow mass can't be parsed, treat as non-kappa to avoid mislabelled tables
                nokappa_rows.append((name, width))
                continue
            kappa_by_mass.setdefault(m, []).append((kappa, width, name))
        else:
            nokappa_rows.append((name, width))

    # Build LaTeX
    parts = []
    parts.append(r"% Auto-generated by extract script. Requires \usepackage{booktabs} and (optionally) \usepackage{array}.")
    # Kappa tables per mass
    for mass in sorted(kappa_by_mass.keys()):
        table = make_kappa_table(kappa_by_mass[mass], mass)
        if table:
            parts.append(table)
            parts.append("")  # blank line

    # Non-kappa grouped table
    if nokappa_rows:
        groups = group_equal_widths(nokappa_rows)
        parts.append(make_nokappa_table(groups))

    tex = "\n".join(parts).strip() + "\n"
    OUTPUT_TEX.write_text(tex, encoding="utf-8")
    print(f"Wrote {OUTPUT_TEX} with {sum(len(v) for v in kappa_by_mass.values())} kappa entries "
          f"across {len(kappa_by_mass)} masses and {len(nokappa_rows)} non-kappa entries.")

if __name__ == "__main__":
    main()