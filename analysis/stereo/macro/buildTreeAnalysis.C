/* buildTreeAnalysis.C
 * Thomas Stroman, University of Utah 2015-05-19
 * This ROOT macro takes one TTree as an argument and returns
 * a new TTree with the results of some processing, based on
 * values in the input tree. The output tree can be added as 
 * a "friend" of the original TTree.
 * 
 * When called by another script, COMPILE this. Example:
 * gROOT->LoadMacro("macro/buildTreeAnalysis.C+");
 * 
 */

#include "TROOT.h"
#include "TTree.h"
#include "TBranch.h"
#include "TLeaf.h"

TTree *buildTreeAnalysis(TTree *t) {
  TTree *at = new TTree();  
  int i;
  int id0, id1;
  int gtube0, gtube1;
  double ext0, ext1;
  double text0, text1, etext0, etext1;
  double tratio0, tratio1, ptratio;
  double time0, time1;
  double rp0, rp1;
  double psi0, psi1;
  char s0[2], s1[2];
  
  at->Branch("id0",&id0,"id0/I");
  at->Branch("id1",&id1,"id1/I");
  
  at->Branch("gtube0",&gtube0,"gtube0/I");
  at->Branch("gtube1",&gtube1,"gtube1/I");  
  
  at->Branch("ext0",&ext0,"ext0/D");
  at->Branch("ext1",&ext1,"ext1/D");    
  
  at->Branch("text0",&text0,"text0/D");
  at->Branch("text1",&text1,"text1/D");  
  at->Branch("etext0",&etext0,"etext0/D");
  at->Branch("etext1",&etext1,"etext1/D");  
  
  at->Branch("tratio0",&tratio0,"tratio0/D");
  at->Branch("tratio1",&tratio1,"tratio1/D");
  at->Branch("ptratio",&ptratio,"ptratio/D");
  
  at->Branch("time0",&time0,"time0/D");
  at->Branch("time1",&time1,"time1/D");
  
  at->Branch("rp0",&rp0,"rp0/D");
  at->Branch("rp1",&rp1,"rp1/D");
  
  at->Branch("psi0",&psi0,"psi0/D");
  at->Branch("psi1",&psi1,"psi1/D");
  
  
  for (i=0; i<t->GetEntries(); i++) {
    t->GetEntry(i);
    switch((int)t->GetLeaf("pcnps")->GetValue()) {
      case 0:
        id0 = 1;
        id1 = 2;
        sprintf(s0,"l");
        sprintf(s1,"m");
        break;
      case 1:
        sprintf(s0,"b");
        sprintf(s1,"m");
        id0 = 0;
        id1 = 2;
        break;
      case 2:
        id0 = 0;
        id1 = 1;
        sprintf(s0,"b");
        sprintf(s1,"l");
    }

    gtube0 = t->GetLeaf(Form("%sgtube",s0))->GetValue();
    gtube1 = t->GetLeaf(Form("%sgtube",s1))->GetValue();
    ext0 = t->GetLeaf(Form("%sext",s0))->GetValue();
    ext1 = t->GetLeaf(Form("%sext",s1))->GetValue();
    text0 = t->GetLeaf(Form("%stext",s0))->GetValue();
    text1 = t->GetLeaf(Form("%stext",s1))->GetValue();
    etext0 = t->GetLeaf(Form("%setext",s0))->GetValue();
    etext1 = t->GetLeaf(Form("%setext",s1))->GetValue();
    tratio0 = text0/etext0;
    tratio1 = text1/etext1;
    ptratio = tratio0*tratio1;
    time0 = t->GetLeaf(Form("%stime",s0))->GetValue();
    time1 = t->GetLeaf(Form("%stime",s1))->GetValue();
    rp0 = t->GetLeaf(Form("%srp",s0))->GetValue();
    rp1 = t->GetLeaf(Form("%srp",s1))->GetValue();
    psi0 = t->GetLeaf(Form("%spsi",s0))->GetValue();
    psi1 = t->GetLeaf(Form("%spsi",s1))->GetValue();

    at->Fill();
  }  
  
  
  return at;
}