// ---------------------------------------------------------------------------------------------------------------------------------------
// ···································································································· //
// ···································································································· //
//
// --- NOTE: In order to execute, command-line arguments are:
//
//           $> ./ttp_Analysis NAME_OF_FILE
//
//           where the string 'NAME_OF_FILE' is the section between the asterisks in
//           in the route: files/list_all_files_*NAME_OF_FILE*
//
// ****************************************************************************
// ***** IMPORTANT: CODE DOES NOT VALIDATE AGAINST COMMAND-LINE ARGUMENTS *****
// ****************************************************************************


// ···································································································· //
// ···································································································· //
// ···································································································· //

#include "Headers_Analysis/headers.hh"  // Contains all headers needed to run the analysis
#include <exception>
#include <TSystem.h>

#ifndef ASE_OBJECT_ETA_MAX
#define ASE_OBJECT_ETA_MAX 2.5
#endif

TFile* ROOTFILE_PTR = nullptr;
bool ROOTFILE_OK = false;

double env_double(const char* name, double fallback)
{
  const char* value = std::getenv(name);
  if(!value || std::strlen(value) == 0) return fallback;
  return std::atof(value);
}

int env_int(const char* name, int fallback)
{
  const char* value = std::getenv(name);
  if(!value || std::strlen(value) == 0) return fallback;
  return std::atoi(value);
}

int sample_poisson(double mean)
{
  if(mean <= 0.0) return 0;
  const double limit = std::exp(-mean);
  int k = 0;
  double product = 1.0;
  do {
    k++;
    product *= (std::rand() + 1.0) / (RAND_MAX + 1.0);
  } while(product > limit);
  return k - 1;
}

class GammaGammaOverlay
{
public:
  GammaGammaOverlay()
    : current_file_(0), reader_(0), fixed_bx_(0), mean_bx_(0.0),
      eta_max_(2.5), pt_min_(0.1), drop_forward_soft_(0),
      forward_eta_min_(2.0), forward_pt_max_(2.0) {}

  ~GammaGammaOverlay()
  {
    if(reader_) {
      delete reader_;
      reader_ = 0;
    }
  }

  void configure(double default_eta_max, double default_pt_min)
  {
    const char* list_path = std::getenv("ASE_GG_OVERLAY_LIST");
    if(list_path && std::strlen(list_path) > 0) {
      std::ifstream input(list_path);
      std::string line;
      while(std::getline(input, line)) {
        if(line.empty() || line[0] == '#') continue;
        files_.push_back(line);
      }
    }

    fixed_bx_ = env_int("ASE_GG_OVERLAY_BX", 0);
    mean_bx_ = env_double("ASE_GG_OVERLAY_MEAN_BX", 0.0);
    eta_max_ = env_double("ASE_GG_OVERLAY_ETA_MAX", default_eta_max);
    pt_min_ = env_double("ASE_GG_OVERLAY_PT_MIN", default_pt_min);
    drop_forward_soft_ = env_int("ASE_GG_OVERLAY_DROP_FORWARD_SOFT", 0);
    forward_eta_min_ = env_double("ASE_GG_OVERLAY_FORWARD_ETA_MIN", 2.0);
    forward_pt_max_ = env_double("ASE_GG_OVERLAY_FORWARD_PT_MAX", 2.0);
    std::srand(env_int("ASE_GG_OVERLAY_SEED", 12345));
  }

  bool enabled() const
  {
    return !files_.empty() && (fixed_bx_ > 0 || mean_bx_ > 0.0);
  }

  int events_for_hard_event() const
  {
    if(mean_bx_ > 0.0) return sample_poisson(mean_bx_);
    return fixed_bx_;
  }

  GenEvent* next_event()
  {
    if(files_.empty()) return 0;
    const unsigned max_attempts = files_.size() + 1;
    for(unsigned attempt = 0; attempt < max_attempts; ++attempt) {
      if(!reader_) {
        reader_ = new IO_GenEvent(files_[current_file_], std::ios::in);
      }
      GenEvent* evt = reader_->read_next_event();
      if(evt) return evt;
      delete reader_;
      reader_ = 0;
      current_file_ = (current_file_ + 1) % files_.size();
    }
    return 0;
  }

  bool keep_particle(const PseudoJet& momentum) const
  {
    if(momentum.pt() < pt_min_) return false;
    if(std::fabs(momentum.eta()) > eta_max_) return false;
    if(drop_forward_soft_ && std::fabs(momentum.eta()) > forward_eta_min_ && momentum.pt() < forward_pt_max_) return false;
    return true;
  }

  std::string summary() const
  {
    std::ostringstream out;
    out << "files=" << files_.size()
        << ", fixed_bx=" << fixed_bx_
        << ", mean_bx=" << mean_bx_
        << ", eta_max=" << eta_max_
        << ", pt_min=" << pt_min_;
    return out.str();
  }

private:
  std::vector<std::string> files_;
  unsigned current_file_;
  IO_GenEvent* reader_;
  int fixed_bx_;
  double mean_bx_;
  double eta_max_;
  double pt_min_;
  int drop_forward_soft_;
  double forward_eta_min_;
  double forward_pt_max_;
};

