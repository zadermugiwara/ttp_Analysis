// ------------------------------------------------------------------------------------------------------------------
// -------------------- Hadron-level plots --------------------
//
//                                          /**************\
// ----------------------------------------- Analysis_ttbar --------- //
//                                          \**************/


// ===== ROOT file ===== //
extern TFile* ROOTFILE_PTR;
if (ROOTFILE_PTR) ROOTFILE_PTR->cd();

// +++++ ROOT Tree +++++ //

TTree* ROOTdist = new TTree("Dists", "epem_ttbar"); // Easy to deal with trees

double B_LFJ_E = -999.0, B_LFJ_px = -999.0, B_LFJ_py = -999.0, B_LFJ_pz = -999.0, B_evt_weight = 0.0, B_rec = -999.0;
int    B_N_FJ = 0, B_N_SJ = 0, B_N_glep = 0;

ROOTdist -> Branch( "LFJ_E",      &B_LFJ_E,      "B_LFJ_E/D"      );
ROOTdist -> Branch( "LFJ_px",     &B_LFJ_px,     "B_LFJ_px/D"     );
ROOTdist -> Branch( "LFJ_py",     &B_LFJ_py,     "B_LFJ_py/D"     );
ROOTdist -> Branch( "LFJ_pz",     &B_LFJ_pz,     "B_LFJ_pz/D"     );
ROOTdist -> Branch( "evt_weight", &B_evt_weight, "B_evt_weight/D" );
ROOTdist -> Branch( "rec",        &B_rec,        "B_rec/D"        );

ROOTdist -> Branch( "N_FJ",   &B_N_FJ,   "B_N_FJ/I"   );
ROOTdist -> Branch( "N_SJ",   &B_N_SJ,   "B_N_SJ/I"   );
ROOTdist -> Branch( "N_glep", &B_N_glep, "B_N_glep/I" );


TTree* Tdist = new TTree("TDists", "epem_ttbar"); // Easy to deal with trees

double T_LFJ_E = -999.0, T_LFJ_px = -999.0, T_LFJ_py = -999.0, T_LFJ_pz = -999.0, T_rec = -999.0;

Tdist -> Branch( "LFJ_E",      &T_LFJ_E,      "T_LFJ_E/D"      );
Tdist -> Branch( "LFJ_px",     &T_LFJ_px,     "T_LFJ_px/D"     );
Tdist -> Branch( "LFJ_py",     &T_LFJ_py,     "T_LFJ_py/D"     );
Tdist -> Branch( "LFJ_pz",     &T_LFJ_pz,     "T_LFJ_pz/D"     );
Tdist -> Branch( "rec",        &T_rec,        "T_rec/D"        );


TH1F* deltaRjet = new TH1F("deltaRjet","",1000,-0,10);
TH1F* deltaRlepton = new TH1F("deltaRlepton","",1000,0,10);
TH1F* m_recoil = new TH1F("m_recoil","",5000,0,5000);
TH1F* m_fatjet = new TH1F("mass","",1000,0,1200);
TH1F* m_fatjetpost = new TH1F("mass_post","",1000,0,1200);
TH1F* m_fatjetlead = new TH1F("mass_lead","",1000,0,1200);
TH1F* Ht = new TH1F("Ht","",1000,0,3500);
TH1F* fatjetHt = new TH1F("fatjetHt","",100,0,2);
TH1F* fatjet2Ht = new TH1F("fatjet2Ht","",100,0,2);
TH1F* fatjetpostHt = new TH1F("fatjetpostHt","",50,0,1);

TH1F* fatjetleadHthem = new TH1F("fatjetleadHthem","",1000,0,5000);
TH1F* fatjet2Hthem = new TH1F("fatjet2Hthem","",1000,0,5000);

TH1F* m_fatjetpost2 = new TH1F("mass_post2","",1000,0,1200);
TH1F* m_recoil2 = new TH1F("m_recoil2","",5000,0,5000);
TH1F* fatjetpostHt2 = new TH1F("fatjetpostHt2","",50,0,1);

TH1F* pt_fatjetpost = new TH1F("pt_fatjetpost","",1000,0,5000);
TH1F* pt_fatjetpost2 = new TH1F("pt_fatjetpost2","",1000,0,5000);

TH1F* goodFJ = new TH1F("goodFJ","",3,0,3);
TH1F* m_recoil05 = new TH1F("m_recoil0.5","",5000,0,5000);
TH1F* m_recoil0 = new TH1F("m_recoil0","",5000,0,5000);

