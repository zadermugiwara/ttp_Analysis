#include<iostream>
#include <TFile.h>
#include <TH1D.h>
#include <TString.h>
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>

#include "TFile.h"
#include "TH1D.h"
#include "TString.h"
#include "TH1F.h"
#include "TCanvas.h"
#include "THStack.h"


int run(){

TFile f1200("VLQ100kdecayed1_output.root");
TFile f1600("VLQ100kdecayed2_output.root");
TFile f2000("VLQ100kdecayed3_output.root");
TFile f2400("VLQ100kdecayed4_output.root");
TCanvas* c3 = new TCanvas("c3", "Histograms 1 & 2", 600, 400);




TH1F* mass1200,* mass1600,* mass2000,* mass2400;
f1200.GetObject("m_recoil", mass1200);
f1600.GetObject("m_recoil", mass1600);
f2000.GetObject("m_recoil", mass2000);
f2400.GetObject("m_recoil", mass2400);

mass1200->SetDirectory(0);
mass1600->SetDirectory(0);
mass2000->SetDirectory(0);
mass2400->SetDirectory(0);



mass1200->Draw();
c3->cd();
mass1200->Scale(1.0/mass1200->Integral());
mass1200->SetLineColor(1);
mass1200->Draw("HIST");
mass1600->Scale(1.0/mass1600->Integral());
mass1600->SetLineColor(2);
mass1600->Draw("HIST SAME");
mass2000->Scale(1.0/mass2000->Integral());
mass2000->SetLineColor(3);
mass2000->Draw("HIST SAME");
mass2400->Scale(1.0/mass2400->Integral());
mass2400->SetLineColor(4);
mass2400->Draw("HIST SAME");
//histo1->Rebin(5);
//histo2->Rebin(5);
//histo3->Rebin(5);
//histo4->Rebin(5);







return 0;
}
