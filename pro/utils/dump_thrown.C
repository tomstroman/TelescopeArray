#include "TROOT.h"
#include "TFile.h"
#include "TTree.h"
#include "TH1.h"
void dump_thrown(const char* infile) {
  TFile f(infile);
  TTree *rts = (TTree*)gROOT->FindObject("rts");
  TH1D *thrown_e = new TH1D("thrown_e", "thrown_e", 50, 16.5, 21.5);
  rts->Project("thrown_e", "e");
  int i, nbins;
  nbins = thrown_e->GetNbinsX();
  for (i=1; i<=nbins; i++) {
    printf("BIN %.2f %d\n", thrown_e->GetBinCenter(i), thrown_e->GetBinContent(i));
  }
  TH1D *thrown_x = new TH1D("thrown_x", "thrown_x", 60, 400, 1600);
  rts->Project("thrown_x", "xmax");
  nbins = thrown_x->GetNbinsX();
  for (i=1; i<=nbins; i++) {
    printf("BIN %.2f %d\n", thrown_x->GetBinCenter(i), thrown_x->GetBinContent(i));
  }
}
