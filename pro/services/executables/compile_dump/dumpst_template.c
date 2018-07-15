/* Syntax for compiling:
gcc -DRTDATA=\"$RTDATA\" -c dumpst.c -ggdb -I$TADSTINC -I$TRUMP/inc
gcc -o dumpst.run dumpst.o -L$TADSTLIB -ldst2k -L$GCCLIB -lm -lz -lbz2 -L$TRUMP/lib  -lraytrace -lairshower -ltoolbox 
grep BRANCH dumpst.c | gawk 'BEGIN {printf("char format[1024] = \"")} (NR > 3) {printf("%s:",$NF)} END {print "END\";\n"}' | sed "s/:END//g" > dumpst-format.h
grep BRANCH dumpst.c | gawk '(NR > 3) {printf("%s:",$NF)} END {print "END"}' | sed "s/:END//g" > dumpst-rootformat.txt
grep BRANCH dumpst.c | gawk 'NR > 3 {print NR-3,$NF}' > dumpst-columns.txt
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

#  define MEC_A0 _META_REPLACE_MEC_A0_
#  define MEC_A1 _META_REPLACE_MEC_A1_
#  define MEC_A2 _META_REPLACE_MEC_A2_

#define getMissingEnergyCorrection(LE) ((MEC_A0)+(MEC_A1)*(LE)+(MEC_A2)*(LE)*(LE))
// (1 - 0.045)/(1 - 0.05*0.045)
#define CONV_50KEV_TO_1MEV 0.95715359559
#define PRFCFIT 2

GaisserHillasParameters ghp;
double getEnergyByGram (double x);
  
int main(int argc, char *argv[]) {
  if (argc != 2) {
    fprintf(stdout,"COMPILED WITH DEDX_MODEL %d\n",DEDX_MODEL);
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
  fdtubeprofile_dst_common *mtp;
  
  sttubeprofile_dst_common *stp;

  
#define SBR 0
#define SLR 1
#define SMD 2
#define SST 3
  int mc = FALSE;  
  int isPresent[4] = {0};
  int isGood[4] = {0};
  
  

  
   
  int i, i0, rc = -1;

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
    
    i0 = (nps==0); // index of stplane bank entry to use
    mjlday2ymdsec((double)splane->juliancore[i0] + (double)splane->jseccore[i0]/86400 - MJLDOFF,&ymd,&sec);
    
    // event/reconstruction metadata
    fprintf(stdout,"%08d %07d %07d %07d %1d %1d %1d %d %d ",
        ymd,                                        // BRANCH ymd/I
        isPresent[SBR]?(bplane->part*100000 + bplane->event_num):0,  // BRANCH brid/I
        isPresent[SLR]?(lplane->part*100000 + lplane->event_num):0,  // BRANCH lrid/I
        isPresent[SMD]?(mplane->part*100000 + mplane->event_num):0,  // BRANCH mdid/I
        isPresent[SBR]?bplane->type:0,                      // BRANCH btype/I
        isPresent[SLR]?lplane->type:0,                      // BRANCH ltype/I
        isPresent[SMD]?mplane->type:0,                      // BRANCH mtype/I
        nps,                                         // BRANCH nps/I
        pcnps);                                      // BRANCH pcnps/I

    


    
    
    azm=atan2(-splane->showerVector[1],-splane->showerVector[0]);
    while (azm < 0.)
      azm += 2.*M_PI;
    
    cpyvec(splane->showerVector,as.trackuv);
    cpyvec(splane->impactPoint,as.impactv);
    
    // shower geometry (global) and core time per site
    fprintf(stdout,"%.3f %.3f %.3f %.3f %.3f %05d.%09d %05d.%09d %05d.%09d ",
            splane->impactPoint[0]/1000.,               // BRANCH xcore/D
            splane->impactPoint[1]/1000.,               // BRANCH ycore/D
            splane->sdp_angle[icomb]*R2D,                   // BRANCH sdpa/D
            acos(-splane->showerVector[2])*R2D,         // BRANCH zen/D
            azm*R2D,                                      // BRANCH azm/D
            isPresent[SBR]?((splane->jseccore[SBR]+43200) % 86400):0,
            isPresent[SBR]?splane->nanocore[SBR]:0,     // BRANCH btime/D
            isPresent[SLR]?((splane->jseccore[SLR]+43200) % 86400):0,
            isPresent[SLR]?splane->nanocore[SLR]:0,     // BRANCH ltime/D
            isPresent[SMD]?((splane->jseccore[SMD]+43200) % 86400):0,
            isPresent[SMD]?splane->nanocore[SMD]:0);     // BRANCH mtime/D    
    
    // per site: numbers of tubes, plane-fit quality, and track length
    fprintf(stdout,"%d %d %d %d %d %d %f %f %f %f %f %f ",       
            isPresent[SBR]?bplane->ntube:0,             // BRANCH btube/I
            isPresent[SBR]?bplane->ngtube:0,            // BRANCH bgtube/I
            isPresent[SLR]?lplane->ntube:0,             // BRANCH ltube/I
            isPresent[SLR]?lplane->ngtube:0,            // BRANCH lgtube/I
            isPresent[SMD]?mplane->ntube:0,             // BRANCH mtube/I
            isPresent[SMD]?mplane->ngtube:0,            // BRANCH mgtube/I
           isPresent[SBR]?bplane->sdp_chi2:0,                           // BRANCH bchi2/D
           isPresent[SLR]?lplane->sdp_chi2:0,                           // BRANCH lchi2/D
           isPresent[SMD]?mplane->sdp_chi2:0,                           // BRANCH mchi2/D
           isPresent[SBR]?(bplane->azm_extent*R2D):0,                     // BRANCH bext/D
           isPresent[SLR]?(lplane->azm_extent*R2D):0,                     // BRANCH lext/D
           isPresent[SMD]?(mplane->azm_extent*R2D):0);                     // BRANCH mext/D

    if (isPresent[SBR]) {
      bsdptheta = acos(bplane->sdp_n[2]);
      bsdpphi = atan2(bplane->sdp_n[1],bplane->sdp_n[0]);
    }
    else
      bsdptheta = bsdpphi = 0;
    
    if (isPresent[SLR]) {
      lsdptheta = acos(lplane->sdp_n[2]);
      lsdpphi = atan2(lplane->sdp_n[1],lplane->sdp_n[0]);
    }
    else
      lsdptheta = lsdpphi = 0;

    if (isPresent[SMD]) {
      msdptheta = acos(mplane->sdp_n[2]);
      msdpphi = atan2(mplane->sdp_n[1],mplane->sdp_n[0]);
    }
    else
      msdptheta = msdpphi = 0;    
    // per site: SDP normal in polar coordinates
    fprintf(stdout,"%f %f %f %f %f %f ",
            bsdptheta*R2D,                  // BRANCH bsdptheta/D
            bsdpphi*R2D,                    // BRANCH bsdpphi/D
            lsdptheta*R2D,                  // BRANCH lsdptheta/D
            lsdpphi*R2D,                    // BRANCH lsdpphi/D
            msdptheta*R2D,                  // BRANCH msdptheta/D
            msdpphi*R2D);                   // BRANCH msdpphi/D
    // per site: event duration and expected duration based on stereo geometry
    fprintf(stdout,"%f %f %f %f %f %f ",            
            isPresent[SBR]?bplane->time_extent:0,                        // BRANCH btext/D
            isPresent[SBR]?splane->expected_duration[SBR]:0,               // BRANCH betext/D
            isPresent[SLR]?lplane->time_extent:0,                        // BRANCH ltext/D
            isPresent[SLR]?splane->expected_duration[SLR]:0,               // BRANCH letext/D
            isPresent[SMD]?mplane->time_extent:0,                    // BRANCH mtext/D
            isPresent[SMD]?splane->expected_duration[SMD]:0);             // BRANCH metext/D

    // per site: in-plane shower geometry
    fprintf(stdout,"%f %f %f %f %f %f ",                
//             isPresent[SBR]?splane->rp[SBR]:0,                   // BRA~NCH brp/D 
//             isPresent[SBR]?(splane->psi[SBR]*R2D):0,                  // BRA~NCH bpsi/D
//             isPresent[SLR]?splane->rp[SLR]:0,                   // BRA~NCH lrp/D
//             isPresent[SLR]?(splane->psi[SLR]*R2D):0,                  // BRA~NCH lpsi/D
//             isPresent[SMD]?splane->rp[SMD]:0,                   // BRA~NCH mrp/D
//             isPresent[SMD]?(splane->psi[SMD]*R2D):0);                 // BRA~NCH mpsi/D
    
            isPresent[SBR]?getRpVector(geo[SBR],&as,dummy):0,          // BRANCH brp/D
            isPresent[SBR]?(getPsiAngle(geo[SBR],&as)*R2D):0,              // BRANCH bpsi/D            
            isPresent[SLR]?getRpVector(geo[SLR],&as,dummy):0,          // BRANCH lrp/D
            isPresent[SLR]?(getPsiAngle(geo[SLR],&as)*R2D):0,              // BRANCH lpsi/D
            isPresent[SMD]?getRpVector(geo[SMD],&as,dummy):0,          // BRANCH mrp/D
            isPresent[SMD]?(getPsiAngle(geo[SMD],&as)*R2D):0);              // BRANCH mpsi/D
    
    btp = (isPresent[SBR])?&brtubeprofile_:NULL;
    ltp = (isPresent[SLR])?&lrtubeprofile_:NULL;
    prfc = (isPresent[SMD])?&prfc_:NULL;
    
    double bx1, bx2, lx1, lx2, mx1, mx2;
    double bcenaz, bcenalt, lcenaz, lcenalt, mcenaz, mcenalt;


    double bnpedeg, lnpedeg, mnpedeg;
    double ballnpe, lallnpe, mallnpe;
    double bflux, bcvfrac, lflux, lcvfrac, mflux, mcvfrac;
    int b6sig, bg6sig, l6sig, lg6sig; 
    double sum;
    bnpedeg = 0;
    b6sig = bg6sig = 0;
    ballnpe = 0;
    bcenaz = 0;
    bcenalt = 0;   
    bx1 = bx2 = 0;
    
    
    int bmir = 0, bgmir = 0, lmir = 0, lgmir = 0, mmir = 0, mgmir = 0;
    int tubesInMir[14] = {0};
    int goodTubesInMir[14] = {0};
    
    bflux = bcvfrac = 0;
    if (isPresent[SBR] && bplane->ntube > 0) {
      bx1 = 1e9;
      bx2 = -1e9;
      
      sum = 0;
      for (i=0; i<bplane->ntube; i++) {
        tubesInMir[bplane->camera[i]]++;
        ballnpe += bplane->npe[i];
        if (bplane->sigma[i] >= 6.0)
          b6sig++;
        if (bplane->tube_qual[i] == TRUE) {
          goodTubesInMir[bplane->camera[i]]++;
          sum += bplane->npe[i];
          if (bplane->sigma[i] >= 6.0)
            bg6sig++;
          bcenaz += bplane->npe[i]*bplane->azm[i];
          bcenalt += bplane->npe[i]*bplane->alt[i];
        }
      }
      
      bcenaz /= (sum*D2R);
      bcenalt /= (sum*D2R);
      bnpedeg = sum/(bplane->azm_extent * R2D);
      
      for (i=0; i<btp->ntube; i++) 
        if (btp->tube_qual[0][i]) {
          bx1 = min(btp->x[0][i],bx1);
          bx2 = max(btp->x[0][i],bx2);
          bflux += btp->simflux[0][i];
          bcvfrac += (btp->ncvdir[0][i] + btp->ncvmie[0][i] + btp->ncvray[0][i]);
        }
      for (i=0; i<geo[SBR]->nmir; i++) {
  //       printf("BR mir %d: %d tubes (%d good)\n",i,tubesInMir[i],goodTubesInMir[i]);
        bmir += (tubesInMir[i] > 0);
        bgmir += (goodTubesInMir[i] > 0);
        tubesInMir[i] = 0;
        goodTubesInMir[i] = 0;
      }  
    }
    


    lnpedeg = 0;
    lallnpe = 0;
    l6sig = lg6sig = 0;
    lcenaz = 0;
    lcenalt = 0;
    lx1 = lx2 = 0;  
    lflux = lcvfrac = 0;
    if (isPresent[SLR] && lplane->ntube > 0) {
      lx1 = 1e9;
      lx2 = -1e9;

      sum = 0;
      for (i=0; i<lplane->ntube; i++) {
        tubesInMir[lplane->camera[i]]++;
        lallnpe += lplane->npe[i];
        if (lplane->sigma[i] >= 6.0)
          l6sig++;
        if (lplane->tube_qual[i] == TRUE) {
          goodTubesInMir[lplane->camera[i]]++;
          sum += lplane->npe[i];
          if (lplane->sigma[i] >= 6.0)
            lg6sig++;
          lcenaz += lplane->npe[i]*asin(sin(lplane->azm[i]));
          lcenalt += lplane->npe[i]*asin(sin(lplane->alt[i]));
        }
      }
      
      lcenaz /= (sum * D2R);
      lcenalt /= (sum * D2R);
      lnpedeg = sum/(lplane->azm_extent * R2D);
      
      for (i=0; i<ltp->ntube; i++) 
        if (ltp->tube_qual[0][i]) {
          lx1 = min(ltp->x[0][i],lx1);
          lx2 = max(ltp->x[0][i],lx2);
          lflux += ltp->simflux[0][i];
          lcvfrac += (ltp->ncvdir[0][i] + ltp->ncvmie[0][i] + ltp->ncvray[0][i]);
        }
      for (i=0; i<geo[SLR]->nmir; i++) {
  //       printf("LR mir %d: %d tubes (%d good)\n",i,tubesInMir[i],goodTubesInMir[i]);
        lmir += (tubesInMir[i] > 0);
        lgmir += (goodTubesInMir[i] > 0);
        tubesInMir[i] = 0;
        goodTubesInMir[i] = 0;
      }
    }
  
    
    mnpedeg = 0;
    mallnpe = 0;
    mcenaz = 0;
    mcenalt = 0;    
    mx1 = mx2 = 0;

    mflux = mcvfrac = 0;
    if (isPresent[SMD] && mplane->ntube > 0) {
      mx1 = 1e9;
      mx2 = -1e9;

      sum = 0;
      for (i=0; i<mplane->ntube; i++) {
        tubesInMir[mplane->camera[i]]++;
        if (mplane->tube_qual[i] == TRUE) {
          goodTubesInMir[mplane->camera[i]]++;
          sum += mplane->npe[i];
          mcenaz += mplane->npe[i]*mplane->azm[i];
          mcenalt += mplane->npe[i]*mplane->alt[i];
        }
      }
      
      mcenaz /= (sum * D2R);
      mcenalt /= (sum * D2R);
      mnpedeg = sum/(mplane->azm_extent * R2D);
      
      for (i=0; i<prfc->nbin[PRFCFIT]; i++) 
        if (prfc->ig[PRFCFIT][i]) {
          mx1 = min(prfc->dep[PRFCFIT][i],mx1);
          mx2 = max(prfc->dep[PRFCFIT][i],mx2);
          mflux += prfc->sigmc[PRFCFIT][i];
          mcvfrac += (prfc->crnk[PRFCFIT][i] + prfc->aero[PRFCFIT][i] + prfc->rayl[PRFCFIT][i]);
        }
      for (i=0; i<geo[SMD]->nmir; i++) {
  //       printf("LR mir %d: %d tubes (%d good)\n",i,tubesInMir[i],goodTubesInMir[i]);
        mmir += (tubesInMir[i] > 0);
        mgmir += (goodTubesInMir[i] > 0);
        tubesInMir[i] = 0;
        goodTubesInMir[i] = 0;
      }
    }
    // number of mirrors and good mirrors by site
    fprintf(stdout,"%d %d %d %d %d %d %d %d %d %d ",
            bmir,                                       // BRANCH bmir/I
            bgmir,                                      // BRANCH bgmir/I
            b6sig,                                      // BRANCH b6sig/I
            bg6sig,                                     // BRANCH bg6sig/I
            lmir,                                       // BRANCH lmir/I
            lgmir,                                      // BRANCH lgmir/I 
            l6sig,                                      // BRANCH l6sig/I
            lg6sig,                                     // BRANCH lg6sig/I
            mmir,                                       // BRANCH mmir/I
            mgmir);                                     // BRANCH mgmir/I
    
    // shower brightness and centroid location
    fprintf(stdout,"%f %f %f %f %f %f %f %f %f %f %f %f ",
            bnpedeg,                    // BRANCH bnpedeg/D
            ballnpe,                    // BRANCH ballnpe/D
            bcenalt,                    // BRANCH bcenalt/D
            bcenaz,                     // BRANCH bcenaz/D
            lnpedeg,                    // BRANCH lnpedeg/D
            lallnpe,                    // BRANCH lallnpe/D
            lcenalt,                    // BRANCH lcenalt/D
            lcenaz,                     // BRANCH lcenaz/D
            mnpedeg,                    // BRANCH mnpedeg/D
            mallnpe,                    // BRANCH mallnpe/D
            mcenalt,                    // BRANCH mcenalt/D
            mcenaz);                    // BRANCH mcenaz/D

    // first and last bin by grammage
    fprintf(stdout,"%f %f %f %f %f %f ",
            bx1,                        // BRANCH bx1/D
            bx2,                        // BRANCH bx2/D
            lx1,                        // BRANCH lx1/D
            lx2,                        // BRANCH lx2/D
            mx1,                        // BRANCH mx1/D
            mx2);                       // BRANCH mx2/D
    
    // finally some profile reconstruction!
    // status and chi-squared
    fprintf(stdout,"%d %d %d %f %f %f ",
            isPresent[SBR]?btp->status[0]:-9,           // BRANCH bstat/I
            isPresent[SLR]?ltp->status[0]:-9,           // BRANCH lstat/I
            isPresent[SMD]?prfc->failmode[PRFCFIT]:-9,   // BRANCH mstat/I
            isPresent[SBR]?btp->chi2[0]:0,              // BRANCH bpchi2/D
            isPresent[SLR]?ltp->chi2[0]:0,              // BRANCH lpchi2/D
            (isPresent[SMD] && !prfc->failmode[PRFCFIT])?(prfc->chi2[PRFCFIT]/prfc->ndf[PRFCFIT]):0); // BRANCH mpchi2/D
    
    // Cherenkov fraction
    fprintf(stdout,"%f %f %f ",
            isPresent[SBR]?bcvfrac/bflux:0,                   // BRANCH bcvfrac/D
            isPresent[SLR]?lcvfrac/lflux:0,                   // BRANCH lcvfrac/D
            isPresent[SMD]?mcvfrac/mflux:0);                  // BRANCH mcvfrac/D
    
    // Gaisser-Hillas parameters and errors, calorimetric energy, corrected energy
    if (isPresent[SBR]) {
      
      if ((btp->Nmax[0] - btp->Nmax[0]) != 0) {
        btp->Nmax[0] = 0;
        btp->Energy[0] = 0;
      }
      
      fprintf(stdout,"%f %f %f %f %f %f %f %f %f %f ",
              btp->Nmax[0]?log10(btp->Nmax[0]):0,                      // BRANCH bnmax/D
              btp->Nmax[0]?(btp->eNmax[0]/(btp->Nmax[0]*log(10.))):0,    // BRANCH ebnmax/D
              btp->Xmax[0],                             // BRANCH bxmax/D
              btp->eXmax[0],                            // BRANCH ebxmax/D
              btp->X0[0],                               // BRANCH bx0/D
              btp->eX0[0],                              // BRANCH ebx0/D
              btp->Lambda[0],                           // BRANCH blam/D
              btp->eLambda[0],                          // BRANCH eblam/D
              btp->Nmax[0]?log10(btp->Energy[0]):0,                    // BRANCH becal/D
              btp->Nmax[0]?(log10(btp->Energy[0]) -
              log10(getMissingEnergyCorrection(log10(btp->Energy[0])))):0); // BRANCH bepri/D
    }
    else
      fprintf(stdout,"0 0 0 0 0 0 0 0 0 0 ");
    
    if (isPresent[SLR]) {
      if ((ltp->Nmax[0] * 0) != 0) {
        fprintf(stderr,"INF/NAN detected in LR\n");
        ltp->Nmax[0] = 0;
        ltp->Energy[0] = 0;
      }
      fprintf(stdout,"%f %f %f %f %f %f %f %f %f %f ",
              ltp->Nmax[0]?log10(ltp->Nmax[0]):0,                      // BRANCH lnmax/D
              ltp->Nmax[0]?(ltp->eNmax[0]/(ltp->Nmax[0]*log(10.))):0,    // BRANCH elnmax/D
              ltp->Xmax[0],                             // BRANCH lxmax/D
              ltp->eXmax[0],                            // BRANCH elxmax/D
              ltp->X0[0],                               // BRANCH lx0/D
              ltp->eX0[0],                              // BRANCH elx0/D
              ltp->Lambda[0],                           // BRANCH llam/D
              ltp->eLambda[0],                          // BRANCH ellam/D
              ltp->Nmax[0]?log10(ltp->Energy[0]):0,     // BRANCH lecal/D
              ltp->Nmax[0]?(log10(ltp->Energy[0]) -
              log10(getMissingEnergyCorrection(log10(ltp->Energy[0])))):0); // BRANCH lepri/D
    }
    else
      fprintf(stdout,"0 0 0 0 0 0 0 0 0 0 ");
    
    if (isPresent[SMD]) {
      if (prfc->failmode[PRFCFIT] == 0) {
        ghp.nmax = prfc->szmx[PRFCFIT]*CONV_50KEV_TO_1MEV;
        ghp.xmax = prfc->xm[PRFCFIT];
        ghp.x0 = prfc->x0[PRFCFIT];
        ghp.lambda = prfc->lambda[PRFCFIT];
        mecal = qsimp(getEnergyByGram, 0., 5000., 1.e-3);
      }
      else
        mecal = 0;
      fprintf(stdout,"%f %f %f %f %f %f %f %f %f %f %f ",
              prfc->szmx[PRFCFIT]?log10(prfc->szmx[PRFCFIT]*CONV_50KEV_TO_1MEV):0,                      // BRANCH mnmax/D
              prfc->szmx[PRFCFIT]?(0.5*fabs(prfc->rszmx[PRFCFIT]-prfc->lszmx[PRFCFIT])/(prfc->szmx[PRFCFIT]*log(10.))):0,    // BRANCH emnmax/D
              prfc->xm[PRFCFIT],                             // BRANCH mxmax/D
              0.5*fabs(prfc->rxm[PRFCFIT]-prfc->lxm[PRFCFIT]),                            // BRANCH emxmax/D
              prfc->x0[PRFCFIT],                               // BRANCH mx0/D
              0.5*fabs(prfc->rx0[PRFCFIT]-prfc->lx0[PRFCFIT]),                              // BRANCH emx0/D
              prfc->lambda[PRFCFIT],                           // BRANCH mlam/D
              0.5*fabs(prfc->rlambda[PRFCFIT]-prfc->llambda[PRFCFIT]),                          // BRANCH emlam/D
              prfc->szmx[PRFCFIT]?(log10(prfc->eng[PRFCFIT])+18.):0,                    // BRANCH mecal_rc/D
              prfc->szmx[PRFCFIT]?log10(mecal):0,                                    // BRANCH mecal/D
              prfc->szmx[PRFCFIT]?(log10(mecal) -
              log10(getMissingEnergyCorrection(log10(mecal)))):0);//BRANCH mepri/D
    }
    else
      fprintf(stdout,"0 0 0 0 0 0 0 0 0 0 0 ");    


    if (mc) {
      azm=atan2(-tmc->showerVector[1],-tmc->showerVector[0]);
      while (azm < 0.)
        azm += 2.*M_PI;
      
      cpyvec(tmc->showerVector,as.trackuv);
      cpyvec(tmc->impactPoint,as.impactv);
      switch(pcnps) {
        case 0:
          getRpVector(geo[SLR],&as,dummy);          
          getSDPNVector(dummy,as.trackuv,nplnA);
          getRpVector(geo[SMD],&as,dummy);          
          break;
        case 1:
          getRpVector(geo[SBR],&as,dummy);          
          getSDPNVector(dummy,as.trackuv,nplnA);
          getRpVector(geo[SMD],&as,dummy);          
          break;          
        case 2:
          getRpVector(geo[SBR],&as,dummy);          
          getSDPNVector(dummy,as.trackuv,nplnA);
          getRpVector(geo[SLR],&as,dummy);          
          break;
      }
      getSDPNVector(dummy,as.trackuv,nplnB);
      unitVector(nplnA,nplnA);
      unitVector(nplnB,nplnB);
      fprintf(stdout,"%7.3f %7.3f %8.3f %8.3f %8.3f %5d.%09d ",              
              tmc->impactPoint[0]/1000.,                // BRANCH xcore_mc/D
              tmc->impactPoint[1]/1000.,                // BRANCH ycore_mc/D
              acos(dotProduct(nplnA,nplnB))*R2D,            // BRANCH sdpa_mc/D
              acos(-tmc->showerVector[2])*R2D,          // BRANCH zen_mc/D
              azm*R2D,                                    // BRANCH azm_mc/D
              (tmc->jsec+43200) % 86400,tmc->nano);      // BRANCH ttime/D
      fprintf(stdout,"%f %f %f %f ",
              acos(nplnA[2])*R2D,                       // BRANCH sdptheta0_mc/D
              atan2(nplnA[1],nplnA[0])*R2D,             // BRANCH sdpphi0_mc/D
              acos(nplnB[2])*R2D,                       // BRANCH sdptheta1_mc/D
              atan2(nplnB[1],nplnB[0])*R2D);            // BRANCH sdpphi1_mc/D
      fprintf(stdout,"%7.2f %7.2f %7.2f %6.2f %6.2f %6.2f ",
              getRpVector(geo[SBR],&as,dummy),          // BRANCH brp_mc/D
              getRpVector(geo[SLR],&as,dummy),          // BRANCH lrp_mc/D
              getRpVector(geo[SMD],&as,dummy),          // BRANCH mrp_mc/D
              getPsiAngle(geo[SBR],&as)*R2D,              // BRANCH bpsi_mc/D
              getPsiAngle(geo[SLR],&as)*R2D,              // BRANCH lpsi_mc/D
              getPsiAngle(geo[SMD],&as)*R2D);              // BRANCH mpsi_mc/D
      
      fprintf(stdout,"%d %f %f %f %f %f\n",
              tmc->primary,                             // BRANCH spec/I
              log10(tmc->energy),                       // BRANCH epri_mc/D
              tmc->ghParm[0],                           // BRANCH x0_mc/D
              tmc->ghParm[1],                           // BRANCH xmax_mc/D
              log10(tmc->ghParm[2]),                    // BRANCH nmax_mc/D
              tmc->ghParm[3]                            // BRANCH lambda_mc/D
             );
    }
    else {
      fprintf(stdout,"-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1\n");
    }
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
