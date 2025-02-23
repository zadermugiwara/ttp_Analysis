#source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh
import ROOT
from ROOT import TFile, TTree, gRandom, TCanvas, TH1D, TH1F, TLegend
from array import array
import numpy as np
import math

from ROOT import gROOT
import sys

def mayor(max1200, max1600, max2000, max2400):
    if((max1200>max1600)and(max1200>max2000)and(max1200>max2400)):
        return 1
    if((max1600>max1200)and(max1600>max2000)and(max1600>max2400)):
        return 2
    if((max2000>max1600)and(max2000>max1200)and(max2000>max2400)):
        return 3
    if((max2400>max1600)and(max2400>max2000)and(max2400>max1200)):
        return 4


if(np.size(sys.argv) == 2):
    name = sys.argv[1]
    print("Let's read the arguments from command line")
    print(sys.argv[1])
else:
    name = 'Tt1M'
file = TFile(name + "output.root",'recreate')

nombres = ['deltaRjet',"deltaRlepton","m_recoil","mass","mass_post","mass_lead","Ht",
                            "fatjetHt","fatjet2Ht","fatjetpostHt",
                            "mass_post2","m_recoil2","fatjetpostHt2","pt_fatjetpost","pt_fatjetpost2",
                            "goodFJ","m_recoil0.5","m_recoil0","masstoplike","mrecoil toplikes","No_FJ",
                            "No_top_FJ","mrecoil_isolated_toplikes_rec_cut","m_recoilcut","topHt","m_recoil_isolated_toplikes",
                            "TPmass","topmass","topdecmass","truth_recoil","truth_deltaR_jet_TP","truth_deltaR_jet_top",
                            "truth_deltaR_jet_topdec","truth_deltaR_leptons_TP","truth_deltaR_leptons_top","truth_deltaR_leptons_topdec",
                            "truth_deltaR_fatjet_TP","truth_deltaR_fatjet_top","truth_deltaR_fatjet_topdec","good_deltaRjet",
                            "good_deltaRlepton","good_m_recoil","good_m_fatjet","good_pt_fatjet","good_E_fatjet",
                            "good_Ht_fatjet","bad_deltaRjet","bad_deltaRlepton","bad_m_recoil","bad_m_fatjet",
                            "bad_pt_fatjet","bad_E_fatjet","bad_Ht_fatjet"]
background = ['bkgsm1200','bkgsm1600','bkgsm2000','bkgsm2400','bkgsm2800','bkgsm3200','bkgsm3600','bkgsm4000','bkgsm4400']
backgroundnames = ['w+w-veve','ttveve','ttz','w+w-z','tth','W+W-','hveve','zz','hz']

Luminosity = 5*(10**18)

