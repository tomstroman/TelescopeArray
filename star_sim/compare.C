/* compare.C
 * Thomas Stroman, University of Utah, 2017-02-08
 * ROOT script (root.cern.ch) to compare observed and simulated
 * detection of starlight by Telescope Array fluorescence detectors.
 * 
 * Observation comes from calibrated FADC excesses, and simulation
 * comes from TRUMP ray-tracing routines and stellar coordinates
 * ascertained from Stellarium for the observation period.
 */

#include "TROOT.h"
#include "TTree.h"
#include "TH2.h"
#include "TProfile2D.h"
#include "TCanvas.h"
#include "TStyle.h"
#include "TMath.h"
#include "TGraph.h"
#include "TGraph2D.h"

#define SEC_PER_BIN 5
#define PMTGAP 0.002
#define PMTPTP 0.0693
#define PMTFTF 0.06
#define COS30 0.866025403784438708

double pmtX[256], pmtY[256];
double dist[256][256];

double utc_sec(double jd) {
  return fmod(jd - 0.5, 1.0) * 86400.0;
}

void fillPmtCoords(double *x, double *y) {
  int i, row, col;
  for (i=0; i<256; i++) {
    col = (i - (i % 16) )/ 16;
    row = i % 16;
    
    x[i] = -(PMTFTF + PMTGAP) * ((double)col - 7.75 + 0.5*(double)(row % 2));
    y[i] = (PMTPTP + PMTGAP/COS30)*0.75 * (7.5 - (double)row);
  }
}

TCanvas *camFace() {
  char canvname[64] = "camface";
  TCanvas *camface = (TCanvas*)gROOT->FindObject(canvname);
  if (!camface) {
    camface = new TCanvas(canvname, "cam", 580 + 28, 505 + 4);
  }
  TGraph *box = new TGraph(5);
  box->SetTitle("Camera face;-x (m);y (m)");
  Double_t wbox = 1.16;
  Double_t hbox = 1.01;
  
  Double_t xbox[5] = {-1, 1, 1, -1, -1};
  Double_t ybox[5] = {1, 1, -1, -1, 1};
  int i, v;
  for (i=0; i<5; i++) {
    box->SetPoint(i, 0.5*wbox*xbox[i], 0.5*hbox*ybox[i]);
  }
  
  box->Draw("al");
  
  Double_t xpmt[7] = {0, COS30, COS30, 0, -COS30, -COS30, 0};
  Double_t ypmt[7] = {1, 0.5, -0.5, -1, -0.5, 0.5, 1};
  
  TGraph *pmthex[256];
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
  
  return camface;
}

// this is likely a premature optimization but we'll be doing so many
// calculations of distance between two PMT centers that it's probably
// better to calculate every possible combination and build a lookup table
void calculateDistances(double x[256], double y[256], double r[256][256]) {
  int i, j;
  for (i=0; i<256; i++) {
    for (j=0; j<256; j++) {
      r[i][j] = TMath::Sqrt((x[i]-x[j])*(x[i]-x[j]) + (y[i]-y[j])*(y[i]-y[j]));
    }
  }
}

