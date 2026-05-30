#include <iostream>
#define VLQ100kdecayed2_cxx
#include "VLQ100kdecayed2.h"
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>

#include "TH1F.h"
#include "TCanvas.h"
#include "THStack.h"
#include "TFile.h"




using namespace std;
int run(){
  
  VLQ100kdecayed2 t;
  t.Loop();

  return 0;
}

void VLQ100kdecayed2::Loop()
{


   if (fChain == 0) return;
   

   TH1F* mass = new TH1F("mass","",100,0,3000);
   TH1F* Pt = new TH1F("Pt","",1000,0,1300);
   TH1F* Eta = new TH1F("Eta","",1000,-5,5);
   TH1F* Rapidity = new TH1F("Rapidity","",1000,-5,5);
   TH1F* deltaTPbPhi = new TH1F("deltaTPbPhi","",1000,0,5);
   TH1F* deltaTPbEta = new TH1F("deltaTPbEta","",1000,0,10);
   TH1F* deltaTPbR = new TH1F("deltaTPbR","",1000,0,10);   
   TH1F* tRapidity = new TH1F("tRapidity","",1000,-5,5);
   TH1F* tPt = new TH1F("tPt","",1000,0,1300);
   TH1F* tEta = new TH1F("tEta","",1000,-5,5);
   TH1F* deltaTPWD1Phi = new TH1F("deltaTPWD1Phi","",1000,0,5);
   TH1F* deltaTPWD1Eta = new TH1F("deltaTPWD1Eta","",1000,0,10);
   TH1F* deltaTPWD1R = new TH1F("deltaTPWD1R","",1000,0,10);
   TH1F* deltaTPWD2Phi = new TH1F("deltaTPWD2Phi","",1000,0,5);
   TH1F* deltaTPWD2Eta = new TH1F("deltaTPWD2Eta","",1000,0,10);
   TH1F* deltaTPWD2R = new TH1F("deltaTPWD2R","",1000,0,10);
   TH1F* deltaWD1bPhi = new TH1F("deltaWD1bPhi","",1000,0,5);
   TH1F* deltaWD1bEta = new TH1F("deltaWD1bEta","",1000,0,10);
   TH1F* deltaWD1bR = new TH1F("deltaWD1bR","",1000,0,10);
   TH1F* deltaWD2bPhi = new TH1F("deltaWD2bPhi","",1000,0,5);
   TH1F* deltaWD2bEta = new TH1F("deltaWD2bEta","",1000,0,10);
   TH1F* deltaWD2bR = new TH1F("deltaWD2bR","",1000,0,10);
   TH1F* deltaWD1WD2Phi = new TH1F("deltaWD1WD2Phi","",1000,0,5);
   TH1F* deltaWD1WD2Eta = new TH1F("deltaWD1WD2Eta","",1000,0,10);
   TH1F* deltaWD1WD2R = new TH1F("deltaWD1WD2R","",1000,0,10);
   TH1F* tmass = new TH1F("tmass","",100,0,500);
   TH1F* bPt = new TH1F("bPt","",1000,0,1300);
   TH1F* m_recoil = new TH1F("m_recoil","",1000,0,3000);
   
   Long64_t nentries = fChain->GetEntriesFast();
   TLorentzVector TP, b, t, WD1, WD2,tsum;
   int j=0,m1,m2;
   Long64_t nbytes = 0, nb = 0;
   for (Long64_t jentry=0; jentry<nentries;jentry++) {
      Long64_t ientry = LoadTree(jentry);
      if (ientry < 0) break;
      nb = fChain->GetEntry(jentry);   nbytes += nb;
      // if (Cut(ientry) < 0) continue;
      j=0;
      for(int i=0; i<numpart; i++){
      m1=M1[i];
      m2=M1[m1];
      if(abs(pdgid[i])==6000006){
      TP.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);

      }
      if((abs(pdgid[i])==5)&&(abs(pdgid[m1])==6)){
      b.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);

      }
      if(abs(pdgid[i])==6){
      t.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);

      }
      
      if((abs(pdgid[m1])==24)&&(abs(pdgid[m2])==6)&&(j==0)){
      WD1.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
      j = j + 1;
      }
      if((abs(pdgid[m1])==24)&&(abs(pdgid[m2])==6)&&(j==1)){
      WD2.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
      
      }
      
      //cout<<M1[i]<<endl;
      }
      

      mass->Fill(TP.M());
      Pt->Fill(TP.Pt());
      Eta->Fill(TP.Eta());
      Rapidity->Fill(TP.Rapidity());
      deltaTPbEta->Fill(abs(TP.Eta()-b.Eta()));
      deltaTPbPhi->Fill(ROOT::Math::VectorUtil::DeltaPhi(TP,b));
      deltaTPbR->Fill(ROOT::Math::VectorUtil::DeltaR(TP,b));
      tPt->Fill(TP.Pt());
      tEta->Fill(TP.Eta());
      tRapidity->Fill(TP.Rapidity());
      deltaTPWD1Phi->Fill(ROOT::Math::VectorUtil::DeltaPhi(TP,WD1));
      deltaTPWD1Eta->Fill(abs(TP.Eta()-WD1.Eta()));
      deltaTPWD1R->Fill(ROOT::Math::VectorUtil::DeltaR(TP,WD1));
      deltaTPWD2Phi->Fill(ROOT::Math::VectorUtil::DeltaPhi(TP,WD2));
      deltaTPWD2Eta->Fill(abs(TP.Eta()-WD2.Eta()));
      deltaTPWD2R->Fill(ROOT::Math::VectorUtil::DeltaR(TP,WD2));
      deltaWD1bPhi->Fill(ROOT::Math::VectorUtil::DeltaPhi(WD1,b));
      deltaWD1bEta->Fill(abs(WD1.Eta()-b.Eta()));
      deltaWD1bR->Fill(ROOT::Math::VectorUtil::DeltaR(WD1,b));
      deltaWD2bPhi->Fill(ROOT::Math::VectorUtil::DeltaPhi(WD2,b));
      deltaWD2bEta->Fill(abs(WD2.Eta()-b.Eta()));
      deltaWD2bR->Fill(ROOT::Math::VectorUtil::DeltaR(WD2,b));
      deltaWD1WD2Phi->Fill(ROOT::Math::VectorUtil::DeltaPhi(WD1,WD2));
      deltaWD1WD2Eta->Fill(abs(WD1.Eta()-WD2.Eta()));
      deltaWD1WD2R->Fill(ROOT::Math::VectorUtil::DeltaR(WD1,WD2));
      bPt->Fill(b.Pt());
      tsum=b+WD1+WD2;
      tmass->Fill(tsum.M());
      m_recoil->Fill(sqrt((3000*3000)-(2*tsum.E()*3000)+(tsum.M()*tsum.M())));
   }

	mass->SetStats(0);
	mass->Rebin(1);
	mass->SetLineColor(2);
	//mass->SetFillColor(3);
	mass->GetXaxis()->SetTitle("m_{Top partner} [GeV]");
	mass->GetYaxis()->SetTitle("# of events");
	mass->Draw("HIST");
	
        Pt->SetStats(0);
        Pt->Rebin(5);
	Pt->SetLineColor(2);
	//Pt->SetFillColor(3);
	Pt->GetXaxis()->SetTitle("PT_{Top partner} [GeV]");
	Pt->GetYaxis()->SetTitle("# of events");
	Pt->Draw("HIST");
	

        Eta->SetStats(0);
        Eta->Rebin(10);
	Eta->SetLineColor(2);
	//Eta->SetFillColor(3);
	Eta->GetXaxis()->SetTitle("#eta_{Top partner}");
	Eta->GetYaxis()->SetTitle("# of events");
	Eta->Draw("HIST");
        
        Rapidity->SetStats(0);
        Rapidity->Rebin(5);
	Rapidity->SetLineColor(2);
	//Rapidity->SetFillColor(3);
	Rapidity->GetXaxis()->SetTitle("y_{Top partner}");
	Rapidity->GetYaxis()->SetTitle("# of events");
	Rapidity->Draw("HIST");
	
	deltaTPbEta->SetStats(0);
	deltaTPbEta->Rebin(10);
	deltaTPbEta->SetLineColor(2);
	//deltaTPbEta->SetFillColor(3);
	deltaTPbEta->GetXaxis()->SetTitle("#Delta#eta(T,b_{top})");
	deltaTPbEta->GetYaxis()->SetTitle("# of events");
	deltaTPbEta->Draw("HIST");
	
	deltaTPbPhi->SetStats(0);
	deltaTPbPhi->Rebin(5);
	deltaTPbPhi->SetLineColor(2);
	//deltaTPbPhi->SetFillColor(3);
	deltaTPbPhi->GetXaxis()->SetTitle("#Delta#phi(T,b_{top})");
	deltaTPbPhi->GetYaxis()->SetTitle("# of events");
	deltaTPbPhi->Draw("HIST");
	
	deltaTPbR->SetStats(0);
	deltaTPbR->Rebin(5);
	deltaTPbR->SetLineColor(2);
	//deltaTPbR->SetFillColor(3);
	deltaTPbR->GetXaxis()->SetTitle("#Delta R(T,b_{top})");
	deltaTPbR->GetYaxis()->SetTitle("# of events");
	deltaTPbR->Draw("HIST");
	
	tPt->SetStats(0);
	tPt->Rebin(5);
	tPt->SetLineColor(2);
	//tPt->SetFillColor(3);
	tPt->GetXaxis()->SetTitle("PT_{top} [GeV}");
	tPt->GetYaxis()->SetTitle("# of events");
	tPt->Draw("HIST");
        
        tEta->SetStats(0);
        tEta->Rebin(10);
	tEta->SetLineColor(2);
	//tEta->SetFillColor(3);
	tEta->GetXaxis()->SetTitle("Eta_{t}");
	tEta->GetYaxis()->SetTitle("# of events");
	tEta->Draw("HIST");
        
        tRapidity->SetStats(0);
        tRapidity->Rebin(10);
	tRapidity->SetLineColor(2);
	//tRapidity->SetFillColor(3);
	tRapidity->GetXaxis()->SetTitle("y_{t}");
	tRapidity->GetYaxis()->SetTitle("# of events");
	tRapidity->Draw("HIST");
	
	deltaTPWD1Eta->SetStats(0);
	deltaTPWD1Eta->Rebin(10);
	deltaTPWD1Eta->SetLineColor(2);
	//deltaTPWD1Eta->SetFillColor(3);
	deltaTPWD1Eta->GetXaxis()->SetTitle("#Delta#eta(T,Wdau_{1})");
	deltaTPWD1Eta->GetYaxis()->SetTitle("# of events");
	deltaTPWD1Eta->Draw("HIST");
	
	deltaTPWD1Phi->SetStats(0);
	deltaTPWD1Phi->Rebin(5);
	deltaTPWD1Phi->SetLineColor(2);
	//deltaTPWD1Phi->SetFillColor(3);
	deltaTPWD1Phi->GetXaxis()->SetTitle("#Delta#phi(T,Wdau_{1})");
	deltaTPWD1Phi->GetYaxis()->SetTitle("# of events");
	deltaTPWD1Phi->Draw("HIST");
	
	deltaTPWD1R->SetStats(0);
	deltaTPWD1R->Rebin(5);
	deltaTPWD1R->SetLineColor(2);
	//deltaTPWD1R->SetFillColor(3);
	deltaTPWD1R->GetXaxis()->SetTitle("#Delta R(T,Wdau_{1})");
	deltaTPWD1R->GetYaxis()->SetTitle("# of events");
	deltaTPWD1R->Draw("HIST");
	
	deltaTPWD2Eta->SetStats(0);
	deltaTPWD2Eta->Rebin(10);
	deltaTPWD2Eta->SetLineColor(2);
	//deltaTPWD2Eta->SetFillColor(3);
	deltaTPWD2Eta->GetXaxis()->SetTitle("#Delta#eta(T,Wdau_{2})");
	deltaTPWD2Eta->GetYaxis()->SetTitle("# of events");
	deltaTPWD2Eta->Draw("HIST");
	
	deltaTPWD2Phi->SetStats(0);
	deltaTPWD2Phi->Rebin(5);
	deltaTPWD2Phi->SetLineColor(2);
	//deltaTPWD2Phi->SetFillColor(3);
	deltaTPWD2Phi->GetXaxis()->SetTitle("#Delta#phi(T,Wdau_{2})");
	deltaTPWD2Phi->GetYaxis()->SetTitle("# of events");
	deltaTPWD2Phi->Draw("HIST");
	
	deltaTPWD2R->SetStats(0);
	deltaTPWD2R->Rebin(5);
	deltaTPWD2R->SetLineColor(2);
	//deltaTPWD2R->SetFillColor(3);
	deltaTPWD2R->GetXaxis()->SetTitle("#Delta R(T,Wdau_{2})");
	deltaTPWD2R->GetYaxis()->SetTitle("# of events");
	deltaTPWD2R->Draw("HIST");
	
	deltaWD1bEta->SetStats(0);
	deltaWD1bEta->Rebin(10);
	deltaWD1bEta->SetLineColor(2);
	//deltaWD1bEta->SetFillColor(3);
	deltaWD1bEta->GetXaxis()->SetTitle("#Delta#eta(Wdau_{1},b_{top})");
	deltaWD1bEta->GetYaxis()->SetTitle("# of events");
	deltaWD1bEta->Draw("HIST");
	
	deltaWD1bPhi->SetStats(0);
	deltaWD1bPhi->Rebin(5);
	deltaWD1bPhi->SetLineColor(2);
	//deltaWD1bPhi->SetFillColor(3);
	deltaWD1bPhi->GetXaxis()->SetTitle("#Delta#phi(Wdau_{1},b_{top})");
	deltaWD1bPhi->GetYaxis()->SetTitle("# of events");
	deltaWD1bPhi->Draw("HIST");
	
	deltaWD1bR->SetStats(0);
	deltaWD1bR->SetLineColor(2);
	//deltaWD1bR->SetFillColor(3);
	deltaWD1bR->Rebin(5);
	deltaWD1bR->GetXaxis()->SetTitle("#Delta R(Wdau_{1},b_{top})");
	deltaWD1bR->GetYaxis()->SetTitle("# of events");
	deltaWD1bR->Draw("HIST");
	
	deltaWD2bEta->SetStats(0);
	deltaWD2bEta->Rebin(10);
	deltaWD2bEta->SetLineColor(2);
	//deltaWD2bEta->SetFillColor(3);
	deltaWD2bEta->GetXaxis()->SetTitle("#Delta#eta(Wdau_{2},b_{top})");
	deltaWD2bEta->GetYaxis()->SetTitle("# of events");
	deltaWD2bEta->Draw("HIST");
	
	deltaWD2bPhi->SetStats(0);
	deltaWD2bPhi->Rebin(5);
	deltaWD2bPhi->SetLineColor(2);
	//deltaWD2bPhi->SetFillColor(3);
	deltaWD2bPhi->GetXaxis()->SetTitle("#Delta#phi(Wdau_{2},b_{top})");
	deltaWD2bPhi->GetYaxis()->SetTitle("# of events");
	deltaWD2bPhi->Draw("HIST");
	
	deltaWD2bR->SetStats(0);
	deltaWD2bR->Rebin(5);
	deltaWD2bR->SetLineColor(2);
	//deltaWD2bR->SetFillColor(3);
	deltaWD2bR->GetXaxis()->SetTitle("#Delta R(Wdau_{2},b_{top})");
	deltaWD2bR->GetYaxis()->SetTitle("# of events");
	deltaWD2bR->Draw("HIST");
	
	deltaWD1WD2Eta->SetStats(0);
	deltaWD1WD2Eta->Rebin(10);
	deltaWD1WD2Eta->SetLineColor(2);
	//deltaWD1WD2Eta->SetFillColor(3);
	deltaWD1WD2Eta->GetXaxis()->SetTitle("#Delta#eta(Wdau_{1},Wdau_{2})");
	deltaWD1WD2Eta->GetYaxis()->SetTitle("# of events");
	deltaWD1WD2Eta->Draw("HIST");
	
	deltaWD1WD2Phi->SetStats(0);
	deltaWD1WD2Phi->Rebin(5);
	deltaWD1WD2Phi->SetLineColor(2);
	//deltaWD1WD2Phi->SetFillColor(3);
	deltaWD1WD2Phi->GetXaxis()->SetTitle("#Delta#phi(Wdau_{1},Wdau_{2})");
	deltaWD1WD2Phi->GetYaxis()->SetTitle("# of events");
	deltaWD1WD2Phi->Draw("HIST");
	
	deltaWD1WD2R->SetStats(0);
	deltaWD1WD2R->Rebin(5);
	deltaWD1WD2R->SetLineColor(2);
	//deltaWD1WD2R->SetFillColor(3);
	deltaWD1WD2R->GetXaxis()->SetTitle("#Delta R(Wdau_{1},Wdau_{2})");
	deltaWD1WD2R->GetYaxis()->SetTitle("# of events");
	deltaWD1WD2R->Draw("HIST");
	
	//tmass->SetStats(0);
	tmass->Rebin(1);
	tmass->SetLineColor(2);
	//tmass->SetFillColor(3);
	tmass->GetXaxis()->SetTitle("m_{t} [GeV]");
	tmass->GetYaxis()->SetTitle("# of events");
	tmass->Draw("HIST");
	
	bPt->SetStats(0);
	bPt->Rebin(10);
	bPt->SetLineColor(2);
	//bPt->SetFillColor(3);
	bPt->GetXaxis()->SetTitle("PT_{b}");
	bPt->GetYaxis()->SetTitle("# of events");
	bPt->Draw("HIST");
	
	m_recoil->SetStats(0);
	m_recoil->Rebin(1);
	m_recoil->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil->GetXaxis()->SetTitle("recoil mass [GeV]");
	m_recoil->GetYaxis()->SetTitle("# of events");
	m_recoil->Draw("HIST");
	
	TFile f1("VLQ100kdecayed2_output.root","RECREATE");
	mass->Write();
	Pt->Write();
	Eta->Write();
	Rapidity->Write();
	deltaTPbEta->Write();
	deltaTPbPhi->Write();
	deltaTPbR->Write();
	tPt->Write();
	tEta->Write();
	tRapidity->Write();
	deltaTPWD1Eta->Write();
	deltaTPWD1Phi->Write();
	deltaTPWD1R->Write();
	deltaTPWD2Eta->Write();
	deltaTPWD2Phi->Write();
	deltaTPWD2R->Write();
	deltaWD1bEta->Write();
	deltaWD1bPhi->Write();
	deltaWD1bR->Write();
	deltaWD2bEta->Write();
	deltaWD2bPhi->Write();
	deltaWD2bR->Write();
	deltaWD1WD2Eta->Write();
	deltaWD1WD2Phi->Write();
	deltaWD1WD2R->Write();
	bPt->Write();
	tmass->Write();
	m_recoil->Write();
	
	f1.Close();
}
