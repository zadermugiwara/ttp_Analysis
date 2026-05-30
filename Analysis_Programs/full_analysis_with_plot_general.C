// full_analysis_with_plot_general.C
// ------------------------------------------------------------------
// Single entry point to run the 2-D discovery scan for any signal
// mass and scenario. Usage from ROOT:
//   root -l -b -q 'Analysis_Programs/full_analysis_with_plot_general.C+(1600,"default","ttp_Analysis")'
// The macro knows about several scenarios (default, plus80, minus80,
// ISR, plus80ISR) and reuses the same shape-based discovery workflow
// that lived in the mass-specific macros.
// ------------------------------------------------------------------

#include <algorithm>
#include <cctype>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <sstream>
#include <string>
#include <vector>

#include <fstream>
#include <unordered_map>

#include "TFile.h"
#include "TH1.h"
#include "TSystem.h"
#include "TString.h"
#include "TError.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TLine.h"
#include "TLatex.h"
#include "Math/MinimizerOptions.h"

#include "RooWorkspace.h"
#include "RooRealVar.h"
#include "RooDataHist.h"
#include "RooHistPdf.h"
#include "RooFormulaVar.h"
#include "RooAddPdf.h"
#include "RooPlot.h"
#include "RooStats/ModelConfig.h"
#include "RooStats/HypoTestResult.h"
#include "RooStats/ProfileLikelihoodTestStat.h"
#include "RooStats/FrequentistCalculator.h"
#include "RooStats/ToyMCSampler.h"
#include "RooStats/AsymptoticCalculator.h"

#include "ROOT/RConfig.hxx"
#ifndef __has_include
#  define __has_include(x) 0
#endif

#if __has_include("ROOT/EnableImplicitMT.hxx")
#  include "ROOT/EnableImplicitMT.hxx"
#  define ASE_HAS_IMPLICIT_MT 1
#else
#  define ASE_HAS_IMPLICIT_MT 0
#endif

using namespace RooFit;
using namespace RooStats;

namespace analysis {

struct SampleCfg {
    std::string file;
    std::string hname;
    std::string dh;
    std::string pdf;
    double      xsec_pb;
};

struct ScenarioConfig {
    std::string canonicalName;
    std::string signalFilePattern;
    std::string signalHist;
    std::string signalDh;
    std::string signalPdf;
    std::map<int, double> signalXsecs;
    std::vector<SampleCfg> backgrounds;

    std::optional<double> signalXsec(int mass) const {
        auto it = signalXsecs.find(mass);
        if (it != signalXsecs.end()) {
            return it->second;
        }
        return std::nullopt;
    }
};

constexpr double LUMI_FB = 5000.0;                 // fb^-1
constexpr double LUMI_PB = LUMI_FB * 1e3;          // pb^-1
constexpr double FULL_MIN   = 900.0;
constexpr double FULL_MAX   = 4000.0;
constexpr double STEP_POS   = 10.0;
constexpr double WIN_MIN_W  = 30.0;
constexpr double WIN_MAX_W  = 150.0;
constexpr double WIN_STEP_W = 5.0;
constexpr int    REBIN      = 15;
constexpr double EPS_BIN    = 1e-3;

static std::string joinPath(const std::string& base, const std::string& leaf) {
    if (leaf.empty()) {
        return leaf;
    }
    if (!leaf.empty() && (leaf.front() == '/' || leaf.find(":") != std::string::npos)) {
        return leaf;
    }
    if (base.empty() || base == "." || base == "./") {
        return leaf;
    }
    if (base.back() == '/') {
        return base + leaf;
    }
    return base + "/" + leaf;
}

static std::string sanitizeTag(const std::string& raw) {
    std::string out;
    out.reserve(raw.size());
    for (char c : raw) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        } else if (c == '+') {
            out += "p";
        } else if (c == '-') {
            out += "m";
        } else if (c == '_') {
            out.push_back('_');
        }
    }
    if (out.empty()) {
        out = "default";
    }
    return out;
}

static std::string canonicalKey(const std::string& raw) {
    std::string key;
    key.reserve(raw.size());
    for (char c : raw) {
        if (c == '+') {
            key += "plus";
        } else if (c == '-') {
            key += "minus";
        } else if (std::isalnum(static_cast<unsigned char>(c))) {
            key.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        }
    }
    if (key.empty()) {
        key = "default";
    }
    return key;
}

