void plot_canvas2D(TH2F *cvptr, string run_name, const char *output_eps)
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

  delete c100;

  cvptr->Write();
}
