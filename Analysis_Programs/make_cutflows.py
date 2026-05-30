#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_cutflows_all.py  (efficiencies OFF by default)

- Reads ALL *.dat in --basedir (default: CWD).
- If a file has multiple cutflow blocks, keeps exactly one
  (default policy: 'longest'; override with --block-policy first or --block-index N).
- Builds one LaTeX table per dataset, no efficiencies unless you pass --eff/--cumeff.

No jinja2 required.
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd

# ----------- Parsing helpers -----------

LINE_RE = re.compile(r'^\s*(\d+)\s+(.*?)\s+(\d+)\s+([0-9]+(?:\.[0-9]+)?)\s*$')

def parse_rows_in_order(text: str) -> List[Tuple[int,str,int,float]]:
    rows = []
    for raw in text.splitlines():
        m = LINE_RE.match(raw.replace('\t', ' '))
        if m:
            step = int(m.group(1))
            name = m.group(2).strip()
            events = int(m.group(3))
            yld = float(m.group(4))
            rows.append((step, name, events, yld))
    return rows

def split_into_blocks(rows: List[Tuple[int,str,int,float]]) -> List[pd.DataFrame]:
    """Split into blocks when step index resets or a new '0' appears after data."""
    blocks = []
    cur = []
    prev_step: Optional[int] = None
    for step, name, events, yld in rows:
        if prev_step is not None and (step < prev_step or (step == 0 and cur)):
            if cur:
                blocks.append(cur)
            cur = []
        cur.append((step, name, events, yld))
        prev_step = step
    if cur:
        blocks.append(cur)
    dfs = []
    for b in blocks:
        df = pd.DataFrame(b, columns=["Step","Cut","Events","Yield"]).sort_values("Step")
        dfs.append(df)
    return dfs

def parse_cutflow_file(path: Path,
                       block_policy: str = "longest",
                       block_index: Optional[int] = None):
    text = path.read_text(errors='ignore')
    rows = parse_rows_in_order(text)
    if not rows:
        return pd.DataFrame(), None, None, -1
    blocks = split_into_blocks(rows)

    # Choose one block
    if block_index is not None and 0 <= block_index < len(blocks):
        chosen = block_index
    elif block_policy == "first":
        chosen = 0
    else:  # longest
        lengths = [len(df) for df in blocks]
        chosen = int(np.argmax(lengths))

    df = blocks[chosen]

    # Metadata (optional)
    m_ev = re.search(r'Total events analysed:\s*([0-9]+)', text)
    m_xs = re.search(r'Total cross section \[pb\]:\s*([0-9.Ee+\-]+)', text)
    total_events = int(m_ev.group(1)) if m_ev else None
    total_xs = float(m_xs.group(1)) if m_xs else None

    return df, total_events, total_xs, chosen

def add_efficiencies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    e0 = float(out["Events"].iloc[0])
    prev = out["Events"].shift(1).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["StepEff"] = np.where(prev > 0, out["Events"].astype(float) / prev, np.nan)
        out["CumEff"]  = np.where(e0 > 0, out["Events"].astype(float) / e0, np.nan)
    return out

# ----------- LaTeX builders -----------

def _esc(s: str) -> str:
    return (s.replace('\\', r'\textbackslash ')
             .replace('_', r'\_')
             .replace('{', r'\{').replace('}', r'\}')
             .replace('%', r'\%').replace('&', r'\&'))