static const ScenarioConfig& scenarioDefault() {
    static const ScenarioConfig cfg{
        "default",
        "root/Tt1M%d.root",
        "mrecoil_isolated_toplikes_rec_missE_cut",
        "dh_sig",
        "pdf_sig",
        {{1200, 0.00024646},
         {1600, 0.00018864},
         {2000, 0.00012084},
         {2400, 0.00005332}},
        {
            {"root/tth.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_tth",   "pdf_tth",   0.000804664},
            {"root/ttz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttz",   "pdf_ttz",   0.06135961},
            {"root/ttbar.root", "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttbar", "pdf_ttbar", 0.0191426},
            {"root/wwz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_wwz",   "pdf_wwz",   0.0261182}
        }
    };
    return cfg;
}

static const ScenarioConfig& scenarioPlus80() {
    static const ScenarioConfig cfg{
        "plus80",
        "root/Tt1M%d.root",
        "mrecoil_isolated_toplikes_rec_missE_cut",
        "dh_sig",
        "pdf_sig",
        {{1200, 0.00022097},
         {1600, 0.00016914},
         {2000, 0.00010835},
         {2400, 0.000047812}},
        {
            {"root/tth.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_tth",   "pdf_tth",   0.000290824},
            {"root/ttz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttz",   "pdf_ttz",   0.000882585},
            {"root/ttbar.root", "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttbar", "pdf_ttbar", 0.0134477},
            {"root/wwz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_wwz",   "pdf_wwz",   0.00673714}
        }
    };
    return cfg;
}

static const ScenarioConfig& scenarioMinus80() {
    static const ScenarioConfig cfg{
        "minus80",
        "root/Tt1M%d.root",
        "mrecoil_isolated_toplikes_rec_missE_cut",
        "dh_sig",
        "pdf_sig",
        {{1200, 0.00027191},
         {1600, 0.00027191},
         {2000, 0.00013332},
         {2400, 0.00005883}},
        {
            {"root/tth.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_tth",   "pdf_tth",   0.00052637},
            {"root/ttz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttz",   "pdf_ttz",   0.00242068},
            {"root/ttbar.root", "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttbar", "pdf_ttbar", 0.024836},
            {"root/wwz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_wwz",   "pdf_wwz",   0.0593784}
        }
    };
    return cfg;
}

static const ScenarioConfig& scenarioISR() {
    static const ScenarioConfig cfg{
        "isr",
        "root/Tt1M%d.root",
        "mrecoil_isolated_toplikes_rec_missE_cut",
        "dh_sig",
        "pdf_sig",
        {{1200, 0.00025326},
         {1600, 0.00017351},
         {2000, 0.000098746},
         {2400, 0.000037462}},
        {
            {"root/tth.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_tth",   "pdf_tth",   0.000510609},
            {"root/ttz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttz",   "pdf_ttz",   0.00188746},
            {"root/ttbar.root", "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttbar", "pdf_ttbar", 0.028716},
            {"root/wwz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_wwz",   "pdf_wwz",   0.0355571}
        }
    };
    return cfg;
}

static const ScenarioConfig& scenarioPlus80ISR() {
    static const ScenarioConfig cfg{
        "plus80isr",
        "root/Tt1M%d.root",
        "mrecoil_isolated_toplikes_rec_missE_cut",
        "dh_sig",
        "pdf_sig",
        {{1200, 0.00022714},
         {1600, 0.00015563},
         {2000, 0.000088552},
         {2400, 0.000033595}},
        {
            {"root/tth.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_tth",   "pdf_tth",   0.000360634},
            {"root/ttz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttz",   "pdf_ttz",   0.00101029},
            {"root/ttbar.root", "mrecoil_isolated_toplikes_rec_missE_cut", "dh_ttbar", "pdf_ttbar", 0.020091},
            {"root/wwz.root",   "mrecoil_isolated_toplikes_rec_missE_cut", "dh_wwz",   "pdf_wwz",   0.00726982}
        }
    };
    return cfg;
}

