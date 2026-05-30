// void plot_canvas(TH1F *cvptr, string run_name, const char *output_data, const char *output_eps)  // ----- Original format -----

void plot_canvas(TH1F *cvptr, string run_name, const char *output_eps)
{
  TCanvas *c100 = new TCanvas("c100","");  
  c100->cd();
  
  string output_datei_eps(run_name);
  output_datei_eps = output_datei_eps+output_eps;
  
  const char *output_datei_eps_l = output_datei_eps.c_str();
  
  cvptr->SetMarkerStyle(8);
  cvptr->SetMarkerColor(1);
  cvptr->SetLineColor(1);
  cvptr->Draw(); 
  c100->SaveAs(output_datei_eps_l);
  
  /*
  int nbins = cvptr->GetNbinsX();
  double dummy_evn = cvptr->GetSumOfWeights();
  
  string output_datei_data(run_name);
  output_datei_data=output_datei_data+output_data;
  
  const char *output_datei_data_l = output_datei_data.c_str();
  
  ofstream filetotcross100(output_datei_data_l);
  for(int i=1; i<=nbins; i++) 
    filetotcross100 << cvptr->GetBinCenter(i) << "\t\t" << cvptr->GetBinContent(i) << "\t\t" << dummy_evn << endl;
  
  filetotcross100.close();
  */
  
  delete c100;

  cvptr->Write();

}
