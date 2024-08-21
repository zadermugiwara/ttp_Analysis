// ***************************** //
// ***** General libraries ***** //
// ***************************** //

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <exception>
#include <ext/hash_map>
#include <fstream>
#include <iomanip>  
#include <iostream>
#include <list>
#include <math.h>
#include <map>
#include <random>
#include <sstream>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <string.h>
#include <vector>
#include <sstream>  // needed for internal io
#include <iomanip>  
  

// ************************ //
// ***** ROOT headers ***** //
// ************************ //

#include "TApplication.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TGClient.h"
#include "TH1F.h"
#include "TH1I.h"
#include "TH2.h"
#include "THStack.h"
//#include "TLorentzVector.h"
#include "TTree.h"

// *************************** //
// ***** FastJet headers ***** //
// *************************** //

//#include "fastjet/CDFJetCluPlugin.hh"
#include "fastjet/ClusterSequence.hh"
#include "fastjet/ClusterSequenceArea.hh"
#include "fastjet/PseudoJet.hh"
#include "fastjet/internal/BasicRandom.hh"
#include "fastjet/contrib/ValenciaPlugin.hh"
#include "fastjet/Selector.hh"
#include "fastjet/tools/JHTopTagger.hh"

using namespace fastjet;

// ************************* //
// ***** HepMC headers ***** //
// ************************* //

#include "HepMC/GenEvent.h"
#include "HepMC/GenVertex.h"
#include "HepMC/IO_GenEvent.h"
#include "HepMC/GenCrossSection.h"
using namespace HepMC;

// ************************** //
// ***** LHAPDF headers ***** //
// ************************** //

//#include "LHAPDF/GridPDF.h"
//#include "LHAPDF/LHAPDF.h"
//using namespace LHAPDF;

// ******************************** //
// ***** Multipurpose headers ***** //
// ******************************** //

using namespace std;                                         // ===== Symbols =====
using namespace fastjet;
#define vetoEvent {delete evt; ascii_in >> evt; continue;}   // ===== Define 'vetoEvent' =====
clock_t t0, tf;                                              // ===== Clock tic counts, to keep track of elapsed time =====
#include "plot_canvas.hh"                                    // ===== 1D plots on the fly, for debugging purposes ====
#include "plot_canvas2D.hh"                                  // ===== 2D plots on the fly, for debugging purposes =====
#include "utilities.hh"                                      // ===== User-defined functions =====
ostream & operator<<(ostream &, const PseudoJet &);


// ++++++++++++++++++++++++++++ //
// +++++ Analysis headers +++++ //
// ++++++++++++++++++++++++++++ //

#include "formalities.hh"                                    // ===== Formalities for analysis =====
#include "hadrons_classes.hh"                                // ===== Classes defining B- and C-hadrons =====
#include "isolated_leptons.hh"                               // ===== Lepton isolation =====
#include "particles_classes.hh"                              // ===== Classes defining particles =====
