// ------------------------------------------------------------------------------------------------------------------
// -------------------- Hadron-level plots --------------------
//
//                                          /**************\
// ----------------------------------------- Analysis_ttbar --------- //
//                                          \**************/


// ===== ROOT file ===== //
TFile ROOTfile(rootfile, "RECREATE");               // Name passed from main analysis



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
TH1F* m_recoil = new TH1F("m_recoil","",1000,0,5000);
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
TH1F* m_recoil2 = new TH1F("m_recoil2","",1000,0,5000);
TH1F* fatjetpostHt2 = new TH1F("fatjetpostHt2","",50,0,1);

TH1F* pt_fatjetpost = new TH1F("pt_fatjetpost","",1000,0,5000);
TH1F* pt_fatjetpost2 = new TH1F("pt_fatjetpost2","",1000,0,5000);

TH1F* goodFJ = new TH1F("goodFJ","",3,0,3);
TH1F* m_recoil05 = new TH1F("m_recoil0.5","",1000,0,5000);
TH1F* m_recoil0 = new TH1F("m_recoil0","",1000,0,5000);

TH2F* EFJvsmrecoil = new TH2F("EFJvsmrecoil","",3000,0,3000,3000,0,3000);
TH2F* m_FJvspt_FJ = new TH2F("m_FJvspt_FJ","",3000,0,3000,3000,0,3000);

TH1F* m_toplikes = new TH1F("masstoplike","",1000,0,1200);
TH1F* m_recoiltoplikes = new TH1F("mrecoil toplikes","",3000,0,3000);

TH1F* No_FJ = new TH1F("No_FJ","",5,0,5);
TH1F* No_top_FJ = new TH1F("No_top_FJ","",5,0,5);

TH2F* EFJvsmass = new TH2F("EFJvsmass","",3000,0,3000,3000,0,3000);
TH2F* EFJvspt = new TH2F("EFJvspt","",3000,0,3000,3000,0,3000);
TH2F* massvspt = new TH2F("massvspt","",3000,0,3000,3000,0,3000);

TH1F* mrecoil_top_E_cut = new TH1F("mrecoil_top_E_cut","",3000,0,3000);



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
	m_recoil->GetXaxis()->SetTitle("recoil mass [GeV]");
	m_recoil->GetYaxis()->SetTitle("# of events");
	
	m_recoil2->SetStats(0);
	m_recoil2->Rebin(1);
	m_recoil2->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil2->GetXaxis()->SetTitle("recoil mass [GeV]");
	m_recoil2->GetYaxis()->SetTitle("# of events");
	
	m_recoil05->SetStats(0);
	m_recoil05->Rebin(1);
	m_recoil05->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil05->GetXaxis()->SetTitle("recoil mass [GeV]");
	m_recoil05->GetYaxis()->SetTitle("# of events");
	
	m_recoil0->SetStats(0);
	m_recoil0->Rebin(1);
	m_recoil0->SetLineColor(2);
	//m_recoil->SetFillColor(3);
	m_recoil0->GetXaxis()->SetTitle("recoil mass [GeV]");
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
