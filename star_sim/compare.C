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
#include "TGraph2D.h"
#define SEC_PER_BIN 5

double utc_sec(double jd) {
  return fmod(jd - 0.5, 1.0) * 86400.0;
}

void fillPmtCoords(double *x, double *y) {
  Double_t pmtgap = 0.002, pmtptp = 0.0693, pmtftf = 0.06;
  Double_t cos30 = TMath::Cos(30*TMath::DegToRad());
  int i, row, col;
  for (i=0; i<256; i++) {
    col = (i - (i % 16) )/ 16;
    row = i % 16;
    
    x[i] = -(pmtftf + pmtgap) * ((double)col - 7.75 + 0.5*(double)(row % 2));
    y[i] = (pmtptp + pmtgap/cos30)*0.75 * (7.5 - (double)row);
  }
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
  TCanvas *c1 = new TCanvas("c1", "c1");
  c1->cd();
//   obspmt->Draw("colz");
  
  sim->Project("simpmt", "pmt:utc_sec(jtime)", "pmt>=0");
//   TCanvas *c2 = new TCanvas("c2", "c2");
//   c2->cd();
//   simpmt->Draw("colz");
  
  double pmtX[256], pmtY[256];
  double dist[256][256];
  fillPmtCoords(pmtX, pmtY);
  calculateDistances(pmtX, pmtY, dist);

  
  TGraph2D *simcentroid = new TGraph2D(1);
  simcentroid->SetName("simcentroid");
  
  TGraph2D *obscentroid = new TGraph2D(1);
  obscentroid->SetName("obscentroid");

  int i, j;
  double x, y, w, sum;
  double ox, oy, ow, osum;
  TH1D *spy, *opy;
  int smaxpmt, omaxpmt;
  double utc_sec;
  for (i=1; i<=nbins; i++) {
    utc_sec = simpmt->GetBinCenter(i);
    simpmt->ProjectionY("spy", i, i);
    spy = (TH1D*)gROOT->FindObject("spy");
    smaxpmt = spy->GetMaximumBin() - 1;
    
    obspmt->ProjectionY("opy", i, i);
    opy = (TH1D*)gROOT->FindObject("opy");
    omaxpmt = opy->GetMaximumBin() - 1;
    
    if (dist[smaxpmt][omaxpmt] > 0.15) {
      printf("Bin %d (utc %f): s %d, but o %d (dist %f)\n", 
             i, utc_sec, smaxpmt, omaxpmt, dist[smaxpmt][omaxpmt]);
      break;
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
    simcentroid->SetPoint(i-1, x, y, utc_sec);
    
    if (osum > 0) {
      ox /= osum;
      oy /= osum;
    }
    else {
      ox = oy = 0;
    }
    obscentroid->SetPoint(i-1, ox, oy, utc_sec);
  }
  
  
  
}

