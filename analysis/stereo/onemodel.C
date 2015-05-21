/* onemodel.C
 * Thomas Stroman, University of Utah, 2015-05-21
 * This ROOT macro is designed to load the output of a single analysis
 * into an interactive session ("CINT") for exploration with minimal
 * additional processing.
 * 
 * For convenience with variable scope, this is not a named macro.
 * The downside is that the filename to be read must be hard-coded
 * into the macro at execution time, rather than passed as an argument.
 */

{
  // hard-code the input filename here.
  char infile[1024] = "/data/stereo/data/20150520/gdas_j1.4.qgsjetii-03.width1-mdghd.TupleProf.nature_mc-proton0_mc-iron0.root";
  
  // load the infile and print its contents to the screen.
  TFile *model = new TFile(infile);
  model->GetListOfKeys()->Print();
  
  
  
  // USE_PRA tells the code how to incorporate or ignore the
  // third-party pattern-recognition analysis cuts, if available.
  // USE_PRA = 0: do not use
  //           1: require for all events
  //           2: require for single-profile events
  
  int USE_PRA = 0;
  
  // now we can load the standard set of quality cuts.
#include "cuts.h"  
  
  // to save processing time in the future, store one-time analysis results
  // in a complementary file specific to this USE_PRA value. Insert .compN
  // before .root in the input filename to determine the comp filename.
  
  char compfile[1024];
  strcpy(compfile,infile);
  int l = strlen(compfile);
  strcpy(&compfile[l-5],Form(".comp%d.root",USE_PRA));
  
  // check for the existence of compfile. If it's missing, create it.
  if (gSystem->AccessPathName(compfile)) { // false if exists!
    printf("%s not found. Building...\n",compfile);
    
    // prepare to run one-time macros    
    TCut pcut[3] = {bprof, lprof, mprof};
    
    gROOT->LoadMacro("macro/buildTreeAnalysis.C+");
    gROOT->LoadMacro("macro/buildTreeRecon.C");
    
    // Each species in model has its own TTree with one of these names:
#define NSPEC 5
    char treeNames[NSPEC][10] = {"f","g","h","n","he"};
    
    for (int s=0; s<NSPEC; s++) {
      // check to see if this species is present, and assign it to t.
      model->cd(); // reset "working directory" in between writes
      TTree *t = (TTree*)gROOT->FindObject(treeNames[s]);
      if ( t == NULL)
        continue;
      
      // First, build the "analysis" helper tree.
      TTree *a = buildTreeAnalysis(t);
      
      // Analysis helper tree is needed for "reconstruction" helper tree.
      t->AddFriend(a,"a");     
      TTree *r = buildTreeRecon(t);
      t->RemoveFriend(a);
      
      // now write these to a file. "UPDATE" means append.
      TFile *fp = new TFile(compfile,"UPDATE");
      a->Write(Form("a%s",treeNames[s]));
      r->Write(Form("r%s",treeNames[s]));
      fp->Close();
      delete fp;
    }
    printf("Done building %s\n",compfile);
  }
  
  
  
  
  
}