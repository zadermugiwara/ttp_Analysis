import ROOT
from ROOT import TCanvas, TPad, TFile, TPaveLabel, TPaveText
from ROOT import gROOT

def plot():
    global f
    f = ROOT.TF1("f1", "sin(x)/x", 0., 10.)
    f.Draw()

plot()
file = TFile("prueba.root",'recreate')
File = "root/ttbarra1200.root"
 
background = ['ttbarra1200', 'bkgsm1200','bkgsm1600']

c1 = TCanvas( 'c1', 'Histogram Drawing Options', 200, 10, 700, 900 )
example = TFile("root/Tt1M1200.root")
#example.ls()
c1.cd()
hpx = gROOT.FindObject( 'm_recoil_isolated_toplikes' )
hpx.DrawCopy("HIST")
c1.Update()

if (ROOT.gSystem.AccessPathName(File)) :
    ROOT.Info("import ROOT.py", File+" does not exist")
    exit()
for y in background:
    example = TFile("root/"+y+".root")
    #example.ls()
    c1.cd()
    hpx = gROOT.FindObject( 'm_recoil_isolated_toplikes' )
    hpx.DrawCopy("HIST SAME")
    c1.Update()
file.WriteObject(c1,'xd')
file.Close