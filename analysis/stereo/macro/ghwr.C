/* functions for manipulating Gaisser-Hillas profile parameters into
 * various combinations. Specifically, recasting X0 and Lambda into
 * width and ratio values is in view here.
 */

#include "TROOT.h"
#include "TMath.h"

#define LN256 5.54517744447956229
#define SQRTLN256 2.35482004503094933

double ghwidth(double xmax, double x0, double lambda) {
  return TMath::Sqrt(lambda * (xmax - x0)) * SQRTLN256;
}

double ghratio(double xmax, double x0, double lambda) {
  return lambda / (xmax - x0);
}