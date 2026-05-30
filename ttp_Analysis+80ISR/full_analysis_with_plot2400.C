// full_analysis_with_plot.C  — 2‑D shape‑based discovery scan (complete)
// -----------------------------------------------------------------------------
// * Scans window width (140–400 GeV in 20 GeV steps) and position (100 GeV steps)
// * Builds a full-binned likelihood model per slice, injects Asimov μ=1 signal
// * Runs a shape-based profile-likelihood test with toys
// * Prints p₀ and Z for each window and reports the global maximum
// -----------------------------------------------------------------------------
// Compile & run:
//   root -l full_analysis_with_plot.C+
//   root [0] full_analysis_with_plot()
// -----------------------------------------------------------------------------

#include <memory>
#include <iostream>
#include <vector>
#include <iomanip>
#include <limits>

#include "TFile.h"
#include "TH1.h"
#include "TSystem.h"
#include "TError.h"
#include "Math/MinimizerOptions.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TLine.h"
#include "TLatex.h"

#include "RooWorkspace.h"
#include "RooRealVar.h"
#include "RooDataHist.h"
#include "RooHistPdf.h"
#include "RooFormulaVar.h"
#include "RooAddPdf.h"
#include "RooStats/ModelConfig.h"
#include "RooPlot.h"
#include "RooStats/HypoTestResult.h"
#include "RooStats/ProfileLikelihoodTestStat.h"
#include "RooStats/FrequentistCalculator.h"
#include "RooStats/ToyMCSampler.h"
#include "RooStats/AsymptoticCalculator.h"
#include "RooStats/ModelConfig.h"

#include <TROOT.h>


using namespace RooFit;
using namespace RooStats;

// sample configuration
struct SampleCfg { const char* file; const char* hname; const char* dh; const char* pdf; double xsec_pb; };
constexpr double LUMI_FB = 5000.0;  // fb^-1
constexpr double LUMI_PB = LUMI_FB * 1e3;
const SampleCfg SIG = {"root/Tt1M2400.root","mrecoil_isolated_toplikes_rec_missE_cut","dh_sig","pdf_sig",0.000033595};
const std::vector<SampleCfg> BKGS = {
    {"root/tth.root","mrecoil_isolated_toplikes_rec_missE_cut","dh_tth","pdf_tth",0.000360634},
    {"root/ttz.root","mrecoil_isolated_toplikes_rec_missE_cut","dh_ttz","pdf_ttz",0.00101029},
    {"root/ttbar.root","mrecoil_isolated_toplikes_rec_missE_cut","dh_ttbar","pdf_ttbar",0.020091},
    {"root/wwz.root","mrecoil_isolated_toplikes_rec_missE_cut","dh_wwz","pdf_wwz",0.00726982}
};

// scan parameters
constexpr double FULL_MIN   = 1155.0;
constexpr double FULL_MAX   = 2500.0;
constexpr double STEP_POS   = 10.0;
constexpr double WIN_MIN_W  = 30.0;
constexpr double WIN_MAX_W  = 100.0;
constexpr double WIN_STEP_W = 5.0;

// histogram tweaks
constexpr int    REBIN   = 15;
constexpr double EPS_BIN = 1e-3;

// helper to avoid log(0)
static void fixEmpty(TH1* h, double eps = EPS_BIN) {
    for (int i = 1; i <= h->GetNbinsX(); ++i) {
        if (h->GetBinContent(i) <= 0.0) {
            h->SetBinContent(i, eps);
            h->SetBinError(i, eps);
        }
    }
}

