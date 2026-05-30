# Revision Status

## Completed

- Created `JHEP_Revised/` as the only active manuscript revision folder.
- Copied the reviewed PDF into the revision package as `reviewed_source.pdf`.
- Imported current figures and scan CSVs into `figs/` and `data/`.
- Added `build_revision_tables.py` so manuscript tables are generated from CSV
  and width inputs rather than manual numbers.
- Rewrote the manuscript around a defensible two-level interpretation:
  idealized recoil proof-of-concept plus ISR/polarization stress tests.
- Added a reproducibility table, background-status table, width-validity table,
  systematic counting cross-checks, related-work comparison, and response
  matrix.
- Updated `Analysis_Programs/ttp_Analysis.cc` so the nominal object fiducial
  acceptance defaults to `|eta| < 2.5`.
- Fixed `vlq_recoil_discovery.py` so the default asymptotic result comes from a
  manual binned profile-likelihood closure instead of the local RooStats path
  that returned `p0 = 0.5`; RooStats can still be run explicitly as a diagnostic.
- Added systematic counting cross-check options to `vlq_recoil_discovery.py`.
- Standardized ISR MadGraph/Pythia card metadata on the Expansion-drive samples:
  missing lepton QED shower settings were added, and stale copied `output`
  labels in ISR `proc_card_mg5.dat` files were repaired.
- Added tools for MG5 ISR-only command generation, `sqrt(s')` LHE diagnostics,
  macOS `IntxLNK` symlink repair in copied MG5 projects, and a local
  Herwig-based `gamma gamma -> hadrons` overlay stress-test library.
- Ran the `sqrt(s')` diagnostic over four 1.2 TeV samples with 1,000,000 events
  each: baseline, `clic3000ll` ISR, `+80% clic3000ll`, and `-80% clic3000ll`.
- Implemented optional `gamma gamma -> hadrons` overlay in
  `Analysis_Programs/ttp_Analysis.cc`; a 10-event hard-sample smoke test with
  one overlay event per hard event completed.
- Completed the full ISR-only `isronlyll_nev10000` MG5 production set on the
  Expansion drive: 24/24 command files returned valid outputs.  The production
  manifest, MG5 cross-section summary, reconstruction cutflows, and `sqrt(s')`
  summary are in `JHEP_Revised/logs/` and
  `JHEP_Revised/data/sqrt_s_prime_isronlyll_nev10000/`.
- Reconstructed all 24 ISR-only production samples with the nominal FastJet
  analysis and with one `gamma gamma -> hadrons` overlay event per hard event:
  48/48 reconstruction jobs completed.
- Full 24-sample CLIC luminosity-spectrum production was completed on
  2026-05-29 using fresh project directories under
  `/media/higinio/Expansion1/MadgraphFresh`.
- The fresh full-statistics CLIC queue completed 24/24 MG5 jobs:
  `JHEP_Revised/logs/mg5_queue_clic3000ll_fresh_status.csv`.  All 24 samples
  have hard LHE, decayed LHE, compressed HepMC, and decompressed HepMC outputs;
  the manifest is `JHEP_Revised/logs/production_manifest_clic3000ll_fresh.csv`.
- The full fresh CLIC `sqrt(s')` diagnostic completed for all 24 samples:
  `JHEP_Revised/data/sqrt_s_prime_clic3000ll_fresh_nev10000/sqrt_s_prime_summary.csv`.
- FastJet reconstruction completed for the fresh CLIC set in clean and one-BX
  `gamma gamma -> hadrons` overlay modes: both reconstruction queues are 24/24
  `ok`.  Cutflow CSVs were written to
  `JHEP_Revised/logs/reconstruction_cutflows_clic3000ll_fresh.csv` and
  `JHEP_Revised/logs/reconstruction_cutflows_clic3000ll_fresh_overlay.csv`.
- Added `tools/build_fresh_clic_results.py`, which generates fresh CLIC
  reach, overlay-impact, ISR-comparison, and `sqrt(s')` manuscript tables from
  the completed CSV outputs.
- Ran the binned profile-likelihood closure for the four unpolarized fresh CLIC
  mass points using mass-matched BDT recoil histograms rebinned to
  `100 GeV`.  The summary is
  `JHEP_Revised/validation/profile_clic_unpol_rebin100_summary.csv`.
- Rebuilt `JHEP_Revised/main.pdf` with the fresh CLIC luminosity-spectrum,
  overlay, profile-closure, and comparison tables included.
- Added resumable queue/manifest helpers:
  `tools/run_mg5_queue.py`, `tools/build_production_manifests.py`,
  `tools/run_reconstruction_queue.py`, and
  `tools/run_sqrt_s_prime_from_manifest.py`.

## Not Completed By Current Local Inputs

- No GEANT4/CLICdet full simulation was available.
- Delphes/WHIZARD/CLIC beam-spectrum production was not available on PATH during
  this revision pass.
- The old reused MG5 project directories on the Expansion NTFS volume remain
  suspect because of the earlier I/O failures and corrupted `results.dat`
  entries.  The successful production used fresh project directories under
  `/media/higinio/Expansion1/MadgraphFresh`; future reruns should continue to
  use fresh directories rather than relaunching the damaged old projects.
- New forced-decay, high-priority missing-background, and
  finite-width/interference samples still need production.
- Existing legacy plots still come from the reviewed `|eta| < 5` samples and are
  labeled as such in the manuscript.

## Acceptance State

The manuscript now answers the reviewer questions in text, tables, or appendix
items, but it intentionally does not claim final CLIC-realistic discovery reach
until the missing production tasks above are complete.
