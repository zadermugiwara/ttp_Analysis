#source /home/higinio/Documentos/ASE/Analysis/root/root/bin/thisroot.sh
import ROOT
from ROOT import TFile, TTree, gRandom, TCanvas, TH1D, TH1F, TLegend, THStack, TLatex, TH2F, TGraph, gStyle
from array import array
import numpy as np
import math

from ROOT import gROOT
import sys

gStyle.SetOptStat(0)

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
    #name = sys.argv[1]
    print("Let's read the arguments from command line")
    print(sys.argv[1])
#else:
    #name = 'Tt1M'
#file = TFile(name + "output.root",'recreate')

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
                            "bad_pt_fatjet","bad_E_fatjet","bad_Ht_fatjet",'Miss_Energy','mrecoil_isolated_toplikes_rec_missE_cut']
#background = ['w+w-veve','ttveve','ttz','w+w-z','tth']
background = [  'ttz', 'w+w-z', 'tth']
backgroundnames = ['ttz','w+w-z','tth','tt','Tt * 10']
names = ['Tt m_{T}=1200','Tt m_{T}=1600','Tt m_{T}=2000','10 x Tt m_{T}=2400']
bkgcompare = ['mrecoil_isolated_toplikes_rec_cut', 'Miss_Energy','No_FJ', 'No_top_FJ','Ht', 'fatjetpostHt', 'mrecoil_isolated_toplikes_rec_missE_cut', 'mrecoil_BDT1200_cut', 'mrecoil_BDT_ttbar', 'mrecoil_BDT2400_cut']
bkgstack = ['mrecoil_isolated_toplikes_rec_cut', 'mrecoil_isolated_toplikes_rec_missE_cut', 'mrecoil_BDT1200_cut', 'mrecoil_BDT_ttbar', 'mrecoil_BDT1600_cut','mrecoil_BDT2000_cut','mrecoil_BDT2400_cut']
bkgstackcolor = [610, 880, 800, 400, 590]
histo2D = ['EFJvsmrecoil', 'm_FJvspt_FJ', 'EFJvsmass', 'EFJvspt', 'massvspt', 'mrecoilvspt', 'EvsHt', 'ptvsHt', 'mrecoilvsHt', 'ptfatvsHt', 'truth_deltaR_fatjet_top_vs_deltaR_fatjet_topdec','METvsmrecoil']


