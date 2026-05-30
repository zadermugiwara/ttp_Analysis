import ROOT
from ROOT import TFile, TTree, gRandom
from array import array
import numpy as np
from lhereader import LHEReader

file = TFile("VLQ.root",'recreate')
tree = TTree("VLQ","VLQ")
reader = LHEReader('/home/higinio/Documentos/ASE/Madgraph/MG5_aMC_v3_4_1/VLQprueba1/Events/run_03/unweighted_events.lhe')
NMax = 0
for iev, event in enumerate(reader):
    if(np.size(event.particles)>NMax):
        NMax = np.size(event.particles)
numpart = array('i',[0])
noevent = array('d',NMax*[0.])
pdgid = array('d',NMax*[0.])
px = array('d',NMax*[0.])
py = array('d',NMax*[0.])
pz = array('d',NMax*[0.])
energy = array('d',NMax*[0.])
mass = array('d',NMax*[0.])
M1 = array('d',NMax*[0.])
D1 = array('d',NMax*[0.])

tree.Branch("numpart", numpart, 'numpart/I')
tree.Branch("noevent", noevent, 'noevent/D')
tree.Branch("pdgid", pdgid, 'pdgid/D')
tree.Branch("px", px, 'px/D')
tree.Branch("py", py, 'py/D')
tree.Branch("pz", pz, 'pz/D')
tree.Branch("energy", energy, 'energy/D')
tree.Branch("mass", mass, 'mass/D')
tree.Branch("M1", M1, 'M1/D')
tree.Branch("D1", D1, 'D1/D')


for iev, event in enumerate(reader):
    for i, x in enumerate(event.particles):
    
        noevent[i]=i
    
        pdgid[i] = event.particles[i].pdgid

        px[i] = event.particles[i].px 

        py[i] = event.particles[i].py 

        pz[i] = event.particles[i].pz
        
        

        M1[i] = event.particles[i].parent 

        #M2 = event.particles[i].M2 

        D1[i] = -1 

        #D2 = event.particles[i].D2 
        if(event.particles[i].parent>=0):
            D1[event.particles[i].parent]=i

        energy[i] = event.particles[i].energy  

        mass[i] = event.particles[i].mass
    
    numpart[0]=np.size(event.particles)
    
    tree.Fill()



tree.Write("", ROOT.TObject.kOverwrite);
file.Close()
