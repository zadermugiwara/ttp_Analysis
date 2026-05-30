// find_resonance_agnostic.C
// ------------------------------------------------------------------
// Data-driven resonance locator:
//   * reads a RooWorkspace (default: myWS) containing the observed dataset
//     and the composite model (signal + backgrounds).
//   * builds binned versions of the observed spectrum and the background-only
//     expectation (by setting mu = 0).
//   * subtracts the background to estimate the excess spectrum.
//   * identifies the resonance peak without using the nominal mass label,
//     then scans sliding mass windows that contain the peak and evaluates
//     the Cowan discovery significance approximation.
//   * reports the best window and saves diagnostic plots.
//
// Run from ROOT:
//   root -l -b -q 'Analysis_Programs/find_resonance_agnostic.C+("ttp_Analysis/myWS1600.root")'
// ------------------------------------------------------------------

#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "TCanvas.h"
#include "TFile.h"
#include "TLegend.h"
#include "TLine.h"
#include "TBox.h"
#include "TLatex.h"
#include "TH1.h"
#include "TStyle.h"

#include "RooAbsData.h"
#include "RooWorkspace.h"
#include "RooAbsPdf.h"
#include "RooRealVar.h"
#include "RooDataSet.h"
#include "RooDataHist.h"
#include "RooArgList.h"
#include "RooArgSet.h"
#include "RooBinning.h"
#include "RooGlobalFunc.h"