static const ScenarioConfig& resolveScenario(const std::string& name) {
    const std::string key = canonicalKey(name);
    if (key == "default" ||
        key == "ttpanalysis" ||
        key.find("kappa") != std::string::npos) {
        return scenarioDefault();
    }
    if (key.find("plus80isr") != std::string::npos ||
        key.find("minus80isr") != std::string::npos) {
        return scenarioPlus80ISR();
    }
    if (key.find("plus80") != std::string::npos) {
        return scenarioPlus80();
    }
    if (key.find("minus80") != std::string::npos) {
        return scenarioMinus80();
    }
    if (key.find("isr") != std::string::npos) {
        return scenarioISR();
    }
    return scenarioDefault();
}

static void fixEmpty(TH1* h, double eps = EPS_BIN) {
    for (int i = 1; i <= h->GetNbinsX(); ++i) {
        if (h->GetBinContent(i) <= 0.0) {
            h->SetBinContent(i, eps);
            h->SetBinError(i, eps);
        }
    }
}

static std::unique_ptr<TH1> loadSampleHistogram(const SampleCfg& sample,
                                                double mMin,
                                                double mMax,
                                                const std::string& baseDir,
                                                double xsecOverride) {
    const std::string path = joinPath(baseDir, sample.file);
    TFile file(path.c_str());
    if (!file.IsOpen()) {
        throw std::runtime_error("Cannot open ROOT file: " + path);
    }
    TH1* raw = nullptr;
    file.GetObject(sample.hname.c_str(), raw);
    if (!raw) {
        throw std::runtime_error("Histogram '" + std::string(sample.hname) +
                                 "' not found in " + path);
    }
    TString cloneName = TString::Format("%s_clone_%p", sample.hname.c_str(), raw);
    std::unique_ptr<TH1> h(static_cast<TH1*>(raw->Clone(cloneName)));
    h->SetDirectory(nullptr);
    if (mMax > mMin) {
        h->GetXaxis()->SetRangeUser(mMin, mMax);
    }
    if (REBIN > 1) {
        h->Rebin(REBIN);
    }
    const double entries = h->GetEntries();
    if (entries <= 0.0) {
        throw std::runtime_error("Histogram '" + std::string(sample.hname) +
                                 "' from " + path + " has no entries after selection.");
    }
    const double xsec = xsecOverride > 0.0 ? xsecOverride : sample.xsec_pb;
    h->Scale(xsec * LUMI_PB / entries);
    fixEmpty(h.get());
    return h;
}

static std::optional<double> parseCrossSectionLine(const std::string& line, const std::string& key) {
    auto pos = line.find(key);
    if (pos == std::string::npos) {
        return std::nullopt;
    }
    auto colon = line.find_last_of(':');
    if (colon == std::string::npos || colon + 1 >= line.size()) {
        return std::nullopt;
    }
    try {
        return std::stod(line.substr(colon + 1));
    } catch (...) {
        return std::nullopt;
    }
}

static std::optional<double> readCrossSectionReport(const std::string& baseDir, const std::string& tag) {
    const std::string path = joinPath(baseDir, "output/out_" + tag + ".dat");
    std::ifstream in(path);
    if (!in.is_open()) {
        return std::nullopt;
    }
    std::string line;
    while (std::getline(in, line)) {
        if (auto xsec = parseCrossSectionLine(line, "Cross section [pb]")) {
            return xsec;
        }
    }
    return std::nullopt;
}

static std::string sampleReportTag(const SampleCfg& sample, int mass) {
    static const std::unordered_map<std::string, std::string> overrides = {
        {"ttbar", "ttbarra"},
        {"ttbarra", "ttbarra"},
        {"wwz", "w+w-z"},
        {"w+w-z", "w+w-z"},
        {"w+w-", "w+w-"},
    };

    std::string name = sample.file;
    auto slash = name.find_last_of("/\\");
    if (slash != std::string::npos) {
        name = name.substr(slash + 1);
    }
    auto dot = name.find_last_of('.');
    if (dot != std::string::npos) {
        name = name.substr(0, dot);
    }
    if (name.rfind("Tt1M", 0) == 0) {
        if (mass > 0) {
            return std::string("Tt1M") + std::to_string(mass);
        }
        return name;
    }
    auto it = overrides.find(name);
    if (it != overrides.end()) {
        return it->second;
    }
    return name;
}

