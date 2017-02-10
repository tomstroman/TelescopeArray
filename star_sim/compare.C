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

#define SEC_PER_BIN 5

double utc_sec(double jd) {
  return fmod(jd - 0.5, 1.0) * 86400.0;
}
void compare(const char *obsfile, const char *simfile) {
  gStyle->SetNumberContours(50);
  TTree *obs = new TTree();
  obs->ReadFile(obsfile, "jtime/D:cam/I:pmt:m0:npe/F");
  
//   TTree *sim = new TTree();
//   sim->ReadFile(simfile, "jtime/D:cam/I:pmt:x/F:y");
  
//   printf("obs entries: %ld; sim rays: %ld\n", obs->GetEntries(), sim->GetEntries());
  
  double jstart = obs->GetMinimum("jtime");
  double jend = obs->GetMaximum("jtime");
  double dur_sec = (jend - jstart) * 86400.;
  int start_sec_utc = (int)utc_sec(jstart);  
  
  
  int nbins = (int)(dur_sec / SEC_PER_BIN) + 1;
  
  TProfile2D *pmtbin = new TProfile2D("pmtbin", "", 
                          nbins, start_sec_utc, start_sec_utc + nbins*SEC_PER_BIN, 
                          256, 0, 256);
  
  TProfile2D *obspmt = (TProfile2D*)pmtbin->Clone("obspmt");
  
  obs->Project("obspmt", "npe:pmt:utc_sec(jtime)", "", "prof");
  
  obspmt->Draw("colz");
}

