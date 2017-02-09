/* compare.C
 * Thomas Stroman, University of Utah, 2017-02-08
 * ROOT script (root.cern.ch) to compare observed and simulated
 * detection of starlight by Telescope Array fluorescence detectors.
 * 
 * Observation comes from calibrated FADC excesses, and simulation
 * comes from TRUMP ray-tracing routines and stellar coordinates
 * ascertained from Stellarium for the observation period.
 */

void compare(const char *obsfile, const char *simfile) {
  TTree *obs = new TTree();
  obs->ReadFile(obsfile, "jtime/D:cam/I:pmt:m0:npe/F");
}

