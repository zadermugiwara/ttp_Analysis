#include <iostream>
//#define TRUTH_cxx
//#include "TRUTH.h"
#define Tmadspin1_cxx
#include "Tmadspin1.h"
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>

#include "TH1F.h"
#include "TCanvas.h"
#include "THStack.h"
#include "TFile.h"
#include "TLegend.h"

using namespace std;
int run(){
  
  Tmadspin1 t;
  t.Loop();

  return 0;
}
// pt del top vs pt del top que decayo del Tp
//Suma de pt de todas las particulas top + decaimientos del Tp o las de estado final
// Histogramas de Px, Py, Pz para t y Tp
void Tmadspin1::Loop()
{

   if (fChain == 0) return;
   TH1F* tPt = new TH1F("tPt","",1000,0,1500);
   TH1F* tdecPt = new TH1F("tPtdec","",1000,0,1500);
   TH1F* tpx = new TH1F("tpx","",1000,0,1500);
   TH1F* tpy = new TH1F("tpy","",1000,0,1500);
   TH1F* tpz = new TH1F("tpz","",1000,0,1500);
   TH1F* Tppx = new TH1F("Tppx","",1000,0,1500);
   TH1F* Tppy = new TH1F("Tppy","",1000,0,1500);
   TH1F* Tppz = new TH1F("Tppz","",1000,0,1500);
   TH1F* Httop = new TH1F("Httop","",100,0,1);
   TH1F* Httopdec = new TH1F("Httopdec","",100,0,1);
   
   
   
   TH2F* tpt = new TH2F("tpt","",1000,0,1500,1000,0,1500);
   TH2F* PTpvst = new TH2F("PTpvst","",100,0,2000,100,0,2000);
   TH2F* ETpvst = new TH2F("ETpvst","",100,0,2000,100,0,2000);
   TH2F* PtTpvst = new TH2F("PtTpvst","",100,0,2000,100,0,2000);
   TH2F* Httopvstopdec = new TH2F("Httopvstopdec","",100,0,1,100,0,1);
   TH2F* HttopvsPtTp = new TH2F("HttopvsPtTp","",100,0,1,100,0,2000);

   
   TLegend *leg2 = new TLegend(0.12,0.65,0.42,0.85);
      TLegend *leg3 = new TLegend(0.12,0.65,0.42,0.85);
   
   Long64_t nentries = fChain->GetEntriesFast();

   Long64_t nbytes = 0, nb = 0;
   TLorentzVector TP, b, t, WD1, WD2,tsum,tdec,part;
   int j=0,m1,m2;
   
   for (Long64_t jentry=0; jentry<nentries;jentry++) {
      Long64_t ientry = LoadTree(jentry);
      if (ientry < 0) break;
      nb = fChain->GetEntry(jentry);   nbytes += nb;
      // if (Cut(ientry) < 0) continue;
      float ptotal=0;
      int numtopdec = 0, numtop = 0;
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
          if(abs(pdgid[m1])==6000006){
            numtopdec++;
            tdec.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
          }else{
            numtop++;
            t.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
          }
        }
            
        if((abs(pdgid[m1])==24)&&(abs(pdgid[m2])==6)&&(j==0)){
          WD1.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
          j = j + 1;
        }
        if((abs(pdgid[m1])==24)&&(abs(pdgid[m2])==6)&&(j==1)){
          WD2.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
        }
        if(D1[i] == -1){
         part.SetPxPyPzE(px[i],py[i],pz[i],energy[i]);
         ptotal += part.Pt();
        }
        
      

      }
      //cout<<ptotal<<endl;      
      tPt->Fill(t.Pt());
      tpx->Fill(t.Px());
      tpy->Fill(t.Py());
      tpz->Fill(t.Pz());
      Tppx->Fill(TP.Px());
      Tppy->Fill(TP.Py());
      Tppz->Fill(TP.Pz());

      if(numtopdec==1){
      Httop->Fill(t.Pt()/ptotal);
      tdecPt->Fill(tdec.Pt());
      tpt->Fill(t.Pt(),tdec.Pt());
      Httopdec->Fill(tdec.Pt()/ptotal);
      Httopvstopdec->Fill(t.Pt()/ptotal,tdec.Pt()/ptotal);
      HttopvsPtTp->Fill(t.Pt()/ptotal,TP.Pt());
      }
      ETpvst->Fill(t.E(),TP.E());
      PtTpvst->Fill(t.Pt(),TP.Pt());
      float PTP =  sqrt(TP.Px()*TP.Px()+TP.Py()*TP.Py()+TP.Pz()*TP.Pz()), Ptop =  sqrt(t.Px()*t.Px()+t.Py()*t.Py()+t.Pz()*t.Pz());
      PTpvst->Fill(Ptop,PTP);
      
   }
   
   TH1D* Httopdecproy= Httopvstopdec->ProjectionY();
   
   TCanvas* Pt = new TCanvas("Pt", "Pt", 600, 400);
        Pt->cd();
