# VLQ Single-T CLIC Reproduction Programs

This repository contains the programs and configuration needed to regenerate
the simulation outputs, reconstructed histograms, significance scans, and
figures used by the paper. It intentionally contains no LaTeX manuscript files,
generated plots, ROOT files, HEPMC/LHE events, or compiled binaries.

## Included Workflow

1. `generation/` contains the VLQ UFO model, campaign cards, benchmark widths,
   and a script that creates the MadGraph process template.
2. `manage_ase.py` configures mass, coupling, polarization, ISR, event count,
   MadSpin/Pythia execution, and HEPMC placement.
3. `Analysis_Programs/ttp_Analysis.cc` performs the HepMC reconstruction,
   boosted-top selection, recoil calculation, cutflow, and ROOT histogram
   production.
4. `Analysis_Programs/Histograms.py` normalizes signal/background samples and
   creates the ROOT canvases used by the paper plots.
5. `Analysis_Programs/kappa_vs_significance_3d_auto.py` builds the
   `(m_T, kappa_T)` counting-significance scans.
6. `plotting/` exports the signal overlay, baseline recoil spectrum, and
   baseline-versus-ISR/polarization comparisons.
7. `scripts/extract_widths.py` reconstructs the width table as CSV, while
   `scripts/run_paper_results.sh` generates all paper result figures.

## External Dependencies

- MadGraph5_aMC@NLO 3.5.x with MadSpin and Pythia 8
- ROOT with PyROOT, RooFit, RooStats, and TMVA
- HepMC 2
- FastJet with `fastjet-contrib`, including `JHTopTagger` and `ValenciaPlugin`
- A C++17 compiler and GNU Make

Large generated samples are not stored in Git. Set:

```bash
export ASE_MADGRAPH_ROOT=/path/to/MadgraphProcesses
export ASE_HEPMC_ROOT=/path/to/Hepmcs
export HEPMC_PREFIX=/path/to/hepmc2
```

Source ROOT and any FastJet/HepMC environment before building.

## Generation

Create the initial `Tt1200` MadGraph template:

```bash
python3 generation/create_process.py \
  --mg5 /path/to/MG5_aMC/bin/mg5_aMC \
  --output "$ASE_MADGRAPH_ROOT/Tt1200"
```

Then launch the interactive campaign manager:

```bash
python3 manage_ase.py
```

Generate the baseline, ISR plus `+80%` polarization, and kappa benchmark
campaigns used in the paper. `manage_ase.py` updates the top-partner width from
`generation/widths.csv` for every listed mass/coupling benchmark.

## Reconstruction

Build the analyzer:

```bash
make -C Analysis_Programs HEPMC_PREFIX="$HEPMC_PREFIX"
```

Each analysis directory must contain files named
`files/list_all_files_DATASET`, with one HEPMC path per line. Run all available
datasets and build histogram canvases with:

```bash
Analysis_Programs/smart_analysis.sh --histos
```

Expected analysis directory names include:

```text
ttp_Analysis
ttp_Analysis+80ISR
ttp_Analysis_kappa010 ... ttp_Analysis_kappa065
ttp_Analysis_kappa010+80ISR ... ttp_Analysis_kappa065+80ISR
```

## Paper Results

After reconstruction and histogram production:

```bash
scripts/run_paper_results.sh
```

This writes the signal recoil overlay, baseline recoil plot, four
baseline-versus-ISR comparison plots, and the baseline and `+80%` ISR kappa
scans under `results/paper/`.

Extract the generated widths independently with:

```bash
python3 scripts/extract_widths.py \
  --madgraph-root "$ASE_MADGRAPH_ROOT" \
  --output results/widths.csv
```
