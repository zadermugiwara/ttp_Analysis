# JHEP Revised Package

This folder is the active revision package for the reviewer-driven manuscript
update.  The reviewed PDF is copied here as `reviewed_source.pdf`; older drafts
under `Paper/` and `VLQ_SingleT_CLIC_Paper/` are references only.

## Build

Regenerate derived tables from the copied CSV and width inputs:

```bash
python3 build_revision_tables.py
python3 tools/build_fresh_clic_results.py
```

Build the manuscript:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The expected output is `main.pdf`.

The complete production and analysis workflow is documented in
`workflow.tex`.  Build it with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error workflow.tex
```

## Beam and Overlay Production Tools

Audit and repair existing Expansion-drive ISR cards:

```bash
python3 tools/audit_madgraph_isr.py --fix
python3 tools/repair_madgraph_intxlnk.py --all-isr --fix
```

Generate MG5 command files for ISR-only reruns:

```bash
python3 tools/write_mg5_beam_configs.py --scenario isronlyll --nevents 10000
```

Generate the corresponding CLIC luminosity-spectrum/beamstrahlung command
files:

```bash
python3 tools/write_mg5_beam_configs.py --scenario clic3000ll --nevents 10000
```

For production on the Expansion drive, prefer fresh project directories rather
than relaunching the previously damaged MG5 projects in place:

```bash
python3 tools/prepare_fresh_mg5_projects.py \
  --scenario clic3000ll \
  --nevents 10000 \
  --overwrite
```

Run a resumable MG5 queue with a scenario-specific status file:

```bash
python3 tools/run_mg5_queue.py \
  --glob 'JHEP_Revised/config/madgraph_runs/*_clic3000ll_nev10000.mg5' \
  --rerun-failed \
  --status JHEP_Revised/logs/mg5_queue_clic3000ll_status.csv \
  --log-dir JHEP_Revised/logs/mg5_queue_clic3000ll
```

Fresh-project CLIC production was run with:

```bash
python3 tools/run_mg5_queue.py \
  --glob 'JHEP_Revised/config/madgraph_runs_fresh/*_clic3000ll_nev10000_fresh.mg5' \
  --rerun-failed \
  --require-path /media/higinio/Expansion1/MadgraphFresh \
  --status JHEP_Revised/logs/mg5_queue_clic3000ll_fresh_status.csv \
  --log-dir JHEP_Revised/logs/mg5_queue_clic3000ll_fresh
```

For cautious single-job retries after repairing the external volume, pass one
command file explicitly and require the mounted MG5 path:

```bash
python3 tools/run_mg5_queue.py \
  JHEP_Revised/config/madgraph_runs/Tt1200ISR_clic3000ll_nev10000.mg5 \
  --rerun-failed \
  --require-path /media/higinio/Expansion1/Madgraph \
  --status JHEP_Revised/logs/mg5_queue_clic3000ll_status.csv \
  --log-dir JHEP_Revised/logs/mg5_queue_clic3000ll
```

Run the truth-level luminosity-spectrum diagnostic:

```bash
python3 tools/sqrt_s_prime_analysis.py
```

After MG5 production, run the same diagnostic from the production manifest:

```bash
python3 tools/run_sqrt_s_prime_from_manifest.py
```

Build list files and an auditable manifest from completed MG5 queue jobs:

```bash
python3 tools/build_production_manifests.py --require-ok --decompress-hepmc
```

For the fresh CLIC production:

```bash
python3 tools/build_production_manifests.py \
  --status JHEP_Revised/logs/mg5_queue_clic3000ll_fresh_status.csv \
  --manifest JHEP_Revised/logs/production_manifest_clic3000ll_fresh.csv \
  --require-ok \
  --decompress-hepmc
