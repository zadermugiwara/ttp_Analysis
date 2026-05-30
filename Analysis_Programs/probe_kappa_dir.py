# list classes for the problematic keys
import ROOT, glob
keys = ["mrecoil toplikes","m_recoil","mrecoil_isolated_toplikes_rec_missE_cut",
        "Cross_Section","no_sim"]
for fn in glob.glob("root/*.root"):
    f=ROOT.TFile.Open(fn)
    print("==", fn)
    for k in keys:
        o=f.Get(k)
        print(f"  {k:40s} ->", (o.ClassName() if o else "MISSING"))
    f.Close()