namespace resonance_finder {

struct WindowResult {
    double width   = 0.0;
    double L       = 0.0;
    double R       = 0.0;
    double S       = 0.0;
    double B       = 0.0;
    double Z       = 0.0;
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

static std::unique_ptr<TH1> makeHistogram(const RooAbsData* data,
                                          RooRealVar& obs,
                                          int nBins,
                                          double xmin,
                                          double xmax,
                                          const char* name) {
    if (!data) {
        throw std::runtime_error("Null dataset");
    }
    auto hist = std::make_unique<TH1D>(name, name, nBins, xmin, xmax);
    hist->Sumw2();
    for (std::size_t i = 0; i < static_cast<std::size_t>(data->numEntries()); ++i) {
        const RooArgSet* row = data->get(i);
        if (!row) {
            continue;
        }
        const RooRealVar* v = dynamic_cast<const RooRealVar*>(row->find(obs.GetName()));
        if (!v) {
            continue;
        }
        const double val = v->getVal();
        if (val < xmin || val >= xmax) {
            continue;
        }
        const double weight = data->weight();
        hist->Fill(val, weight);
    }
    return hist;
}

static WindowResult scanWindows(const TH1& hData,
                                const TH1& hBkg,
                                double peakMass,
                                double step,
                                double minWidth,
                                double maxWidth) {
    WindowResult best;
    const double xmin = hData.GetXaxis()->GetXmin();
    const double xmax = hData.GetXaxis()->GetXmax();
    for (double w = minWidth; w <= maxWidth + 1e-6; w += step) {
        for (double L = xmin; L + w <= xmax + 1e-6; L += step) {
            const double R = L + w;
            if (!(L <= peakMass && peakMass <= R)) {
                continue; // enforce windows containing the peak
            }
            const int binL = hData.FindFixBin(L + 1e-6);
            const int binR = hData.FindFixBin(R - 1e-6);
            const double sumData = hData.Integral(binL, binR);
            const double sumBkg  = hBkg.Integral(binL, binR);
            double s = sumData - sumBkg;
            if (s <= 0.0) {
                continue;
            }
            double z = asymptoticDiscoveryZ(s, sumBkg);
            if (z > best.Z) {
                best = WindowResult{w, L, R, s, sumBkg, z};
            }
        }
    }
    return best;
}

static void drawDiagnostics(TH1& hData,
                            const TH1& hBkg,
                            TH1& hExcess,
                            const WindowResult& best,
                            double peakMass,
                            const std::string& outPrefix) {
    gStyle->SetOptStat(0);

    TCanvas c1("c_res_data", "data vs background", 900, 600);
    hData.SetLineColor(kBlack);
    hData.SetMarkerColor(kBlack);
    hData.SetMarkerStyle(20);
    hData.Draw("E");

    TH1* hBclone = static_cast<TH1*>(hBkg.Clone("hB_clone"));
    hBclone->SetLineColor(kRed);
    hBclone->SetLineWidth(2);
    hBclone->Draw("HIST SAME");

    TBox box(best.L, 0, best.R, hData.GetMaximum()*1.05);
    box.SetFillColorAlpha(kAzure + 7, 0.25);
    box.SetLineColor(kAzure + 7);
    box.Draw("same");

    TLine resonanceLine(peakMass, 0, peakMass, hData.GetMaximum()*1.05);
    resonanceLine.SetLineColor(kGreen + 2);
    resonanceLine.SetLineWidth(2);
    resonanceLine.SetLineStyle(kDashed);
    resonanceLine.Draw("same");

    TLegend leg(0.58, 0.65, 0.88, 0.87);
    leg.SetBorderSize(0);
    leg.AddEntry(&hData, "Observed", "lep");
    leg.AddEntry(hBclone, "Background-only", "l");
    leg.AddEntry(&box, "best window", "f");
    leg.AddEntry(&resonanceLine, "peak estimate", "l");
    leg.Draw();

    TLatex latex;
    latex.SetNDC();
    latex.SetTextSize(0.03);
    latex.DrawLatex(0.16, 0.85,
                    Form("Best Z = %.2f  |  window %.0f-%.0f GeV",
                         best.Z, best.L, best.R));

    c1.SaveAs((outPrefix + "_data_vs_bkg.png").c_str());

    TCanvas c2("c_res_excess", "excess spectrum", 900, 400);
    hExcess.SetLineColor(kBlue + 1);
    hExcess.SetMarkerColor(kBlue + 1);
    hExcess.SetMarkerStyle(21);
    hExcess.Draw("HIST E");

    TLine zeroLine(hExcess.GetXaxis()->GetXmin(), 0.0,
                   hExcess.GetXaxis()->GetXmax(), 0.0);
    zeroLine.SetLineColor(kGray + 2);
    zeroLine.SetLineStyle(kDashed);
    zeroLine.Draw("same");

    TLine peakLine(peakMass, hExcess.GetMinimum()*0.9,
                   peakMass, hExcess.GetMaximum()*1.05);
    peakLine.SetLineColor(kGreen + 2);
    peakLine.SetLineStyle(kDashed);
    peakLine.Draw("same");

    c2.SaveAs((outPrefix + "_excess.png").c_str());
    delete hBclone;
}

} // namespace resonance_finder

void find_resonance_agnostic(const char* wsFile,
                             const char* wsName = "myWS",
                             const char* pdfName = "model",
                             const char* dataName = "data",
                             const char* observable = "invMass",
                             double binWidth = 5.0,
                             double minWidth = 30.0,
                             double maxWidth = 150.0,
                             double stepWidth = 5.0,
                             bool savePlots = true) {
    using namespace resonance_finder;

    if (!wsFile) {
        throw std::runtime_error("Workspace file path is null");
    }
    TFile file(wsFile, "READ");
    if (!file.IsOpen()) {
        throw std::runtime_error(std::string("Failed to open workspace file: ") + wsFile);
    }

    RooWorkspace* ws = nullptr;
    file.GetObject(wsName, ws);
    if (!ws) {
        throw std::runtime_error(std::string("Workspace '") + wsName + "' not found in " + wsFile);
    }

    auto* model = ws->pdf(pdfName);
    if (!model) {
        throw std::runtime_error(std::string("PDF '") + pdfName + "' not found in workspace");
    }
    auto* data = ws->data(dataName);
    if (!data) {
        throw std::runtime_error(std::string("Dataset '") + dataName + "' not found in workspace");
    }
    auto* mass = ws->var(observable);
    if (!mass) {
        throw std::runtime_error(std::string("Observable '") + observable + "' not found in workspace");
    }

    const double xmin = mass->getMin();
    const double xmax = mass->getMax();
    if (xmax <= xmin) {
        throw std::runtime_error("Invalid observable range in workspace");
    }
    if (binWidth <= 0.0) {
        throw std::runtime_error("Bin width must be positive");
    }

    const int nBins = static_cast<int>(std::floor((xmax - xmin) / binWidth + 0.5));
    if (nBins < 5) {
        throw std::runtime_error("Computed bin count is too small; adjust binWidth or observable range");
    }

    mass->setRange(xmin, xmax);
    RooArgSet obsSet(*mass);

    std::unique_ptr<TH1> hData = makeHistogram(data, *mass, nBins, xmin, xmax, "hData");

    RooRealVar* mu = ws->var("mu");
    if (!mu) {
        throw std::runtime_error("Parameter 'mu' not found in workspace; cannot build background-only expectation");
    }
    const double muOriginal = mu->getVal();
    mu->setVal(0.0);
    auto hBkg = std::make_unique<TH1D>("hBkg", "hBkg", nBins, xmin, xmax);
    hBkg->Sumw2();
    for (int i = 1; i <= nBins; ++i) {
        const double L = hBkg->GetBinLowEdge(i);
        const double R = hBkg->GetBinLowEdge(i + 1);
        const double center = 0.5 * (L + R);
        mass->setVal(center);
        const double density = model->getVal(obsSet);
        hBkg->SetBinContent(i, density * (R - L));
    }
    const double expected = model->expectedEvents(obsSet);
    const double integral = hBkg->Integral();
    if (integral > 0.0 && expected > 0.0) {
        hBkg->Scale(expected / integral);
    }
    mu->setVal(muOriginal);

    std::unique_ptr<TH1> hExcess(static_cast<TH1*>(hData->Clone("hExcess")));
    hExcess->Add(hBkg.get(), -1.0);

    double weightedSum = 0.0;
    double totalWeight = 0.0;
    const int nBinsHist = hExcess->GetNbinsX();
    for (int i = 1; i <= nBinsHist; ++i) {
        const double val = hExcess->GetBinContent(i);
        if (val > 0.0) {
            const double center = hExcess->GetXaxis()->GetBinCenter(i);
            weightedSum += val * center;
            totalWeight += val;
        }
    }
    double peakMass = 0.0;
    if (totalWeight > 0.0) {
        peakMass = weightedSum / totalWeight;
    } else {
        int maxBin = hExcess->GetMaximumBin();
        peakMass = hExcess->GetXaxis()->GetBinCenter(maxBin);
    }

    const double scanStep = std::max(stepWidth, binWidth);
    WindowResult best = scanWindows(*hData, *hBkg, peakMass, scanStep,
                                    std::max(minWidth, binWidth),
                                    std::max(maxWidth, minWidth));

    std::cout << "\nAgnostic resonance finder results for " << wsFile << "\n"
              << "  Observable range : [" << xmin << ", " << xmax << "] GeV\n"
              << "  Bin width        : " << binWidth << " GeV (" << nBins << " bins)\n"
              << "  Peak estimate    : " << peakMass << " GeV\n";

    if (best.Z <= 0.0) {
        std::cout << "  No positive excess window found that contains the peak.\n";
        return;
    }

    const double center = 0.5 * (best.L + best.R);
    std::cout << "  Best window      : [" << best.L << ", " << best.R
              << "] GeV  (width " << best.width << " GeV, center " << center << " GeV)\n"
              << "  Excess (S)       : " << best.S << " events\n"
              << "  Background (B)   : " << best.B << " events\n"
              << "  Cowan Z          : " << best.Z << "\n\n";

    if (savePlots) {
        const std::string prefixBase =
            std::string(wsFile).substr(std::string(wsFile).find_last_of("/\\") + 1);
        const std::string prefix = "resonance_" + prefixBase;
        drawDiagnostics(*hData, *hBkg, *hExcess, best, peakMass, prefix);
    }
}
