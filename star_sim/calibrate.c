/* calibrate.c
 * Thomas Stroman, University of Utah, 2017-01-31
 * Syntax for compiling:
gcc -DRTDATA=\"$RTDATA\" -c calibrate.c -fopenmp -I$TADSTINC -I$TRUMP/inc
gcc -o calibrate.run calibrate.o -fopenmp -L$TADSTLIB -ldst2k -L$GCCLIB -lm -lz -lbz2 -L$TRUMP/lib -lcontrol -lfadctel -ltoolbox
 * 
 * Load a file containing FDMEAN DST banks. Scan all triggers to find the minimum
 * for each PMT. Then scan through all triggers again, converting the FADC excess
 * above minimum into NPE using time-dependent calibration.
 * Output to stdout (unless output file is specified), one line per PMT per trigger
*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "event.h"
#include "trump.h"

#define IN_UNIT 1
#define MAXNBANK 200
#define DEFAULT_INDEX 0

TACalibration cal;
UCalibration ucal;
RuntimeParameters par;
FILE *fp;
int main(int argc, char *argv[]) {
  fp = stdout;
// Crude validation of arguments
  switch(argc) {
    case 3:
      fp = fopen(argv[2], "w");
    case 2:
      break;
    default:
      fprintf(stderr, "Usage:\n\n  %s dstfile [output]\n\n", argv[0]);
      return -1;
  }
  
// Initial setup
  initializeParameters(&par);
  par.siteid = BLACK_ROCK_SITEID;
  cal.nmir = 12;
  ucal.tc = &cal;
  getTADefaultCalibration(&par, &cal);

  int wantBanks, hasBanks, event;
  wantBanks = newBankList(MAXNBANK);
  hasBanks = newBankList(MAXNBANK);

  fdmean_dst_common *fdmean;
// Hunting for minimum for each PMT - initialize array to number larger than 0xffff
  int ntrig = 0;
  int i, j, k;
  int minmean[12][256];

  for (j=0; j<12; j++)
    for (i=0; i<256; i++)
      minmean[j][i] = 0xffffff;

  double jtime;
// Open the DST file and read it, finding minima, then close it.
  dstOpenUnit(IN_UNIT, argv[1], MODE_READ_DST);
  while (eventRead(IN_UNIT, wantBanks, hasBanks, &event) >= 0 ) {
    if (tstBankList(hasBanks, FDMEAN_BANKID) == 1) {
      fdmean = &fdmean_;
      ntrig += fdmean->ntrig;
      fprintf(stderr, "ntrig: %d\n", ntrig);
      for (i=0; i<fdmean->ntrig; i++) {
        for (j=0; j<12; j++) {
          for (k=0; k<256; k++) {
            if (fdmean->mean[i][j][k][DEFAULT_INDEX] < minmean[j][k]) {
              minmean[j][k] = fdmean->mean[i][j][k][DEFAULT_INDEX];
            }
          }
        }
      }
    }
  }

  dstCloseUnit(IN_UNIT);

  /*
  for (i=0; i<12; i++) {
    fprintf(stderr, "cam %d:\n", i);
    for (j=0; j<256; j++) {
      if (j%16 == 0) {
        fprintf(stderr, "\n");
      }
      fprintf(stderr, "%6d ", minmean[i][j]);
    }
    fprintf(stderr, "\n");
  }
  */
// Scan the DST file again, this time subtracting the per-PMT minimum. Get
// calibration and convert FADC excess to NPE.
  double mean_npe;

  dstOpenUnit(IN_UNIT, argv[1], MODE_READ_DST);
  while (eventRead(IN_UNIT, wantBanks, hasBanks, &event) >= 0 ) {
    if (tstBankList(hasBanks, FDMEAN_BANKID) == 1) {
      fdmean = &fdmean_;
      par.siteid = fdmean->siteid;
      for (i=0; i<fdmean->ntrig; i++) {
        jtime = fdmean->jtime[i];
        par.jday = (int)jtime;
        par.jsec = (int)((jtime - par.jday) * 86400.);
        jul2cal(&par);
        
        getTATimeDependentCalibration(&par, &cal);
        for (j=0; j<12; j++) {
          for (k=0; k<256; k++) {
            mean_npe = (fdmean->mean[i][j][k][DEFAULT_INDEX] - minmean[j][k]) / cal.pmtgain[j][k];
            fprintf(fp, "%.8f %d %d %f\n", jtime, j, k, mean_npe);
          }
        }
      }
    }
  }

  dstCloseUnit(IN_UNIT);

  if (argc == 3) {
    fclose(fp);
  }
  return 0;
}
