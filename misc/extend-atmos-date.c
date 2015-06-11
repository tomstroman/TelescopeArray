// extend-atmos-date.c
// Thomas Stroman, University of Utah, 2015-06-11
/* Compilation instructions that fit within a "head" command:
gcc -c extend-atmos-date.c -I$TADSTINC
gcc -o extend-atmos-date.run extend-atmos-date.o -L$TADSTLIB -ldst2k -L$GCCLIB -lm -lz -lbz2
*/
// This single-use code is intended to modify the range of valid dates in a
// particular calibration file, so that it can be used beyond the original
// end date by date-sensitive simulation and reconstruction code.

#include <stdlib.h>
#include <stdio.h>
#include "event.h"
#include "convtime.h"

int main() {
//   the name of the input (and eventually output) file, hard-coded
  char dstname[1024];
  sprintf(dstname,"atmosParamTypicalDSTBank.dst.gz");
  
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
  
  if (tstBankList(hasBanks,FDATMOS_PARAM_BANKID) == 0) {
    fprintf(stderr,"Error finding fdAtmosParam bank. Is %s present?\n",
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
  
  dstOpenUnit(OUT_UNIT,dstname,MODE_WRITE_DST);
  if (eventWrite(OUT_UNIT,outBanks,TRUE) == 0)
    fprintf(stderr,"Error writing out event.\n");
  
  dstCloseUnit(OUT_UNIT);
  
  return 0;
  
}
  


