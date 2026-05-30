//───────────────────────────────────────────────────────────────
// export_canvases_to_pdf8.C
// Put 8 stored TCanvas objects per PDF page (4×2 grid)
//───────────────────────────────────────────────────────────────
#include <TFile.h>
#include <TKey.h>
#include <TClass.h>
#include <TCanvas.h>
#include <TROOT.h>
#include <TDirectory.h>
#include <vector>
#include <iostream>

namespace {

//-----------------------------------------------------------------
/// Recursively collect every TCanvas* inside a TDirectory
void gather_canvases(TDirectory* dir, std::vector<TCanvas*>& out)
{
   TIter next(dir->GetListOfKeys());
   TKey* key = nullptr;

   while ((key = static_cast<TKey*>(next()))) {
      TClass* cl = gROOT->GetClass(key->GetClassName());

      if (cl && cl->InheritsFrom("TCanvas")) {
         TCanvas* c = static_cast<TCanvas*>(key->ReadObj());
         // Store a *clone* so we don’t alter the original object
         out.push_back(static_cast<TCanvas*>(c->Clone()));
      }
      else if (cl && cl->InheritsFrom("TDirectory")) {
         gather_canvases(static_cast<TDirectory*>(key->ReadObj()), out);
      }
   }
}

//-----------------------------------------------------------------
/// Dump up to nCanv canvases on a multipage-PDF page
void write_page(std::vector<TCanvas*>& buf,
                int cols, int rows,
                const char* pdf, bool& firstPage)
{
   if (buf.empty()) return;

   TCanvas page("page","page", 2400, 2400);
   page.Divide(cols, rows, 0.001, 0.001);

   for (std::size_t i=0;i<buf.size();++i) {
      page.cd(i+1);
      buf[i]->DrawClonePad();
   }

   if (!firstPage) {                        // open multipage file
      page.Print(Form("%s[", pdf));
      firstPage = true;
   }
   page.Print(pdf);                         // append current page

   /* tidy-up memory */
   for (auto* c : buf) delete c;
   buf.clear();
}

} // unnamed namespace
//-----------------------------------------------------------------

void export_canvases_to_pdf(const char* inFile  = "Tt1Moutput.root",
                             const char* outPDF  = "canvases+80.pdf",
                             int cols = 4, int rows = 5)
{
   TFile file(inFile,"READ");
   if (file.IsZombie()) {
      std::cerr << "Cannot open " << inFile << '\n';
      return;
   }

   std::vector<TCanvas*> canv;
   gather_canvases(&file, canv);

   const int perPage = cols*rows;
   std::vector<TCanvas*> buffer; buffer.reserve(perPage);
   bool firstPage = false;

   for (auto* c : canv) {
      buffer.push_back(c);
      if ((int)buffer.size() == perPage) write_page(buffer,cols,rows,outPDF,firstPage);
   }
   /* last partial page */
   write_page(buffer,cols,rows,outPDF,firstPage);

   if (firstPage) {                   // close the PDF
      TCanvas tmp("tmp","tmp");
      tmp.Print(Form("%s]", outPDF));
      std::cout << "Canvases exported to " << outPDF << '\n';
   } else {
      std::cout << "No TCanvas objects found in " << inFile << '\n';
   }
}

