/* For use via #include in ROOT macros (compiled or interpreted): the quality cuts
 * in use for stereo analysis.
 *
 * Note that USE_PRA needs to be defined prior to #include "cuts.h"
 * Also note that weather.C macro needs to be loaded for some of these cuts to work.
 */

#ifndef _cuts_h_
#define _cuts_h_

// cuts to ensure good geometry
double LRMD_MAXSDPA = 170.0; // degrees
double BRMD_MAXSDPA = 170.0;
double BRLR_MAXSDPA = 170.0;
double MIN_TRACK = 6.0; // degrees
double MIN_DUR = 2000.0; //nanoseconds

TCut tmatch = "a.tratio0 > 0.9 && a.tratio1 > 0.9 && a.tratio0 < 1.1 && a.tratio1 < 1.1";
TCut sdpa = Form("( ((pcnps == 0) && (sdpa < %f)) || ((pcnps == 1) && (sdpa < %f)) || ((pcnps ==2 ) && (sdpa < %f)) )",LRMD_MAXSDPA,BRMD_MAXSDPA,BRLR_MAXSDPA);
TCut track = Form("min(a.ext0,a.ext1) >= %f",MIN_TRACK);
TCut dur = Form("min(a.text0,a.text1) >= %f",MIN_DUR);
TCut cut = tmatch + sdpa + track + dur;

// Cuts related to profile reconstruction
TCut bprof = "bstat==3 && bxmax > 401 && bxmax < 1199 && bxmax != 750.0 && bxmax > bx1 && bxmax < bx2";
TCut lprof = "lstat==3 && lxmax > 401 && lxmax < 1199 && lxmax != 750.0 && lxmax > lx1 && lxmax < lx2";
TCut mprof = "mstat==0 && mxmax > mx1 && mxmax < mx2 && mx1 > 50";
TCut bfitprof = bprof;
TCut lfitprof = lprof;
TCut mfitprof = mprof;

if (USE_PRA == 1) {
  bprof += "pra.bpra==1";
  lprof += "pra.lpra==1";
  mprof += "pra.mpra==1";
}  

TCut all = cut;

switch (USE_PRA) {
  case 0:
    all += Form("r.ngprof>=2 && weather(ymd) >= 1");
    break;
  case 1:
    all += Form("r.ngprof>=1 && weather(ymd) >= 1");
    break;
  case 2:
    all += Form("weather(ymd) >= 1 && (r.ngprof>=2 || (r.ngprof==1 && r.onepra==1))");
    break;
}
    
TCut orig = all;  

#endif

