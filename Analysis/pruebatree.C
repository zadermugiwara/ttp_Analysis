#include<iostream>
#include "TTree.h"
#include "TMath.h"

int run(){
  TFile::f1("outwex.1.root","RECREATE");
  
  TTree* tree=new TTree("tree","example tree");
  
  float x,y,weight;
  

  tree->Branch("xval",&x,"x/F");
  tree->Branch("yval",&y,"y/F");
  tree->Branch("weight",&weight,"weight/F");
  
  for(int xval=0; xval<11; xval++){
    for(int yval=0; yval<11; yval++){
      x=(float)xval;
      y=(float)yval;
      weight=TMath::Gaus(x,5,1)*TMath::Gaus(y,5,1);
      
      tree->Fill();
    }
  }
  f1.Write();
  
  
  return 0;


}
