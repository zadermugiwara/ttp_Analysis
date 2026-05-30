//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Thu Feb  2 11:11:38 2023 by ROOT version 6.26/10
// from TTree VLQ100k/VLQ100k
// found on file: VLQ100k.root
//////////////////////////////////////////////////////////

#ifndef VLQ100k_h
#define VLQ100k_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>

// Header file for the classes stored in the TTree if any.

class VLQ100k {
public :
   TTree          *fChain;   //!pointer to the analyzed TTree or TChain
   Int_t           fCurrent; //!current Tree number in a TChain

// Fixed size dimensions of array or collections stored in the TTree if any.

   // Declaration of leaf types
   Int_t           numpart;
   Double_t        noevent;
   Double_t        pdgid;
   Double_t        px;
   Double_t        py;
   Double_t        pz;
   Double_t        energy;
   Double_t        mass;
   Double_t        M1;
   Double_t        D1;

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

   VLQ100k(TTree *tree=0);
   virtual ~VLQ100k();
   virtual Int_t    Cut(Long64_t entry);
   virtual Int_t    GetEntry(Long64_t entry);
   virtual Long64_t LoadTree(Long64_t entry);
   virtual void     Init(TTree *tree);
   virtual void     Loop();
   virtual Bool_t   Notify();
   virtual void     Show(Long64_t entry = -1);
};

#endif

#ifdef VLQ100k_cxx
VLQ100k::VLQ100k(TTree *tree) : fChain(0) 
{
// if parameter tree is not specified (or zero), connect the file
// used to generate this class and read the Tree.
   if (tree == 0) {
      TFile *f = (TFile*)gROOT->GetListOfFiles()->FindObject("VLQ100k.root");
      if (!f || !f->IsOpen()) {
         f = new TFile("VLQ100k.root");
      }
      f->GetObject("VLQ100k",tree);

   }
   Init(tree);
}

VLQ100k::~VLQ100k()
{
   if (!fChain) return;
   delete fChain->GetCurrentFile();
}

Int_t VLQ100k::GetEntry(Long64_t entry)
{
// Read contents of entry.
   if (!fChain) return 0;
   return fChain->GetEntry(entry);
}
Long64_t VLQ100k::LoadTree(Long64_t entry)
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

void VLQ100k::Init(TTree *tree)
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
   fChain->SetBranchAddress("noevent", &noevent, &b_noevent);
   fChain->SetBranchAddress("pdgid", &pdgid, &b_pdgid);
   fChain->SetBranchAddress("px", &px, &b_px);
   fChain->SetBranchAddress("py", &py, &b_py);
   fChain->SetBranchAddress("pz", &pz, &b_pz);
   fChain->SetBranchAddress("energy", &energy, &b_energy);
   fChain->SetBranchAddress("mass", &mass, &b_mass);
   fChain->SetBranchAddress("M1", &M1, &b_M1);
   fChain->SetBranchAddress("D1", &D1, &b_D1);
   Notify();
}

Bool_t VLQ100k::Notify()
{
   // The Notify() function is called when a new file is opened. This
   // can be either for a new TTree in a TChain or when when a new TTree
   // is started when using PROOF. It is normally not necessary to make changes
   // to the generated code, but the routine can be extended by the
   // user if needed. The return value is currently not used.

   return kTRUE;
}

void VLQ100k::Show(Long64_t entry)
{
// Print contents of entry.
// If entry is not specified, print current entry
   if (!fChain) return;
   fChain->Show(entry);
}
Int_t VLQ100k::Cut(Long64_t entry)
{
// This function may be called from Loop.
// returns  1 if entry is accepted.
// returns -1 otherwise.
   return 1;
}
#endif // #ifdef VLQ100k_cxx