TH2F* EFJvsmrecoil = new TH2F("EFJvsmrecoil","",3000,0,3000,3000,0,3000);
TH2F* m_FJvspt_FJ = new TH2F("m_FJvspt_FJ","",3000,0,3000,3000,0,3000);

TH1F* m_toplikes = new TH1F("masstoplike","",1000,0,1200);
TH1F* m_recoiltoplikes = new TH1F("mrecoil toplikes","",5000,0,5000);

TH1F* No_FJ = new TH1F("No_FJ","",5,0,5);
TH1F* No_top_FJ = new TH1F("No_top_FJ","",5,0,5);

TH2F* EFJvsmass = new TH2F("EFJvsmass","",3000,0,3000,3000,0,3000);
TH2F* EFJvspt = new TH2F("EFJvspt","",3000,0,3000,3000,0,3000);
TH2F* massvspt = new TH2F("massvspt","",3000,0,3000,3000,0,3000);

TH1F* mrecoil_isolated_toplikes_rec_cut = new TH1F("mrecoil_isolated_toplikes_rec_cut","",3000,0,3000);

TH2F* mrecoilvspt = new TH2F("mrecoilvspt","",3000,0,3000,3000,0,3000);

TH2F* EvsHt = new TH2F("EvsHt","",3000,0,3000,100,0,2);
TH2F* ptvsHt = new TH2F("ptvsHt","",3000,0,3000,100,0,2);
TH2F* mrecoilvsHt = new TH2F("mrecoilvsHt","",3000,0,3000,100,0,2);

TH2F* ptfatvsHt = new TH2F("ptfatvsHt","",3000,0,3000,3000,0,3000);


TH1F* m_recoilcut = new TH1F("m_recoilcut","",1000,0,5000);
TH1F* topHt = new TH1F("topHt","",100,0,2);

TH1F* m_recoil_isolated_toplikes = new TH1F("m_recoil_isolated_toplikes","",5000,0,5000);

TH1F* TPmass = new TH1F("TPmass","",5000,0,5000);
TH1F* topmass = new TH1F("topmass","",5000,0,5000);
TH1F* topdecmass = new TH1F("topdecmass","",5000,0,5000);
TH1F* truth_recoil = new TH1F("truth_recoil","",5000,0,5000);

TH1F* truth_deltaR_jet_TP = new TH1F("truth_deltaR_jet_TP","",1000,-0,10);
TH1F* truth_deltaR_jet_top = new TH1F("truth_deltaR_jet_top","",1000,-0,10);
TH1F* truth_deltaR_jet_topdec = new TH1F("truth_deltaR_jet_topdec","",1000,-0,10);

TH1F* truth_deltaR_leptons_TP = new TH1F("truth_deltaR_leptons_TP","",1000,-0,10);
TH1F* truth_deltaR_leptons_top = new TH1F("truth_deltaR_leptons_top","",1000,-0,10);
TH1F* truth_deltaR_leptons_topdec = new TH1F("truth_deltaR_leptons_topdec","",1000,-0,10);

TH1F* truth_deltaR_fatjet_TP = new TH1F("truth_deltaR_fatjet_TP","",1000,-0,10);
TH1F* truth_deltaR_fatjet_top = new TH1F("truth_deltaR_fatjet_top","",1000,-0,10);
TH1F* truth_deltaR_fatjet_topdec = new TH1F("truth_deltaR_fatjet_topdec","",1000,-0,10);

TH2F* truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec = new TH2F("truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec","",1000,0,10,1000,0,10);


TH1F* cheat_good_deltaRjet = new TH1F("good_deltaRjet","",1000,-0,10);
TH1F* cheat_good_deltaRlepton = new TH1F("good_deltaRlepton","",1000,0,10);
TH1F* cheat_good_m_recoil = new TH1F("good_m_recoil","",5000,0,5000);
TH1F* cheat_good_m_fatjet = new TH1F("good_m_fatjet","",1000,0,1200);
TH1F* cheat_good_pt_fatjet = new TH1F("good_pt_fatjet","",3000,0,3000);
TH1F* cheat_good_E_fatjet = new TH1F("good_E_fatjet","",3000,0,3000);
TH1F* cheat_good_Ht_fatjet = new TH1F("good_Ht_fatjet","",100,0,2);



