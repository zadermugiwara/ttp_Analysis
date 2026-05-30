# Production Notes

## Completed In This Pass

- `python3 tools/audit_madgraph_isr.py --fix`
  - Added missing explicit lepton QED shower settings to ISR Pythia cards.
  - Repaired stale copied `output ...` labels in ISR `proc_card_mg5.dat` files.
  - Manifest: `logs/madgraph_isr_card_audit.csv`.

- `python3 tools/sqrt_s_prime_analysis.py --write-events`
  - Processed 1,000,000 events each for:
    - `Tt1200_baseline`
    - `Tt1200_ISR_clic3000ll`
    - `Tt1200_plus80_ISR_clic3000ll`
    - `Tt1200_minus80_ISR_clic3000ll` using `run_02`.
  - Summary: `data/sqrt_s_prime/sqrt_s_prime_summary.csv`.
  - Per-event diagnostics are compressed as
    `data/sqrt_s_prime/sqrt_s_prime_events.csv.gz`.
  - Figures: `figs/sqrt_s_prime/*.svg`.

- `NEVENTS=1000 tools/run_gamma_gamma_overlay.sh`
  - Produced a local Herwig stress-test overlay library:
    `data/overlay/gamma_gamma_hadrons_3tev.hepmc`.
  - Produced overlay list:
    `data/overlay/gamma_gamma_overlay_files.txt`.

- Overlay smoke test:
  - Built `Analysis_Programs/ttp_Analysis` with optional overlay support.
  - Ran a 10-event hard-sample test with
    `ASE_GG_OVERLAY_BX=1`.

## Blocker

The first MG5 ISR-only pilot was launched with:

```bash
/home/higinio/Documentos/ASE/HERWIG/opt/MG5_aMC_v3_5_1/bin/mg5_aMC \
  JHEP_Revised/config/madgraph_runs/Tt1200ISR_isronlyll_nev1000.mg5
```

The copied MadGraph directory first needed repair of macOS `IntxLNK`
placeholder files:

```bash
python3 tools/repair_madgraph_intxlnk.py /media/higinio/Expansion1/Madgraph/Tt1200ISR --fix
```

After this repair, MG5 completed the parton-level survey/refine/generation for
1,000 events and reported:

```text
Cross-section : 0.0002533 +- 1.453e-06 pb
Nb of events  : 1000
```

MadSpin then failed with `/dev/sda2` I/O errors.  The kernel subsequently
reported:

```text
ntfs3: sda2: volume is dirty and "force" flag is not set
```

`udisksctl mount -b /dev/sda2` therefore refused to remount the Expansion drive.
Run filesystem repair/checking outside this production workflow before
continuing full MG5 generation.

The drive was later remounted read-only with:

```bash
udisksctl mount -b /dev/sda2 -o ro
```

This is sufficient for inspection and copying inputs, but not for production
runs that write back into `/media/higinio/Expansion1`.

## Local ISR-Only Pilot

To continue without writing to the dirty NTFS volume, a lean copy of
`Tt1200ISR` was made under local scratch:

```bash
rsync -a --delete --exclude Events --exclude HTML \
  /media/higinio/Expansion1/Madgraph/Tt1200ISR/ \
  JHEP_Revised/scratch/Tt1200ISR_local/
mkdir -p JHEP_Revised/scratch/Tt1200ISR_local/Events \
         JHEP_Revised/scratch/Tt1200ISR_local/HTML
```

The local ISR-only pilot then completed through MadSpin and Pythia8:

```bash
/home/higinio/Documentos/ASE/HERWIG/opt/MG5_aMC_v3_5_1/bin/mg5_aMC \
  JHEP_Revised/config/madgraph_runs/Tt1200ISR_local_isronlyll_nev1000.mg5
```

Parton-level result:

```text
Cross-section : 0.0002528 +- 7.726e-07 pb
Nb of events  : 1000
```

Main outputs:

- `scratch/Tt1200ISR_local/Events/isronlyll_nev1000_decayed_1/unweighted_events.lhe.gz`
- `scratch/Tt1200ISR_local/Events/isronlyll_nev1000_decayed_1/tag_1_pythia8_events.hepmc.gz`
- `data/isronlyll_local/Tt1200ISRonly_nev1000.hepmc`
- `data/sqrt_s_prime_isronlyll_local_decayed/sqrt_s_prime_summary.csv`

The 1000-event reconstructed cutflow was run both without overlay and with one
local `gamma gamma -> hadrons` overlay event per hard event.  The CSV summary is:

```text
data/isronlyll_local/cutflow_Tt1200ISRonly_nev1000.csv
```

## Resume Commands After Drive Repair

Repair all copied ISR projects if needed:

```bash
python3 JHEP_Revised/tools/repair_madgraph_intxlnk.py --all-isr --fix
```

Generate full ISR-only command files:

```bash
python3 JHEP_Revised/tools/write_mg5_beam_configs.py --scenario isronlyll --nevents 10000
```

Run the command files, for example:

```bash
/home/higinio/Documentos/ASE/HERWIG/opt/MG5_aMC_v3_5_1/bin/mg5_aMC \
  JHEP_Revised/config/madgraph_runs/Tt1200ISR_isronlyll_nev10000.mg5
```