Luminosity = 5*(10**18)
kappa = ['Tt1M']
#kappa = ['Tt100kkappa01']
#kappa = ['Tt100kkappa03']
#f1200 = TFile("root/Tt1M1200.root")
#f1600 = TFile("root/Tt1M1600.root")
#f2000 = TFile("root/Tt1M2000.root")
#f2400 = TFile("root/Tt1M2400.root")
#TFile.Open("pyroot005_file_1.root", "recreate") as f
for name in kappa:
    file = TFile(name + "output.root",'recreate')
    with TFile.Open("root/"+name+"1200.root", "read") as f1200:
        with TFile.Open("root/"+name+"1600.root", "read") as f1600:
            with TFile.Open("root/"+name+"2000.root", "read") as f2000:
                with TFile.Open("root/"+name+"2400.root", "read") as f2400:

                    sign = [f1200, f1600, f2000, f2400]
                    #sign = [f1200, f1600, f2000]
                    scaling = [1,1,1,10]

                    for w in bkgstack:
                        counter1 = 0
                        for i in sign:
                            plot = TCanvas( 'm_recoil', 'm_recoil' , 1800,1200 )
                            canva = TCanvas( 'stack', 'stack' , 1800,1200 )
                            example = TFile("root/ttbarra.root")
                            plot.cd()
                                
                            stack = THStack(w + 'stack',"")
                                
                            bkg1 = gROOT.FindObject( w )
                            xs = gROOT.FindObject( 'Cross_Section' )
                            xsbinmax = xs.GetMaximumBin() 
                            crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                            print(crossSection)
                            num = gROOT.FindObject( 'no_sim' )
                            numbinmax = num.GetMaximumBin() 
                            numsim = num.GetXaxis().GetBinCenter(numbinmax)
                            bkg1.GetXaxis().SetTitle("Recoil mass [GeV]")
                            bkg1.GetYaxis().SetTitle("Number of Events")
                            bkg1.Scale((Luminosity*crossSection*10**(-12))/numsim)
                            bkg1.SetLineColor(1)
                            bkg1.Rebin(40)
                            bkg1.SetFillColor(0)
                            bkg1.SetDirectory(0)
                            bkg1.SetStats(0)
                            bkg1.DrawCopy("HIST")
                            
                            #plot.Update()

                            m_recoil = i[w]
                            xs = i['Cross_Section']
                            xsbinmax = xs.GetMaximumBin() 
                            crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                            num = i['no_sim']
                            numbinmax = num.GetMaximumBin() 
                            numsim = math.floor(num.GetXaxis().GetBinCenter(numbinmax))
                            print(numsim)
                            m_recoil.Scale((scaling[counter1]*Luminosity*crossSection*10**(-12))/numsim)#sigma L / numero de simulaciones
                            m_recoil.GetYaxis().SetTitle("Number of Events")
                            m_recoil.Rebin(40)
                            m_recoil.SetFillColor(counter1 + 1)
                            m_recoil.SetLineColor(counter1 + 1)
                            m_recoil.SetDirectory(0)
                            #plot.cd()
                            
                            counter2 = 0
                            counter1 += 1
                            leg = TLegend(.73,.32,.97,.53)
                            #leg.AddEntry(bkg1,"tt","l")
                            #leg.AddEntry(m_recoil,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l")
                            
                            

                            bkg = []
                            


                            for y in background:
                                example = TFile("root/"+y+".root")
                                #plot.cd()
                                counter2 += 1
                                
                                
                                bkg.append(gROOT.FindObject( w ))
                                xs = gROOT.FindObject( 'Cross_Section' )
                                xsbinmax = xs.GetMaximumBin() 
                                crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                                
                                num = gROOT.FindObject( 'no_sim' )
                                numbinmax = num.GetMaximumBin() 
                                numsim = math.floor(num.GetXaxis().GetBinCenter(numbinmax))
                                #print(numsim)
                                #####################################
                                #
                                ####################################
                                bkg[counter2-1].GetYaxis().SetTitle("Number of Events")
                                bkg[counter2-1].Scale((Luminosity*crossSection*10**(-12))/numsim)
                                bkg[counter2-1].SetLineColor(bkgstackcolor[counter2-1])
                                bkg[counter2-1].Rebin(40)
                                bkg[counter2-1].SetFillColor(bkgstackcolor[counter2-1])
                                bkg[counter2-1].SetDirectory(0)
                                bkg[counter2-1].DrawCopy("HIST SAME")
                                stack.Add(bkg[counter2-1])
                                
                                #leg.AddEntry(bkg[counter2-1],backgroundnames[counter2-1],"l")
                                #leg.Draw()
                                #plot.Update()
                                #bkg[counter2-1].SetFillColor(1)
                                #bkg[counter2-1].SetLineColor(1)
                                
                                
                                
                            m_recoil.Draw("HIST SAME")
                            
                            bkg.append(bkg1)
                            bkg.append(m_recoil)
                            
                            cont = 0
                            for help in bkg:
                                if(help.GetEntries() == 0):
                                    cont += 1
                                    continue
                                if(cont == 6):
                                    leg.AddEntry(help,names[counter1-1],"f")
                                    continue
                                leg.AddEntry(help,backgroundnames[cont],"f")
                                cont += 1
                            leg.SetBorderSize(0)
                            leg.SetFillColor(0)
                            leg.SetTextFont(42)
                            leg.Draw()
                            file.WriteObject(plot, w + str(counter1) + 'Cross Section')
                            #for y in background:
                                #bkg[counter2-1].SetFillColor(1)
                                
                            stack.Add(bkg1)
                            stack.Add(m_recoil)
                            canva.cd()
                            sizex = math.ceil(bkg1.GetXaxis().GetBinCenter(bkg1.GetNbinsX()))
                            sizey = stack.GetMaximum()
                            
                            stack.Draw('HIST')
                            stack.GetXaxis().SetTitle("Recoil mass [GeV]")
                            stack.GetYaxis().SetTitle("Number of Events")
                            leg.Draw()
                            c = ROOT.TLatex()
                            c.SetTextFont(42)
                            c.SetTextSize(0.05)
                            c.DrawLatex(sizex*0.01, sizey*1.06,"e^{+}e^{-} collider")
                            e = ROOT.TLatex()
                            e.SetTextFont(42)
                            e.SetTextSize(0.05)
                            e.DrawLatex(sizex*0.8, sizey*1.06,"#sqrt{s} = 3 TeV")
                            
                            canva.Update()
                            
                            file.WriteObject(canva,'stack' + w + str(counter1) + 'Cross Section')

    with TFile.Open("root/"+name+"1200.root", "read") as f1200:
        with TFile.Open("root/"+name+"1600.root", "read") as f1600:
            with TFile.Open("root/"+name+"2000.root", "read") as f2000:
                with TFile.Open("root/"+name+"2400.root", "read") as f2400:

                    sign = [f1200, f1600, f2000, f2400]
                    #sign = [f1200, f1600, f2000]

                    for f in bkgcompare:

                        for i in sign:
                            plot = TCanvas( 'm_recoil', 'm_recoil' , 1800,1200 )
                            example = TFile("root/ttbarra.root")
                            plot.cd()
                                
                                
                                
                            bkg1 = gROOT.FindObject( f )
                            
                            bkg1.Scale(1/bkg1.Integral())
                            bkg1.SetLineColor(1)
                            #bkg1.GetXaxis().SetTitle("Missing Energy [GeV]")
                            bkg1.GetYaxis().SetTitle("Arbitrary Units")
                            bkg1.Rebin(20)
                            #bkg1.SetFillColor(1)
                            bkg1.SetDirectory(0)
                            bkg1.SetStats(0)
                            bkg1.DrawCopy("HIST")
                            #plot.Update()

                            m_recoil = i[f]
                            
                            print(numsim)
                            m_recoil.Scale(1/m_recoil.Integral())#sigma L / numero de simulaciones
                            m_recoil.Rebin(20)
                            m_recoil.GetYaxis().SetTitle("Arbitrary Units")
                            m_recoil.SetFillColor(0)
                            m_recoil.SetLineColor(46)
                            m_recoil.SetDirectory(0)
                            #plot.cd()
                            
                            counter2 = 0
                            counter1 += 1
                            leg = TLegend(.73,.32,.97,.53)
                            #leg.AddEntry(bkg1,"tt","l")
                            #leg.AddEntry(m_recoil,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l")
                            
                            

                            bkg = []
                            


                            for y in background:
                                example = TFile("root/"+y+".root")
                                #plot.cd()
                                counter2 += 1
                                
                                
                                bkg.append(gROOT.FindObject( f ))
                                
                                
                                num = gROOT.FindObject( 'no_sim' )
                                numbinmax = num.GetMaximumBin() 
                                numsim = math.floor(num.GetXaxis().GetBinCenter(numbinmax))
                                #print(numsim)
                                #if (bkg[counter2-1].Integral() == 0):
                                #   continue
                                #bkg[counter2-1].Scale(1/bkg[counter2-1].Integral())
                                bkg[counter2-1].SetLineColor(bkgstackcolor[counter2-1])
                                bkg[counter2-1].Rebin(20)
                                #bkg[counter2-1].SetFillColor(counter2+1)
                                bkg[counter2-1].SetDirectory(0)
                                bkg[counter2-1].DrawCopy("HIST SAME")
                                #leg.AddEntry(bkg[counter2-1],backgroundnames[counter2-1],"l")
                                leg.Draw()
                                #plot.Update()
                                
                            m_recoil.Draw("HIST SAME")
                            bkg.append(bkg1)
                            bkg.append(m_recoil)
                            cont = 0
                            for help in bkg:
                                
                                leg.AddEntry(help,backgroundnames[cont],"l")
                                cont += 1
                            leg.SetBorderSize(0)
                            leg.SetFillColor(0)
                            leg.SetTextFont(42)
                            leg.Draw()
                            sizex = math.ceil(bkg1.GetXaxis().GetBinCenter(bkg1.GetNbinsX()))
                            sizey = bkg1.GetMaximum()
                            c = ROOT.TLatex()
                            c.SetTextFont(42)
                            c.SetTextSize(0.05)
                            c.DrawLatex(sizex*0.01, sizey*1.06,"e^{+}e^{-} collider")
                            e = ROOT.TLatex()
                            e.SetTextFont(42)
                            e.SetTextSize(0.05)
                            e.DrawLatex(sizex*0.8, sizey*1.06,"#sqrt{s} = 3 TeV")
                            file.WriteObject(plot, "m_recoil "+f+str(counter1)+'Integral')

    with TFile.Open("root/"+name+"1200.root", "read") as f1200:
        with TFile.Open("root/"+name+"1600.root", "read") as f1600:
            with TFile.Open("root/"+name+"2000.root", "read") as f2000:
                with TFile.Open("root/"+name+"2400.root", "read") as f2400:

                    sign = [f1200, f1600, f2000, f2400]
                    #sign = [f1200, f1600, f2000]

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
                        mass1200.SetStats(0)
                        mass1200.GetXaxis().SetTitle("recoil mass [GeV]")
                        mass1200.GetYaxis().SetTitle("Arbitrary Units")
                        
                        mass1200.Rebin(20)
                        mass1600.Rebin(20)
                        mass2000.Rebin(20)
                        mass2400.Rebin(20)
                        
                        mass1600.Scale(1.0/mass1600.Integral())
                        mass1600.SetLineColor(2)
                        mass1600.SetStats(0)
                        mass1600.GetXaxis().SetTitle("recoil mass [GeV]")
                        mass1600.GetYaxis().SetTitle("Arbitrary Units")
                        
                        
                        mass2000.Scale(1.0/mass2000.Integral())
                        mass2000.SetLineColor(3)
                        mass2000.SetStats(0)
                        mass2000.GetXaxis().SetTitle("recoil mass [GeV]")
                        mass2000.GetYaxis().SetTitle("Arbitrary Units")
                        
                        
                        mass2400.Scale(1.0/mass2400.Integral())
                        mass2400.SetLineColor(4)
                        mass2400.SetStats(0)
                        mass2400.GetXaxis().SetTitle("recoil mass [GeV]")
                        mass2400.GetYaxis().SetTitle("Arbitrary Units")
                        

                        num = mayor(mass1200.GetMaximum(), mass1600.GetMaximum(), mass2000.GetMaximum(), mass2400.GetMaximum())
                        #num = 1

                        if(num == 1):
                            
                            mass1200.Draw("HIST")
                            
                            mass1600.Draw("HIST SAME")
                            
                            mass2000.Draw("HIST SAME")
                            
                            mass2400.Draw("HIST SAME")
                            sizey = mass1200.GetMaximum()

                        elif(num == 2):
                            mass1600.Draw("HIST")

                            mass1200.Draw("HIST SAME")

                            mass2000.Draw("HIST SAME")

                            mass2400.Draw("HIST SAME")
                            sizey = mass1600.GetMaximum()

                        elif(num == 3):
                            mass2000.Draw("HIST")

                            mass1600.Draw("HIST SAME")

                            mass1200.Draw("HIST SAME")

                            mass2400.Draw("HIST SAME")
                            sizey = mass2000.GetMaximum()

                        elif(num == 4):
                            mass2400.Draw("HIST")
                            
                            mass1600.Draw("HIST SAME")

                            mass1200.Draw("HIST SAME")

                            mass2000.Draw("HIST SAME")
                            sizey = mass2400.GetMaximum()

                            


                        leg = TLegend(.73,.32,.97,.53)
                        leg.AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=22.3178 GeV","l")
                        leg.AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=53.271 GeV","l")
                        leg.AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=104.38 GeV","l")
                        leg.AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=180.682 GeV","l")
                        leg.SetBorderSize(0)
                        leg.SetFillColor(0)
                        leg.SetTextFont(42)
                        leg.Draw()
                        sizex = math.ceil(mass1200.GetXaxis().GetBinCenter(mass1200.GetNbinsX()))
                        
                    
                        c = ROOT.TLatex()
                        c.SetTextFont(42)
                        c.SetTextSize(0.05)
                        c.DrawLatex(sizex*0.01, sizey*1.06,"e^{+}e^{-} collider")
                        e = ROOT.TLatex()
                        e.SetTextFont(42)
                        e.SetTextSize(0.05)
                        e.DrawLatex(sizex*0.8, sizey*1.06,"#sqrt{s} = 3 TeV")
        
                        file.WriteObject(c1, x)
                    background = ['w+w-veve','ttveve','ttz','w+w-z','tth','ttbarra']
                    señal = ['Tt m_{T} = 1200','Tt m_{T} = 1600','Tt m_{T} = 2000','Tt m_{T} = 2400']

                    for x in histo2D:
                        counter = 0
                        for i in sign:
                            c1 = TCanvas( x, x , 1800,1200 )
                            mass1200 = i[x]
                            

                            c1.cd()

                        

                        
                            sizex = math.ceil(mass1200.GetXaxis().GetBinCenter(mass1200.GetNbinsX()))
                            sizey = math.ceil(mass1200.GetYaxis().GetBinCenter(mass1200.GetNbinsY()))
                            mass1200.RebinX(100)
                            #mass1200.SetStats(0)
                            #mass1200.GetXaxis().SetTitle("Missin Energy [GeV]")
            
                            #mass1200.GetYaxis().SetTitle("recoil mass [GeV]")
                            
                            if(mass1200.GetNbinsY()<1000):
                                mass1200.RebinY(2)
                            else:
                                mass1200.RebinY(100)
                            mass1200.SetDirectory(0)
                            mass1200.Draw("COLZ")
                            c = ROOT.TLatex()
                            c.SetTextFont(42)
                            c.SetTextSize(0.05)
                            c.DrawLatex(sizex*0.01, sizey*1.01,"e^{+}e^{-} collider")
                            e = ROOT.TLatex()
                            e.SetTextFont(42)
                            e.SetTextSize(0.05)
                            e.DrawLatex(sizex*0.8, sizey*1.01,"#sqrt{s} = 3 TeV")
                            d = ROOT.TLatex()
                            d.SetTextFont(42)
                            d.SetTextSize(0.05)
                            d.DrawLatex(sizex*0.4, sizey*1.05,señal[counter])
                            counter += 1
                                
                            file.WriteObject(c1,x)
                            
                            

                            #print('sizex: ' + str(sizex) + ' \n sizey: '+str(sizey))
                            
                        for y in background:
                            with TFile.Open("root/"+y+".root", "read") as i:
                                plot = TCanvas( 'm_recoil', 'm_recoil' , 1800,1200 )
                                mass1200 = i[x]
                                plot.cd()
            
                                sizex = math.ceil(mass1200.GetXaxis().GetBinCenter(mass1200.GetNbinsX()))
                                sizey = math.ceil(mass1200.GetYaxis().GetBinCenter(mass1200.GetNbinsY()))
                                mass1200.RebinX(100)
                                #mass1200.SetStats(0)
                                #mass1200.GetXaxis().SetTitle("Missin Energy [GeV]")
            
                                #mass1200.GetYaxis().SetTitle("recoil mass [GeV]")

                                if(mass1200.GetNbinsY()<1000):
                                    mass1200.RebinY(2)
                                else:
                                    mass1200.RebinY(100)
                                plot.cd()
            
                                mass1200.SetDirectory(0)
                                mass1200.Draw("COLZ")
                                c = ROOT.TLatex()
                                c.SetTextFont(42)
                                c.SetTextSize(0.05)
                                c.DrawLatex(sizex*0.01, sizey*1.01,"e^{+}e^{-} collider")
                                e = ROOT.TLatex()
                                e.SetTextFont(42)
                                e.SetTextSize(0.05)
                                e.DrawLatex(sizex*0.8, sizey*1.01,"#sqrt{s} = 3 TeV")
                                d = ROOT.TLatex()
                                d.SetTextFont(42)
                                d.SetTextSize(0.05)
                                d.DrawLatex(sizex*0.4, sizey*1.05,y)
                                
                                file.WriteObject(plot,x+' '+y)
                                plot.Update()
                                example = TFile("root/"+y+".root")
                        
                                #hpxpy  = TH2F( 'hpxpy', 'py vs px', 40, -4, 4, 40, -4, 4 )
                                #c2 = TCanvas( x, x , 1800,1200 )
                           #     histos2D = gROOT.FindObject( x )
                                #hpxpy = (mass1200)
                                #hpxpy.RebinX(10)
                                #mass1200.GetNbinsX()

                                #c2.cd()
                    

                    
                                #sizex = math.ceil(mass1200.GetXaxis().GetBinCenter(mass1200.GetNbinsX()))
                                #sizey = math.ceil(mass1200.GetYaxis().GetBinCenter(mass1200.GetNbinsY()))
                        
                                 #if(mass1200.GetNbinsY()<1000):
                                #   mass1200.RebinY(2)
                                #else:
                                #  mass1200.RebinY(10)

                                #print('sizex: ' + str(sizex) + ' \n sizey: '+str(sizey))
                    
                                #histos2D.cd()
                                #histos2D.SetDirectory(0)
                                #c = ROOT.TLatex()
                                #c.SetTextFont(42)
                                #c.SetTextSize(0.05)
                                #c.DrawLatex(sizex*0.01, sizey*1.01,"e^{+}e^{-} collider")
                                #e = ROOT.TLatex()
                                #e.SetTextFont(42)
                                #e.SetTextSize(0.05)
                                #e.DrawLatex(sizex*0.8, sizey*1.01,"#sqrt{s} = 3 TeV")
                                #counter += 1
                                #file.WriteObject(histos2D, x + y )

                        #c1 = TCanvas( x, x , 1800,1200 )
                        #c1.cd()
                        #mass1200.Draw("COLZ")
                        #c = ROOT.TLatex()
                        #c.SetTextFont(42)
                        #c.SetTextSize(0.05)
                        #c.DrawLatex(sizex*0.01, sizey*1.01,"e^{+}e^{-} collider")
                        #e = ROOT.TLatex()
                        #e.SetTextFont(42)
                        #e.SetTextSize(0.05)
                        #e.DrawLatex(sizex*0.8, sizey*1.01,"#sqrt{s} = 3 TeV")
                        #counter += 1
                        #file.WriteObject(c1, x + str(counter))

                    bkgweighted = 0
                    

                    for y in background:
                        example = TFile("root/"+y+".root")
                        bkg1 = gROOT.FindObject( 'mrecoil_isolated_toplikes_rec_missE_cut' )
                        xs = gROOT.FindObject( 'Cross_Section' )
                        xsbinmax = xs.GetMaximumBin() 
                        crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                        print(crossSection)
                        num = gROOT.FindObject( 'no_sim' )
                        numbinmax = num.GetMaximumBin() 
                        numsim = num.GetXaxis().GetBinCenter(numbinmax)    
                        scale = (Luminosity*crossSection*10**(-12))/numsim
                        bkgweighted +=  bkg1.GetEntries()*scale

                    Tmasssig = array( 'd' )
                    Tmasszexcl = array( 'd' )
                    Tmasszdisc = array( 'd' )
                    Tmass = array( 'd' )
                    Tmass.append(1200)
                    Tmass.append(1600)
                    Tmass.append(2000)
                    Tmass.append(2400)
                    
                    c = TCanvas( 'Lumvssig', 'Lumvssig' , 1800,1200 )
                    drawption = ["ACP*","CP*","CP*","CP*"]
                    contador = 0
                    graph = []
                    for i in sign:
                        signal = i['mrecoil_isolated_toplikes_rec_missE_cut']
                        xs = i['Cross_Section']
                        xsbinmax = xs.GetMaximumBin() 
                        crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                        print(crossSection)
                        num = i['no_sim']
                        numbinmax = num.GetMaximumBin() 
                        numsim = num.GetXaxis().GetBinCenter(numbinmax)    
                        scale = (Luminosity*crossSection*10**(-12))/numsim
                        
                    
                        print(signal.GetEntries())
                        signal1 =  signal.GetEntries()*scale
                        print(signal1)
                        sig_est = signal1/((signal1 + bkgweighted)**(1/2))
                        zdisc = (2*((signal1 + bkgweighted)*math.log(1+(signal1/bkgweighted))-signal1))**(1/2)
                        zexcl = (2*(signal1 - bkgweighted*math.log(1+(signal1/bkgweighted))))**(1/2)
                        Tmasssig.append(sig_est)
                        Tmasszexcl.append(zexcl)
                        Tmasszdisc.append(zdisc)
                        print (sig_est)
                        print (zexcl)
                        print (zdisc)
                        
                        
                        
                        Lumsig  = array( 'd' )
                        Lumi = array( 'd' )
                        for f in range(0,100,1):
                            scale = (0.1*f*Luminosity*crossSection*10**(-12))/numsim
                            signal1 =  signal.GetEntries()*scale
                            sig_estlum = signal1/((signal1 + bkgweighted)**(1/2))
                            Lum = (0.1*f*Luminosity)/(10**18)
                            Lumi.append(Lum)
                            Lumsig.append(sig_estlum)
                            
                        c.cd()
                        c.SetGrid()
                        #print(Lumi)
                        graph.append(TGraph(50, Lumi, Lumsig))
                        
                        graph[contador].SetLineColor(contador + 1 )
                        
                        graph[contador].SetMarkerColor( contador + 1 )
                        graph[contador].GetXaxis().SetTitle( 'Luminosidad [ab^{-1} ]' )
                        graph[contador].GetYaxis().SetTitle( 'Significancia estadistica' )
                        graph[contador].SetTitle( 'Luminosidad vs Significancia estadistica' )
                        graph[contador].Draw(drawption[contador])
                        leg = TLegend(.73,.32,.97,.53)
                        #leg.AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=5.5796 GeV","l")
                        #leg.AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=13.3178 GeV","l")
                        #leg.AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=26.095 GeV","l")
                        #leg.AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=45.171 GeV","l")
                        leg.AddEntry(mass1200,"m_{T}=1200 GeV, #Gamma_{T}=50.215 GeV","l")
                        leg.AddEntry(mass1600,"m_{T}=1600 GeV, #Gamma_{T}=119.859 GeV","l")
                        leg.AddEntry(mass2000,"m_{T}=2000 GeV, #Gamma_{T}=234.856 GeV","l")
                        leg.AddEntry(mass2400,"m_{T}=2400 GeV, #Gamma_{T}=406.53 GeV","l")
                        leg.SetBorderSize(0)
                        leg.SetFillColor(0)
                        leg.SetTextFont(42)
                        leg.Draw()
                        contador += 1

                        
                    #pic = TGraph(len(Tmass),Tmass, Tmasssig)
                    file.WriteObject(c, 'Lumvssig')
                    n = 4
                    pic = TGraph( n, Tmass, Tmasssig )


                    c1 = TCanvas( 'Tmassvssig', 'Tmassvssig' , 1800,1200 )
                    c1.cd()
                    c1.SetGrid()
                    pic.GetXaxis().SetTitle( 'Masa T' )
                    pic.GetYaxis().SetTitle( 'Significancia estadistica' )
                    pic.SetTitle( 'Masa vs Significancia estadistica' )
                    pic.Draw("ACP*")
                    file.WriteObject(c1, 'Tmassvssig')

                    pic2 = TGraph( n, Tmass, Tmasszexcl )
                    c2 = TCanvas( 'Tmassvszexcl', 'Tmassvszexcl' , 1800,1200 )
                    c2.cd()
                    c2.SetGrid()
                    pic2.GetXaxis().SetTitle( 'Masa T' )
                    pic2.GetYaxis().SetTitle( 'Z excl' )
                    pic2.SetTitle( 'Masa vs Z excl' )
                    pic2.Draw("ACP*")
                    file.WriteObject(c2, 'Tmassvszexcl')

                    pic3 = TGraph( n, Tmass, Tmasszdisc )
                    c3 = TCanvas( 'Tmassvszdisc', 'Tmassvszdisc' , 1800,1200 )
                    c3.cd()
                    c3.SetGrid()
                    pic3.GetXaxis().SetTitle( 'Masa T' )
                    pic3.GetYaxis().SetTitle( 'Z disc' )
                    pic3.SetTitle( 'Masa vs Z disc' )
                    pic3.Draw("ACP*")
                    file.WriteObject(c3, 'Tmassvszdisc')


    with TFile.Open("root/"+name+"1200.root", "read") as f1200:
        with TFile.Open("root/"+name+"1600.root", "read") as f1600:
            with TFile.Open("root/"+name+"2000.root", "read") as f2000:
                with TFile.Open("root/"+name+"2400.root", "read") as f2400:

                    sign = [f1200, f1600, f2000, f2400]   
                    stack = THStack( 'stack',"")
                    for y in background:
                        example = TFile("root/"+y+".root")
                        bkg1 = gROOT.FindObject( 'mrecoil_isolated_toplikes_rec_missE_cut' )
                        xs = gROOT.FindObject( 'Cross_Section' )
                        xsbinmax = xs.GetMaximumBin() 
                        crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                        #print(crossSection)
                        num = gROOT.FindObject( 'no_sim' )
                        numbinmax = num.GetMaximumBin() 
                        numsim = num.GetXaxis().GetBinCenter(numbinmax)    
                        scale = (Luminosity*crossSection*10**(-12))/numsim
                        bkg1.Scale(scale)
                        print(y + '     '+str(scale*bkg1.GetEntries()))
                        bkg1.Rebin(40)    
                        c1 = TCanvas( 'Tmassvssig', 'Tmassvssig' , 1800,1200 )
                        c1.cd()
                        bkg1.Draw("HIST")
                        bkg1.SetDirectory(0)
                        stack.Add(bkg1)
                        file.WriteObject(c1, y + 'mrecoil_isolated_toplikes_rec_missE_cut')    
                    c2 = TCanvas( 'stack', 'stack' , 1800,1200 )
                    c2.cd()
                    stack.Draw('HIST')
                    file.WriteObject(stack, 'stackmrecoil_isolated_toplikes_rec_missE_cut')
                    for i in sign:
                        signal = i['mrecoil_isolated_toplikes_rec_missE_cut']
                        xs = i['Cross_Section']
                        xsbinmax = xs.GetMaximumBin() 
                        crossSection = xs.GetXaxis().GetBinCenter(xsbinmax)
                        #print(crossSection)
                        num = i['no_sim']
                        numbinmax = num.GetMaximumBin() 
                        numsim = num.GetXaxis().GetBinCenter(numbinmax)    
                        scale = (Luminosity*crossSection*10**(-12))/numsim
                        signal.Scale(scale)
                        print('     '+str(scale*signal.GetEntries()))
                        signal.Rebin(20)
                        c2 = TCanvas( 'Tmassvssig', 'Tmassvssig' , 1800,1200 )  
                        c2.cd()
                        signal.Draw("HIST")
                        file.WriteObject(c2, 'Tt' + 'mrecoil_isolated_toplikes_rec_missE_cut')         

                        
                        
                        
                
                    
                    
                    



    file.Close()
    