TH1F* cheat_bad_deltaRjet = new TH1F("bad_deltaRjet","",1000,-0,10);
TH1F* cheat_bad_deltaRlepton = new TH1F("bad_deltaRlepton","",1000,0,10);
TH1F* cheat_bad_m_recoil = new TH1F("bad_m_recoil","",5000,0,5000);
TH1F* cheat_bad_m_fatjet = new TH1F("bad_m_fatjet","",1000,0,1200);
TH1F* cheat_bad_pt_fatjet = new TH1F("bad_pt_fatjet","",3000,0,3000);
TH1F* cheat_bad_E_fatjet = new TH1F("bad_E_fatjet","",3000,0,3000);
TH1F* cheat_bad_Ht_fatjet = new TH1F("bad_Ht_fatjet","",100,0,2);

TH1F* XS = new TH1F("Cross_Section","",100000000,0,1);
TH1F* no_sim = new TH1F("no_sim","",100000000,0,10000000);
TH1F* Miss_Energy = new TH1F("Miss_Energy","",3000,0,3000);

TH1F* mrecoil_isolated_toplikes_rec_missE_cut = new TH1F("mrecoil_isolated_toplikes_rec_missE_cut","",5000,0,5000);

TH2F* METvsmrecoil = new TH2F("METvsmrecoil","",5000,0,5000,5000,0,5000);

TH1F* massetacut = new TH1F("massetacut","",5000,0,5000);


TH1F* mrecoil_isolated_toplikes_subestructure_cut = new TH1F("mrecoil_isolated_toplikes_subestructure_cut","",5000,0,5000);

TH1F* mrecoil_BDT1200_cut = new TH1F("mrecoil_BDT1200_cut","",5000,0,5000);
TH1F* mrecoil_BDT1600_cut = new TH1F("mrecoil_BDT1600_cut","",5000,0,5000);
TH1F* mrecoil_BDT2000_cut = new TH1F("mrecoil_BDT2000_cut","",5000,0,5000);
TH1F* mrecoil_BDT2400_cut = new TH1F("mrecoil_BDT2400_cut","",5000,0,5000);




TH1F* mrecoil_BDT_ttbar = new TH1F("mrecoil_BDT_ttbar","",5000,0,5000);




TTree* BDT = new TTree("BDT", "epem_ttbar"); // Easy to deal with trees

float ptjet1 = -999.0, ptjet2 = -999.0, ptjet3 = -999.0, ptjet4 = -999.0, pt_FJ_BDT = -999.00, Ht_BDT = -999.0, weight_BDT = -999.0;
float   No_FJ_BDT = 0, No_jets_BDT = 0, No_leptons_BDT = 0;


BDT -> Branch( "ptjet1",     &ptjet1,     "ptjet1/F"     );
BDT -> Branch( "ptjet2",     &ptjet2,     "ptjet2/F"     );
BDT -> Branch( "ptjet3",     &ptjet3,     "ptjet3/F"     );
BDT -> Branch( "ptjet4",     &ptjet4,     "ptjet4/F"     );
BDT -> Branch( "pt_FJ_BDT",  &pt_FJ_BDT,  "pt_FJ_BDT/F"  );
BDT -> Branch( "Ht_BDT",     &Ht_BDT,     "Ht_BDT/F"     );
BDT -> Branch( "weight_BDT", &weight_BDT, "weight_BDT/F" );


BDT -> Branch( "No_FJ_BDT",      &No_FJ_BDT,   "No_FJ_BDT/F"      );
BDT -> Branch( "No_jets_BDT",    &B_N_SJ,      "No_jets_BDT/F"    );
BDT -> Branch( "No_leptons_BDT", &B_N_glep,    "No_leptons_BDT/F" );

#include "tmva.hh"