```

Run the FastJet reconstruction over the manifest:

```bash
python3 tools/run_reconstruction_queue.py
```

Build a local `gamma gamma -> hadrons` overlay stress-test library:

```bash
NEVENTS=1000 tools/run_gamma_gamma_overlay.sh
```

Apply overlay during reconstruction by setting:

```bash
export ASE_GG_OVERLAY_LIST="$PWD/data/overlay/gamma_gamma_overlay_files.txt"
export ASE_GG_OVERLAY_BX=1
```

or run the reconstruction queue with a separate output suffix:

```bash
python3 tools/run_reconstruction_queue.py --overlay-bx 1
```

Fresh CLIC reconstruction was run with:

```bash
python3 tools/run_reconstruction_queue.py \
  --manifest JHEP_Revised/logs/production_manifest_clic3000ll_fresh.csv \
  --status JHEP_Revised/logs/reconstruction_queue_clic3000ll_fresh_status.csv \
  --log-dir JHEP_Revised/logs/reconstruction_queue_clic3000ll_fresh

python3 tools/run_reconstruction_queue.py \
  --manifest JHEP_Revised/logs/production_manifest_clic3000ll_fresh.csv \
  --status JHEP_Revised/logs/reconstruction_queue_clic3000ll_fresh_overlay_status.csv \
  --log-dir JHEP_Revised/logs/reconstruction_queue_clic3000ll_fresh_overlay \
  --overlay-bx 1
```

## Current Scope

Implemented in this package:

- Unsupported “fully simulated” wording is removed.
- The detector treatment is stated as custom FastJet-based reconstruction, not
  GEANT4/CLICdet full simulation.
- Object definitions, recoil selection, missing-energy selection, and the
  isolation-veto logic are documented.
- The width interpretation is restricted to `Gamma_T / m_T <= 10%`.
- Existing baseline, ISR `+80%`, and ISR `-80%` CSVs are imported into
  generated yield/significance tables.
- The existing MG5 ISR cards on the Expansion drive have been standardized for
  lepton QED shower settings, and copied-process `output` labels have been
  repaired in the card metadata.
- A truth-level `sqrt(s')` diagnostic from LHE incoming particles has been run
  for the 1.2 TeV baseline, ISR, ISR `+80%`, and ISR `-80%` samples.
- The full ISR-only `isronlyll_nev10000` production completed for 24 samples
  and was reconstructed in clean and one-BX gamma-gamma-overlay modes.
- The full fresh CLIC luminosity-spectrum `clic3000ll_nev10000_fresh`
  production completed for 24 samples and was reconstructed in clean and
  one-BX gamma-gamma-overlay modes.
- Fresh CLIC reach, overlay-impact, ISR-comparison, and `sqrt(s')` manuscript
  tables are generated from CSV outputs by `tools/build_fresh_clic_results.py`.
- Binned profile-likelihood closure was run for the four unpolarized fresh CLIC
  benchmarks with `100 GeV` recoil bins; the summary CSV is
  `validation/profile_clic_unpol_rebin100_summary.csv`.
- Optional `gamma gamma -> hadrons` overlay support is implemented in
  `Analysis_Programs/ttp_Analysis.cc` through `ASE_GG_OVERLAY_*` environment
  variables.
- The profile-likelihood validation uses a manual binned Asimov closure by
  default; `--run-roostats-asymptotic` keeps the RooStats path as a diagnostic.
- The reviewer-response matrix is part of the manuscript appendix.

Still required before a final JHEP reach claim:

- Continue using fresh Expansion project directories for MG5 production.  The
  old reused projects under `/media/higinio/Expansion1/Madgraph` remain suspect
  after the earlier NTFS/I/O failures.
- Rerun the analysis with the nominal `|eta| < 2.5` object acceptance.
- Include or bound W-fusion single top and high-mass `V+jets` backgrounds.
- Replace truth b-subjet matching with calibrated b-tag efficiency/mistag
  assumptions.
- Produce forced-decay validation samples for `T -> Wb`, `T -> Zt`, and
  `T -> Ht`.
- Run at least one full-matrix-element finite-width/interference stress test
  near `Gamma_T / m_T = 10%`.
