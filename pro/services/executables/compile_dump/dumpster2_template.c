/* Syntax for compiling:
gcc -DRTDATA=\"$RTDATA\" -c dumpster2.c -ggdb -I$TADSTINC -I$TRUMP/inc
gcc -o dumpster2.run dumpster2.o -L$TADSTLIB -ldst2k -L$GCCLIB -lm -lz -lbz2 -L$TRUMP/lib  -lraytrace -lairshower -ltoolbox 
*/


/* This code reads processed event DSTs and produces ASCII output of the desired fields.
 * Specifically written for stereo analysis, it requires events to have an STPLANE bank
 * and data from 2 or 3 FDs. It's possible for an event to have an unsuccessful
 * profile reconstruction at one or more sites, so it is necessary to use an intelligent
 * reconstruction-combination scheme.
 * 
 * Here is how reconstructions are categorized:
 * 0: only BRM profile
 * 1: only LR profile
 * 2: only MD profile
 * 3: BRM + LR
 * 4: BRM + MD
 * 5: LR + MD
 * 6: BRM + LR + MD
 * 
 * Combination of profiles will be done two ways: once unweighted, in which the 
 * arithmetic mean Xmax and geometric mean Epri are calculated without regard to
 * fit uncertainties, and a weighted mean using the reduced chi-squared 
 * goodness-of-fit statistic.
 * 
 * There is also space given for a combined-data reconstruction.
 */

 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "event.h"
#include "trump.h"
#include "fdsite.h"
#include "toolbox.h"
#include "convcoord.h"
#define IN_UNIT 1
#define MAXNBANK 200

#  define MEC_A0 -0.5717
#  define MEC_A1  0.1416
#  define MEC_A2 -0.003328

#define getMissingEnergyCorrection(LE) ((MEC_A0)+(MEC_A1)*(LE)+(MEC_A2)*(LE)*(LE))

#define PRFCFIT 2

GaisserHillasParameters ghp;
double getEnergyByGram (double x);
 
static void reorder(int n, double *arr, int *indx);

