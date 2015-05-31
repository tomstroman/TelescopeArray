/* utafd_shower_average.C
 * Thomas Stroman, University of Utah, 2015-05-31
 * ROOT script for a single purpose: calculate the value to be used in
 * UTAFD simulation software given five other values. The output value
 * is the average energy deposit over the entire age of a cosmic-ray air
 * shower, given the energy deposit per particle as a function of age
 * and assuming the number of particles has a Gaussian-in-age evolution.
 */
#include "TROOT.h"
#include "TMath.h"
#include "TF1.h"
double gaussian_in_age(double *s, double *p) {
  // Age = s[0]
  // Nmax = p[0]
  // sigma = p[1]
  if (s[0] < 0 || s[0] > 3)
    return 0;
  double arg = (s[0] - 1.0)/p[1];
  return p[0] * TMath::Exp(-0.5*arg*arg);  
}

double nerling_alpha(double *s, double *p) {
  // Age = s[0]
  // Nerling "c" parameters (5x) = p[0] - p[4]
  return p[0] / TMath::Power(p[1]+s[0],p[2]) + p[3] + p[4]*s[0];
}

double gia_weighted_alpha(double *s, double *p) {
// p has seven parameters: Nmax, sigma_s, then the five alpha coefficients
  double *c = &p[2];
  
  return gaussian_in_age(s,p) * nerling_alpha(s,c);
}

double nmax_ratio(double orig_cut_mev, double new_cut_mev) {
  return (1.0 - 0.045*new_cut_mev)/(1.0-0.045*orig_cut_mev);
}

double utafd_shower_average(double c1, double c2, double c3, 
                            double c4, double c5, double ecut_mev = 0.05) {
  double p[7] = {1.0,0.2,c1,c2,c3,c4,c5};
  TF1 *gia = new TF1("gia",gaussian_in_age,0,3,2);
  TF1 *gwa = new TF1("gwa",gia_weighted_alpha,0,3,7);
  gia->SetParameters(p);
  gwa->SetParameters(p);
  printf("Input values use ecut = 1 MeV; output is average energy deposit\n");
  printf("per particle above %f MeV.\n",ecut_mev);
  return gwa->Integral(0,3)/gia->Integral(0,3) * 
         nmax_ratio(ecut_mev,1.0); 
}