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
#include "TLegend.h"


int run(){

TFile f1200("VLQ100khadronized1_outputfatjet1200.root");
TFile f1600("VLQ100khadronized1_outputfatjet1600.root");
TFile f2000("VLQ100khadronized1_outputfatjet2000.root");
TFile f2400("VLQ100khadronized1_outputfatjet2400.root");
TCanvas* Mass = new TCanvas("Mass", "Mass", 600, 400);
TCanvas* Pt = new TCanvas("Pt", "Pt", 600, 400);
/*TCanvas* deltaRWD1WD2 = new TCanvas("deltaRWD1WD2", "deltaRWD1WD2", 600, 400);
TCanvas* deltaRWD1b = new TCanvas("deltaRWD1b", "deltaRWD1b", 600, 400);
TCanvas* deltaRWD2b = new TCanvas("deltaRWD2b", "deltaRWD2b", 600, 400);*/


f1200.ls();

TH1F* mass1200,* mass1600,* mass2000,* mass2400;
TLegend *leg = new TLegend(0.5,0.65,0.8,0.85);
f1200.GetObject("m_recoil", mass1200);
f1600.GetObject("m_recoil", mass1600);
f2000.GetObject("m_recoil", mass2000);
f2400.GetObject("m_recoil", mass2400);

mass1200->SetDirectory(0);
mass1600->SetDirectory(0);
mass2000->SetDirectory(0);
mass2400->SetDirectory(0);



mass1200->Draw();
Mass->cd();
mass1200->Rebin(5);
mass1200->Scale(1.0/mass1200->Integral());
mass1200->SetLineColor(1);

mass1200->Draw("HIST");
mass1600->Rebin(5);
mass1600->Scale(1.0/mass1600->Integral());
mass1600->SetLineColor(2);

mass1600->Draw("HIST SAME");
mass2000->Rebin(5);
mass2000->Scale(1.0/mass2000->Integral());
mass2000->SetLineColor(3);

mass2000->Draw("HIST SAME");
mass2400->Rebin(5);
mass2400->Scale(1.0/mass2400->Integral());
mass2400->SetLineColor(4);

mass2400->Draw("HIST SAME");
leg->AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
leg->AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
leg->AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
leg->AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
leg->SetBorderSize(0);
leg->SetFillColor(0);
leg->SetTextFont(42);
leg->Draw();
Mass->Print("Massfat_recoil.pdf");

TH1F* pt1200,* pt1600,* pt2000,* pt2400;
TLegend *leg2 = new TLegend(0.12,0.65,0.42,0.85);
f1200.GetObject("Ptfat", pt1200);
f1600.GetObject("Ptfat", pt1600);
f2000.GetObject("Ptfat", pt2000);
f2400.GetObject("Ptfat", pt2400);

pt1200->SetDirectory(0);
pt1600->SetDirectory(0);
pt2000->SetDirectory(0);
pt2400->SetDirectory(0);



//pt1200->Draw();
Pt->cd();
pt1200->Rebin(10);
pt1200->Scale(1.0/pt1200->Integral());
pt1200->SetLineColor(1);

pt1200->Draw("HISTE");
pt1600->Rebin(10);
pt1600->Scale(1.0/pt1600->Integral());
pt1600->SetLineColor(2);

pt1600->Draw("HISTE SAME");
pt2000->Rebin(10);
pt2000->Scale(1.0/pt2000->Integral());
pt2000->SetLineColor(3);

pt2000->Draw("HISTE SAME");
pt2400->Rebin(10);
pt2400->Scale(1.0/pt2400->Integral());
pt2400->SetLineColor(4);

pt2400->Draw("HISTE SAME");
leg2->AddEntry(pt1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
leg2->AddEntry(pt1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
leg2->AddEntry(pt2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
leg2->AddEntry(pt2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
leg2->SetBorderSize(0);
leg2->SetFillColor(0);
leg2->SetTextFont(42);
leg2->Draw();
Pt->Print("Ptfat.pdf");
//histo1->Rebin(5);
//histo2->Rebin(5);
//histo3->Rebin(5);
//histo4->Rebin(5);*/
/*
TH1F* deltaRWD1WD21200,* deltaRWD1WD21600,* deltaRWD1WD22000,* deltaRWD1WD22400;
TLegend *leg3 = new TLegend(0.15,0.65,0.5,0.85);
f1200.GetObject("deltaWD1WD2R", deltaRWD1WD21200);
f1600.GetObject("deltaWD1WD2R", deltaRWD1WD21600);
f2000.GetObject("deltaWD1WD2R", deltaRWD1WD22000);
f2400.GetObject("deltaWD1WD2R", deltaRWD1WD22400);

deltaRWD1WD21200->SetDirectory(0);
deltaRWD1WD21600->SetDirectory(0);
deltaRWD1WD22000->SetDirectory(0);
deltaRWD1WD22400->SetDirectory(0);



//pt1200->Draw();
deltaRWD1WD2->cd();
deltaRWD1WD21200->Scale(1.0/deltaRWD1WD21200->Integral());
deltaRWD1WD21200->SetLineColor(1);
deltaRWD1WD21200->Draw("HISTE");
deltaRWD1WD21600->Scale(1.0/deltaRWD1WD21600->Integral());
deltaRWD1WD21600->SetLineColor(2);
deltaRWD1WD21600->Draw("HISTE SAME");
deltaRWD1WD22000->Scale(1.0/deltaRWD1WD22000->Integral());
deltaRWD1WD22000->SetLineColor(3);
deltaRWD1WD22000->Draw("HISTE SAME");
deltaRWD1WD22400->Scale(1.0/deltaRWD1WD22400->Integral());
deltaRWD1WD22400->SetLineColor(4);
deltaRWD1WD22400->Draw("HISTE SAME");
leg3->AddEntry(deltaRWD1WD21200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
leg3->AddEntry(deltaRWD1WD21600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
leg3->AddEntry(deltaRWD1WD22000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
leg3->AddEntry(deltaRWD1WD22400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
leg3->SetBorderSize(0);
leg3->SetFillColor(0);
leg3->SetTextFont(42);
leg3->Draw();
//histo1->Rebin(5);
//histo2->Rebin(5);
//histo3->Rebin(5);
//histo4->Rebin(5);

TH1F* deltaRWD1b1200,* deltaRWD1b1600,* deltaRWD1b2000,* deltaRWD1b2400;
TLegend *leg4 = new TLegend(0.15,0.65,0.5,0.85);
f1200.GetObject("deltaWD1bR", deltaRWD1b1200);
f1600.GetObject("deltaWD1bR", deltaRWD1b1600);
f2000.GetObject("deltaWD1bR", deltaRWD1b2000);
f2400.GetObject("deltaWD1bR", deltaRWD1b2400);

deltaRWD1b1200->SetDirectory(0);
deltaRWD1b1600->SetDirectory(0);
deltaRWD1b2000->SetDirectory(0);
deltaRWD1b2400->SetDirectory(0);



//pt1200->Draw();
deltaRWD1b->cd();
deltaRWD1b1200->Scale(1.0/deltaRWD1b1200->Integral());
deltaRWD1b1200->SetLineColor(1);
deltaRWD1b1200->Draw("HISTE");
deltaRWD1b1600->Scale(1.0/deltaRWD1b1600->Integral());
deltaRWD1b1600->SetLineColor(2);
deltaRWD1b1600->Draw("HISTE SAME");
deltaRWD1b2000->Scale(1.0/deltaRWD1b2000->Integral());
deltaRWD1b2000->SetLineColor(3);
deltaRWD1b2000->Draw("HISTE SAME");
deltaRWD1b2400->Scale(1.0/deltaRWD1b2400->Integral());
deltaRWD1b2400->SetLineColor(4);
deltaRWD1b2400->Draw("HISTE SAME");
leg4->AddEntry(deltaRWD1b1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
leg4->AddEntry(deltaRWD1b1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
leg4->AddEntry(deltaRWD1b2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
leg4->AddEntry(deltaRWD1b2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
leg4->SetBorderSize(0);
leg4->SetFillColor(0);
leg4->SetTextFont(42);
leg4->Draw();
//histo1->Rebin(5);
//histo2->Rebin(5);
//histo3->Rebin(5);
//histo4->Rebin(5);

TH1F* deltaRWD2b1200,* deltaRWD2b1600,* deltaRWD2b2000,* deltaRWD2b2400;
TLegend *leg5 = new TLegend(0.15,0.65,0.5,0.85);
f1200.GetObject("deltaWD2bR", deltaRWD2b1200);
f1600.GetObject("deltaWD2bR", deltaRWD2b1600);
f2000.GetObject("deltaWD2bR", deltaRWD2b2000);
f2400.GetObject("deltaWD2bR", deltaRWD2b2400);

deltaRWD2b1200->SetDirectory(0);
deltaRWD2b1600->SetDirectory(0);
deltaRWD2b2000->SetDirectory(0);
deltaRWD2b2400->SetDirectory(0);



//pt1200->Draw();
deltaRWD2b->cd();
deltaRWD2b1200->Scale(1.0/deltaRWD2b1200->Integral());
deltaRWD2b1200->SetLineColor(1);
deltaRWD2b1200->Draw("HISTE");
deltaRWD2b1600->Scale(1.0/deltaRWD2b1600->Integral());
deltaRWD2b1600->SetLineColor(2);
deltaRWD2b1600->Draw("HISTE SAME");
deltaRWD2b2000->Scale(1.0/deltaRWD2b2000->Integral());
deltaRWD2b2000->SetLineColor(3);
deltaRWD2b2000->Draw("HISTE SAME");
deltaRWD2b2400->Scale(1.0/deltaRWD2b2400->Integral());
deltaRWD2b2400->SetLineColor(4);
deltaRWD2b2400->Draw("HISTE SAME");
leg5->AddEntry(deltaRWD2b1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
leg5->AddEntry(deltaRWD2b1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
leg5->AddEntry(deltaRWD2b2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
leg5->AddEntry(deltaRWD2b2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
leg5->SetBorderSize(0);
leg5->SetFillColor(0);
leg5->SetTextFont(42);
leg5->Draw();*/
//histo1->Rebin(5);
//histo2->Rebin(5);
//histo3->Rebin(5);
//histo4->Rebin(5);*/







return 0;
}