#f1200 = TFile("root/Tt1M1200.root")
#f1600 = TFile("root/Tt1M1600.root")
#f2000 = TFile("root/Tt1M2000.root")
#f2400 = TFile("root/Tt1M2400.root")
#TFile.Open("pyroot005_file_1.root", "recreate") as f
with TFile.Open("root/"+name+"1200.root", "read") as f1200:
    with TFile.Open("root/"+name+"1600.root", "read") as f1600:
        with TFile.Open("root/"+name+"2000.root", "read") as f2000:
            with TFile.Open("root/"+name+"2400.root", "read") as f2400:

                sign = [f1200, f1600, f2000, f2400]

                counter1 = 0

                for i in sign:
                    plot = TCanvas( 'm_recoil', 'm_recoil' , 1800,1200 )
                    example = TFile("root/ttbarra1200.root")
                    #plot.cd()
                        
                        
                        
                    bkg = gROOT.FindObject( 'mrecoil_isolated_toplikes_rec_cut' )
                    xs = gROOT.FindObject( 'Cross_Section' )
                    xsbinmax = xs.GetMaximumBin() 
                    crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                    print(crossSection)
                    num = gROOT.FindObject( 'no_sim' )
                    numbinmax = num.GetMaximumBin() 
                    numsim = num.GetXaxis().GetBinCenter(numbinmax)
                    bkg.Scale((Luminosity*crossSection*10**(-12))/numsim)
                    bkg.SetLineColor(1)
                    bkg.Rebin(10)
                    bkg.SetFillColor(1)
                    bkg.DrawCopy("HIST")
                    plot.Update()

                    m_recoil = i['mrecoil_isolated_toplikes_rec_cut']
                    xs = i['Cross_Section']
                    xsbinmax = xs.GetMaximumBin() 
                    crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                    num = i['no_sim']
                    numbinmax = num.GetMaximumBin() 
                    numsim = math.floor(num.GetXaxis().GetBinCenter(numbinmax))
                    print(numsim)
                    m_recoil.Scale((Luminosity*crossSection*10**(-12))/numsim)#sigma L / numero de simulaciones
                    m_recoil.Rebin(10)
                    m_recoil.SetFillColor(46)
                    plot.cd()
                    
                    counter2 = 0
                    counter1 += 1
                    leg = TLegend(.73,.32,.97,.53)
                    leg.AddEntry(m_recoil,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l")
                    leg.AddEntry(bkg,"tt","l")
                    leg.SetBorderSize(0)
                    leg.SetFillColor(0)
                    leg.SetTextFont(42)
                     


                    for y in background:
                        example = TFile("root/"+y+".root")
                        #plot.cd()
                        counter2 += 1
                        
                        
                        bkg = gROOT.FindObject( 'mrecoil_isolated_toplikes_rec_cut' )
                        xs = gROOT.FindObject( 'Cross_Section' )
                        xsbinmax = xs.GetMaximumBin() 
                        crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                        
                        num = gROOT.FindObject( 'no_sim' )
                        numbinmax = num.GetMaximumBin() 
                        numsim = math.floor(num.GetXaxis().GetBinCenter(numbinmax))
                        #print(numsim)
                        bkg.Scale((Luminosity*crossSection*10**(-12))/numsim)
                        bkg.SetLineColor(counter2+1)
                        bkg.Rebin(10)
                        bkg.SetFillColor(counter2+1)
                        bkg.DrawCopy("HIST SAME")
                        leg.AddEntry(bkg,backgroundnames[counter2-1],"f")
                        plot.Update()
                        
                    m_recoil.Draw("HIST SAME")
                    leg.Draw()
                    file.WriteObject(plot, "m_recoil "+str(counter1))

                for x in nombres:
                    c1 = TCanvas( x, x , 1800,1200 )
                    mass1200 = f1200[x]
                    mass1600 = f1600[x]
                    mass2000 = f2000[x]
                    mass2400 = f2400[x]

                    #print(mass1200.GetMaximum())
        

                    c1.cd()

                    mass1200.Scale(1.0/mass1200.Integral())#sigma L / numero de simulaciones
                    mass1200.SetLineColor(1)
                    
                    mass1600.Scale(1.0/mass1600.Integral())
                    mass1600.SetLineColor(2)
                    
                    mass2000.Scale(1.0/mass2000.Integral())
                    mass2000.SetLineColor(3)
                    
                    mass2400.Scale(1.0/mass2400.Integral())
                    mass2400.SetLineColor(4)

                    num = mayor(mass1200.GetMaximum(), mass1600.GetMaximum(), mass2000.GetMaximum(), mass2400.GetMaximum())

                    if(num == 1):
                        mass1200.Draw("HIST")
                        
                        mass1600.Draw("HIST SAME")
                        
                        mass2000.Draw("HIST SAME")
                        
                        mass2400.Draw("HIST SAME")

                    elif(num == 2):
                        mass1600.Draw("HIST")

                        mass1200.Draw("HIST SAME")

                        mass2000.Draw("HIST SAME")

                        mass2400.Draw("HIST SAME")

                    elif(num == 3):
                        mass2000.Draw("HIST")

                        mass1600.Draw("HIST SAME")

                        mass1200.Draw("HIST SAME")

                        mass2400.Draw("HIST SAME")

                    elif(num == 4):
                        mass2400.Draw("HIST")
                        
                        mass1600.Draw("HIST SAME")

                        mass1200.Draw("HIST SAME")

                        mass2000.Draw("HIST SAME")

                        


                    leg = TLegend(.73,.32,.97,.53)
                    leg.AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l")
                    leg.AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l")
                    leg.AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l")
                    leg.AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l")
                    leg.SetBorderSize(0)
                    leg.SetFillColor(0)
                    leg.SetTextFont(42)
                    leg.Draw()
    
                    file.WriteObject(c1, x)
                
                    
                    
                    



file.Close()