// build model in [mMin,mMax]
static void AddModel(RooWorkspace* w, double mMin, double mMax) {
    w->factory(TString::Format("invMass[%.1f,%.1f]", mMin, mMax));
    auto& inv = *w->var("invMass");
    // signal
    TFile fs(SIG.file); TH1* hs = nullptr; fs.GetObject(SIG.hname, hs);
    hs->GetXaxis()->SetRangeUser(mMin, mMax); hs->Rebin(REBIN);
    hs->Scale(SIG.xsec_pb * LUMI_PB / hs->GetEntries()); fixEmpty(hs);
    double Nsig0 = hs->Integral();
    RooDataHist dhs(SIG.dh, "sig", RooArgList(inv), hs); w->import(dhs);
    w->factory(TString::Format("RooHistPdf::%s(invMass,%s,2)", SIG.pdf, SIG.dh).Data());
    // backgrounds
    std::vector<double> Nbkg;
    for (auto const& s : BKGS) {
        TFile f(s.file); TH1* h = nullptr; f.GetObject(s.hname, h);
        h->GetXaxis()->SetRangeUser(mMin, mMax);
        h->Scale(s.xsec_pb * LUMI_PB / h->GetEntries()); fixEmpty(h);
        h->Rebin(REBIN);
        h->SetDirectory(0); // prevent deletion
        Nbkg.push_back(h->Integral());
        RooDataHist db(s.dh, s.dh, RooArgList(inv), h); w->import(db);
        w->factory(TString::Format("RooHistPdf::%s(invMass,%s,2)", s.pdf, s.dh).Data());
    }
    // parameters
    w->factory("mu[1,1e-4,1]");
    w->factory(Form("Nsig0[%.1f]", Nsig0));
    for (size_t i = 0; i < Nbkg.size(); ++i)
        w->factory(Form("NB%zu[%.1f]", i+1, Nbkg[i]));
    RooFormulaVar nsig("nsig","mu*Nsig0",RooArgList(*w->var("mu"),*w->var("Nsig0"))); w->import(nsig);
    w->factory("kB1[1,0.5,1.5]");
    w->factory("prod::NB1scaled(kB1,NB1)");
    RooArgList pdfs(*w->pdf(SIG.pdf));
    RooArgList ys(*w->function("nsig"));
    for (auto const& s : BKGS) pdfs.add(*w->pdf(s.pdf));
    ys.add(*w->function("NB1scaled"));
    for (size_t i = 2; i <= Nbkg.size(); ++i) ys.add(*w->var(Form("NB%zu", i)));
    RooAddPdf m("model","sig+bkgs",pdfs,ys); w->import(m);
    ModelConfig mc("ModelConfig"); mc.SetWorkspace(*w); mc.SetPdf(m);
    mc.SetObservables(RooArgSet(inv)); mc.SetParametersOfInterest(RooArgSet(*w->var("mu")));
    w->import(mc);
    w->var("Nsig0")->setConstant(true); w->var("NB1")->setConstant(true);
    for (size_t i = 2; i <= Nbkg.size(); ++i) w->var(Form("NB%zu", i))->setConstant(true);
}
// generate Asimov data
static void AddData(RooWorkspace* w) {
    w->var("mu")->setVal(1.0); w->var("mu")->setConstant(kTRUE);
    auto* d = w->pdf("model")->generateBinned(*w->var("invMass"),Name("data"),Extended());
    w->import(*d); w->var("mu")->setConstant(kFALSE);
}
// shape-based discovery test with FrequentistCalculator (toys)
static void DiscoveryTest(RooWorkspace* w, double& p0, double& Z)
{
    gSystem->RedirectOutput("/dev/null","w");

    auto* data  = w->data("data");
    auto* mc_sb = static_cast<ModelConfig*>(w->obj("ModelConfig"));        // S+B
    auto* mc_b  = static_cast<ModelConfig*>(mc_sb->Clone("mc_b"));         // B-only
    w->import(*mc_b);

            // ---- snapshots for the POI (required by AsymptoticCalculator) ----
    RooRealVar* poi = dynamic_cast<RooRealVar*>(
        mc_sb->GetParametersOfInterest()->first());

    // build persistent argsets and pass them by reference
        poi->setVal(0.0);
    RooArgSet snapB("snapB"); snapB.add(*poi);
    mc_b->SetSnapshot(snapB);
        poi->setVal(1.0);
    RooArgSet snapSB("snapSB"); snapSB.add(*poi);
    mc_sb->SetSnapshot(snapSB);
    // ------------------------------------------------------------------

    AsymptoticCalculator ac(*data, *mc_b, *mc_sb, /*oneSided=*/true);
    std::unique_ptr<HypoTestResult> h(ac.GetHypoTest());

    p0 = h->NullPValue();
    Z  = h->Significance();

    gSystem->RedirectOutput(nullptr);
}


// -----------------------------------------------------------------------------
// helper to draw the invariant‑mass distribution of the *best* window

// ...existing code...