static double resolveSampleXsec(const SampleCfg& sample,
                                int mass,
                                const std::string& baseDir,
                                double fallback) {
    if (mass > 0 || sample.file.find("Tt1M") == std::string::npos) {
        const std::string tag = sampleReportTag(sample, mass);
        if (auto xsec = readCrossSectionReport(baseDir, tag)) {
            if (*xsec > 0.0) {
                return *xsec;
            }
        }
    }
    if (fallback > 0.0) {
        return fallback;
    }
    std::ostringstream oss;
    oss << "Unable to determine cross section for sample '" << sample.file
        << "' in " << baseDir;
    if (mass > 0) {
        oss << " (mass " << mass << ")";
    }
    throw std::runtime_error(oss.str());
}

struct WindowSeed {
    double width = 0.0;
    double L = 0.0;
    double R = 0.0;
    double S = 0.0;
    double B = 0.0;
    double Z = 0.0;
    bool valid() const { return Z > 0.0 && L < R; }
};

static double asymptoticDiscoveryZ(double s, double b) {
    if (s <= 0.0 || b <= 0.0) {
        return 0.0;
    }
    const double term = (s + b) * std::log(1.0 + s / b) - s;
    if (term <= 0.0) {
        return 0.0;
    }
    return std::sqrt(2.0 * term);
}

static double locatePeak(const TH1& h) {
    int maxBin = -1;
    double maxVal = -1.0;
    for (int i = 1; i <= h.GetNbinsX(); ++i) {
        const double val = h.GetBinContent(i);
        if (val > maxVal) {
            maxVal = val;
            maxBin = i;
        }
    }
    if (maxBin <= 0) {
        return -1.0;
    }
    return h.GetXaxis()->GetBinCenter(maxBin);
}

static WindowSeed scanWindows(const TH1& hData,
                              const TH1& hBkg,
                              double peakMass,
                              double widthStep,
                              double posStep,
                              double minWidth,
                              double maxWidth) {
    WindowSeed best;
    const double xmin = hData.GetXaxis()->GetXmin();
    const double xmax = hData.GetXaxis()->GetXmax();
    for (double w = minWidth; w <= maxWidth + 1e-6; w += widthStep) {
        for (double L = xmin; L + w <= xmax + 1e-6; L += posStep) {
            const double R = L + w;
            if (peakMass > 0.0 && !(L <= peakMass && peakMass <= R)) {
                continue;
            }
            const int binL = hData.FindFixBin(L + 1e-6);
            const int binR = hData.FindFixBin(R - 1e-6);
            const double sumData = hData.Integral(binL, binR);
            const double sumBkg  = hBkg.Integral(binL, binR);
            const double s = sumData - sumBkg;
            if (s <= 0.0 || sumBkg <= 0.0) {
                continue;
            }
            const double z = asymptoticDiscoveryZ(s, sumBkg);
            if (z > best.Z) {
                best = WindowSeed{w, L, R, s, sumBkg, z};
            }
        }
    }
    return best;
}

struct ResonanceSeed {
    double peakMass = -1.0;
    WindowSeed window;
};

static ResonanceSeed buildResonanceSeed(const SampleCfg& sig,
                                        const std::vector<SampleCfg>& bkgs,
                                        const std::string& baseDir,
                                        int mass) {
    ResonanceSeed seed;
    const double sigXsec = resolveSampleXsec(sig, mass, baseDir, sig.xsec_pb);
    auto sigHist = loadSampleHistogram(sig, FULL_MIN, FULL_MAX, baseDir, sigXsec);
    auto bkgSum = std::unique_ptr<TH1>(static_cast<TH1*>(sigHist->Clone("bkg_template")));
    bkgSum->Reset("ICES");
    bkgSum->Sumw2();
    for (auto const& b : bkgs) {
        const double bXsec = resolveSampleXsec(b, -1, baseDir, b.xsec_pb);
        auto hb = loadSampleHistogram(b, FULL_MIN, FULL_MAX, baseDir, bXsec);
        bkgSum->Add(hb.get());
    }
    auto dataHist = std::unique_ptr<TH1>(static_cast<TH1*>(bkgSum->Clone("sb_template")));
    dataHist->Add(sigHist.get());
    seed.peakMass = locatePeak(*sigHist);
    seed.window = scanWindows(*dataHist,
                              *bkgSum,
                              seed.peakMass,
                              WIN_STEP_W,
                              STEP_POS,
                              WIN_MIN_W,
                              WIN_MAX_W);
    return seed;
}