void append_overlay_particles(
  const GenEvent* overlay_evt,
  const GammaGammaOverlay& overlay,
  std::vector<PseudoJet>& hadrons,
  std::vector<PseudoJet>& leptons,
  PseudoJet& pvisible,
  double& visible_energy
)
{
  for(GenEvent::particle_const_iterator p = overlay_evt->particles_begin(); p != overlay_evt->particles_end(); ++p) {
    const int pdgid = (*p)->pdg_id();
    const int apdgid = std::abs(pdgid);
    if((*p)->status() != 1 || (*p)->end_vertex()) continue;
    if(apdgid == 12 || apdgid == 14 || apdgid == 16) continue;

    PseudoJet momentum(
      (*p)->momentum().px(),
      (*p)->momentum().py(),
      (*p)->momentum().pz(),
      (*p)->momentum().e()
    );
    momentum.set_user_index(pdgid);
    if(!overlay.keep_particle(momentum)) continue;

    visible_energy += momentum.e();
    pvisible += momentum;
    if(apdgid == 11 || apdgid == 13) {
      leptons.push_back(momentum);
    } else {
      hadrons.push_back(momentum);
    }
  }
}


// ···································································································· //
// ···································································································· //
// ···································································································· //


// ====================== //
// === BEGIN ANALYSIS === //
// ====================== //

int main(int argc, char* argv[])
{ 
  if (argc < 2) {
    std::cerr << "Usage: " << argv[0] << " DATASET_NAME\n";
    return 2;
  }
  // **************************** //
  // *** PARAMETERS & OBJECTS *** //
  // **************************** //
  
  // ------------------------------------ //
  // ----- Events, files & settings ----- //
  // ------------------------------------ //
  
  // ***** File to read-in HepMC files from *****
  
  string   _AnalysisN_(argv[1]);
  string   list_of_file = "files/list_all_files_" + _AnalysisN_;// HepMC route
  ifstream fin(list_of_file.c_str());
  string   name_of_file;
  int      no_of_files = 0;
  getline(fin, name_of_file);
  
    
  // ***** Output/log file *****
  
  ofstream outfile;
  gSystem->mkdir("output", true);
  outfile.open("output/out_" + _AnalysisN_ + ".dat");

  
  // ***** ROOT file *****
  
  gSystem->mkdir("root", true);
  string rootname("root/" + _AnalysisN_ + ".root");
  const char *rootfile(rootname.c_str());
  ROOTFILE_PTR = TFile::Open(rootfile, "RECREATE");
  ROOTFILE_OK = ROOTFILE_PTR && ROOTFILE_PTR->IsOpen();
  if (!ROOTFILE_OK) {
    std::cerr << "[WARN] Could not open ROOT file: " << rootname << "\n";
  }
  
#include "Headers_Analysis/plots.hh"    // ===== List of branches =====
//#include "Headers_Analysis/tmva.hh"

  
  // ***** Events to be analysed *****
  
  int number_of_events = 1000000;        // ===== Number of events per HepMC file =====


  
  // -------------------------- //
  // ----- Define objects ----- //
  // -------------------------- //
  
  // ***** Jets *****
  
  vector<double> RR         = {0.5, 1.0};      // ===== Jet 'radius' for small R jets and fatjets =====
  vector<double> pTmin_jets = {20, 100.0};     // ===== Minimum pT for small R jets and fatjets =====
  
   //Valencia Algorithm
  /*contrib::ValenciaPlugin* vlc_plugin_a = new contrib::ValenciaPlugin(RR[0], 1.0, 1.0);
  JetDefinition jet_def_a(vlc_plugin_a);

  contrib::ValenciaPlugin* vlc_plugin_b = new contrib::ValenciaPlugin(RR[1], 1.0, 1.0);
  JetDefinition jet_def_b(vlc_plugin_b);*/

  // Anti-kt algorithm
  /*JetDefinition jet_def_a(antikt_algorithm, RR[0]);
  JetDefinition jet_def_b(antikt_algorithm, RR[1]);*/
  
  // Cambridge algorithm
  JetDefinition jet_def_a(cambridge_algorithm, RR[0]);
  JetDefinition jet_def_b(cambridge_algorithm, RR[1]);
  
  
  // ***** Experimental cuts *****
  
  double etamax_objects = ASE_OBJECT_ETA_MAX;  // === Nominal detector fiducial range ===
  double etamax_leptons = 2.5;                 // === Tracker range for isolated leptons ===
  double pTmin          = 0.1;                 // === Minimum pT for optimal resolution ===
  GammaGammaOverlay gg_overlay;
  gg_overlay.configure(etamax_objects, pTmin);
  if(gg_overlay.enabled()) {
    cout << "[OVERLAY] gamma gamma -> hadrons overlay enabled: " << gg_overlay.summary() << endl;
    outfile << "[OVERLAY] gamma gamma -> hadrons overlay enabled: " << gg_overlay.summary() << endl;
  }
  
  
  
  // -------------------- //
  // ----- Counters ----- //
  // -------------------- //
  
  // ***** XS and event counters *****
  
  double CrossSection = 0.0;                                         // === Keeps track of XS from all analysed events ===
  double totalxs      = 0.0;
  double EvtWeight    = 0.0;                                         // === Keeps track of per-event weight ===
  int    total_events = 0;                                           // === All events analysed in list_all_files ===
  int    icount       = 0;                                           // === Event counter per HepMC file ===
  int    cf[12]        = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};       // === Cutflow counter === 
  double Luminosity   = 5*(pow(10, 18));
  
  // ***** cuts
  int    mass_cut           = 140 ;  
  int    pt_cut             = 400 ;
  int    m_recoil_cut       = 1100;
  int    missing_energy_cut = 1000;
  
  string CF[12] = {"All    ", "Fatjet ","top tagged", "subestructure cut", "Isolated", "M recoil > " + to_string(m_recoil_cut), "Miss Energy < " + to_string(missing_energy_cut), "BDT ttbar", "BDT 1200", "BDT 1600", "BDT 2000", "BDT 2400"};    // === Cutflow labels ===


  
  // ---------------------- //
  // ----- PseudoJets ----- //
  // ---------------------- //

  PseudoJet momentum(0.0, 0.0, 0.0, 0.0);         // === Momentum of each particle ===
  PseudoJet pvisible(0.0, 0.0, 0.0, 0.0);         // === All the visible momentum in each event ===
  
  vector<PseudoJet> hadrons;                      // === For each event's hadrons' Pseudojets ===
  vector<PseudoJet> leptons;                      // === For each event's leptons' Pseudojets ===
  
  vector<PseudoJet> jets;                         // === For the Pseudojets of every jet with fixed radius ===
  vector<vector<PseudoJet>> jets_matrix;          // === For the Pseudojets of every jet ===

  PseudoJet TP(0.0, 0.0, 0.0, 0.0);
  PseudoJet top(0.0, 0.0, 0.0, 0.0);
  PseudoJet topdec(0.0, 0.0, 0.0, 0.0);
  vector<PseudoJet> btagger;

  
  // ***** Classes for HepMC objects ***
  
  Is_FinalState IsFinalState;
  Is_electron IsElectron;
  Is_muon IsMuon;
  Is_nu IsNu;

  
  // ***** Variables for event classification *****

  int Njets[2] = {0, 0};    // === Array for the number of jets with each radius ===
  
  
