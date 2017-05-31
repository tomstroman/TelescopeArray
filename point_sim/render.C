/* render.C
 * Thomas Stroman, University of Utah 2017-05-26
 * ROOT script:
 * Create an image from the positions listed in the output from $TRUMP/bin/localpoint.run
 * showing the expected pattern of illumination on a screen affixed to the outside of a
 * Telescope Array camera.
 */

#include "TROOT.h"
#include "TCanvas.h"
#include "TGraph.h"
#include "TTree.h"
#include "TH2.h"
#include "TAxis.h"
#include "TStyle.h"

// Constants
#define PMTGAP 0.002
#define PMTPTP 0.0693
#define PMTFTF 0.06
#define COS30 0.866025403784438708

// global
double pmtX[256], pmtY[256];
int coords_defined = 0;
void fillPmtCoords(double *x, double *y) {
  if (coords_defined)
    return;
  
  int i, row, col;
  for (i=0; i<256; i++) {
    col = (i - (i % 16) )/ 16;
    row = i % 16;
    
    x[i] = -(PMTFTF + PMTGAP) * ((double)col - 7.75 + 0.5*(double)(row % 2));
    y[i] = (PMTPTP + PMTGAP/COS30)*0.75 * (7.5 - (double)row);
  }
  coords_defined = 1;
}

TH2F *sqmmHeatMap() {
  TH2F *map = new TH2F("map", "map;-x (m);y (m)", 1160, -0.580, 0.580, 1010, -0.505, 0.505);
  return map;
}

TCanvas *camFaceCanvas(TH2F *map = NULL, int drawPMTs = 1) {
  char canvname[64] = "camface";
  TCanvas *camface = (TCanvas*)gROOT->FindObject(canvname);
  if (!camface) {
    camface = new TCanvas(canvname, "cam", 580 + 4, 505 + 28);
  }
  
  if (!map) {
    map = sqmmHeatMap();
  }
  
  
  TGraph *box=  new TGraph(5);

  Double_t wbox = 1.16;
  Double_t hbox = 1.01;
  
  Double_t xbox[5] = {-1, 1, 1, -1, -1};
  Double_t ybox[5] = {1, 1, -1, -1, 1};
  int i, v;
  for (i=0; i<5; i++) {
    box->SetPoint(i, 0.5*wbox*xbox[i], 0.5*hbox*ybox[i]);
  }
  box->SetTitle(Form("%s;%s;%s", map->GetTitle(), map->GetXaxis()->GetTitle(), map->GetYaxis()->GetTitle()));
  box->Draw("al");
  map->Draw("colz same");
  box->Draw("l");
  
  if (drawPMTs) {
    Double_t xpmt[7] = {0, COS30, COS30, 0, -COS30, -COS30, 0};
    Double_t ypmt[7] = {1, 0.5, -0.5, -1, -0.5, 0.5, 1};
      
    TGraph *pmthex[256];
    if (!coords_defined) {
      fillPmtCoords(pmtX, pmtY);
    }
    for (i=0; i<256; i++) {
      pmthex[i] = new TGraph(7);
      for (v=0; v<7; v++) {
        pmthex[i]->SetPoint(v, pmtX[i] + xpmt[v]*0.5*PMTPTP,
                            pmtY[i] + ypmt[v]*0.5*PMTPTP);
      }
      pmthex[i]->SetLineColor(15);
      pmthex[i]->SetLineWidth(0.1);
      pmthex[i]->Draw();
    }
  }  
  return camface;
}

void render(const char* infile=NULL, const char* title=NULL) {
  gStyle->SetNumberContours(50);
  TCanvas *cam;
  if (!infile) {
    printf("generating empty camera face and exiting\n");
    cam = camFaceCanvas();
    return;
  }
  
  char *graphTitle;
  graphTitle = title?(char *)title:(char *)infile;

  TTree *rays = new TTree();
  char infile_format[64] = "cam/I:pmt:x/F:y";
  rays->ReadFile(infile, infile_format);
  TH2F *map = sqmmHeatMap();
  map->SetTitle(Form("%s;-x (m);y (m)", graphTitle));
  rays->Project("map", "y:-x");
//   rays->Draw("y:-x", "", "same");
  cam = camFaceCanvas(map, 0);
//   map->Draw("colz");
  cam->Print(Form("%s.pdf", infile));
}