static SampleCfg makeSignalSample(const ScenarioConfig& cfg, int mass, double overrideXsec) {
    double xsec = overrideXsec;
    if (xsec <= 0.0) {
        if (auto preset = cfg.signalXsec(mass)) {
            xsec = *preset;
        } else {
            xsec = -1.0;
        }
    }
    SampleCfg sig{
        TString::Format(cfg.signalFilePattern.c_str(), mass).Data(),
        cfg.signalHist,
        cfg.signalDh,
        cfg.signalPdf,
        xsec
    };
    return sig;
}

static void AddModel(RooWorkspace* w,
                     double mMin,
                     double mMax,
                     const SampleCfg& sig,
                     const std::vector<SampleCfg>& bkgs,
                     const std::string& baseDir,
                     int mass) {
    w->factory(TString::Format("invMass[%.1f,%.1f]", mMin, mMax));
    auto& inv = *w->var("invMass");

    // signal
    const double sigXsec = resolveSampleXsec(sig, mass, baseDir, sig.xsec_pb);
    auto sigHist = loadSampleHistogram(sig, mMin, mMax, baseDir, sigXsec);
    const double Nsig0 = sigHist->Integral();
    RooDataHist dhs(sig.dh.c_str(), "sig", RooArgList(inv), sigHist.get());
    w->import(dhs);
    w->factory(TString::Format("RooHistPdf::%s(invMass,%s,2)", sig.pdf.c_str(), sig.dh.c_str()).Data());
    w->factory(TString::Format("Nsig0[%.8g]", Nsig0));

    // backgrounds
    std::vector<double> Nbkg;
    Nbkg.reserve(bkgs.size());
    for (size_t i = 0; i < bkgs.size(); ++i) {
        const double bXsec = resolveSampleXsec(bkgs[i], -1, baseDir, bkgs[i].xsec_pb);
        auto hb = loadSampleHistogram(bkgs[i], mMin, mMax, baseDir, bXsec);
        const double integral = hb->Integral();
        Nbkg.push_back(integral);
        RooDataHist db(bkgs[i].dh.c_str(), bkgs[i].dh.c_str(), RooArgList(inv), hb.get());
        w->import(db);
        w->factory(TString::Format("RooHistPdf::%s(invMass,%s,2)", bkgs[i].pdf.c_str(), bkgs[i].dh.c_str()).Data());
    }

    w->factory("mu[1,1e-4,1]");
    RooFormulaVar nsig("nsig", "mu*Nsig0", RooArgList(*w->var("mu"), *w->var("Nsig0")));
    w->import(nsig);

    RooArgList pdfs(*w->pdf(sig.pdf.c_str()));
    RooArgList yields(*w->function("nsig"));

    if (!Nbkg.empty()) {
        w->factory("kB1[1,0.5,1.5]");
    }
    for (size_t i = 0; i < Nbkg.size(); ++i) {
        w->factory(TString::Format("NB%zu[%.8g]", i + 1, Nbkg[i]));
        if (i == 0) {
            w->factory("prod::NB1scaled(kB1,NB1)");
            yields.add(*w->function("NB1scaled"));
        } else {
            yields.add(*w->var(TString::Format("NB%zu", i + 1)));
        }
        pdfs.add(*w->pdf(bkgs[i].pdf.c_str()));
    }

    RooAddPdf model("model", "sig+bkgs", pdfs, yields);
    w->import(model);

    ModelConfig mc("ModelConfig");
    mc.SetWorkspace(*w);
    mc.SetPdf(model);
    mc.SetObservables(RooArgSet(inv));
    mc.SetParametersOfInterest(RooArgSet(*w->var("mu")));
    w->import(mc);

    w->var("Nsig0")->setConstant(true);
    if (!Nbkg.empty()) {
        w->var("NB1")->setConstant(true);
    }
    for (size_t i = 1; i < Nbkg.size(); ++i) {
        w->var(TString::Format("NB%zu", i + 1))->setConstant(true);
    }
}

static void AddData(RooWorkspace* w) {
    w->var("mu")->setVal(1.0);
    w->var("mu")->setConstant(kTRUE);
    std::unique_ptr<RooDataHist> data(
        w->pdf("model")->generateBinned(*w->var("invMass"),
                                        RooFit::Name("data"),
                                        RooFit::Extended(kTRUE)));
    w->import(*data);
    w->var("mu")->setConstant(kFALSE);
}

