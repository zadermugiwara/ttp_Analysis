#include <iostream>
#define Tmadspin1_cxx
#include "Tmadspin1.h"
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>
#include "TH1F.h"
#include "TCanvas.h"
#include "THStack.h"
#include "TFile.h"

using namespace std;
int run(){
  
  Tmadspin1 t;
  t.Loop();

  return 0;
}
void Tmadspin1::Loop()
{

   
   if (fChain == 0) return;
   TH1F* mass = new TH1F("mass","Histogram 1",100,0,200);

   Long64_t nentries = fChain->GetEntriesFast();
    int m1;
    double Wb=0,Ht=0,tZ=0,j=0;
    TLorentzVector Tdau;
   Long64_t nbytes = 0, nb = 0;
   for (Long64_t jentry=0; jentry<nentries;jentry++) {
      Long64_t ientry = LoadTree(jentry);
      if (ientry < 0) break;
      nb = fChain->GetEntry(jentry);   nbytes += nb;
      // if (Cut(ientry) < 0) continue;
      for(int i=0; i<numpart; i++){
      m1=M1[i];
      if(abs(pdgid[m1])==6000006){
      Tdau.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
      if(abs(pdgid[i])==5){
      Wb=Wb+1;
      }
      if(pdgid[i]==25){
      Ht=Ht+1;
      }
      if(pdgid[i]==23){
      tZ=tZ+1;
      }
      }
      
      }
      mass->Fill(Tdau.M());
      j=j+1;
   }
   
   mass->SetLineColor(2);
	mass->SetFillColor(3);
	mass->GetXaxis()->SetTitle("m_{Tdau} [GeV]");
	mass->GetYaxis()->SetTitle("# of events");
	mass->Draw("HIST");
	TFile f1("Tmadspin1_output.root","RECREATE");
	mass->Write();
	f1.Close();
   
   cout<<"Decaimiento T > W b "<< (Wb/j)*100<<"% \nDecaimiento T > H t "<< (Ht/j)*100<< "% \nDecaimiento T > t Z "<< (tZ/j)*100<<"%" <<endl;
}
