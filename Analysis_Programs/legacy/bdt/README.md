# Legacy BDT implementation

This directory preserves the TMVA reader configuration from an earlier BDT-based
analysis. It is intentionally excluded from the current recoil-only analysis and
from the paper-reproduction workflow.

The current paper does not use BDT selections or BDT histograms. The original
TMVA weight XML files are not distributed in this repository, so the archived
configuration is not runnable by itself.

For a future exclusive-decay study, such as `T -> t Z`, reuse this file only
after providing newly trained weight files, documenting their inputs and
training samples, and reintegrating the BDT evaluation deliberately into a
separate analysis path. The removal of the old runtime code is recorded in the
repository history.