static void DiscoveryTest(RooWorkspace* w, double& p0, double& Z) {
    gSystem->RedirectOutput("/dev/null", "w");

    auto* data = w->data("data");
    auto* mc_sb = static_cast<ModelConfig*>(w->obj("ModelConfig"));
    auto* mc_b = static_cast<ModelConfig*>(mc_sb->Clone("mc_b"));
    w->import(*mc_b);

    RooRealVar* poi = dynamic_cast<RooRealVar*>(mc_sb->GetParametersOfInterest()->first());
    poi->setVal(0.0);
    RooArgSet snapB("snapB");
    snapB.add(*poi);
    mc_b->SetSnapshot(snapB);

    poi->setVal(1.0);
    RooArgSet snapSB("snapSB");
    snapSB.add(*poi);
    mc_sb->SetSnapshot(snapSB);

    AsymptoticCalculator ac(*data, *mc_b, *mc_sb, true);
    std::unique_ptr<HypoTestResult> h(ac.GetHypoTest());

    p0 = h->NullPValue();
    Z  = h->Significance();

    gSystem->RedirectOutput(nullptr);
}

static void PlotBestWindow(double L,
                           double R,
                           double bestZ,
                           const SampleCfg& signal,
                           const ScenarioConfig& scenario,
                           const std::string& baseDir,
                           const std::string& prefix,
                           int mass) {
    RooWorkspace ws("ws_plot");
    AddModel(&ws, L, R, signal, scenario.backgrounds, baseDir, mass);

    RooRealVar& m = *ws.var("invMass");
    RooAbsPdf*  pdf = ws.pdf("model");

    ws.var("mu")->setVal(1.0);
    auto dataSB = std::unique_ptr<RooDataHist>(
        pdf->generateBinned(m, RooFit::Extended(true), RooFit::Name("dataSB")));
    double nEvtSB = dataSB->sumEntries();

    ws.var("mu")->setVal(0.0);
    auto dataB = std::unique_ptr<RooDataHist>(
        pdf->generateBinned(m, RooFit::Extended(true), RooFit::Name("dataB")));
    double nEvtB = dataB->sumEntries();

    std::unique_ptr<RooPlot> frameTop(m.frame(RooFit::Title("Best window: B-only, S, and S+B")));

    dataSB->plotOn(frameTop.get(), RooFit::MarkerStyle(20), RooFit::Name("Asimov"));

    ws.var("mu")->setVal(0.0);
    pdf->plotOn(frameTop.get(),
                RooFit::LineColor(kBlue),
                RooFit::LineStyle(kDashed),
                RooFit::Name("Bonly"),
                RooFit::Normalization(nEvtB, RooAbsReal::NumEvent));

    ws.var("mu")->setVal(1.0);
    pdf->plotOn(frameTop.get(),
                RooFit::LineColor(kRed),
                RooFit::Name("SplusB"),
                RooFit::Normalization(nEvtSB, RooAbsReal::NumEvent));

    RooAbsPdf* pdfSig = ws.pdf(signal.pdf.c_str());
    if (pdfSig) {
        pdfSig->plotOn(frameTop.get(),
                       RooFit::LineColor(kGreen + 2),
                       RooFit::LineStyle(kDotted),
                       RooFit::Name("SigScaled"),
                       RooFit::Normalization(nEvtSB, RooAbsReal::NumEvent));
    }

    TCanvas c1("c_bestTop", "best window absolute", 800, 600);
    frameTop->Draw();

    TLegend leg(0.58, 0.15, 0.88, 0.35);
    leg.SetBorderSize(0);
    leg.AddEntry(frameTop->findObject("Bonly"), "Background only", "l");
    leg.AddEntry(frameTop->findObject("SplusB"), "Signal + background", "l");
    if (frameTop->findObject("SigScaled")) {
        leg.AddEntry(frameTop->findObject("SigScaled"), "Signal (scaled)", "l");
    }
    leg.AddEntry(frameTop->findObject("Asimov"), "Asimov S+B", "p");
    leg.Draw();

    TLatex latex;
    latex.SetNDC();
    latex.SetTextSize(0.03);
    latex.SetTextAlign(13);
    latex.DrawLatex(0.15, 0.85, TString::Format("Best Z: %.2f", bestZ));

    c1.SaveAs(joinPath(baseDir, prefix + "_bestWindow_invMass.png").c_str());

    std::unique_ptr<TH1> hSB(dataSB->createHistogram("hSB", m));
    std::unique_ptr<TH1> hB(dataB->createHistogram("hB", m));
    hSB->Sumw2();
    hB->Sumw2();
    hSB->Divide(hB.get());
    hSB->SetLineColor(kBlack);
    hSB->SetMarkerStyle(20);
    hSB->GetYaxis()->SetTitle("(S+B)/B");
    hSB->GetYaxis()->SetNdivisions(505);
    hSB->GetYaxis()->SetRangeUser(0.9, 1.1);

    TCanvas c2("c_bestRatio", "ratio (S+B)/B", 800, 400);
    hSB->Draw("EP");
    TLine l1(L, 1.0, R, 1.0);
    l1.SetLineStyle(kDashed);
    l1.Draw();
    c2.SaveAs(joinPath(baseDir, prefix + "_bestWindow_ratio.png").c_str());

    TFile fout(joinPath(baseDir, prefix + "_bestWindow_canvases.root").c_str(), "RECREATE");
    c1.Write();
    c2.Write();
    fout.Close();
}

