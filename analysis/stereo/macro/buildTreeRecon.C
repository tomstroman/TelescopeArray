/* buildTreeRecon.C
 * Thomas Stroman, University of Utah 2015-05-19
 * This ROOT macro takes one TTree as an argument and returns
 * a new TTree with the results of some processing, based on
 * values in the input tree. The output tree can be added as 
 * a "friend" of the original TTree.
 * 
 * When called by another script, DO NOT COMPILE this. Example:
 * gROOT->LoadMacro("macro/buildTreeRecon.C"); // not '.C+");'
 * 
 * Expect Int_t USE_PRA to be defined.
 * Expect TCut cut, pcut[3] to be defined.
 */
#include "TROOT.h"
#include "TTree.h"
#include "TBranch.h"
#include "TLeaf.h"
#include "TCut.h"
#include "TEventList.h"

TTree *buildTreeRecon(TTree *t)/*, TCut *cut, TCut pcut[3], int USE_PRA)*/ {
//   printf("in buildTreeRecon for 0x%x.\n",t);
  printf("USE_PRA: %d. Cuts:\n",USE_PRA);
  t->GetListOfFriends()->Print();
  cut.Print();
  pcut[0].Print();
  pcut[1].Print();
  pcut[2].Print();
  
  TCut rcut = cut;
  TCut bprof = pcut[0];
  TCut lprof = pcut[1];
  TCut mprof = pcut[2];
  
  TTree *rt = new TTree();

  int i;
  TEventList *elist = new TEventList("elist","elist");
  
  int ngprof;
  double xmax, epri, ecal;
  double xmaxa[3];
  double epria[3], ecala[3];
  int nps;
  int onepra;
  
  int gprof[3][1000000] = {{0}};
//   
  rt->Branch("ngprof",&ngprof,"ngprof/I");
  rt->Branch("xmax",&xmax,"xmax/D");
  rt->Branch("xmax0",&xmaxa[0],"xmax0/D");
  rt->Branch("xmax1",&xmaxa[1],"xmax1/D");
  rt->Branch("xmax2",&xmaxa[2],"xmax2/D");
  rt->Branch("epri",&epri,"epri/D");
  rt->Branch("epri0",&epria[0],"epri0/D");
  rt->Branch("epri1",&epria[1],"epri1/D");
  rt->Branch("epri2",&epria[2],"epri2/D");
  rt->Branch("ecal",&ecal,"ecal/D");
  rt->Branch("ecal0",&ecala[0],"ecal0/D");
  rt->Branch("ecal1",&ecala[1],"ecal1/D");
  rt->Branch("ecal2",&ecala[2],"ecal2/D");
  rt->Branch("onepra",&onepra,"onepra/I");
  
  for (i=0; i<1000000; i++) {
    gprof[0][i] = gprof[1][i] = gprof[2][i] = 0;
  }
  printf("prior to first Draw\n");
  TCut cut0 = cut + "nps != 0" + pcut[0];
  TCut testcut = "nps != 0";
  t->Draw(">>elist",cut + pcut[0] + "nps != 0");
  printf("after first Draw\n");
  for (i=0; i<elist->GetN(); i++)
    gprof[0][elist->GetEntry(i)] = 1;
  
  t->Draw(">>elist",cut+"nps != 1" + pcut[1]);
  for (i=0; i<elist->GetN(); i++)
    gprof[1][elist->GetEntry(i)] = 1;
  
  t->Draw(">>elist",cut+"nps != 2" + pcut[2]);
  for (i=0; i<elist->GetN(); i++)
    gprof[2][elist->GetEntry(i)] = 1;
  
  for (i=0; i<t->GetEntries(); i++) {

    t->GetEntry(i);

    ngprof = 0;
    xmax = 0;
    epri = 0;
    ecal = 0;
    xmaxa[0] = xmaxa[1] = xmaxa[2] = 0;
    epria[0] = epria[1] = epria[2] = 0;
    ecala[0] = ecala[1] = ecala[2] = 0;
    if (gprof[0][i] == 1) {
      xmaxa[ngprof] = t->GetLeaf("bxmax")->GetValue();
      xmax += xmaxa[ngprof];
      epria[ngprof] = t->GetLeaf("bepri")->GetValue();
      epri += epria[ngprof];
      ecala[ngprof] = t->GetLeaf("becal")->GetValue();
      ecal += ecala[ngprof];
      ngprof++;
    }
    
    if (gprof[1][i] == 1) {
      xmaxa[ngprof] = t->GetLeaf("lxmax")->GetValue();
      xmax += xmaxa[ngprof];
      epria[ngprof] = t->GetLeaf("lepri")->GetValue();
      epri += epria[ngprof];
      ecala[ngprof] = t->GetLeaf("lecal")->GetValue();
      ecal += ecala[ngprof];
      ngprof++;        
    }
    
    if (gprof[2][i] == 1) {
      xmaxa[ngprof] = t->GetLeaf("mxmax")->GetValue();
      xmax += xmaxa[ngprof];
      epria[ngprof] = t->GetLeaf("mepri_rc")->GetValue();
      epri += epria[ngprof];
      ecala[ngprof] = t->GetLeaf("mecal")->GetValue();
      ecal += ecala[ngprof];
      ngprof++;
    }
    
    if (ngprof) {
      xmax /= ngprof;
      epri /= ngprof; 
      ecal /= ngprof;
//         if (USE_PRA==2) {

//         }
    }
    if (USE_PRA)
      onepra = (((gprof[0][i] == 1 && t->GetLeaf("bpra")->GetValue()==1) + (gprof[1][i] == 1 && t->GetLeaf("lpra")->GetValue()==1) + (gprof[2][i] == 1 && t->GetLeaf("mpra")->GetValue()==1))==1 && ngprof==1);
//     
//     
// //       printf("%d %d %f %f\n",i,ngprof,xmax,epri);
    rt->Fill();
//     printf("%d\n",i);
  }
  delete elist;
  printf("About to return.\n");
  return rt;
}