int main(int argc, char *argv[]) {
  if (argc != 2) {
    fprintf(stderr,"Usage: \n\n  %s dstfile\n\n",argv[0]);
    return -1;
  }

  int wantBanks, hasBanks, event;
  wantBanks = newBankList(MAXNBANK);
  hasBanks = newBankList(MAXNBANK);

  
  // fdplane banks (FD site observations)
  
  fdplane_dst_common *bplane;
  fdplane_dst_common *lplane;
  fdplane_dst_common *mplane;
  
  // stereo bank
  stplane_dst_common *splane; 
  
  // event MC bank
  trumpmc_dst_common *tmc;
  
  // profile reconstructions
  fdtubeprofile_dst_common *btp;
  fdtubeprofile_dst_common *ltp;
  
  prfc_dst_common *prfc;
  hcbin_dst_common *hcbin;
  fdtubeprofile_dst_common *mtp;
  
  sttubeprofile_dst_common *stp;

  int seq[TA_UNIV_MAXTUBE];
  
#define SBR 0
#define SLR 1
#define SMD 2
#define SST 3
  int mc = FALSE;  
  int isPresent[4] = {0};
  int isGood[4] = {0};
  
  

  
   
  int i, i0, rc = -1;
  int k;        // for FDPLANE tube index
  int nps, pcnps;                      // non-participating site

  int ymd;  
  double sec;
  AirShower as;
  double mecal;
  double bsdptheta,bsdpphi,lsdptheta,lsdpphi,msdptheta,msdpphi;
  double clfcore[3], clfshower_uv[3];
  double nplnA[3], nplnB[3];
  double dummy[3];
  double azm; 
  
  geofd_dst_common *geo[3];
  char brgeo[1024], lrgeo[1024], mdgeo[1024];
//   sprintf(brgeo,"%s/fdgeom/geobr_ssp20131002cen.dst.gz",RTDATA);
//   sprintf(lrgeo,"%s/fdgeom/geolr_ssp20131002cen.dst.gz",RTDATA);
//   sprintf(brgeo,"%s/fdgeom/geobr_tokuno20131111cen.dst.gz",RTDATA);
//   sprintf(lrgeo,"%s/fdgeom/geolr_tokuno20131111cen.dst.gz",RTDATA);  
  sprintf(brgeo,"%s/fdgeom/geobr_joint.dst.gz",RTDATA);
  sprintf(lrgeo,"%s/fdgeom/geolr_joint.dst.gz",RTDATA);
  sprintf(mdgeo,"%s/fdgeom/geomd_20131002.dst.gz",RTDATA);
  dstOpenUnit(IN_UNIT, brgeo, MODE_READ_DST);
//   while (
  eventRead(IN_UNIT, wantBanks, hasBanks, &event);// >= 0)
  if (tstBankList(hasBanks,GEOBR_BANKID)==1)
    geo[0] = &geobr_;
  dstCloseUnit(IN_UNIT);
  
  dstOpenUnit(IN_UNIT, lrgeo, MODE_READ_DST);
//   while (
  eventRead(IN_UNIT, wantBanks, hasBanks, &event);//>=0)
  if (tstBankList(hasBanks,GEOLR_BANKID)==1)
    geo[1] = &geolr_;
  dstCloseUnit(IN_UNIT);
  
  dstOpenUnit(IN_UNIT, mdgeo, MODE_READ_DST);
  eventRead(IN_UNIT, wantBanks, hasBanks, &event);//>=0)
  if (tstBankList(hasBanks,GEOMD_BANKID)==1)
    geo[2] = &geomd_;
  dstCloseUnit(IN_UNIT);  
//   double R[2][3][3];
//   matrixInverse(geo[0]->site2clf,R[0]);
//   matrixInverse(geo[1]->site2clf,R[1]);
  
//   fdplane_dst_common *plane0, *plane1;
  double balt,bazm,bpalt,bpazm,bnpe;
  double lalt,lazm,lpalt,lpazm,lnpe;
  double malt,mazm,mpalt,mpazm,mnpe;
  int site0 = -1, site1 = -1;
  dstOpenUnit(IN_UNIT, argv[1], MODE_READ_DST);

  while (eventRead(IN_UNIT, wantBanks, hasBanks, &event) >= 0 ) {
    
    if (tstBankList( hasBanks, STPLANE_BANKID) == 1)
      splane = &stplane_;
    else {
      fprintf(stderr,"Error: event does not contain STPLANE bank. Skipping...\n");
      continue;
    }
    
    if (tstBankList ( hasBanks, TRUMPMC_BANKID) == 1) {
      mc = TRUE;
      tmc = &trumpmc_;
    }
    else
      mc = FALSE;
    
    // test for profile reconstructions
    isPresent[SBR] = (tstBankList( hasBanks, BRPLANE_BANKID) == 1 
      && tstBankList( hasBanks, BRTUBEPROFILE_BANKID) == 1);
    isPresent[SLR] = (tstBankList(hasBanks, LRPLANE_BANKID) == 1
      && tstBankList(hasBanks, LRTUBEPROFILE_BANKID) == 1);
    isPresent[SMD] = (tstBankList(hasBanks, FDPLANE_BANKID) == 1
      && tstBankList(hasBanks, PRFC_BANKID) == 1);
    isPresent[SST] = (tstBankList(hasBanks, STTUBEPROFILE_BANKID));
    
    bplane=(isPresent[SBR])?&brplane_:NULL;
    lplane=(isPresent[SLR])?&lrplane_:NULL;
    mplane=(isPresent[SMD])?&fdplane_:NULL;

    // identify the non-participating site. If value remains at -1, all sites observed it.
    nps = -1;
    pcnps = -1;
    for (i=0; i<3; i++)
      if (splane->sites[i] == 0) {
        nps=i;
        pcnps=i;
      }

    // if there was no non-participating site, need to figure out which one was omitted.
    // This technique works because stplane.run isn't thorough. It only calculates the 
    // crossing angle for the planes it actually used.
    
    // determine geometry combination index
    int icomb = 0;
    while (splane->sdp_angle[icomb] == 0 && icomb < 6)
      icomb++;
    if (pcnps==-1) {
      switch (icomb) {
        case 0: 
          pcnps = MIDDLE_DRUM_SITEID;
          break;
        case 1:
          pcnps = LONG_RIDGE_SITEID;
          break;
        case 3:
          pcnps = BLACK_ROCK_SITEID;
          break;
        default:
          fprintf(stderr,"Error: invalid site combination inferred from plane-crossing angle.\n");
          continue;
      }

    }
    btp = (isPresent[SBR])?&brtubeprofile_:NULL;
    ltp = (isPresent[SLR])?&lrtubeprofile_:NULL;
    prfc = (isPresent[SMD])?&prfc_:NULL;
    hcbin = (isPresent[SMD])?&hcbin_:NULL;
    
    i0 = (nps==0); // index of stplane bank entry to use
    mjlday2ymdsec((double)splane->juliancore[i0] + (double)splane->jseccore[i0]/86400 - MJLDOFF,&ymd,&sec);
    
    // event/reconstruction metadata
    fprintf(stdout,"%08d %07d %07d %07d %d %d %d ",
        ymd,                                        // BRANCH ymd/I
        isPresent[SBR]?(bplane->part*100000 + bplane->event_num):0,  // BRANCH brid/I
        isPresent[SLR]?(lplane->part*100000 + lplane->event_num):0,  // BRANCH lrid/I
        isPresent[SMD]?(mplane->part*100000 + mplane->event_num):0,  // BRANCH mdid/I
        isPresent[SBR]?btp->ntube:0,                      // BRANCH bptube/I
        isPresent[SLR]?ltp->ntube:0,                      // BRANCH lptube/I
        isPresent[SMD]?prfc->nbin[PRFCFIT]:0);                                      // BRANCH pcnps/I

    


//     
    // finally some profile reconstruction!
    // status and chi-squared
    fprintf(stdout,"%d %d %d\n",
            isPresent[SBR]?btp->status[0]:-9,           // BRANCH bstat/I
            isPresent[SLR]?ltp->status[0]:-9,           // BRANCH lstat/I
            isPresent[SMD]?prfc->failmode[PRFCFIT]:-9   // BRANCH mstat/I
    ); // BRANCH mpchi2/D
    
    // Gaisser-Hillas parameters and errors, calorimetric energy, corrected energy
    if (isPresent[SBR] && btp->status[0] >= 0) {

      reorder(btp->ntube, btp->x[0], seq);
      fprintf(stdout,"0 %d\n",btp->ntube);
      for (i=0; i<btp->ntube; i++) {
        for (k=0; k<bplane->ntube; k++) {
          if ((bplane->camera[k] == btp->camera[seq[i]]) && (bplane->tube[k] == btp->tube[seq[i]]))
            break;
        }
        if (k >= bplane->ntube) {
          fprintf(stderr,"Warning: couldn't match BTP index %d\n",i); 
          balt = bazm = bpalt = bpazm = bnpe = -1;         
        }
        else {
//           printf("tbfl pmt %d (%d, %d) matches plane pmt %d (%d, %d)\n",
//                  i,btp->camera[seq[i]],btp->tube[seq[i]],k,bplane->camera[k],bplane->tube[k]);
          balt = bplane->alt[k];
          bazm = bplane->azm[k];
          bpalt = bplane->plane_alt[k];
          bpazm = bplane->plane_azm[k];
          bnpe = bplane->npe[k];
        }
        fprintf(stdout,"%d %d %d %f %e %e %e %f %f %f %f %f\n",
                seq[i],
                btp->camera[seq[i]],
                btp->tube[seq[i]],
                btp->x[0][seq[i]],
                btp->flux[0][seq[i]]/R2D,
                btp->simflux[0][seq[i]]/R2D,
                btp->eflux[0][seq[i]]/R2D,
                balt*R2D,
                bazm*R2D,
                bpalt*R2D,
                bpazm*R2D,
                bnpe
        );
      }
     
    }
    else
      fprintf(stdout,"0 0 \n");
    
    if (isPresent[SLR] && ltp->status[0] >= 0) {

      reorder(ltp->ntube, ltp->x[0], seq);
      fprintf(stdout,"1 %d\n",ltp->ntube);
      for (i=0; i<ltp->ntube; i++) {
        for (k=0; k<lplane->ntube; k++) {
          if (lplane->camera[k] == ltp->camera[seq[i]] && lplane->tube[k] == ltp->tube[seq[i]])
            break;
        }
        if (k >= lplane->ntube) {
          fprintf(stderr,"Warning: couldn't match LTP index %d\n",i); 
          lalt = lazm = lpalt = lpazm = lnpe = -1;         
        }
        else {
          lalt = lplane->alt[k];
          lazm = lplane->azm[k];
          lpalt = lplane->plane_alt[k];
          lpazm = lplane->plane_azm[k];
          lnpe = lplane->npe[k];
        }    
        fprintf(stdout,"%d %d %d %f %e %e %e %f %f %f %f %f\n",
                seq[i],
                ltp->camera[seq[i]],
                ltp->tube[seq[i]],
                ltp->x[0][seq[i]],
                ltp->flux[0][seq[i]]/R2D,
                ltp->simflux[0][seq[i]]/R2D,
                ltp->eflux[0][seq[i]]/R2D,
                lalt*R2D,
                lazm*R2D,
                lpalt*R2D,
                lpazm*R2D,
                lnpe
        );
      }

    }
    else
      fprintf(stdout,"1 0 \n");
    
    if (isPresent[SMD] && prfc->failmode[PRFCFIT] == 0) {
      fprintf(stdout,"2 %d\n",prfc->nbin[PRFCFIT]);
      for (i=0; i<prfc->nbin[PRFCFIT]; i++) {

//         fprintf(stdout,"%f %e %e\n",
//                 prfc->dep[PRFCFIT][i],
//                 prfc->sig[PRFCFIT][i],
//                 prfc->sigmc[PRFCFIT][i]
//          );
        // need to figure out how to calculate these for bins.
        // hcbin bank has bvx, bvy, bvz but no comments to tell ho they're used.
        malt = mazm = mpalt = mpazm = mnpe = 0;
        fprintf(stdout,"%f %e %e %e %f %f %f %f %f\n",
                prfc->dep[PRFCFIT][i],
                prfc->sig[PRFCFIT][i],
                prfc->sigmc[PRFCFIT][i],
                hcbin->sigerr[PRFCFIT][i],
                malt*R2D,
                mazm*R2D,
                mpalt*R2D,
                mpazm*R2D,
                mnpe        
        );
      }

    }
    else
      fprintf(stdout,"2 0\n");    

    
  }
  dstCloseUnit(IN_UNIT);
  
  
  
  return 0;
}

