#!/bin/bash

herwig
./ttp_Analysis $1
source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh
/bin/python3 /home/higinio/Documentos/ASE/ttp_Analysis/Histograms.py $1