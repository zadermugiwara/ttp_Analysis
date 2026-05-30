//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Wed Jan 17 11:24:08 2024 by ROOT version 6.30/02
// from TTree truth/truth
// found on file: truth.root
//////////////////////////////////////////////////////////

#ifndef TRUTH_h
#define TRUTH_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TRef.h>
#include <TRefArray.h>
#include <TLorentzVector.h>

// Header file for the classes stored in the TTree if any.
#include "TClonesArray.h"
#include "TObject.h"
#include "TRefArray.h"
#include "TLorentzVector.h"

#include "TVectorD.h"
#include "TMath.h"

#include "Math/Point3D.h"
#include "Math/Vector3D.h"
#include "Math/Vector4D.h"
#include "Math/GenVector/Rotation3D.h"
#include "Math/GenVector/EulerAngles.h"
#include "Math/GenVector/AxisAngle.h"
#include "Math/GenVector/Quaternion.h"
#include "Math/GenVector/RotationX.h"
#include "Math/GenVector/RotationY.h"
#include "Math/GenVector/RotationZ.h"
#include "Math/GenVector/RotationZYX.h"
#include "Math/GenVector/LorentzRotation.h"
#include "Math/GenVector/Boost.h"
#include "Math/GenVector/BoostX.h"
#include "Math/GenVector/BoostY.h"
#include "Math/GenVector/BoostZ.h"
#include "Math/GenVector/Transform3D.h"
#include "Math/GenVector/Plane3D.h"
#include "Math/GenVector/VectorUtil.h"

// Header file for the classes stored in the TTree if any.

class TRUTH {
public :
   TTree          *fChain;   //!pointer to the analyzed TTree or TChain
   Int_t           fCurrent; //!current Tree number in a TChain

// Fixed size dimensions of array or collections stored in the TTree if any.

   // Declaration of leaf types
   Int_t           numpart;
   Double_t        noevent[14];
   Double_t        pdgid[14];
   Double_t        px[14];
   Double_t        py[14];
   Double_t        pz[14];
   Double_t        energy[14];
   Double_t        mass[14];
   Double_t        M1[14];
   Double_t        D1[14];

   // List of branches
   TBranch        *b_numpart;   //!
   TBranch        *b_noevent;   //!
   TBranch        *b_pdgid;   //!
   TBranch        *b_px;   //!
   TBranch        *b_py;   //!
   TBranch        *b_pz;   //!
   TBranch        *b_energy;   //!
   TBranch        *b_mass;   //!
   TBranch        *b_M1;   //!
   TBranch        *b_D1;   //!

   TRUTH(TTree *tree=0);
   virtual ~TRUTH();
   virtual Int_t    Cut(Long64_t entry);
   virtual Int_t    GetEntry(Long64_t entry);
   virtual Long64_t LoadTree(Long64_t entry);
   virtual void     Init(TTree *tree);
   virtual void     Loop();
   virtual Bool_t   Notify();
   virtual void     Show(Long64_t entry = -1);
};

#endif

#ifdef TRUTH_cxx
TRUTH::TRUTH(TTree *tree) : fChain(0) 
{
// if parameter tree is not specified (or zero), connect the file
// used to generate this class and read the Tree.
   if (tree == 0) {
      TFile *f = (TFile*)gROOT->GetListOfFiles()->FindObject("truth.root");
      if (!f || !f->IsOpen()) {
         f = new TFile("truth.root");
      }
      f->GetObject("truth",tree);

   }
   Init(tree);
}

TRUTH::~TRUTH()
{
   if (!fChain) return;
   delete fChain->GetCurrentFile();
}

Int_t TRUTH::GetEntry(Long64_t entry)
{
// Read contents of entry.
   if (!fChain) return 0;
   return fChain->GetEntry(entry);
}
Long64_t TRUTH::LoadTree(Long64_t entry)
{
// Set the environment to read one entry
   if (!fChain) return -5;
   Long64_t centry = fChain->LoadTree(entry);
   if (centry < 0) return centry;
   if (fChain->GetTreeNumber() != fCurrent) {
      fCurrent = fChain->GetTreeNumber();
      Notify();
   }
   return centry;
}

void TRUTH::Init(TTree *tree)
{
   // The Init() function is called when the selector needs to initialize
   // a new tree or chain. Typically here the branch addresses and branch
   // pointers of the tree will be set.
   // It is normally not necessary to make changes to the generated
   // code, but the routine can be extended by the user if needed.
   // Init() will be called many times when running on PROOF
   // (once per file to be processed).

   // Set branch addresses and branch pointers
   if (!tree) return;
   fChain = tree;
   fCurrent = -1;
   fChain->SetMakeClass(1);

   fChain->SetBranchAddress("numpart", &numpart, &b_numpart);
   fChain->SetBranchAddress("noevent", noevent, &b_noevent);
   fChain->SetBranchAddress("pdgid", pdgid, &b_pdgid);
   fChain->SetBranchAddress("px", px, &b_px);
   fChain->SetBranchAddress("py", py, &b_py);
   fChain->SetBranchAddress("pz", pz, &b_pz);
   fChain->SetBranchAddress("energy", energy, &b_energy);
   fChain->SetBranchAddress("mass", mass, &b_mass);
   fChain->SetBranchAddress("M1", M1, &b_M1);
   fChain->SetBranchAddress("D1", D1, &b_D1);
   Notify();
}

Bool_t TRUTH::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}

void TRUTH::Show(Long64_t entry)
{
// Print contents of entry.
// If entry is not specified, print current entry
   if (!fChain) return;
   fChain->Show(entry);
}
Int_t TRUTH::Cut(Long64_t entry)
{
// This function may be called from Loop.
// returns  1 if entry is accepted.
// returns -1 otherwise.
   return 1;
}
#endif // #ifdef TRUTH_cxx
