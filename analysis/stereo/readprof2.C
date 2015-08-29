/* readprof.C
 * Thomas Stroman, University of Utah, 2015-05-18
 * This ROOT macro can be run from the command line and takes two arguments:
 * an ASCII file generated during data processing and preparation (infile),
 * and a descriptive phrase (outname) that will be used twice: once as the
 * name of the TTree object written to disk, and again (with ".root"
 * appended) as the name of the output file.
 * 
 * This program is called by prepare-input.py. It is not designed to handle
 * malformed input robustly.
 */


#include "TROOT.h"
#include "TTree.h"
#include "TFile.h"

int readprof(const char* infile, const char* outname) {
  
  if (!strlen(infile) || !strlen(outname)) {
    fprintf(stderr,"error: missing infile (%s) and/or outname (%s)\n",infile,outname);
    return -1;
  }
  
  
  char line[1024];
  char *tok;
  
  int ymd, brid, lrid, mdid,bgtube,lgtube,mgbin,nps,pcnps,bstat,lstat,mstat;
  float bchi2,lchi2,mchi2;
  
  
  
  
  int site, nstep;
  
#define NSTEPS 10000
  int bindex[NSTEPS],lindex[NSTEPS];
  int bcam[NSTEPS],lcam[NSTEPS];
  int btube[NSTEPS],ltube[NSTEPS];
  float bx[NSTEPS], lx[NSTEPS], mx[NSTEPS];
  float bflux[NSTEPS], lflux[NSTEPS],mflux[NSTEPS];
  float ebflux[NSTEPS], elflux[NSTEPS], emflux[NSTEPS];
  float bsimflux[NSTEPS], lsimflux[NSTEPS], msimflux[NSTEPS];
  
  float balt[NSTEPS], bazm[NSTEPS], bpalt[NSTEPS], bpazm[NSTEPS], bnpe[NSTEPS];
  float lalt[NSTEPS], lazm[NSTEPS], lpalt[NSTEPS], lpazm[NSTEPS], lnpe[NSTEPS];
  float malt[NSTEPS], mazm[NSTEPS], mpalt[NSTEPS], mpazm[NSTEPS], mnpe[NSTEPS];
  TTree *p = new TTree("p","");
  p->Branch("ymd",&ymd,"ymd/I");
  p->Branch("brid",&brid,"brid/I");
  p->Branch("lrid",&lrid,"lrid/I");
  p->Branch("mdid",&mdid,"mdid/I");
  p->Branch("bgtube",&bgtube,"bgtube/I");
  p->Branch("lgtube",&lgtube,"lgtube/I");
  p->Branch("mgbin",&mgbin,"mgbin/I");
  p->Branch("bstat",&bstat,"bstat/I");
  p->Branch("lstat",&lstat,"lstat/I");
  p->Branch("mstat",&mstat,"mstat/I");
  p->Branch("bindex",bindex,"bindex[bgtube]/I");
  p->Branch("bcam",bcam,"bcam[bgtube]/I");
  p->Branch("btube",btube,"btube[bgtube]/I");
  p->Branch("bx",bx,"bx[bgtube]");
  p->Branch("bflux",bflux,"bflux[bgtube]");
  p->Branch("ebflux",ebflux,"ebflux[bgtube]");
  p->Branch("bsimflux",bsimflux,"bsimflux[bgtube]");
  p->Branch("balt",balt,"balt[bgtube]");
  p->Branch("bazm",bazm,"bazm[bgtube]");
  p->Branch("bpalt",bpalt,"bpalt[bgtube]");
  p->Branch("bpazm",bpazm,"bpazm[bgtube]");
  p->Branch("bnpe",bnpe,"bnpe[bgtube]");
  p->Branch("lindex",lindex,"lindex[lgtube]/I");
  p->Branch("lcam",lcam,"lcam[lgtube]/I");
  p->Branch("ltube",ltube,"ltube[lgtube]/I");
  p->Branch("lx",lx,"lx[lgtube]");
  p->Branch("lflux",lflux,"lflux[lgtube]");
  p->Branch("elflux",elflux,"elflux[lgtube]");
  p->Branch("lsimflux",lsimflux,"lsimflux[lgtube]");    
  p->Branch("lalt",lalt,"lalt[lgtube]");
  p->Branch("lazm",lazm,"lazm[lgtube]");
  p->Branch("lpalt",lpalt,"lpalt[lgtube]");
  p->Branch("lpazm",lpazm,"lpazm[lgtube]");
  p->Branch("lnpe",lnpe,"lnpe[lgtube]"); 
  p->Branch("mx",mx,"mx[mgbin]");
  p->Branch("mflux",mflux,"mflux[mgbin]");
  p->Branch("msimflux",msimflux,"msimflux[mgbin]");
  p->Branch("emflux",emflux,"emflux[mgbin]");
  p->Branch("malt",malt,"malt[mgbin]");
  p->Branch("mazm",mazm,"mazm[mgbin]");
  p->Branch("mpalt",mpalt,"mpalt[mgbin]");
  p->Branch("mpazm",mpazm,"mpazm[mgbin]");
  p->Branch("mnpe",mnpe,"mnpe[mgbin]");  
  
  int i;
  FILE *fp = fopen(infile,"r");
  if (!fp) {
    fprintf(stderr,"Error: not found: %s\n",infile);
    return -1;
  }
  while (fgets(line,1000,fp)) {
    
//     printf(line);
    sscanf(line,"%d %d %d %d %d %d %d %d %d %d",
           &ymd, &brid, &lrid, &mdid,
           &bgtube, &lgtube, &mgbin,
           &bstat, &lstat, &mstat
           );
    
    fgets(line,1000,fp);
    sscanf(line,"%d %d",&site,&nstep);
    if (site != 0 || (nstep != bgtube && bstat>=0) ) {
      fprintf(stderr,"Error! BRM mismatch. %d != 0 or %d != %d\n",site,nstep,bgtube);
      break;
    }
    for (i=0; i<nstep; i++) {
      fgets(line,1000,fp);
      sscanf(line,"%d %d %d %f %e %e %e %f %f %f %f %f",
             &bindex[i], &bcam[i], &btube[i], &bx[i], &bflux[i], &bsimflux[i], &ebflux[i], &balt[i], &bazm[i], &bpalt[i], &bpazm[i], &bnpe[i]);      
    }

    fgets(line,1000,fp);
    sscanf(line,"%d %d",&site,&nstep);
    if (site != 1 || (nstep != lgtube && lstat>=0) ) {
      fprintf(stderr,"Error! LR mismatch.\n");
      break;
    }    
    for (i=0; i<nstep; i++) {
      fgets(line,1000,fp);
      sscanf(line,"%d %d %d %f %e %e %e %f %f %f %f %f",
             &lindex[i], &lcam[i], &ltube[i], &lx[i], &lflux[i], &lsimflux[i], &elflux[i], &lalt[i], &lazm[i], &lpalt[i], &lpazm[i], &lnpe[i]);      
    }    
    
    fgets(line,1000,fp);
    sscanf(line,"%d %d",&site,&nstep);
    if (site != 2 || nstep != mgbin) {
      fprintf(stderr,"Error! MD mismatch.\n");
      break;
    }    
    for (i=0; i<nstep; i++) {
      fgets(line,1000,fp);
      sscanf(line,"%f %e %e %e %f %f %f %f %f",
             &mx[i], &mflux[i], &msimflux[i], &emflux[i], &malt[i], &mazm[i], &mpalt[i], &mpazm[i], &mnpe[i]);      
    }
    
    
    p->Fill();
  }
  fclose(fp);
  TFile e(Form("%s.root",outname),"RECREATE");
  p->Write(outname);
  e.Close();
  return 0;
}