def df_to_tabular(df: pd.DataFrame, include_eff: bool, include_cumeff: bool) -> str:
    cols = ["Step","Cut","Events","Yield"]
    if include_eff and "StepEff" in df.columns: cols.append("StepEff")
    if include_cumeff and "CumEff" in df.columns: cols.append("CumEff")
    aligns = ["r" if c != "Cut" else "l" for c in cols]
    header = " & ".join(_esc(c) for c in cols) + r" \\"

    lines = []
    for _, row in df[cols].iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if c == "Cut":
                vals.append(_esc(str(v)))
            elif c == "Events":
                vals.append(f"{int(v):,}".replace(",", r"\,"))
            elif c in ("Yield","StepEff","CumEff"):
                if pd.isna(v) or np.isinf(v):
                    vals.append("-")
                else:
                    vals.append(f"{float(v):.3f}")
            else:
                vals.append(str(v))
        lines.append(" & ".join(vals) + r" \\")
    body = "\n".join(lines)

    return (
        r"\begin{tabular}{" + " ".join(aligns) + "}" + "\n"
        r"\toprule" + "\n" +
        header + "\n" +
        r"\midrule" + "\n" +
        body + "\n" +
        r"\bottomrule" + "\n" +
        r"\end{tabular}"
    )

def one_table(df: pd.DataFrame, name: str,
              total_events: Optional[int], total_xs: Optional[float],
              chosen_block: int,
              include_eff: bool, include_cumeff: bool) -> str:
    disp = _esc(name)
    xs_txt = f"{total_xs:.6g}" if total_xs is not None else "N/A"
    ev_txt = total_events if total_events is not None else (int(df['Events'].iloc[0]) if not df.empty else "N/A")
    label = "tab:cutflow-" + re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-')
    tabular = df_to_tabular(df, include_eff, include_cumeff)
    return (
        r"\begin{table}[H]" "\n"
        r"\centering" "\n" +
        tabular + "\n" +
        rf"\caption{{Cutflow for \texttt{{{disp}}} (block {chosen_block}). Total events analysed: {ev_txt}. Total cross section: {xs_txt}\,pb.}}" "\n" +
        rf"\label{{{label}}}" "\n"
        r"\end{table}" "\n"
    )

# ----------- Main -----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basedir", type=str, default=str(Path.cwd()), help="Directory to scan (default: CWD)")
    ap.add_argument("--recursive", action="store_true", help="Scan subdirectories recursively")
    ap.add_argument("--out", type=str, default=str(Path.cwd() / "cutflows_all.tex"), help="Output .tex file")

    ap.add_argument("--block-policy", choices=["first","longest"], default="longest",
                    help="When a file has multiple cutflows, which one to keep (default: longest)")
    ap.add_argument("--block-index", type=int, default=None,
                    help="Explicit block index (0-based) to keep; overrides --block-policy if set")

    # NEW: efficiencies are OFF by default; opt-in with these flags
    ap.add_argument("--eff", action="store_true", help="Include per-step efficiency column")
    ap.add_argument("--cumeff", action="store_true", help="Include cumulative efficiency column")

    args = ap.parse_args()

    base = Path(args.basedir)
    files = (sorted(base.rglob("*.dat")) if args.recursive else sorted(base.glob("*.dat")))
    if not files:
        raise SystemExit(f"No .dat files found in {base} (use --recursive if needed).")

    preamble = r"""\documentclass{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{array}
\usepackage{amsmath}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\sisetup{detect-all}
\begin{document}
\section*{Cutflow Tables (one block per file)}
"""
    tables = []
    for p in files:
        df, tot_ev, tot_xs, chosen_block = parse_cutflow_file(
            p, block_policy=args.block_policy, block_index=args.block_index
        )
        if df.empty:
            continue

        # Only compute efficiencies if any efficiency column is requested
        if args.eff or args.cumeff:
            df = add_efficiencies(df)

        table = one_table(
            df, p.name, tot_ev, tot_xs, chosen_block,
            include_eff=args.eff,
            include_cumeff=args.cumeff
        )
        tables.append(table)

    tex = preamble + "\n".join(tables) + "\n\\end{document}\n"
    out_path = Path(args.out)
    out_path.write_text(tex)
    print(f"Wrote LaTeX to: {out_path.resolve()}")
    print(f"Processed {len(tables)} files.")

if __name__ == "__main__":
    main()
