#!/usr/bin/env python3
"""
Rebuild the recoil_baseline figure (background total + signal) from
ttp_Analysis/Tt1Moutput.root with a square-root label.
"""
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

source_file = ROOT.TFile.Open('/home/higinio/Documentos/ASE/ttp_Analysis/Tt1Moutput.root')
canvas      = source_file.Get('stack_mrecoil_isolated_toplikes_rec_missE_cut_1200_CrossSection')
stack       = canvas.FindObject('mrecoil_isolated_toplikes_rec_missE_cut_stack_1200')

hists = stack.GetHists()
background_hists = []
signal_hist = None
for idx in range(hists.GetSize()):
    hist = hists.At(idx)
    clone = hist.Clone(f'clone_{idx}')
    clone.SetDirectory(0)
    if 'm_{T}=1200' in hist.GetName():
        signal_hist = clone
    else:
        background_hists.append(clone)

if not signal_hist or not background_hists:
    raise RuntimeError('Could not find required histograms in the stack canvas.')

background = background_hists[0].Clone('background_total')
for hist in background_hists[1:]:
    background.Add(hist)
background.SetDirectory(0)

max_y = max(background.GetMaximum(), signal_hist.GetMaximum())
background.SetMaximum(max_y * 1.25)

background.SetFillColor(ROOT.kBlack)
background.SetFillStyle(1001)
background.SetLineColor(ROOT.kBlack)
background.SetLineWidth(2)
background.GetXaxis().SetTitle('#it{m}_{recoil} [GeV]')
background.GetYaxis().SetTitle('Events (5 ab^{-1})')
for axis in (background.GetXaxis(), background.GetYaxis()):
    axis.SetTitleFont(42)
    axis.SetLabelFont(42)
    axis.SetTitleSize(0.045)
    axis.SetLabelSize(0.042)

signal_hist.SetLineColor(ROOT.kAzure + 2)
signal_hist.SetLineWidth(3)
signal_hist.SetFillStyle(0)
signal_hist.SetMarkerStyle(0)
for axis in (signal_hist.GetXaxis(), signal_hist.GetYaxis()):
    axis.SetTitleFont(42)
    axis.SetLabelFont(42)

c = ROOT.TCanvas('c_recoil_baseline_clean','c_recoil_baseline_clean',1200,850)
c.SetMargin(0.12, 0.05, 0.12, 0.08)
background.Draw('HIST')
signal_hist.Draw('HIST SAME')

legend = ROOT.TLegend(0.62, 0.68, 0.88, 0.86)
legend.SetBorderSize(0)
legend.SetFillStyle(0)
legend.SetTextFont(42)
legend.SetTextSize(0.04)
legend.AddEntry(background, 'Background total', 'f')
legend.AddEntry(signal_hist, 'Signal m_{T}=1200 GeV', 'l')
legend.Draw()

latex = ROOT.TLatex()
latex.SetTextFont(42)
latex.SetTextSize(0.045)
latex.SetTextAlign(13)
latex.DrawLatexNDC(0.12, 0.97, 'e^{+}e^{-} collider')
latex.SetTextAlign(33)
latex.DrawLatexNDC(0.88, 0.97, '#it{#sqrt{s} = 3~TeV}')

for ext in ('png','pdf'):
    c.SaveAs(f'/home/higinio/Documentos/ASE/Paper/figs/recoil_baseline.{ext}')
