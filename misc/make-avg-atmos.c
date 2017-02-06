// make-avg-atmos.c
// Thomas Stroman, University of Utah, 2015-06-26
/* Compilation instructions that fit within a "head" command:
gcc -c make-avg-atmos.c -I$TADSTINC
gcc -o make-avg-atmos.run make-avg-atmos.o -L$TADSTLIB -ldst2k -L$GCCLIB -lm -lz -lbz2
*/
// This single-use code is intended to compute the average values of the 
// atmosphere according to several measurements in one file (gdas.dst.gz),
// provided those measurements apply to a time when the Middle Drum detector
// was running -- as determined by another file (md-ontimes.txt).
// The output will be called gdasParamTypicalDSTBank.dst.gz and it will be
// formatted to satisfy the same description as atmosParamTypicalDSTBank.dst.gz
// (the file used by default in Middle Drum reconstruction, with altitudes
// measured from the CLF and temperatures given in degrees Celsius).

#include <stdlib.h>
#include <stdio.h>
#include "event.h"
#include "convtime.h"

typedef struct {
  int ymd;
  int part;
  int n;
  double epo_s_on;
  double epo_s_off;
} Mdpart;

int main() {
  /* Logical flow:
   * 1. Read the list of data parts, with their start and end times.
   * 2. Step through the GDAS atmosphere records:
   * 2a.  Of the 3-hour window of application, how long was MD running?
   * 2b.  Contribute to a weighted average according to (2a).
   * 3. Write the average profile to an output file.
   */
  
  
  // 1. Read the list of data parts, with their start and end times.
  
  char inlistname[1024];
  /* 
   * the file is expected to be in the same directory, 
   * and formatted in four columns:
   * 
   * yyyymmddpps n s_on s_off
   * 
   * where:
   * 
   * yyyymmddpps = the 11-digit part code beginning with date (8 digits)
   * n = a diagnostic indicator (usually 1 but possibly >1 on some dates with
   *    anomalous data records)
   * s_on = the UTC second (number of seconds since 00:00:00.0 UTC) when
   *    DAQ was enabled
   * s_off = the UTC second when DAQ was disabled
   */
  
#define NMDPART 10000
  // We will work with the first seven years, which involves <10000 parts.
  // This number may need to be increased in the future.  
  Mdpart mdparts[NMDPART];
  int i, nrec = 0;
  sprintf(inlistname,"md-ontimes.txt");
  char inlist[1024];
  FILE *fp = fopen(inlistname,"r");
  fgets(inlist,1000,fp);
  long ymdps;
  int n;
  double s_on, s_off;
  Mdpart *m;
  while (nrec<NMDPART && !feof(fp)) {
    m = &mdparts[nrec++];
    sscanf(inlist,"%ld %d %lf %lf",&ymdps,&n,&s_on,&s_off);
    m->ymd = (int)(ymdps/1000);
    m->part = (int)((ymdps - 1000*(long)m->ymd) / 10);
    m->n = n;
    m->epo_s_on = ymdsec2eposec(m->ymd,s_on);
    m->epo_s_off = ymdsec2eposec(m->ymd,s_off);
    fgets(inlist,1000,fp);
  }
  fclose(fp);
  if (nrec >= NMDPART) {
    fprintf(stderr,"Warning: stopped reading %s at %d records\n",
            inlistname,NMDPART);
  }
  
  printf("Found %d records.\n",nrec);
  for (i=0; i<nrec; i++) {
    printf("%d %f %f (%d %2d)\n",i,mdparts[i].epo_s_on,mdparts[i].epo_s_off,
      mdparts[i].ymd,mdparts[i].part);
  }
  return 0;
  /*
//   the name of the input (and eventually output) file, hard-coded
  char indstname[1024];
  
  
  
  sprintf(dstname,"%s/gdas.dst.gz");
  
  // DST handling
#define MAXNBANK 200
  int wantBanks, hasBanks, event, outBanks;
  wantBanks = newBankList(MAXNBANK);
  hasBanks = newBankList(MAXNBANK);
  outBanks = newBankList(MAXNBANK);

  //   eventAllBanks(wantBanks); // not sure this line will be necessary
  
#define IN_UNIT 1
#define OUT_UNIT 2
  
  // open, read, and close the DST file
  dstOpenUnit(IN_UNIT,dstname,MODE_READ_DST);
  eventRead(IN_UNIT,wantBanks,hasBanks,&event);
  dstCloseUnit(IN_UNIT);
  
  if (tstBankList(hasBanks,GDAS_BANKID) == 0) {
    fprintf(stderr,"Error finding GDAS bank. Is %s present?\n",
            dstname);
    return -1;
  }
  
  // the extern fdatmos_param_dst_common fdatmos_param_ has now been filled.
  // Pointer for convenience.
  fdatmos_param_dst_common *fda = &fdatmos_param_;
  
  // specify final date here. Let's land just a little before the epoch issue.
  int ymd = 20380101;
  double sec = 0;
  
  fda->dateTo = (int)ymdsec2eposec(ymd,sec);
  
  addBankList(outBanks,FDATMOS_PARAM_BANKID);
  
  dstOpenUnit(OUT_UNIT,outdstname,MODE_WRITE_DST);
  if (eventWrite(OUT_UNIT,outBanks,TRUE) == 0)
    fprintf(stderr,"Error writing out event.\n");
  
  dstCloseUnit(OUT_UNIT);
  
  return 0;
  */
}
  