// ···································································································· //
// ···································································································· //
// ···································································································· //
  
  // ***************************** //
  // **** INITIAL FORMALITIES **** //
  // ***************************** //	  	 	  
  
  begin_analysis(_AnalysisN_, &outfile);
  t0 = clock();
  
  
// ···································································································· //
// ···································································································· //
// ···································································································· //

  
  // **************************** //
  // *** READ-IN HEPMC EVENTS *** //
  // **************************** //
  
  while(fin)
    {
    //===============YO====================
    /*string rootname("root/" + _AnalysisN_ + (no_of_files*400 + 1200) + ".root");
  const char *rootfile(rootname.c_str());
  #include "Headers_Analysis/plots.hh"*/
  //=====================================
    
    
    
      // ***** Formalities *****
      
      icount = 0;
      for(unsigned i = 0; i < ( sizeof(cf) / sizeof(int) ); i++) cf[i] = 0;
      info_analysis(number_of_events, list_of_file, name_of_file, &outfile);
      CrossSection = 0;
      
      // ***** Begin reading events *****
      
      IO_GenEvent ascii_in(name_of_file, std::ios::in);
      GenEvent* evt = ascii_in.read_next_event();
      
      while(evt)
	{
	  if(icount == number_of_events) break;
	  
	  icount++;
	  total_events++;
	  
	  if(total_events % 10000 == 0)
	    {
	      tf = clock();
	      cout << "Event " << total_events << "\t[" << ((float)tf - (float)t0)/1e+06 << " s]" << endl;
	    }
	  
	  EvtWeight = (evt) -> weights()[0];
	  CrossSection += EvtWeight;
	  cf[0]++;                           // =============================================================== Cutflow 0 =============================================================
	  double missing_energy = 0;
	  
	  // -------------------------------------------------------- //
	  // --- Search for final-state objects and classify them --- //
	  // -------------------------------------------------------- //

	  // ***** Clear PseudoJet vectors and reset Pseudojets *****
	  
	  hadrons.clear();
	  leptons.clear();
    btagger.clear();
    TP.reset(0.0, 0.0, 0.0, 0.0);
    top.reset(0.0, 0.0, 0.0, 0.0);
    topdec.reset(0.0, 0.0, 0.0, 0.0);
	  momentum.reset(0.0, 0.0, 0.0, 0.0);
	  pvisible.reset(0.0, 0.0, 0.0, 0.0);

//=================Higidios=================
//double Ptotal = 0;
//==================================
	  
	  // ***** Loop over all particles in the event *****
	  //cout << "\t  YOOOOOOOOOOOOOOOOOOOOOO" << endl;
	  for(GenEvent::particle_const_iterator p = evt -> particles_begin(); p != evt -> particles_end(); ++p)
	    {
	      
        
        if((*p)->status() == 22){
          
          if(abs((*p) -> pdg_id()) == 6000006){
            TP.reset( (*p) -> momentum().px(),
			      (*p) -> momentum().py(),
			      (*p) -> momentum().pz(),
			      (*p) -> momentum().e() );
            continue;
          }
          if(abs((*p) -> pdg_id()) == 6){
            GenVertex::particle_iterator mother = (*p)->production_vertex()->particles_begin(HepMC::parents);
            if(abs((*mother) -> pdg_id())==11){
              top.reset( (*p) -> momentum().px(),
			        (*p) -> momentum().py(),
			        (*p) -> momentum().pz(),
			        (*p) -> momentum().e() );                                                                                       
              continue;
            }
            if(abs((*mother) -> pdg_id()) == 6000006){
              topdec.reset( (*p) -> momentum().px(),
			        (*p) -> momentum().py(),
			        (*p) -> momentum().pz(),
			        (*p) -> momentum().e() );
              continue;
            } 
            continue;
          } 
          
          continue;
        }
        /*if(abs((*p) -> pdg_id())==6){
          cout     <<             (*p) ->status()      << endl;
          if ( (*p)->production_vertex() ) {
		    for ( GenVertex::particle_iterator mother = (*p)->production_vertex()->particles_begin(HepMC::parents);
            mother != (*p)->production_vertex()->
			      particles_end(HepMC::parents); 
			      ++mother ) {
			    cout << "\t "<<(*mother)->pdg_id() << endl; 
			    
		    }
        } 
        }*/
        //if((*p)->status() == 51){
          if(abs((*p) -> pdg_id()) == 5){
            //cout << "\t "<<(*p)->pdg_id() << endl;
            //cout << "\t "<<(*p)->status() << endl;
            momentum.reset( (*p) -> momentum().px(),
			      (*p) -> momentum().py(),
			      (*p) -> momentum().pz(),
			      (*p) -> momentum().e() );
            btagger.push_back(momentum);
            continue;
          }
          //continue;
        //}
        
        if( !IsFinalState(*p) ) continue;        // === Look into FS objects only
	      
	      
	      // --- Read particle's momentum and pdgid ---
	      
	      momentum.reset( (*p) -> momentum().px(),
			      (*p) -> momentum().py(),
			      (*p) -> momentum().pz(),
			      (*p) -> momentum().e() );
	      
	      momentum.set_user_index( (*p) -> pdg_id() );
	      
	      
	      // --- Ignore FS neutrinos --- 
	      
	      if( IsNu(*p) ) continue;
	      
	      
	      // --- Detector's acceptance and resolution ---
	      
	      if( !(fabs(momentum.eta()) < etamax_objects) || momentum.pt() < pTmin ) continue;
	      
	      
	      
	      missing_energy += momentum.e();
	      
	      // --- FS charged leptons ---
	      	      
	      if( IsElectron(*p) || IsMuon(*p) )
		    { 
		      leptons.push_back(momentum);
		      pvisible += momentum;
		      continue;
		    }
		
	      //=================Ht (Modificación Higinio)===================
	      //if(momentum.user_index() != 22)  
        //Ptotal += momentum.pt();
	      //==============================================================
	      
	      // --- Hadrons and photons ---
	      
	      hadrons.push_back(momentum);
	      pvisible += momentum;
	      
	    }
	  // +++++ End HepMC particles loop +++++
	  // ------------------------------------

    if(gg_overlay.enabled()) {
      const int overlay_events = gg_overlay.events_for_hard_event();
      for(int ibx = 0; ibx < overlay_events; ++ibx) {
        GenEvent* overlay_evt = gg_overlay.next_event();
        if(!overlay_evt) break;
        append_overlay_particles(overlay_evt, gg_overlay, hadrons, leptons, pvisible, missing_energy);
        delete overlay_evt;
      }
    }
	  
	  
	  // ------------------------ //
	  // --- Isolated leptons --- //
	  // ------------------------ //
	  
	  // ***** Identify isolated leptons and leave them in the 'leptons' vector *****
	  // ***** Non-isolated electrons are moved into the 'hadrons' vector and non-isolated muons are erased *****

	  isolated_leptons(leptons, hadrons);

	  
	  // ***** Erase isolated leptons that are outside the detector's acceptance *****
	  
	  for(unsigned i = 0; i < leptons.size(); i++)
	    if( fabs(leptons[i].eta()) > etamax_leptons )
	      {
		      leptons.erase( leptons.begin() + i );
		      i--;
	      }
	  
	  
	  // ***** Veto events with more than one good lepton (tentatively fully leptonic events) *****
	  // ***** 'vetoEvent' is defined at Headers_Analysis/headers.hh *****

	  //if( leptons.size() > 1 )  vetoEvent;
	  
	  
	  
	  // -------------------------- //
	  // --- Sort objects by pT --- //
	  // -------------------------- //
	  
	  hadrons = sorted_by_pt(hadrons);
	  leptons = sorted_by_pt(leptons);
	  
	  
// ···································································································· //
// ···································································································· //
// ···································································································· //
	  
	  
	  // ----------------------- //
	  // --- Cluster hadrons --- //
	  // ----------------------- //

	  // ***** Put hadrons and jet definitions into ClusterSequences *****
	  
	  ClusterSequence clust_seq_a(hadrons, jet_def_a);     // === Small R jets
	  ClusterSequence clust_seq_b(hadrons, jet_def_b);     // === Fatjets
	  
	  
	  // ***** Fill jets_matrix: jets_matrix[i][n] is the n-th jet with the i-th radius *****
	  
	  jets_matrix.clear();
	  for(unsigned i = 0; i < RR.size(); i++)
	    {
	      jets.clear();

	      if(i == 0)
		      jets = sorted_by_pt( clust_seq_a.inclusive_jets(pTmin_jets[0]) );     // === Small R jets
		
	      if(i == 1)
		      jets = sorted_by_pt( clust_seq_b.inclusive_jets(pTmin_jets[1]) );     // === Fatjets

	      Njets[i] = (int)jets.size();
	      jets_matrix.push_back(jets);
	    }
	      
	  
// ···································································································· //
// ···································································································· //
// ···································································································· //
	  
	  
	  // ---------------- //
	  // --- Analysis --- //
	  // ---------------- //	  
	  
	  // ***** Boosted analysis (1 or more fatjets) *****
	  
	  if( Njets[1] >= 1 ) {
	  
	    
	      cf[1]++;                       // =============================================================== Cutflow 2 ============

	      
	      // --- Fill ROOT tree ---
		  
	      B_LFJ_E      = jets_matrix[1][0].E();
	      B_LFJ_px     = jets_matrix[1][0].px();
	      B_LFJ_py     = jets_matrix[1][0].py();
	      B_LFJ_pz     = jets_matrix[1][0].pz();
	      B_evt_weight = EvtWeight;
	      B_rec        = sqrt( pow(3000, 2) - (2 * 3000 * jets_matrix[1][0].E()) + jets_matrix[1][0].m2() );
	      
	      B_N_FJ   = Njets[1];
	      B_N_SJ   = Njets[0];
	      B_N_glep = leptons.size();
	      
	      ROOTdist -> Fill();
	      //=====================================Modificaciones Higinio============================================================
              
        //==========================================pruebas con Ht=============================================================================
              
       /* double pfat1hem=0, pfat2hem=0;
            
        if(Njets[1]>1){
          for(unsigned i = 0; i < leptons.size(); i++){
            if(dot(leptons[i],jets_matrix[1][0])>=0)  pfat1hem += leptons[i].perp();
                
            if(dot(leptons[i],jets_matrix[1][1])>=0)  pfat2hem += leptons[i].perp();
          
          }
          for(unsigned i = 0; i < hadrons.size(); i++){
            if(dot(hadrons[i],jets_matrix[1][0])>=0)  pfat1hem += hadrons[i].perp();
                
            if(dot(hadrons[i],jets_matrix[1][1])>=0)  pfat2hem += hadrons[i].perp();
          
          }
              
             
             if((pfat1hem-jets_matrix[1][0].perp())>(pfat2hem-jets_matrix[1][1].perp())){
             if(jets_matrix[1][0].perp()/Ptotal<0.5){
              fatjetleadHthem->Fill(sqrt( pow(3000, 2) - (2 * 3000 * jets_matrix[1][0].E()) + jets_matrix[1][0].m2() ));
              }
              
              }else{
              if(jets_matrix[1][1].perp()/Ptotal<0.5){
              fatjetleadHthem->Fill(sqrt( pow(3000, 2) - (2 * 3000 * jets_matrix[1][1].E()) + jets_matrix[1][1].m2() ));
              }
              }
              }
        */
              //============================top tagger==========================================
                        //Masa toplikes   masa toplikes más cortes; Recoil de ambas
                        double delta_p=0.03, delta_r=0.11, cos_theta_W_max = 0.7;
                        
                        JHTopTagger top_tagger(delta_p, delta_r,cos_theta_W_max);
                        top_tagger.set_top_selector(SelectorMassRange(150,200));
                        top_tagger.set_W_selector  (SelectorMassRange( 65, 95));
           
                        PseudoJet tagged = top_tagger(jets_matrix[1][0]);
             
                        /*cout << "Ran the following top tagger: " << top_tagger.description() << endl;
                        cout<< "Event"<<total_events<< endl;
                        if (tagged == 0){
                          cout << "No top substructure found" << endl;
                         // return 0;
                        }else{
                          cout << " top substructure FOOOOUUUUUUND" << endl;
                          cout << "Found top substructure from the hardest jet:" << endl;
                          cout << "  top candidate:     " << tagged << endl;
                          cout << "  |_ W   candidate:  " << tagged.structure_of<JHTopTagger>().W() << endl;
                          cout << "  |  |_  W subjet 1: " << tagged.structure_of<JHTopTagger>().W1() << endl;
                          cout << "  |  |_  W subjet 2: " << tagged.structure_of<JHTopTagger>().W2() << endl;
                          cout << "  |  cos(theta_W) =  " << tagged.structure_of<JHTopTagger>().cos_theta_W() << endl;
                          cout << "  |_ non-W subjet:   " << tagged.structure_of<JHTopTagger>().non_W() << endl;
                          cout << tagged.structure_of<JHTopTagger>().non_W().m()<< endl;
                        }*/
            
                        
                        //===============================================================
              //=======================================================================================================================
       
        TPmass->Fill(TP.m());
        topmass->Fill(top.m());
        if (topdec.m() != 0){
          topdecmass->Fill(topdec.m());
        }
        truth_recoil->Fill(sqrt( pow(3000, 2) - (2 * 3000 * top.E()) + top.m2() ));
        
        

        double Ptotal = 0;

        for(int i=0; i<Njets[0]; i++){
          Ptotal += jets_matrix[0][i].perp();
        }



        m_fatjetlead->Fill(jets_matrix[1][0].m());
        Ht->Fill(Ptotal);
        int ngoodFJ = 0;
        fatjetHt->Fill(jets_matrix[1][0].perp()/Ptotal);
        fatjet2Ht->Fill(jets_matrix[1][1].perp()/Ptotal);
        int  cont3 = 0, cont4 = 0, cont5 = 0, cont6 = 0, cont7 = 0, cont8 = 0, cont9 = 0, cont10 = 0, cont11 = 0, cont12 = 0;
        for(int i=0; i<Njets[1]; i++){
          tagged = top_tagger(jets_matrix[1][i]);
          m_fatjet->Fill(jets_matrix[1][i].m());
          m_FJvspt_FJ->Fill(jets_matrix[1][i].m(),jets_matrix[1][i].perp());
          //if((tagged != 0) && (tagged.structure_of<JHTopTagger>().non_W().perp() < 350)){  
          if(tagged != 0){                        
            m_toplikes->Fill(jets_matrix[1][i].m());
            m_recoiltoplikes->Fill(sqrt( pow(3000, 2) - (2 * 3000 * jets_matrix[1][i].E()) + jets_matrix[1][i].m2() ));

          }
                

	        //if(jets_matrix[1][i].m() < mass_cut) continue;  //mass cut
	        //if(cont1 ==0) cf[1]++;              
	        //cont1++;                
	        
	        
	        //if(jets_matrix[1][i].perp()<pt_cut) continue; //pt cut
	        //if(cont2 ==0) cf[2]++;               
	        //cont2++;
          
          if(tagged == 0) continue;
	        if(cont3 ==0) cf[2]++;      // =============================================================== Cutflow 3 =========================================================================
	        cont3++;
          //cout << btagger.size()  << endl;
          for(unsigned i = 0; i < btagger.size(); i++){
            float deltaR = DeltaR(tagged.structure_of<JHTopTagger>().non_W(),btagger[i]);
            //cout << "  DeltaR:   " << deltaR << endl;
            if(deltaR < 0.4){
            mrecoil_isolated_toplikes_subestructure_cut->Fill(T_rec);
            //cout << "  |_ non-W subjet:   " << tagged.structure_of<JHTopTagger>().non_W() << endl;
            if(cont7 == 0) cf[3]++;       // =============================================================== Cutflow 4 ==================================================================================
            cont7++;
            break;
            }

          }
          if(cont7 == 0) continue;
          
          int nnearjets=0, nnearleptons=0;
          if(abs(jets_matrix[1][i].eta()) > 3){
            //Masa del fatjet
            massetacut->Fill(jets_matrix[1][i].m());
          }
          
          for(int j=0; j<Njets[0]; j++){
            if(jets_matrix[0][j].perp()>25){    
              float deltaR = DeltaR(jets_matrix[1][i],jets_matrix[0][j]);
              float deltaRtop = DeltaR(jets_matrix[1][i],top);
              deltaRjet->Fill(deltaR);
              truth_deltaR_jet_TP->Fill(DeltaR(jets_matrix[0][j],TP));
              truth_deltaR_jet_top->Fill(DeltaR(jets_matrix[0][j],top));
              if(deltaR>1.7 && deltaR<2.5) nnearjets++;
              
              if(topdec.m() == 0) continue;
              truth_deltaR_jet_topdec->Fill(DeltaR(jets_matrix[0][j],topdec));
              if(deltaRtop<1.2){
                cheat_good_deltaRjet->Fill(deltaR);
              }else{
                cheat_bad_deltaRjet->Fill(deltaR);
              }
            }
          }
          for(int j=0; j<leptons.size(); j++){
            if(leptons[j].perp()>25){
              float deltaR = DeltaR(jets_matrix[1][i],leptons[j]);
              float deltaRtop = DeltaR(jets_matrix[1][i],top);
              deltaRlepton->Fill(deltaR);
              truth_deltaR_leptons_TP->Fill(DeltaR(leptons[j],TP));
              truth_deltaR_leptons_top->Fill(DeltaR(leptons[j],top));
              truth_deltaR_leptons_topdec->Fill(DeltaR(leptons[j],topdec));
              if(deltaR<2.5) nnearleptons++;
              if(topdec.m() == 0) continue;
              truth_deltaR_leptons_topdec->Fill(DeltaR(leptons[j],topdec));
              if(deltaRtop<1.2){
                cheat_good_deltaRlepton->Fill(deltaR);
              }else{
                cheat_bad_deltaRlepton->Fill(deltaR);
              }
            }
          }

          
          double Ht = jets_matrix[1][i].perp()/Ptotal;

          if(Ht > 0.4){ 
            if(nnearleptons != 0 || nnearjets != 0) continue;// top tagger cut
          }
          if(cont4 == 0) cf[4]++;       // =============================================================== Cutflow 4 ==================================================================================
          cont4++;

          
                                            
          
          T_LFJ_E      = jets_matrix[1][i].E();
	        T_LFJ_px     = jets_matrix[1][i].px();
	        T_LFJ_py     = jets_matrix[1][i].py();
	        T_LFJ_pz     = jets_matrix[1][i].pz();
	        //T_evt_weight = EvtWeight;
	        T_rec        = sqrt( pow(3000, 2) - (2 * 3000 * jets_matrix[1][i].E()) + jets_matrix[1][i].m2() );
	               
          truth_deltaR_fatjet_TP->Fill(DeltaR(jets_matrix[1][i],TP));
          truth_deltaR_fatjet_top->Fill(DeltaR(jets_matrix[1][i],top));
          if(topdec.m() != 0){
            truth_deltaR_fatjet_topdec->Fill(DeltaR(jets_matrix[1][i],topdec));
            truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec->Fill(DeltaR(jets_matrix[1][i],top),DeltaR(jets_matrix[1][i],topdec));
          }         


	        EFJvsmass->Fill(jets_matrix[1][i].E(),jets_matrix[1][i].m());  
	        EFJvspt->Fill(jets_matrix[1][i].E(),jets_matrix[1][i].perp());
	        massvspt->Fill(jets_matrix[1][i].m(),jets_matrix[1][i].perp());
          ptfatvsHt->Fill(jets_matrix[1][i].perp(),Ptotal);
          topHt->Fill(jets_matrix[1][i].perp()/Ptotal);
          m_recoil_isolated_toplikes->Fill(T_rec);
          missing_energy = 3000-pvisible.E();
          METvsmrecoil->Fill(missing_energy,T_rec);

          if(topdec.m() != 0){
            if(DeltaR(jets_matrix[1][i],top)<1.2){
              cheat_good_m_recoil->Fill(T_rec);
              cheat_good_m_fatjet->Fill(jets_matrix[1][i].m());
              cheat_good_pt_fatjet->Fill(jets_matrix[1][i].perp());
              cheat_good_E_fatjet->Fill(jets_matrix[1][i].E());
              cheat_good_Ht_fatjet->Fill(Ht);
            }else{
              cheat_bad_m_recoil->Fill(T_rec);
              cheat_bad_m_fatjet->Fill(jets_matrix[1][i].m());
              cheat_bad_pt_fatjet->Fill(jets_matrix[1][i].perp());
              cheat_bad_E_fatjet->Fill(jets_matrix[1][i].E());
              cheat_bad_Ht_fatjet->Fill(Ht);
            }
          }
          if(ngoodFJ == 0){
            if(Ht > 0.41){
              m_recoil05->Fill(T_rec);
              //if(jets_matrix[1][i].perp() < 400) continue;
            }else{
              m_recoil0->Fill(T_rec);
              //makeif(jets_matrix[1][i].perp() > 900) continue;
            }
            if(((jets_matrix[1][i].E()/(Ht-1200))<200)&&(jets_matrix[1][i].E()<1300)){
              m_recoilcut->Fill(T_rec);

            }
            //if((jets_matrix[1][i].E() > 900)&&(Ht > 0.5))
            //m_recoil->Fill(T_rec);
            //if((jets_matrix[1][i].E() < 1300)&&(Ht < 0.65))
            m_recoil->Fill(T_rec);
            mrecoilvspt->Fill(T_rec,jets_matrix[1][i].perp());
            EFJvsmrecoil->Fill(jets_matrix[1][i].E(),T_rec);
            EvsHt->Fill(jets_matrix[1][i].E(),Ht);
            ptvsHt->Fill(jets_matrix[1][i].perp(),Ht);
            mrecoilvsHt->Fill(T_rec,Ht);
            m_fatjetpost->Fill(jets_matrix[1][i].m());
            fatjetpostHt->Fill(jets_matrix[1][i].perp()/Ptotal);
            pt_fatjetpost->Fill(jets_matrix[1][i].perp());
          }else if(ngoodFJ == 1){
            m_recoil2->Fill(T_rec);
            m_fatjetpost2->Fill(jets_matrix[1][i].m());
            fatjetpostHt2->Fill(jets_matrix[1][i].perp()/Ptotal);
            pt_fatjetpost2->Fill(jets_matrix[1][i].perp());
          }
          Tdist -> Fill();
          ngoodFJ++;
          
          
          if(T_rec<m_recoil_cut)continue;
          if(cont5 == 0) cf[5]++ ;// =============================================================== Cutflow 5 ========================================================================
          cont5++;
          
          
          mrecoil_isolated_toplikes_rec_cut-> Fill(T_rec);
          
          Miss_Energy->Fill(missing_energy);

          if(missing_energy_cut<missing_energy)continue;
          if(cont6 == 0){
            mrecoil_isolated_toplikes_rec_missE_cut-> Fill(T_rec);
            cf[6]++ ;
          }// =============================================================== Cutflow 6 ========================================================================
          cont6++;

          

          int numjets = 0;
          /*ptjet1 = 0;
          ptjet2 = 0;
          ptjet3 = 0;
          ptjet4 = 0;*/
          for(int j=0; j<Njets[0]; j++){
            if(jets_matrix[0][j].perp()>25){    
              float deltaR = DeltaR(jets_matrix[1][i],jets_matrix[0][j]);
              if(deltaR > 1.7){
                numjets++;
                if(numjets == 1) ptjet1 = (jets_matrix[0][j].perp());
                if(numjets == 2) ptjet2 = (jets_matrix[0][j].perp());
                if(numjets == 3) ptjet3 = (jets_matrix[0][j].perp());
                if(numjets == 4) ptjet4 = (jets_matrix[0][j].perp());
              }
            }
          }
          pt_FJ_BDT      = (jets_matrix[1][i].perp());
          Ht_BDT         = (Ptotal);
          No_FJ_BDT      = (Njets[1]);
          No_jets_BDT    = (Njets[0]);
          No_leptons_BDT = (leptons.size());


          weight_BDT     = (EvtWeight);

          BDT->Fill();

          auto evaluate_bdt = [](TMVA::Reader* reader, const char* name) -> double {
            if (!reader) return -9999.0;
            try {
              return reader->EvaluateMVA(name);
            } catch (const std::exception& ex) {
              std::cerr << "[WARN] TMVA evaluation failed for " << name << ": " << ex.what() << "\n";
            } catch (...) {
              std::cerr << "[WARN] TMVA evaluation failed for " << name << " (unknown error)\n";
            }
            return -9999.0;
          };

          double BDT1200_cut = evaluate_bdt(BDT_trained_1200.get(), "BDT");
          if( BDT1200_cut > -0.12){
            if(cont8 == 0) cf[8]++ ;
            cont8++;
            mrecoil_BDT1200_cut-> Fill(T_rec);
          }

          double BDT_ttbar_cut = evaluate_bdt(BDT_ttbar.get(), "BDT");
          if(BDT_ttbar_cut > -0.12){
            if(cont9 == 0) cf[7]++ ;
            cont9++;
            mrecoil_BDT_ttbar-> Fill(T_rec);
          }

          double BDT1600_cut = evaluate_bdt(BDT_trained_1600.get(), "BDT");
          if( BDT1600_cut > -0.08){
            if(cont10 == 0) cf[9]++ ;
            cont10++;
            mrecoil_BDT1600_cut-> Fill(T_rec);
          }

          double BDT2000_cut = evaluate_bdt(BDT_trained_2000.get(), "BDT");
          if( BDT2000_cut > -0.08){
            if(cont11 == 0) cf[10]++ ;
            cont11++;
            mrecoil_BDT2000_cut-> Fill(T_rec);
          }

          double BDT2400_cut = evaluate_bdt(BDT_trained_2400.get(), "BDT");
          if( BDT2400_cut > -0.07){
            if(cont12 == 0) cf[11]++ ;
            cont12++;
            mrecoil_BDT2400_cut-> Fill(T_rec);
          }
                
                
        } // fin de loop sobre FJ
        goodFJ->Fill(ngoodFJ);
        No_FJ->Fill(cont3); 
        No_top_FJ->Fill(cont4);
	      //======================================Fin modificaciones===============================================================
	      
	    }
	  // +++++ End boosted analysis +++++
	  // ------------------------------------
	  

	  
	  // ***** Resolved analysis (zero fatjets) *****
	    else
	    {
	      //cf[2] += 1;                       // =============================================================== Cutflow 2 =======================================================================
	    }
	  // +++++ End resolved analysis +++++
	  // ------------------------------------
	  
	  
// ···································································································· //
// ···································································································· //
// ···································································································· //
	  
	  
	  // --------------------------- //
	  // ---- FINAL FORMALITIES ---- //
	  // --------------------------- //	  	 	  
	  
	  // ***** Delete current event and load next event *****

	  delete evt;
	  ascii_in >> evt;

	}
      // +++++ End reading-in HepMC event loop +++++
      // -------------------------------------------
      
      
      end_analysis(no_of_files, icount, name_of_file, &outfile);
      
      
      // ***** Cutflow summary *****
      
     
      cutflow( sizeof(cf) / sizeof(int), CF, cf, CrossSection/cf[0], Luminosity, &outfile);
      
      
      
      totalxs += CrossSection;

      
      // ***** Read next file listed *****

      no_of_files++;
      getline(fin, name_of_file);
      
     /* ROOTfile.Write();
      ROOTfile.Close();*/
    }
  // +++++ End reading-in HepMC file loop +++++
  // ------------------------------------------
  
  
