// --------------------------------------------------------------------------------------------------------------------------
// ***************************** //
// ***** GENERAL UTILITIES ***** //
// ***************************** //


// --- Sign function ---
inline int sign(const double x)
{
  return (x > 0) ? 1 : ((x < 0) ? -1 : 0);
}



// --- Sign comparisson ---
inline int sign_comp(const double x, const double y)
{
  return ( sign(x) == sign(y) ) ? 1 : 0;
}



// --- Addition in quadrature of 2 variables ---
inline double add_quad2(const double aa, const double bb)
{
  return sqrt(pow(aa, 2) + pow(bb, 2));
}



// --- Addition in quadrature of 3 variables ---
inline double add_quad3(const double aa, const double bb, const double cc)
{
  return sqrt(pow(aa, 2) + pow(bb, 2) + pow(cc, 2));
}



// --- Random number sampled from a Gaussian distribution ---
double randnorm(const double _mean_, const double _stddev_, const int seed)
{
  default_random_engine generator(seed);
  normal_distribution<double> distribution(_mean_, _stddev_);
  
  return distribution(generator);
}



// --- Random number sampled from a Lognormal distribution ---
double randlognorm(const double _mean_, const double _stddev_, const int seed)
{
  default_random_engine generator(seed);
  lognormal_distribution<double> distribution(_mean_, _stddev_);
  
  return distribution(generator);
}



// --- Find index (upper bound) ---
// *** Easy implementation @GAMBIT: https://gambit.hepforge.org/doxygen/d7/d6d/_utils_8hpp_source.html#l00182 ***
inline size_t binIndex(const double _value_, const vector<double> &binedges, bool allow_overflow = false)
{
  if(_value_ < binedges.front()) return -1;
  if(_value_ >= binedges.back()) return allow_overflow ? int(binedges.size()) - 1 : -1;
  
  return distance(binedges.begin(), --upper_bound(binedges.begin(), binedges.end(), _value_)); // Position of upper bound -1.
}



// --- Difference between 2 numbers ---
inline bool double_equals(const double a, const double b, const double epsilon)
{
  return (a - b) >= epsilon;
}



// --- Variable within given range ---
inline bool inRange(const double xx, const double lower, const double upper)
{
  return (lower < xx && xx < upper);
}



// --- \eta ranges ---
inline bool etaRanges(const PseudoJet pp, const double lower1, const double upper1, const double lower2, const double upper2)
{
  return (lower1 <= fabs(pp.eta()) && fabs(pp.eta()) < upper1) || (lower2 < fabs(pp.eta()) && fabs(pp.eta()) < upper2);
}



// --- \eta difference between 2 jets ---
inline double DeltaEta(const PseudoJet jet1, const PseudoJet jet2)
{
  return jet1.pseudorapidity() - jet2.pseudorapidity();
}



// --- \phi difference between 2 jets ---
inline double DeltaPhi(const PseudoJet jet1, const PseudoJet jet2)
{
  double pi(3.1415926535);
  double DelPhi = jet1.phi() - jet2.phi();
  if(DelPhi > pi)
    DelPhi -= 2.0*pi;
  if(DelPhi < -pi)
    DelPhi += 2.0*pi;
  
  return fabs(DelPhi);
}



// --- Rapidity difference between 2 jets ---
inline double DeltaY(const PseudoJet jet1, const PseudoJet jet2)
{
  return jet1.rap() - jet2.rap();
}



// --- Rapidity product between 2 jets ---
inline double rap_prod(const PseudoJet jet1, const PseudoJet jet2)
{
  return jet1.rap() * jet2.rap();
}



// --- Cylindrical distance between 2 jets (y - \phi plane) ---
inline double DeltaR(const PseudoJet jet1, const PseudoJet jet2)
{
  double dp = DeltaPhi(jet1, jet2);
  double dy = DeltaY(jet1, jet2);
  
  return sqrt((dy*dy) + (dp*dp));
}



// --- Spatial dot product between 2 jets ---
inline double dot(const PseudoJet jet1, const PseudoJet jet2)
{
  return (jet1.px())*(jet2.px()) + (jet1.py())*(jet2.py()) + (jet1.pz())*(jet2.pz());
}



// --- Display observables of a given PseudoJet ---
inline void print_jet(const PseudoJet jet)
{
  cout << "(px, py, pz, e, m, pT, eta, y, phi, PID): (" << jet.px()
       << ", " << setw(3)                               << jet.py()
       << ", " << setw(3)                               << jet.pz()
       << ", " << setw(3)                               << jet.e()
       << ", " << setw(3)                               << jet.m()
       << ", " << setw(3)                               << jet.perp()
       << ", " << setw(3)                               << jet.eta()
       << ", " << setw(3)                               << jet.rap()
       << ", " << setw(3)                               << jet.phi()
       << ", " << setw(3)                               << jet.user_index()
       << ")\n\n==========\n"                           << endl;
}



// ===== Mandelstam variables ===== //

inline double mandelstam_SS(const PseudoJet p1, const PseudoJet p2)
{
  const double e1 = p1.e(), p1x = p1.px(), p1y = p1.py(), p1z = p1.pz();
  const double e2 = p2.e(), p2x = p2.px(), p2y = p2.py(), p2z = p2.pz();

  const double v1 = e1*e1 - p1x*p1x - p1y*p1y - p1z*p1z;
  const double v2 = e2*e2 - p2x*p2x - p2y*p2y - p2z*p2z;
  const double ct = e1*e2 - p1x*p2x - p1y*p2y - p1z*p2z;

  return v1 + 2*ct + v2;
}



inline double mandelstam_TT(const PseudoJet p1, const PseudoJet p2)
{
  const double e1 = p1.e(), p1x = p1.px(), p1y = p1.py(), p1z = p1.pz();
  const double e2 = p2.e(), p2x = p2.px(), p2y = p2.py(), p2z = p2.pz();

  const double v1 = e1*e1 - p1x*p1x - p1y*p1y - p1z*p1z;
  const double v2 = e2*e2 - p2x*p2x - p2y*p2y - p2z*p2z;
  const double ct = e1*e2 - p1x*p2x - p1y*p2y - p1z*p2z;

  return v1 - 2*ct + v2;
}



inline double mandelstam_UU(const PseudoJet p1, const PseudoJet p2)
{
  return mandelstam_TT(p1, p2);
}