void analyzeCentroids(TH2F *simpmt, TProfile2D *obspmt, const char* pdfname = "centroids.pdf") {
  TGraph/*2D*/ *simcentroid = new TGraph/*2D*/(1);
  simcentroid->SetName("simcentroid");
  simcentroid->SetMarkerColor(kRed);
  
  TGraph/*2D*/ *obscentroid = new TGraph/*2D*/(1);
  obscentroid->SetName("obscentroid");
  obscentroid->SetMarkerColor(kBlue);

  TGraph2D *diffcentroid = new TGraph2D(1);
  diffcentroid->SetName("diffcentroid");
  
  TGraph *dcenx = new TGraph(1);
  dcenx->SetName("dcenx");
  dcenx->SetTitle("Centroid X: sim minus obs;UTC second;meters");
//   gDirectory->GetList()->Add(dcenx);
  TGraph *dceny = new TGraph(1);
  dceny->SetName("dceny");
  dceny->SetTitle("Centroid Y: sim minus obs;UTC second;meters");
//   gDirectory->GetList()->Add(dceny);
  TGraph *dcenr = new TGraph(1);
  dcenr->SetName("dcenr");
  dcenr->SetTitle("Centroid distance between sim and obs;UTC second;meters");
//   gDirectory->GetList()->Add(dcenr);
  TGraph *dcenf = new TGraph(1);
  dcenf->SetName("dcenf");
  dcenf->SetTitle("Centroid #phi: obs to sim;UTC second;degrees");
//   gDirectory->GetList()->Add(dcenf);
  
  int i, j;
  double x, y, w, sum;
  double ox, oy, ow, osum;
  TH1D *spy, *opy;
  int smaxpmt, omaxpmt;
  double utc_sec;
  
  int nbins = simpmt->GetNbinsX();
  for (i=1; i<=nbins; i++) {
    utc_sec = simpmt->GetBinCenter(i);
    simpmt->ProjectionY("spy", i, i);
    spy = (TH1D*)gROOT->FindObject("spy");
    smaxpmt = spy->GetMaximumBin() - 1;
    if (spy->GetMaximum() == 0) {
      continue;
    }
    
    obspmt->ProjectionY("opy", i, i);
    opy = (TH1D*)gROOT->FindObject("opy");
    omaxpmt = opy->GetMaximumBin() - 1;
    
    if (dist[smaxpmt][omaxpmt] > 0.15) {
      printf("Bin %d (utc %f): s %d, but o %d (dist %f)\n", 
             i, utc_sec, smaxpmt, omaxpmt, dist[smaxpmt][omaxpmt]);
      continue;
    }
    
//     printf("Max bin: %d (%f) sim, %d (%f) obs\n", 
//            spy->GetMaximumBin(), spy->GetMaximum(),
//            opy->GetMaximumBin(), opy->GetMaximum());
    x = ox = 0;
    y = oy = 0;
    sum = osum = 0;
    w = ow = 0;
    for (j=1; j<=256; j++) {
      w = simpmt->GetBinContent(i, j);
      sum += w;
      x += w * pmtX[j-1];
      y += w * pmtY[j-1];
      
      if (dist[j-1][omaxpmt] < 0.2) {
        ow = obspmt->GetBinContent(i, j);
        osum += ow;
        ox += ow * pmtX[j-1];
        oy += ow * pmtY[j-1];
      }
    }
    if (sum > 0) {
      x /= sum;
      y /= sum;
    }
    else {
      printf("bin %d - no sim (sum=0)\n", i);
      x = y = 0;
    }
    simcentroid->SetPoint(i-1, x, y/*, utc_sec*/);
    
    if (osum > 0) {
      ox /= osum;
      oy /= osum;
    }
    else {
      ox = oy = 0;
    }
    obscentroid->SetPoint(i-1, ox, oy/*, utc_sec*/);
    
    if (sum > 0 && osum > 0) {
      diffcentroid->SetPoint(i-1, x-ox, y-oy, utc_sec);
      dcenx->SetPoint(i-1, utc_sec, x-ox);
      dceny->SetPoint(i-1, utc_sec, y-oy);
      dcenr->SetPoint(i-1, utc_sec, TMath::Sqrt((x-ox)*(x-ox) + (y-oy)*(y-oy)));
      dcenf->SetPoint(i-1, utc_sec, TMath::ATan2(y-oy, x-ox) * TMath::RadToDeg());
    }
    
  }

  TCanvas *camface = camFace();
  simcentroid->Draw("p");
  obscentroid->Draw("p");
  camface->Print(Form("%s(", pdfname), "pdf");
  camface->Close();
  
  TCanvas *c1 = new TCanvas("c1", "c1");
  dcenx->Draw("ap");
  c1->Print(pdfname);
  dceny->Draw("ap");
  c1->Print(pdfname);
  dcenr->Draw("ap");
  c1->Print(pdfname);
  dcenf->Draw("ap");
  c1->Print(Form("%s)", pdfname), "pdf");
  
  c1->Close();
}

void compare(const char *obsfile, const char *simfile) {
  gStyle->SetNumberContours(50);
  TTree *obs = new TTree();
  printf("Reading observation data...\n");
  obs->ReadFile(obsfile, "jtime/D:cam/I:pmt:m0:npe/F");
  
  TTree *sim = new TTree();
  printf("Reading simulation data...\n");
  sim->ReadFile(simfile, "jtime/D:cam/I:pmt:x/F:y");
  
//   printf("obs entries: %ld; sim rays: %ld\n", obs->GetEntries(), sim->GetEntries());
  
  double jstart = obs->GetMinimum("jtime");
  double jend = obs->GetMaximum("jtime");
  double dur_sec = (jend - jstart) * 86400.;
  int start_sec_utc = (int)utc_sec(jstart);  
  printf("start_sec_utc: %d\n", start_sec_utc);
  
  int nbins = (int)(dur_sec / SEC_PER_BIN) + 1;
  
  TProfile2D *obspmt = new TProfile2D("obspmt", "", 
                          nbins, start_sec_utc, start_sec_utc + nbins*SEC_PER_BIN, 
                          256, 0, 256);
  obspmt->SetStats(0);
  TH2F *simpmt = new TH2F("simpmt", "", 
                          nbins, start_sec_utc, start_sec_utc + nbins*SEC_PER_BIN, 
                          256, 0, 256);
  simpmt->SetStats(0);
  
  obs->Project("obspmt", "npe:pmt:utc_sec(jtime)", "", "prof");  

//   obspmt->Draw("colz");
  
  sim->Project("simpmt", "pmt:utc_sec(jtime)", "pmt>=0");
//   TCanvas *c2 = new TCanvas("c2", "c2");
//   c2->cd();
//   simpmt->Draw("colz");
  

  fillPmtCoords(pmtX, pmtY);
  calculateDistances(pmtX, pmtY, dist);

  analyzeCentroids(simpmt, obspmt, "analyze-centroids.pdf");
  


}