// ···································································································· //
// ···································································································· //
// ···································································································· //

  
// NOTE: Scaling factors for XS should be: a) total_events : when running analysis over lhef2hepmc file
//                                         b) no_of_files  : when running analysis over pure hepmc file
//
// For case a), replace no_of_files -> total_events within function 'summary_analysis' under 'Headers_Analysis/formalities.hh'
  
  summary_analysis(no_of_files, total_events, CrossSection, &outfile);
  
  
  // ***** Write and close ROOT file ******

  if (ROOTFILE_OK && ROOTFILE_PTR) {
    ROOTFILE_PTR->cd();
    XS->Fill(totalxs/total_events);
    no_sim->Fill(total_events);
    ROOTFILE_PTR->Write();
    ROOTFILE_PTR->Close();
    delete ROOTFILE_PTR;
    ROOTFILE_PTR = nullptr;
  }
  
  
  // ****** Close output file. End of program ******
  
  outfile.close();
  cout << '\a';
  cout << "\nEND OF PROGRAM\n"<< endl;
  return 0;
  
}
// +++++ int main() +++++
// ----------------------


// ···································································································· //
// ···································································································· //
// ···································································································· //
ostream & operator<<(ostream & ostr, const PseudoJet & jet){
   ostr << "pt, y, phi =" << setprecision(6)
        << " " << setw(9) << jet.perp() 
        << " " << setw(9)  <<  jet.rap()  
        << " " << setw(9)  <<  jet.phi()  
        << ", mass = " << setw(9) << jet.m();
   return ostr;
 }
