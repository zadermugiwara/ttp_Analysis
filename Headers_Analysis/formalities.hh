void begin_analysis(string analysis, ofstream *outfile)
{
  cout     << "\n=================================================="         << endl;
  cout     << "=============== BEGINNING ANALYSIS ==============="           << endl;
  cout     << "=================================================="           << endl;
  cout     << "\n     $$$$$----- Analysis: "   << analysis << " -----$$$$$"  << endl;
  cout     << "\n\n"                                                         << endl;

  *outfile << "\n\n";
  *outfile << "\n==================================================";
  *outfile << "\n=============== BEGINNING ANALYSIS ===============";
  *outfile << "\n==================================================";
  *outfile << "\n\n     $$$$$----- Analysis: " << analysis << " -----$$$$$";
  *outfile << "\n";
}



void info_analysis(int numberofevents, string list_of_file, string name_of_file, ofstream *outfile)
{
  cout     << "Will analyse "  << numberofevents << " events per file in: " << list_of_file << endl;
  cout     << "Opening file: "   << name_of_file                                              << endl;
  cout     << "\n++++++++++++++++++++++++++++++++++++++++++++++++++"                          << endl;     
  cout     << "++++++++++++++++++++++++++++++++++++++++++++++++++"                            << endl;
  cout     << "\n\n"                                                                            << endl;
  
  *outfile << "\n\n\n++++++++++++++++++++++++++++++++++++++++++++++++++\n";      
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "\nWill analyse "  << numberofevents << " events per file in: " << list_of_file;
  *outfile << "\nOpening file: " << name_of_file;
  *outfile << "\n\n++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n";      
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "\n\n\n";
}



void end_analysis(int no_of_files, int icount, string name_of_file, ofstream *outfile)
{
  cout     << "\n++++++++++++++++++++++++++++++++++++++++++++++++++"                       << endl;
  cout     << "+++++++++++++++++ SUMMARY FILE " << no_of_files + 1 << " +++++++++++++++++" << endl;
  cout     << "++++++++++++++++++++++++++++++++++++++++++++++++++\n"                       << endl;
  cout     << "Processed "                      << icount          << " events."           << endl;
  cout     << "Finished working on file: "      << name_of_file                            << endl;
  cout     << "\n++++++++++++++++++++++++++++++++++++++++++++++++++"                       << endl;
  cout     << "++++++++++++++++++++++++++++++++++++++++++++++++++\n"                       << endl;
  
  *outfile << "\n\n\n";
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "+++++++++++++++++ SUMMARY FILE " << no_of_files + 1 << " +++++++++++++++++\n";
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n\n";
  *outfile << "Processed "                      << icount          << " events.\n";
  *outfile << "Finished working on file: "      << name_of_file;
  *outfile << "\n\n++++++++++++++++++++++++++++++++++++++++++++++++++\n";
  *outfile << "++++++++++++++++++++++++++++++++++++++++++++++++++\n\n";
}



void summary_analysis(int no_of_files, int total_events, double CrossSection, ofstream *outfile)
{
  cout     << "\n"                                                              << endl;
  cout     << "=================================================="              << endl;
  cout     << "================= ANALYSIS DONE! ================="              << endl;
  cout     << "=================================================="              << endl;
  cout     << "\nRead " << no_of_files              << " file(s)."              << endl;
  cout     << "\nTotal events analysed: "           << total_events             << endl;
  cout     << "Total cross section [pb]: "          << CrossSection/no_of_files << endl;
  cout     << "\n::::::::::::::::::::::::::::::::::::::::::::::::::"            << endl;
  
  *outfile << "\n\n";
  *outfile << "==================================================\n";
  *outfile << "================= ANALYSIS DONE! =================\n";
  *outfile << "==================================================\n";
  *outfile << "\n::::::::::::::::::::::::::::::::::::::::::::::::::\n";
  *outfile << "::::::::::::::::::::::::::::::::::::::::::::::::::\n";
  *outfile << "\nRead " << no_of_files              << " file(s).";
  *outfile << "\n\nTotal events analysed: "         << total_events;
  *outfile << "\nTotal cross section [pb]: "        << CrossSection/no_of_files;
  *outfile << "\n\n::::::::::::::::::::::::::::::::::::::::::::::::::\n";
  *outfile << "::::::::::::::::::::::::::::::::::::::::::::::::::\n";
}

void cutflow(int size, string CF[], int cf[], double CrossSection, ofstream *outfile)
{
  cout     << "\n   ---------------------"                       << endl;
  cout     << "  --- Cutflow summary ---"                        << endl;
  cout     << "   ---------------------\n"                       << endl;
  cout     << "      ----------------------------"               << endl;
  cout     << "\t    Cut       # of evts"                        << endl;
  cout     << "      ----------------------------"               << endl;
  for(unsigned i = 0; i < ( size ); i++)
	  cout    << "\t" << i << " " << CF[i] << "\t" << cf[i]         << endl;
  cout     << "      ----------------------------"               << endl;
  cout     <<"Cross section [pb]: " << CrossSection              << endl;



  *outfile     << "\n\n   ---------------------\n";
  *outfile     << "  --- Cutflow summary ---\n";
  *outfile     << "   ---------------------\n\n";
  *outfile     << "      ----------------------------\n";
  *outfile     << "\t    Cut       # of evts\n";
  *outfile     << "      ----------------------------\n";
  for(unsigned i = 0; i < ( size ); i++)
	  *outfile    << "\t" << i << " " << CF[i] << "\t" << cf[i] << "\n";
  *outfile     << "      ----------------------------\n";
  *outfile     <<"Cross section [pb]: " << CrossSection;
}


