#!/bin/bash

source /home/higinio/Documentos/ASE/HERWIG/bin/activate
source /home/higinio/Documentos/ASE/Analysis/root/root-new/bin/thisroot.sh

if [ $1 == "Tt1M" ]
then
    [ -f Makefile ] && make
    ./ttp_Analysis Tt1M1200
    ./ttp_Analysis Tt1M1600
    ./ttp_Analysis Tt1M2000
    ./ttp_Analysis Tt1M2400
    source /home/higinio/Documentos/ASE/Analysis/root/root-new/bin/thisroot.sh
    python3.11 /home/higinio/Documentos/ASE/ttp_Analysis/Histograms.py $1
    root -l -q full_analysis_with_plot.C+
elif [ $1 == "ttbarra" ]
then
    [ -f Makefile ] && make
    ./ttp_Analysis ttbarra
elif [ $1 == "bkgsm" ]
then
    [ -f Makefile ] && make
    ./ttp_Analysis w+w-veve
    ./ttp_Analysis ttveve
    ./ttp_Analysis ttz
    ./ttp_Analysis w+w-z
    ./ttp_Analysis tth
    ./ttp_Analysis w+w-
    ./ttp_Analysis hveve
    ./ttp_Analysis zz
    ./ttp_Analysis hz

elif [ $1 == "Tt100kkappa01" ]
then
    [ -f Makefile ] && make
    ./ttp_Analysis Tt100kkappa011200
    ./ttp_Analysis Tt100kkappa011600
    ./ttp_Analysis Tt100kkappa012000
    ./ttp_Analysis Tt100kkappa012400

elif [ $1 == "Tt100kkappa03" ]
then
    [ -f Makefile ] && make
    ./ttp_Analysis Tt100kkappa031200
    ./ttp_Analysis Tt100kkappa031600
    ./ttp_Analysis Tt100kkappa032000
    ./ttp_Analysis Tt100kkappa032400


else
    echo "invalid argument"

fi
