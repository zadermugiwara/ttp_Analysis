// --------------------------------------------------------------------------------------------------------
// *************************** //
// ***** ISOLATE LEPTONS ***** //
// *************************** //
//                /**************\
// --------------- Mini isolation --------- //
//                \**************/


void isolated_leptons(vector<PseudoJet> &leptons, vector<PseudoJet> &hadrons)
{
  double pTcone   = 0.0;   // === Total pT within the cone around a lepton
  double isoratio = 0.1;   // === pTcone to pTlepton threshold ratio
  double iso_R    = 0.0;   // === Isolation test cone's 'radius'
  
  
  // --- Loop over all leptons ---
  
  for(unsigned ii = 0; ii < leptons.size(); ii++)
    { 
      pTcone = 0.0;
      iso_R  = 10 / leptons[ii].pt();
      
      
      // --- Loop over all hadrons ---
      
      for(unsigned jj = 0; jj < hadrons.size(); jj++)
	if( DeltaR(leptons[ii], hadrons[jj]) < iso_R )  // === Look for nearby hadrons
	  pTcone += hadrons[jj].pt();                   // === Sum nearby hadrons' pT
      

      // --- Isolation test ---
      
      if( (pTcone / leptons[ii].pt()) >= isoratio)    // === If the lepton is not hard enough wrt nearby
	{                                             // hadrons, save it with them for jet construction
	  if( abs(leptons[ii].user_index()) == 11 )   // only if it is an electron
	    hadrons.push_back( leptons[ii] );
	  
	  leptons.erase( leptons.begin() + ii );
	  ii--;
	}
    }
  
  leptons = sorted_by_pt(leptons);
  hadrons = sorted_by_pt(hadrons);
}