/*TH1F* ptjet1 = new TH1F("ptjet1","",5000,0,5000);
TH1F* ptjet2 = new TH1F("ptjet2","",5000,0,5000);
TH1F* ptjet3 = new TH1F("ptjet3","",5000,0,5000);
TH1F* ptjet4 = new TH1F("ptjet4","",5000,0,5000);


TH1F* No_FJ_BDT = new TH1F("No_FJ_BDT","",15,0,15);
TH1F* No_jets_BDT = new TH1F("No_jets_BDT","",15,0,15);
TH1F* No_leptons_BDT = new TH1F("No_leptons_BDT","",15,0,15);
TH1F* Ht_BDT = new TH1F("Ht_BDT","",3500,0,3500);

TH1F* pt_FJ_BDT = new TH1F("pt_FJ_BDT","",5000,0,5000);*/

















        deltaRjet->SetStats(0);
        //Eta_post->Rebin(10);
	deltaRjet->SetLineColor(2);
	//deltaRjet->SetFillColor(3);
	deltaRjet->GetXaxis()->SetTitle("#Delta R_{jet}");
	deltaRjet->GetYaxis()->SetTitle("# of events");
	
	deltaRlepton->SetStats(0);
        //Eta_post->Rebin(10);
	deltaRlepton->SetLineColor(2);
	//deltaRelectron->SetFillColor(3);
	deltaRlepton->GetXaxis()->SetTitle("#Delta R_{electron}");
	deltaRlepton->GetYaxis()->SetTitle("# of events");
	
	m_recoil->SetStats(0);
	m_recoil->Rebin(1);
	m_recoil->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil->GetXaxis()->SetTitle("Recoil mass [GeV]");
	m_recoil->GetYaxis()->SetTitle("# of events");
	
	m_recoil2->SetStats(0);
	m_recoil2->Rebin(1);
	m_recoil2->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil2->GetXaxis()->SetTitle("Recoil mass [GeV]");
	m_recoil2->GetYaxis()->SetTitle("# of events");
	
	m_recoil05->SetStats(0);
	m_recoil05->Rebin(1);
	m_recoil05->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil05->GetXaxis()->SetTitle("Recoil mass [GeV]");
	m_recoil05->GetYaxis()->SetTitle("# of events");
	
	m_recoil0->SetStats(0);
	m_recoil0->Rebin(1);
	m_recoil0->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil0->GetXaxis()->SetTitle("Recoil mass [GeV]");
	m_recoil0->GetYaxis()->SetTitle("# of events");
	
	m_fatjet->SetStats(0);
	m_fatjet->Rebin(1);
	m_fatjet->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_fatjet->GetXaxis()->SetTitle("mass [GeV]");
	m_fatjet->GetYaxis()->SetTitle("# of events");
	
	m_fatjetpost->SetStats(0);
	m_fatjetpost->Rebin(1);
	m_fatjetpost->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_fatjetpost->GetXaxis()->SetTitle("mass_post [GeV]");
	m_fatjetpost->GetYaxis()->SetTitle("# of events");
	
	m_fatjetpost2->SetStats(0);
	m_fatjetpost2->Rebin(1);
	m_fatjetpost2->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_fatjetpost2->GetXaxis()->SetTitle("mass_post [GeV]");
	m_fatjetpost2->GetYaxis()->SetTitle("# of events");
	
	m_fatjetlead->SetStats(0);
	m_fatjetlead->Rebin(1);
	m_fatjetlead->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_fatjetlead->GetXaxis()->SetTitle("mass_lead [GeV]");
	m_fatjetlead->GetYaxis()->SetTitle("# of events");
	
	
	Ht->SetStats(0);
	Ht->Rebin(1);
	Ht->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	Ht->GetXaxis()->SetTitle("Ht [GeV]");
	Ht->GetYaxis()->SetTitle("# of events");

	
	EFJvsmrecoil->SetStats(0);
	EFJvsmrecoil->Rebin(1);
	EFJvsmrecoil->GetXaxis()->SetTitle("Energy [GeV]");
	EFJvsmrecoil->GetYaxis()->SetTitle("Recoil mass [GeV]");

	
	m_FJvspt_FJ->SetStats(0);
	m_FJvspt_FJ->Rebin(1);
	m_FJvspt_FJ->GetXaxis()->SetTitle("mass [GeV]");
	m_FJvspt_FJ->GetYaxis()->SetTitle("pt [GeV]");

	EFJvsmass->SetStats(0);
	EFJvsmass->Rebin(1);
	EFJvsmass->GetXaxis()->SetTitle("Energy [GeV]");
	EFJvsmass->GetYaxis()->SetTitle("mass [GeV]");

	EFJvspt->SetStats(0);
	EFJvspt->Rebin(1);
	EFJvspt->GetXaxis()->SetTitle("Energy [GeV]");
	EFJvspt->GetYaxis()->SetTitle("pt [GeV]");


	massvspt->SetStats(0);
	massvspt->Rebin(1);
	massvspt->GetXaxis()->SetTitle("mass[GeV]");
	massvspt->GetYaxis()->SetTitle("pt [GeV]");

	mrecoilvspt->SetStats(0);
	mrecoilvspt->Rebin(1);
	mrecoilvspt->GetXaxis()->SetTitle("Recoil mass [GeV]");
	mrecoilvspt->GetYaxis()->SetTitle("pt [GeV]");

	EvsHt->SetStats(0);
	EvsHt->Rebin(1);
	EvsHt->SetLineColor(2);
	EvsHt->GetXaxis()->SetTitle("Energy [GeV]");
	EvsHt->GetYaxis()->SetTitle("Relative Ht");
	

	ptvsHt->SetStats(0);
	ptvsHt->Rebin(1);
	ptvsHt->GetXaxis()->SetTitle("pt [GeV]");
	ptvsHt->GetYaxis()->SetTitle("Relative Ht");

	mrecoilvsHt->SetStats(0);
	mrecoilvsHt->Rebin(1);
	mrecoilvsHt->GetXaxis()->SetTitle("Recoil mass [GeV]");
	mrecoilvsHt->GetYaxis()->SetTitle("Relative Ht");

	ptfatvsHt->SetStats(0);
	ptfatvsHt->Rebin(1);
	ptfatvsHt->GetXaxis()->SetTitle("pt [GeV]");
	ptfatvsHt->GetYaxis()->SetTitle("Ht [GeV]");

	truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec->SetStats(0);
	truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec->Rebin(1);
	truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec->GetXaxis()->SetTitle("deltaR fatjet truthtop");
	truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec->GetYaxis()->SetTitle("deltaR fatjet truthtopdec");

	
	METvsmrecoil->SetStats(0);
	METvsmrecoil->Rebin(1);
	METvsmrecoil->GetXaxis()->SetTitle("Missing Energy [GeV]");
	METvsmrecoil->GetYaxis()->SetTitle("Recoil mass [GeV]");

	fatjetleadHthem->SetStats(0);
