// ------------------------------------------------------------------------------------------------------------------
// -------------------- Hadron-level plots --------------------
//
//                                          /**************\
// ----------------------------------------- Analysis_ttbar --------- //
//                                          \**************/
#include <fstream>
#include <iostream>
#include <memory>

auto book_reader = [](TMVA::Reader* reader, const std::string& weight_path) {
  std::ifstream fin(weight_path.c_str());
  if (!fin.good()) {
    std::cerr << "[WARN] Missing TMVA weights file: " << weight_path << "\n";
    return false;
  }
  reader->BookMVA("BDT", weight_path.c_str());
  return true;
};








unique_ptr<TMVA::Reader> BDT_trained_1200;
BDT_trained_1200.reset( new TMVA::Reader( "!Color:Silent" ) );
   //dataloader->AddVariable("weight_BDT", 'D');

BDT_trained_1200->AddVariable("ptjet1", &ptjet1);
BDT_trained_1200->AddVariable("ptjet2", &ptjet2);
BDT_trained_1200->AddVariable("ptjet3", &ptjet3);
BDT_trained_1200->AddVariable("ptjet4", &ptjet4);
BDT_trained_1200->AddVariable("pt_FJ_BDT", &pt_FJ_BDT);   
BDT_trained_1200->AddVariable("Ht_BDT", &Ht_BDT);
BDT_trained_1200->AddVariable("No_FJ_BDT", &No_FJ_BDT);
BDT_trained_1200->AddVariable("No_jets_BDT", &No_jets_BDT);
BDT_trained_1200->AddVariable("No_leptons_BDT", &No_leptons_BDT);

bool BDT1200_AVAILABLE = book_reader(BDT_trained_1200.get(), "root/dataset1200bkg/weights/MVAnalysis_BDT.weights.xml");
if (!BDT1200_AVAILABLE) BDT_trained_1200.reset();

unique_ptr<TMVA::Reader> BDT_trained_1600;
BDT_trained_1600.reset( new TMVA::Reader( "!Color:Silent" ) );
   //dataloader->AddVariable("weight_BDT", 'D');

BDT_trained_1600->AddVariable("ptjet1", &ptjet1);
BDT_trained_1600->AddVariable("ptjet2", &ptjet2);
BDT_trained_1600->AddVariable("ptjet3", &ptjet3);
BDT_trained_1600->AddVariable("ptjet4", &ptjet4);
BDT_trained_1600->AddVariable("pt_FJ_BDT", &pt_FJ_BDT);   
BDT_trained_1600->AddVariable("Ht_BDT", &Ht_BDT);
BDT_trained_1600->AddVariable("No_FJ_BDT", &No_FJ_BDT);
BDT_trained_1600->AddVariable("No_jets_BDT", &No_jets_BDT);
BDT_trained_1600->AddVariable("No_leptons_BDT", &No_leptons_BDT);

bool BDT1600_AVAILABLE = book_reader(BDT_trained_1600.get(), "root/dataset1600bkg/weights/MVAnalysis_BDT.weights.xml");
if (!BDT1600_AVAILABLE) BDT_trained_1600.reset();

unique_ptr<TMVA::Reader> BDT_ttbar;
BDT_ttbar.reset( new TMVA::Reader( "!Color:Silent" ) );
   //dataloader->AddVariable("weight_BDT", 'D');

BDT_ttbar->AddVariable("ptjet1", &ptjet1);
BDT_ttbar->AddVariable("ptjet2", &ptjet2);
BDT_ttbar->AddVariable("ptjet3", &ptjet3);
BDT_ttbar->AddVariable("ptjet4", &ptjet4);
BDT_ttbar->AddVariable("pt_FJ_BDT", &pt_FJ_BDT);   
BDT_ttbar->AddVariable("Ht_BDT", &Ht_BDT);
BDT_ttbar->AddVariable("No_FJ_BDT", &No_FJ_BDT);
BDT_ttbar->AddVariable("No_jets_BDT", &No_jets_BDT);
BDT_ttbar->AddVariable("No_leptons_BDT", &No_leptons_BDT);

bool BDT_TTBAR_AVAILABLE = book_reader(BDT_ttbar.get(), "root/datasetttbar/weights/MVAnalysis_BDT.weights.xml");
if (!BDT_TTBAR_AVAILABLE) BDT_ttbar.reset();

unique_ptr<TMVA::Reader> BDT_trained_2000;
BDT_trained_2000.reset( new TMVA::Reader( "!Color:Silent" ) );
   //dataloader->AddVariable("weight_BDT", 'D');

BDT_trained_2000->AddVariable("ptjet1", &ptjet1);
BDT_trained_2000->AddVariable("ptjet2", &ptjet2);
BDT_trained_2000->AddVariable("ptjet3", &ptjet3);
BDT_trained_2000->AddVariable("ptjet4", &ptjet4);
BDT_trained_2000->AddVariable("pt_FJ_BDT", &pt_FJ_BDT);   
BDT_trained_2000->AddVariable("Ht_BDT", &Ht_BDT);
BDT_trained_2000->AddVariable("No_FJ_BDT", &No_FJ_BDT);
BDT_trained_2000->AddVariable("No_jets_BDT", &No_jets_BDT);
BDT_trained_2000->AddVariable("No_leptons_BDT", &No_leptons_BDT);

bool BDT2000_AVAILABLE = book_reader(BDT_trained_2000.get(), "root/dataset2000bkg/weights/MVAnalysis_BDT.weights.xml");
if (!BDT2000_AVAILABLE) BDT_trained_2000.reset();

unique_ptr<TMVA::Reader> BDT_trained_2400;
BDT_trained_2400.reset( new TMVA::Reader( "!Color:Silent" ) );
   //dataloader->AddVariable("weight_BDT", 'D');

BDT_trained_2400->AddVariable("ptjet1", &ptjet1);
BDT_trained_2400->AddVariable("ptjet2", &ptjet2);
BDT_trained_2400->AddVariable("ptjet3", &ptjet3);
BDT_trained_2400->AddVariable("ptjet4", &ptjet4);
BDT_trained_2400->AddVariable("pt_FJ_BDT", &pt_FJ_BDT);   
BDT_trained_2400->AddVariable("Ht_BDT", &Ht_BDT);
BDT_trained_2400->AddVariable("No_FJ_BDT", &No_FJ_BDT);
BDT_trained_2400->AddVariable("No_jets_BDT", &No_jets_BDT);
BDT_trained_2400->AddVariable("No_leptons_BDT", &No_leptons_BDT);

bool BDT2400_AVAILABLE = book_reader(BDT_trained_2400.get(), "root/dataset2400bkg/weights/MVAnalysis_BDT.weights.xml");
if (!BDT2400_AVAILABLE) BDT_trained_2400.reset();
