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

#include "TInterpreter.h"
#include "TCanvas.h"
#include "TSystem.h"
#include "TFile.h"
#include "TH2.h"
#include "TNtuple.h"
#include "TPaveLabel.h"
#include "TPaveText.h"
#include "TFrame.h"
#include "TSystem.h"
#include "TInterpreter.h"


int run(){
    int namenum = 53;

    char nombres[56][30]= {"deltaRjet","deltaRlepton","m_recoil","mass","mass_post","mass_lead","Ht",
                            "fatjetHt","fatjet2Ht","fatjetpostHt",
                            "mass_post2","m_recoil2","fatjetpostHt2","pt_fatjetpost","pt_fatjetpost2",
                            "goodFJ","m_recoil0.5","m_recoil0","masstoplike","mrecoil toplikes","No_FJ",
                            "No_top_FJ","mrecoil_top_E_cut","m_recoilcut","topHt","m_recoil_isolated_toplikes",
                            "TPmass","topmass","topdecmass","truth_recoil","truth_deltaR_jet_TP","truth_deltaR_jet_top",
                            "truth_deltaR_jet_topdec","truth_deltaR_leptons_TP","truth_deltaR_leptons_top","truth_deltaR_leptons_topdec",
                            "truth_deltaR_fatjet_TP","truth_deltaR_fatjet_top","truth_deltaR_fatjet_topdec","good_deltaRjet",
                            "good_deltaRlepton","good_m_recoil","good_m_fatjet","good_pt_fatjet","good_E_fatjet",
                            "good_Ht_fatjet","bad_deltaRjet","bad_deltaRlepton","bad_m_recoil","bad_m_fatjet",
                            "bad_pt_fatjet","bad_E_fatjet","bad_Ht_fatjet"};


    TFile f1200("root/Tt1M1200.root");
    TFile f1600("root/Tt1M1600.root");
    TFile f2000("root/Tt1M2000.root");
    TFile f2400("root/Tt1M2400.root");
    TCanvas* Pt = new TCanvas("Pt", "Pt", 600, 400);
    /*TCanvas* deltaRWD1WD2 = new TCanvas("deltaRWD1WD2", "deltaRWD1WD2", 600, 400);
    TCanvas* deltaRWD1b = new TCanvas("deltaRWD1b", "deltaRWD1b", 600, 400);
    TCanvas* deltaRWD2b = new TCanvas("deltaRWD2b", "deltaRWD2b", 600, 400);*/
    TH1F* mass1200,* mass1600,* mass2000,* mass2400;   

	TFile f1("output.root","RECREATE");
    for (int i = 0; i < namenum; i++) 
    {
        TCanvas* Mass = new TCanvas(nombres[i], nombres[i], 1800, 1200);

        //printf("%s\n", nombres[i]);
        f1200.GetObject(nombres[i], mass1200);
        f1600.GetObject(nombres[i], mass1600);
        f2000.GetObject(nombres[i], mass2000);
        f2400.GetObject(nombres[i], mass2400);

        mass1200->Draw();
        Mass->cd();
        //mass1200->Rebin(5);
        mass1200->Scale(1.0/mass1200->Integral());
        mass1200->SetLineColor(1);

        mass1200->Draw("HIST");
        //mass1600->Rebin(5);
        mass1600->Scale(1.0/mass1600->Integral());
        mass1600->SetLineColor(2);

        mass1600->Draw("HIST SAME");
        //mass2000->Rebin(5);
        mass2000->Scale(1.0/mass2000->Integral());
        mass2000->SetLineColor(3);

        mass2000->Draw("HIST SAME");
        //mass2400->Rebin(5);
        mass2400->Scale(1.0/mass2400->Integral());
        mass2400->SetLineColor(4);

        mass2400->Draw("HIST SAME");

        /*leg->AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l");
        leg->AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l");
        leg->AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l");
        leg->AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l");
        leg->SetBorderSize(0);
        leg->SetFillColor(0);
        leg->SetTextFont(42);
        leg->Draw();*/
        char str[80];
        strcpy(str, nombres[i]);
        strcat(str, ".pdf");
        //Mass->Print(str);
        Mass->Write();
    }

    
	f1.Close();

    

    return 0;
}