fatjet2Hthem->SetStats(0); 
m_fatjetpost2->SetStats(0);
m_recoil2->SetStats(0); 
fatjetpostHt2->SetStats(0); 

pt_fatjetpost->SetStats(0); 
pt_fatjetpost2->SetStats(0); 

goodFJ->SetStats(0); 
m_recoil05->SetStats(0);
m_recoil0->SetStats(0); 

m_toplikes->SetStats(0); 
m_recoiltoplikes->SetStats(0);
No_FJ->SetStats(0); 
No_top_FJ->SetStats(0); 

mrecoil_isolated_toplikes_rec_cut->SetStats(0);

m_recoilcut->SetStats(0);
topHt->SetStats(0); 
m_recoil_isolated_toplikes->SetStats(0);

TPmass->SetStats(0); 
topmass->SetStats(0); 
topdecmass->SetStats(0); 
truth_recoil->SetStats(0); 

truth_deltaR_jet_TP->SetStats(0); 
truth_deltaR_jet_top->SetStats(0); 
truth_deltaR_jet_topdec->SetStats(0); 

truth_deltaR_leptons_TP->SetStats(0); 
truth_deltaR_leptons_top->SetStats(0); 
truth_deltaR_leptons_topdec->SetStats(0); 

truth_deltaR_fatjet_TP->SetStats(0);
truth_deltaR_fatjet_top->SetStats(0); 
truth_deltaR_fatjet_topdec->SetStats(0); 

cheat_good_deltaRjet->SetStats(0); 
cheat_good_deltaRlepton->SetStats(0);
cheat_good_m_recoil->SetStats(0); 
cheat_good_m_fatjet->SetStats(0); 
cheat_good_pt_fatjet->SetStats(0);
cheat_good_E_fatjet->SetStats(0); 
cheat_good_Ht_fatjet->SetStats(0);



cheat_bad_deltaRjet->SetStats(0); 
cheat_bad_deltaRlepton->SetStats(0); 
cheat_bad_m_recoil->SetStats(0); 
cheat_bad_m_fatjet->SetStats(0); 
cheat_bad_pt_fatjet->SetStats(0);
cheat_bad_E_fatjet->SetStats(0); 
cheat_bad_Ht_fatjet->SetStats(0);

Miss_Energy->SetStats(0);

mrecoil_isolated_toplikes_rec_missE_cut->SetStats(0);

massetacut->SetStats(0);

mrecoil_isolated_toplikes_subestructure_cut->SetStats(0);

mrecoil_BDT1200_cut->SetStats(0);
mrecoil_BDT1600_cut->SetStats(0);
mrecoil_BDT2000_cut->SetStats(0);
mrecoil_BDT2400_cut->SetStats(0);