tPt->Rebin(2);
tPt->Scale(1.0/tPt->Integral());
tPt->SetLineColor(1);
tPt->Draw("HISTE");

tdecPt->Rebin(2);
tdecPt->Scale(1.0/tdecPt->Integral());
tdecPt->SetLineColor(2);
tdecPt->Draw("HISTE SAME");
leg2->AddEntry(tPt,"tPt","l");
leg2->AddEntry(tdecPt,"tdecPt","l");
leg2->SetBorderSize(0);
leg2->SetFillColor(0);
leg2->SetTextFont(42);
leg2->Draw();
Pt->Print("Pt.pdf");
TCanvas* ppt = new TCanvas("Pt", "Pt", 600, 400);
        ppt->cd();
        tpt->GetXaxis()->SetTitle("PT_{top} [GeV}");
	tpt->GetYaxis()->SetTitle("#PT_{top decayed} [GeV}");
        tpt->Draw("COLZ");
        ppt->Print("ppt.pdf");
        
        TCanvas* Ht = new TCanvas("Pt", "Pt", 600, 400);
        Ht->cd();
Httop->Rebin(2);
Httop->Scale(1.0/*/Httop->Integral()*/);
Httop->SetLineColor(1);
Httop->Draw("HISTE");

Httopdec->Rebin(2);
Httopdec->Scale(1.0/*/Httopdec->Integral()*/);
Httopdec->SetLineColor(2);
Httopdec->Draw("HISTE SAME");
leg3->AddEntry(tPt,"Httop","l");
leg3->AddEntry(tdecPt,"Httopdec","l");
leg3->SetBorderSize(0);
leg3->SetFillColor(0);
leg3->SetTextFont(42);
leg3->Draw();
Ht->Print("Ht.pdf");
        
        //TCanvas* TpvstP = new TCanvas("P", "P", 600, 400);
        //TpvstP->cd();
        PTpvst->GetXaxis()->SetTitle("P_{top} [GeV]");
	PTpvst->GetYaxis()->SetTitle("#P_{TP} [GeV]");
        PTpvst->Draw("COLZ");
        //TpvstP->Print("TpvstP.pdf");
        
        //TCanvas* TpvstPt = new TCanvas("Pt", "Pt", 600, 400);
        //TpvstPt->cd();
        PtTpvst->GetXaxis()->SetTitle("PT_{top} [GeV]");
	PtTpvst->GetYaxis()->SetTitle("#PT_{TP} [GeV]");
        PtTpvst->Draw("COLZ");
        //TpvstP->Print("TpvstPt.pdf");
        
        //TCanvas* TpvstE = new TCanvas("E", "E", 600, 400);
        //TpvstE->cd();
        ETpvst->GetXaxis()->SetTitle("E_{top} [GeV]");
	ETpvst->GetYaxis()->SetTitle("#E_{TP} [GeV]");
        ETpvst->Draw("COLZ");
        //TpvstE->Print("TpvstE.pdf");
        
        
        HttopvsPtTp->GetXaxis()->SetTitle("Ht_{top} ");
	HttopvsPtTp->GetYaxis()->SetTitle("Pt_{TP} [GeV]");
        HttopvsPtTp->Draw("COLZ");
        
        
        Httopvstopdec->GetXaxis()->SetTitle("Ht_{top}");
	Httopvstopdec->GetYaxis()->SetTitle("Ht_{topdec}");
        Httopvstopdec->Draw("COLZ");
        
        Httopdecproy->Draw("HIST");
        



tpx->Rebin(2);
//tpx->Scale(1.0/tpx->Integral());
tpx->SetLineColor(1);
tpx->Draw("HIST");

tpy->Rebin(2);
//tpy->Scale(1.0/tpy->Integral());
tpy->SetLineColor(1);
tpy->Draw("HIST");

tpz->Rebin(2);
//tpz->Scale(1.0/tpz->Integral());
tpz->SetLineColor(1);
tpz->Draw("HIST");

Tppx->Rebin(2);
//Tppx->Scale(1.0/Tppx->Integral());
Tppx->SetLineColor(1);
Tppx->Draw("HIST");

Tppy->Rebin(2);
//Tppy->Scale(1.0/Tppy->Integral());
Tppy->SetLineColor(1);
Tppy->Draw("HIST");

Tppz->Rebin(2);
//Tppz->Scale(1.0/Tppz->Integral());
Tppz->SetLineColor(1);
Tppz->Draw("HIST");

        TFile f1("TRUTH_output.root","RECREATE");
	/*mass->Write();
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
	m_recoil->Write();*/////
	
	tpt->Write();
	tPt->Write();
	tpx->Write();
	tpy->Write();
	tpz->Write();
	Tppx->Write();
	Tppy->Write();
	Tppz->Write();
	PTpvst->Write();
	PtTpvst->Write();
	ETpvst->Write();	
	Httop->Write();
	Httopdec->Write();
	HttopvsPtTp->Write();
	Httopvstopdec->Write();
	Httopdecproy->Write();
	
	f1.Close();
}
