#!/bin/bash

# Dispatch helper for kappa scans with P(e- ) = -80% and ISR.
# Each label kappaXYZ maps to its corresponding ttp_Analysis_kappaXYZ-80ISR directory.

if [ $1 == "kappa010" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa010-80ISR
elif [ $1 == "kappa015" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa015-80ISR
elif [ $1 == "kappa020" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa020-80ISR
elif [ $1 == "kappa025" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa025-80ISR
elif [ $1 == "kappa030" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa030-80ISR
elif [ $1 == "kappa035" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa035-80ISR
elif [ $1 == "kappa040" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa040-80ISR
elif [ $1 == "kappa045" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa045-80ISR
elif [ $1 == "kappa050" ]; then
    cd /home/higinio/Documentos/ASE/ttp_Analysis_kappa050-80ISR
else
    echo "invalid argument: $1"
    exit 1
fi

# If you need to (re)run the histogram builder inside these dirs, uncomment:
# source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh
# /bin/python "/home/higinio/Documentos/ASE/Analysis_Programs/Histograms.py"
