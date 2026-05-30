# ASE Analysis Repository

This repository contains the source code, analysis scripts, configuration files,
and manuscript material for the VLQ single-T CLIC analysis workflow.

The GitHub snapshot intentionally excludes generated event samples, ROOT files,
compiled binaries, local toolchain installs, logs, caches, and scratch outputs.
Those artifacts should be regenerated locally from the scripts and configuration
kept here.

## Main Folders

- `Analysis_Programs/`: C++/ROOT analysis code, headers, shell helpers, and
  Python utilities.
- `JHEP_Revised/`: active revision package, production tools, tables,
  manuscript source, and lightweight derived CSV inputs.
- `Paper/` and `VLQ_SingleT_CLIC_Paper/`: earlier manuscript/reference material.
- `ttp_Analysis*/`: analysis variants with source files and input list
  manifests, without generated ROOT outputs.