double getEnergyByGram (double x) {
  double age, alpha, ne;

  age = ageS (x, ghp.xmax);
  alpha = getAlphaEff (age);
  ne = (ghp.lambda==-1)?gaussianInAgeFunction(&ghp, x):gaisserHillasFunction (&ghp, x);

  return ne * alpha;
}
static void reorder(int n, double *arr, int *indx){
  // this function orders the array arr by generating the index array
  // indx. The result is such that the array arr[indx[i]] is the
  // ordered.

  int l,j,ir,indxt,i,k;
  double q;
  if (n<=0) return;
  indx-=1;
  arr -=1; // to account for stupid Fortran conventions
  for (j=1;j<=n;j++) indx[j]=j;
  if (n==1) {indx[1]=0; return;}
  l=(n >> 1) + 1;
  ir = n;
  for (;;) {
    if (l>1) q=arr[(indxt=indx[--l])];
    else {
      q=arr[(indxt=indx[ir])];
      indx[ir]=indx[1];
      if (--ir==1) {
        indx[1]=indxt;
        for (k=1;k<=n;k++) indx[k]--;
        return;
      }
    }
    i=l;
    j=l << 1;
    while (j<=ir) {
      if (j < ir && arr[indx[j]] < arr[indx[j+1]]) j++;
      if (q < arr[indx[j]]) {
        indx[i]=indx[j];
        j += (i=j);
      } else j=ir+1;
    }
    indx[i]=indxt;
  }
}