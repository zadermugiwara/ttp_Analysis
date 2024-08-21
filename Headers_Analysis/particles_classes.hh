// =============================== //
// ===== HepMC2 STATUS CODES ===== //
// =============================== //

// http://hepmc.web.cern.ch/hepmc/releases/HepMC2_user_manual.pdf (p. 13)
// http://home.thep.lu.se/~torbjorn/pythia81html/ParticleProperties.html
// https://home.fnal.gov/~mrenna/HCPSS/HCPSShepmc.html

// 1      : Final-state particle, i.e., a particle that is not decayed further by the 
//          generator (may also include unstable particles that are to be decayed later, 
//          as part of the detector simulation [usually at .lhe-level/hard scattering]).

class Is_FinalState
{
public:
  bool operator()(const GenParticle* p)
  {
    if(p->status() == 1 && !p->end_vertex())
      return 1;
    return 0;
  }
};


// 2      : Decayed SM hadron or tau or mu lepton, excepting virtual intermediate states 
//          thereof, i.e., the particle must undergo a normal decay, not e.g. a shower branching.

class Is_DecayedFrag
{
public:
  bool operator()(const GenParticle* p)
  {
    if(p->status() == 2)
      return 1;
    return 0;
  }
};


// 3      : Labels the beam and the hard process.

class Is_BeamHP
{
public:
  bool operator()(const GenParticle* p)
  {
    if(p->status() == 3)
      return 1;
    return 0;
  }
};


// 11-200 : Intermediate (decayed/branched/...) particle that does not fulfill the 
//          criteria of status code 2.

class Is_Branched
{
public:
  bool operator()(const GenParticle* p)
  {
    if(p->status() == 23) // ~~~~~ OUTGOING PARTICLE OF HARDEST SUBPROCESS ~~~~~
      return 1;
    return 0;
  }
};



// =============================== //
// ===== FERMIONS AND BOSONS ===== //
// =============================== //

// Is_down : returns true if input particle is d-quark.
class Is_down
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 1)
      return 1;
    return 0;
  }
};


// Is_up : returns true if input particle is u-quark.
class Is_up
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 2)
      return 1;
    return 0;
  }
};


// Is_strange : returns true if input particle is s-quark.
class Is_strange
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 3)
      return 1;
    return 0;
  }
};


// Is_charm : returns true if input particle is c-quark.
class Is_charm
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 4)
      return 1;
    return 0;
  }
};


// Is_bottom : returns true if input particle is b-quark.
class Is_bottom
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 5)
      return 1;
    return 0;
  }
};


// Is_top : returns true if input particle is t-quark.
class Is_top
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 6)
      return 1;
    return 0;
  }
};


// Is_electron : returns true if input particle is electron.
class Is_electron
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 11)
      return 1;
    return 0;
  }
};


// Is_muon : returns true if input particle is muon.
class Is_muon
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 13)
      return 1;
    return 0;
  }
};


// Is_tau : returns true if input particle is tau.
class Is_tau
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 15)
      return 1;
    return 0;
  }
};


// Is_nu : returns true if input particle is neutrino.
class Is_nu
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 12 || abs(p->pdg_id()) == 14 || abs(p->pdg_id()) == 16)
      return 1;
    return 0;
  }
};


// Is_gluon : returns true if input particle is g.
class Is_gluon
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 21)
      return 1;
    return 0;
  }
};


// Is_photon : returns true if input particle is a.
class Is_photon
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 22)
      return 1;
    return 0;
  }
};


// Is_Zboson : returns true if input particle is Z.
class Is_Zboson
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 23)
      return 1;
    return 0;
  }
};


// Is_Wboson : returns true if input particle is W.
class Is_Wboson
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 24)
      return 1;
    return 0;
  }
};


// Is_Hboson : returns true if input particle is H.
class Is_Hboson
{
public:
  bool operator()(const GenParticle* p)
  {
    if(abs(p->pdg_id()) == 25)
      return 1;
    return 0;
  }
};