static void PlotBestWindow(double L, double R, double bestZ)
{
    // Build workspace for this slice
    RooWorkspace ws("ws_plot");
    AddModel(&ws, L, R);

    RooRealVar& m    = *ws.var("invMass");
    RooAbsPdf*  pdf  = ws.pdf("model");

    // --- generate Asimov datasets ---
    ws.var("mu")->setVal(1.0);
    auto* dataSB = pdf->generateBinned(m, Extended(true), Name("dataSB"));
    double nEvtSB = dataSB->sumEntries();

    ws.var("mu")->setVal(0.0);
    auto* dataB = pdf->generateBinned(m, Extended(true), Name("dataB"));
    double nEvtB = dataB->sumEntries();

    // ---------------- top canvas: absolute yields ----------------
    std::unique_ptr<RooPlot> frameTop(m.frame(Title("Best window: B-only, S, and S+B")));

    // plot Asimov (S+B) points
    dataSB->plotOn(frameTop.get(), MarkerStyle(20), Name("Asimov"));

    // B‑only curve
    ws.var("mu")->setVal(0.0);
    pdf->plotOn(frameTop.get(), LineColor(kBlue), LineStyle(kDashed), Name("Bonly"),
                Normalization(nEvtB, RooAbsReal::NumEvent));

    // S + B curve
    ws.var("mu")->setVal(1.0);
    pdf->plotOn(frameTop.get(), LineColor(kRed), Name("SplusB"),
                Normalization(nEvtSB, RooAbsReal::NumEvent));

    // ------- extra: make the *signal‑only* component visible (×30 scale) -------
    RooAbsPdf* pdfSig = ws.pdf("pdf_sig");                 // your signal PDF name
    if (pdfSig) {
        pdfSig->plotOn(frameTop.get(),
            LineColor(kGreen+2), LineStyle(kDotted), Name("SigScaled"),
            Normalization(1.0 * nEvtSB, RooAbsReal::NumEvent));   // ×0 boost
    }

    TCanvas c1("c_bestTop", "best window absolute", 800, 600);
    frameTop->Draw();

    // Add legend
    TLegend leg(0.58, 0.15, 0.88, 0.35);
    leg.SetBorderSize(0);
    leg.AddEntry(frameTop->findObject("Bonly"), "Background only", "l");
    leg.AddEntry(frameTop->findObject("SplusB"), "Signal + background", "l");
    if (frameTop->findObject("SigScaled"))
        leg.AddEntry(frameTop->findObject("SigScaled"), "Signal ", "l");
    leg.AddEntry(frameTop->findObject("Asimov"), "Asimov S+B", "p");
    leg.Draw();

    // Draw bestZ value on the canvas
    TLatex latex;
    latex.SetNDC();
    latex.SetTextSize(0.03);
    latex.SetTextAlign(13); // Align at top-left
    latex.DrawLatex(0.15, 0.85, TString::Format("Best Z: %.2f", bestZ));

    c1.SaveAs("bestWindow_invMass2400.png");

    // ---------------- second canvas: ratio ----------------
    TH1* hSB = dataSB->createHistogram("hSB", m);
    TH1* hB  = dataB->createHistogram("hB", m);
    hSB->Sumw2(); hB->Sumw2();
    hSB->Divide(hB);                       // (S+B)/B
    hSB->SetLineColor(kBlack);
    hSB->SetMarkerStyle(20);
    hSB->GetYaxis()->SetTitle("(S+B)/B");
    hSB->GetYaxis()->SetNdivisions(505);
    hSB->GetYaxis()->SetRangeUser(0.9, 1.1);

    TCanvas c2("c_bestRatio", "ratio (S+B)/B", 800, 400);
    hSB->Draw("EP");
    TLine l1(L, 1.0, R, 1.0); l1.SetLineStyle(kDashed); l1.Draw();
    c2.SaveAs("bestWindow_ratio2400.png");

    // --- also save both canvases to a ROOT file so they can be reused interactively
    TFile fout("bestWindow_canvases2400.root", "RECREATE");
    c1.Write();   // writes as object named c_bestTop
    c2.Write();   // writes as object named c_bestRatio
    fout.Close();
    
}

// ...existing code...


// -----------------------------------------------------------------------------
// main scan
void full_analysis_with_plot2400() {
    // enable implicit multithreading for fast toy sampling
    ROOT::EnableImplicitMT();
    RooMsgService::instance().setGlobalKillBelow(RooFit::FATAL);
    RooMsgService::instance().setSilentMode(true);
    ROOT::Math::MinimizerOptions::SetDefaultPrintLevel(0);
    gErrorIgnoreLevel=kFatal;
    cout<<"\n2-D discovery scan (shape-based, toys)\n"
        <<" width  window[GeV]     p0        Z\n"
        <<" -------------------------------------------\n";
    double bestZ=-1e9,bestP0=1.0,bestW=0,bestL=0,bestR=0;
    for(double w=WIN_MIN_W;w<=WIN_MAX_W;w+=WIN_STEP_W){
        for(double L=FULL_MIN;L+w<=FULL_MAX;L+=STEP_POS){
            double R=L+w;RooWorkspace ws("ws");AddModel(&ws,L,R);
            // ---- skip windows with no statistical power ----
            double expS = ws.var("Nsig0")->getVal();          // expected signal
            double expB = ws.var("NB1")->getVal() *           // leading background
                           ws.var("kB1")->getVal();
            if (expS < 2.0 || expB < 3.0) {
                cout << setw(6) << w << "  "
                     << setw(4) << L << "-" << setw(4) << R << "  "
                     << "  -- skipped (S=" << fixed << setprecision(1) << expS
                     << ", B=" << expB << ")\n";
                continue;                                     // <‑‑ skip this slice
            }
            AddData(&ws);
            double p0 = 1.0, Z = 0.0;
            DiscoveryTest(&ws, p0, Z);
            if (Z < 0.0 || p0 > 0.5) Z = 0.0;   // suppress downward fluctuations
            cout<<setw(6)<<w<<"  "<<setw(4)<<L<<"-"<<setw(4)<<R<<"  "
                <<scientific<<setprecision(2)<<p0<<"  "
                <<fixed<<setprecision(2)<<Z<<"\n";
            if(Z>bestZ){bestZ=Z;bestP0=p0;bestW=w;bestL=L;bestR=R;}
            ws.Delete();                                    // <‑‑ cleanup
        }
    }
    cout<<"\n>>> Global maximum Z = "<<fixed<<setprecision(2)<<bestZ
        <<" at width="<<bestW<<" GeV, window "<<bestL<<"-"<<bestR<<" GeV"
        <<" (p0="<<scientific<<bestP0<<")\n";

    // plot the invariant-mass distribution of the best window
    PlotBestWindow(bestL, bestR, bestZ);    
    
  
}
