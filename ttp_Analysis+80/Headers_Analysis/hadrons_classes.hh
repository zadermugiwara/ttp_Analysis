// ***** NOTE: NEEDS TO BE PERIODICALLY UPDATED ACCORDING TO PDG's LATEST RESULTS *****

// Check for each particle if it's B-hadron and if its children
// are NO B-hadrons. This would mean that you found the B-hadron 
// before it decays. A B-hadron is identified by its PDGID.

class Is_Bhadron
{
public:
  bool operator()(const GenParticle* p)
  {
    if ((abs(p->pdg_id()) == 511   || abs(p->pdg_id()) == 521   || abs(p->pdg_id()) == 531   || 
	 abs(p->pdg_id()) == 10511 || abs(p->pdg_id()) == 10521 || abs(p->pdg_id()) == 513   ||
	 abs(p->pdg_id()) == 523   || abs(p->pdg_id()) == 10513 || abs(p->pdg_id()) == 10523 ||
	 abs(p->pdg_id()) == 20513 || abs(p->pdg_id()) == 20523 || abs(p->pdg_id()) == 515   ||
	 abs(p->pdg_id()) == 525   || abs(p->pdg_id()) == 10531 || abs(p->pdg_id()) == 533   ||
	 abs(p->pdg_id()) == 10533 || abs(p->pdg_id()) == 20533 || abs(p->pdg_id()) == 535   ||
	 abs(p->pdg_id()) == 541   || abs(p->pdg_id()) == 10541 || abs(p->pdg_id()) == 543   ||
	 abs(p->pdg_id()) == 10543 || abs(p->pdg_id()) == 20543 || abs(p->pdg_id()) == 545   || 
	 abs(p->pdg_id()) == 5122  || abs(p->pdg_id()) == 5112  || abs(p->pdg_id()) == 5212  ||
	 abs(p->pdg_id()) == 5222  || abs(p->pdg_id()) == 5114  || abs(p->pdg_id()) == 5214  || 
	 abs(p->pdg_id()) == 5224  || abs(p->pdg_id()) == 5132  || abs(p->pdg_id()) == 5232  ||           
	 abs(p->pdg_id()) == 5312  || abs(p->pdg_id()) == 5322  || abs(p->pdg_id()) == 5314  ||           
	 abs(p->pdg_id()) == 5324  || abs(p->pdg_id()) == 5332  || abs(p->pdg_id()) == 5334  ||           
	 abs(p->pdg_id()) == 5142  || abs(p->pdg_id()) == 5242  || abs(p->pdg_id()) == 5412  ||           
	 abs(p->pdg_id()) == 5422  || abs(p->pdg_id()) == 5414  || abs(p->pdg_id()) == 5424  ||           
	 abs(p->pdg_id()) == 5342  || abs(p->pdg_id()) == 5432  || abs(p->pdg_id()) == 5434  ||           
	 abs(p->pdg_id()) == 5442  || abs(p->pdg_id()) == 5444  || abs(p->pdg_id()) == 5512  ||           
	 abs(p->pdg_id()) == 5522  || abs(p->pdg_id()) == 5514  || abs(p->pdg_id()) == 5524  ||           
	 abs(p->pdg_id()) == 5532  || abs(p->pdg_id()) == 5534  || abs(p->pdg_id()) == 5542  ||           
	 abs(p->pdg_id()) == 5544  || abs(p->pdg_id()) == 5554))
      return 1;
    return 0;
  }
};


// Check for each particle if it's C-hadron and if its children
// are NO C-hadrons. This would mean that you found the C-hadron 
// before it decays. A C-hadron is identified by its PDGID.

class Is_Chadron
{
public:
  bool operator()(const GenParticle* p)
  {
    if ((abs(p->pdg_id()) == 411   || abs(p->pdg_id()) == 421   || abs(p->pdg_id()) == 10411 || 
	 abs(p->pdg_id()) == 10421 || abs(p->pdg_id()) == 413   || abs(p->pdg_id()) == 423   ||
	 abs(p->pdg_id()) == 10413 || abs(p->pdg_id()) == 10423 || abs(p->pdg_id()) == 20413 ||
	 abs(p->pdg_id()) == 20423 || abs(p->pdg_id()) == 415   || abs(p->pdg_id()) == 425   ||
	 abs(p->pdg_id()) == 431   || abs(p->pdg_id()) == 10431 || abs(p->pdg_id()) == 433   ||
	 abs(p->pdg_id()) == 10433 || abs(p->pdg_id()) == 20433 || abs(p->pdg_id()) == 435   ||
	 abs(p->pdg_id()) == 4122  || abs(p->pdg_id()) == 4222  || abs(p->pdg_id()) == 4212  ||
	 abs(p->pdg_id()) == 4112  || abs(p->pdg_id()) == 4224  || abs(p->pdg_id()) == 4214  || 
	 abs(p->pdg_id()) == 4114  || abs(p->pdg_id()) == 4232  || abs(p->pdg_id()) == 4132  ||
	 abs(p->pdg_id()) == 4322  || abs(p->pdg_id()) == 4312  || abs(p->pdg_id()) == 4324  || 
	 abs(p->pdg_id()) == 4314  || abs(p->pdg_id()) == 4332  || abs(p->pdg_id()) == 4334  ||           
	 abs(p->pdg_id()) == 4412  || abs(p->pdg_id()) == 4422  || abs(p->pdg_id()) == 4414  ||           
	 abs(p->pdg_id()) == 4424  || abs(p->pdg_id()) == 4432  || abs(p->pdg_id()) == 4434  ||           
	 abs(p->pdg_id()) == 4444))
      return 1;
    return 0;
  }
};