struct WindowResult {
    double width = 0.0;
    double L = 0.0;
    double R = 0.0;
    double p0 = 1.0;
    double Z = 0.0;
    double expS = 0.0;
    double expB = 0.0;
};

static std::string niceScenarioLabel(const ScenarioConfig& cfg) {
    return cfg.canonicalName;
}

void runDiscoveryScan(int mass,
                      const std::string& scenarioName,
                      const std::string& baseDir,
                      double overrideSignalXsec) {
    const ScenarioConfig& scenario = resolveScenario(scenarioName);
    const SampleCfg signal = makeSignalSample(scenario, mass, overrideSignalXsec);
    const std::string tag = sanitizeTag(scenario.canonicalName);
    const std::string prefix = tag + "_m" + std::to_string(mass);

    #if ASE_HAS_IMPLICIT_MT
        ROOT::EnableImplicitMT();
    #else
        std::cout << "[warning] ROOT::EnableImplicitMT not available in this ROOT build; continuing single-threaded.\n";
    #endif
    RooMsgService::instance().setGlobalKillBelow(RooFit::FATAL);
    RooMsgService::instance().setSilentMode(true);
    ROOT::Math::MinimizerOptions::SetDefaultPrintLevel(0);
    gErrorIgnoreLevel = kFatal;

    std::vector<WindowResult> results;
    results.reserve(static_cast<size_t>((WIN_MAX_W - WIN_MIN_W) / WIN_STEP_W + 1) *
                    static_cast<size_t>((FULL_MAX - FULL_MIN) / STEP_POS + 1));

    double bestZ  = -1e9;
    double bestP0 = 1.0;
    double bestW  = 0.0;
    double bestL  = 0.0;
    double bestR  = 0.0;

    std::cout << "\nScenario: " << niceScenarioLabel(scenario)
              << " | mass = " << mass
              << " GeV | signal xsec = " << signal.xsec_pb
              << " pb\n";
    std::cout << "2-D discovery scan (shape-based, asymptotic toys)\n"
              << " width  window[GeV]     p0        Z\n"
              << " -------------------------------------------\n";

    ResonanceSeed seed;
    try {
        seed = buildResonanceSeed(signal, scenario.backgrounds, baseDir, mass);
        if (seed.peakMass > 0.0) {
            std::cout << "Seed: peak ≈ " << std::fixed << std::setprecision(1) << seed.peakMass << " GeV";
            if (seed.window.valid()) {
                std::cout << ", window ≈ [" << seed.window.L << ", " << seed.window.R << "] GeV"
                          << " (Z ≈ " << std::setprecision(2) << seed.window.Z << ")\n"
                          << "Restricting scan to windows that include the resonance seed.\n";
            } else {
                std::cout << " (no positive pre-scan window)\nScanning full window space.\n";
            }
        } else {
            std::cout << "Seed: unable to locate positive signal peak; scanning full window space.\n";
        }
    } catch (const std::exception& ex) {
        std::cout << "[warning] Resonance seed extraction failed: " << ex.what()
                  << "\nProceeding with full window scan.\n";
        seed.peakMass = -1.0;
    }
    std::cout << std::defaultfloat << std::setprecision(6);
    const bool enforcePeak = seed.peakMass > 0.0 && seed.window.valid() && seed.window.Z >= 0.15;
    double peakGuardL = seed.peakMass - std::max(seed.window.width > 0.0 ? seed.window.width : WIN_MAX_W, WIN_MAX_W);
    double peakGuardR = seed.peakMass + std::max(seed.window.width > 0.0 ? seed.window.width : WIN_MAX_W, WIN_MAX_W);
    if (!enforcePeak) {
        peakGuardL = FULL_MIN;
        peakGuardR = FULL_MAX;
    } else {
        peakGuardL = std::max(FULL_MIN, peakGuardL);
        peakGuardR = std::min(FULL_MAX, peakGuardR);
    }

    for (double w = WIN_MIN_W; w <= WIN_MAX_W + 1e-6; w += WIN_STEP_W) {
        for (double L = FULL_MIN; L + w <= FULL_MAX + 1e-6; L += STEP_POS) {
            const double R = L + w;
            if (enforcePeak && (R < peakGuardL || L > peakGuardR)) {
                continue;
            }
            RooWorkspace ws("ws");
            AddModel(&ws, L, R, signal, scenario.backgrounds, baseDir, mass);

            const double expS = ws.var("Nsig0")->getVal();
            double expB = 0.0;
            if (!scenario.backgrounds.empty()) {
                expB = ws.var("NB1")->getVal() * ws.var("kB1")->getVal();
            }
            if (expS < 0.2 || expB < 0.5) {
                std::cout << std::setw(6) << w << "  "
                          << std::setw(4) << L << "-" << std::setw(4) << R << "  "
                          << "  -- skipped (S=" << std::fixed << std::setprecision(1) << expS
                          << ", B=" << expB << ")\n";
                continue;
            }

            AddData(&ws);
            double p0 = 1.0;
            double Z  = 0.0;
            DiscoveryTest(&ws, p0, Z);
            if (!std::isfinite(p0) || p0 < 0.0) {
                p0 = 1.0;
            }
            if (!std::isfinite(Z)) {
                Z = 0.0;
            }
            if (Z < 0.0 || p0 > 0.5) {
                Z = 0.0;
            }
            results.push_back({w, L, R, p0, Z, expS, expB});
            std::cout << std::setw(6) << w << "  "
                      << std::setw(4) << L << "-" << std::setw(4) << R << "  "
                      << std::scientific << std::setprecision(2) << p0 << "  "
                      << std::fixed << std::setprecision(2) << Z << "\n";
            if (Z > bestZ) {
                bestZ = Z;
                bestP0 = p0;
                bestW = w;
                bestL = L;
                bestR = R;
            }
        }
    }

    if (bestZ <= -1e8 && seed.window.valid()) {
        bestZ = seed.window.Z;
        bestW = seed.window.width;
        bestL = seed.window.L;
        bestR = seed.window.R;
        bestP0 = std::numeric_limits<double>::quiet_NaN();
        std::cout << "[info] Falling back to resonance seed window (RooStats scan produced no surviving candidates).\n";
    }

    std::cout << "\n>>> Global maximum Z = " << std::fixed << std::setprecision(2) << bestZ
              << " at width=" << bestW << " GeV, window "
              << bestL << "-" << bestR << " GeV (p0=" << std::scientific << bestP0 << ")\n";

    PlotBestWindow(bestL, bestR, bestZ, signal, scenario, baseDir, prefix, mass);
}

} // namespace analysis

void full_analysis_with_plot(int mass = 1600,
                             const char* scenarioName = "default",
                             const char* baseDir = ".",
                             double overrideSignalXsec = -1.0) {
    analysis::runDiscoveryScan(mass,
                               scenarioName ? scenarioName : std::string("default"),
                               baseDir ? baseDir : std::string("."),
                               overrideSignalXsec);
}

void full_analysis_with_plot_general(int mass = 1600,
                                     const char* scenarioName = "default",
                                     const char* baseDir = ".",
                                     double overrideSignalXsec = -1.0) {
    full_analysis_with_plot(mass, scenarioName, baseDir, overrideSignalXsec);
}