fatjetleadHthem->GetYaxis()->SetTitle("Relative Ht");
fatjet2Hthem->GetYaxis()->SetTitle("Relative Ht"); 
m_fatjetpost2->GetYaxis()->SetTitle("mass [GeV]");
m_recoil2->GetYaxis()->SetTitle("Recoil mass [GeV]"); 
fatjetpostHt2->GetYaxis()->SetTitle("Relative Ht"); 

pt_fatjetpost->GetYaxis()->SetTitle("pt [GeV]"); 
pt_fatjetpost2->GetYaxis()->SetTitle("pt [GeV]"); 

goodFJ->GetYaxis()->SetTitle("No. good fatjet"); 
m_recoil05->GetYaxis()->SetTitle("Recoil mass [GeV]");
m_recoil0->GetYaxis()->SetTitle("Recoil mass [GeV]"); 

m_toplikes->GetYaxis()->SetTitle("mass [GeV]"); 
m_recoiltoplikes->GetYaxis()->SetTitle("Recoil mass [GeV]");
No_FJ->GetYaxis()->SetTitle("No. fatjet"); 
No_top_FJ->GetYaxis()->SetTitle("No. fatjet"); 

mrecoil_isolated_toplikes_rec_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");

m_recoilcut->GetYaxis()->SetTitle("Recoil mass [GeV]");
topHt->GetYaxis()->SetTitle("Ht [GeV]"); 
m_recoil_isolated_toplikes->GetYaxis()->SetTitle("Recoil mass [GeV]");

TPmass->GetYaxis()->SetTitle("mass [GeV]"); 
topmass->GetYaxis()->SetTitle("mass [GeV]"); 
topdecmass->GetYaxis()->SetTitle("mass [GeV]"); 
truth_recoil->GetYaxis()->SetTitle("Recoil mass [GeV]"); 

truth_deltaR_jet_TP->GetYaxis()->SetTitle("#Delta R_{T}"); 
truth_deltaR_jet_top->GetYaxis()->SetTitle("#Delta R_{top}"); 
truth_deltaR_jet_topdec->GetYaxis()->SetTitle("#Delta R_{topdec}"); 

truth_deltaR_leptons_TP->GetYaxis()->SetTitle("#Delta R_{T}"); 
truth_deltaR_leptons_top->GetYaxis()->SetTitle("#Delta R_{top}"); 
truth_deltaR_leptons_topdec->GetYaxis()->SetTitle("#Delta R_{topdec}"); 

truth_deltaR_fatjet_TP->GetYaxis()->SetTitle("#Delta R_{T}");
truth_deltaR_fatjet_top->GetYaxis()->SetTitle("#Delta R_{top}"); 
truth_deltaR_fatjet_topdec->GetYaxis()->SetTitle("#Delta R_{topdec}"); 

cheat_good_deltaRjet->GetYaxis()->SetTitle("#Delta R_{jet}"); 
cheat_good_deltaRlepton->GetYaxis()->SetTitle("#Delta R_{lepton}");
cheat_good_m_recoil->GetYaxis()->SetTitle("Recoil mass [GeV]"); 
cheat_good_m_fatjet->GetYaxis()->SetTitle("mass [GeV]"); 
cheat_good_pt_fatjet->GetYaxis()->SetTitle("pt [GeV]");
cheat_good_E_fatjet->GetYaxis()->SetTitle("Energy [GeV]"); 
cheat_good_Ht_fatjet->GetYaxis()->SetTitle("Relative Ht");



cheat_bad_deltaRjet->GetYaxis()->SetTitle("#Delta R_{jet}"); 
cheat_bad_deltaRlepton->GetYaxis()->SetTitle("#Delta R_{lepton}"); 
cheat_bad_m_recoil->GetYaxis()->SetTitle("Recoil mass [GeV]"); 
cheat_bad_m_fatjet->GetYaxis()->SetTitle("mass [GeV]"); 
cheat_bad_pt_fatjet->GetYaxis()->SetTitle("pt [GeV]");
cheat_bad_E_fatjet->GetYaxis()->SetTitle("Energy [GeV]"); 
cheat_bad_Ht_fatjet->GetYaxis()->SetTitle("Relative Ht");

Miss_Energy->GetYaxis()->SetTitle("Missing Energy [GeV]");

mrecoil_isolated_toplikes_rec_missE_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");

massetacut->GetYaxis()->SetTitle("mass [GeV]");

mrecoil_isolated_toplikes_subestructure_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");

mrecoil_BDT1200_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");
mrecoil_BDT1600_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");
mrecoil_BDT2000_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");
mrecoil_BDT2400_cut->GetYaxis()->SetTitle("Recoil mass [GeV]");


	
