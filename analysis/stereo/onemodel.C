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
  
    // Each species in model has its own TTree with one of these names:
#define NSPEC 5
    char treeNames[NSPEC][10] = {"f","g","h","n","he"};  
    char longTreeNames[NSPEC][32] = {"nature","proton","iron","nitro","helium"};
    
  // A single analysis will have up to:
  
#define NTREE           5 

  // separate TTree objects, indexed by:
  
#define TUPLE           0
#define ANALYSIS        1
#define RECON           2
#define PROFILE         3
#define PRA             4
    
    
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
  

  
  


  // Array of TChains, one for each species.
  TChain *m[NSPEC][NTREE];
  
  for (int s=0; s<NSPEC; s++) {
    // grab the main "tuple" tree
    m[s][TUPLE] = new TChain(treeNames[s]);
    m[s][TUPLE]->Add(infile);
    
    // Go no further if species doesn't exist.
    // This method will throw an error message if the tree wasn't found,
    // but it's non-fatal and returns the desired zero.
    if (m[s][TUPLE]->GetEntries() == 0) {
      m[s][TUPLE] = NULL;
      continue;
    }
    
    
    // and the "profile" tree
    m[s][PROFILE] = new TChain(Form("%sprof",longTreeNames[s]));
    m[s][PROFILE]->Add(infile);
    m[s][TUPLE]->AddFriend(m[s][PROFILE],"p");
    
    if (USE_PRA > 0) {
      // grab PRA if needed/available...
      m[s][PRA] = new TChain(Form("%spra",treeNames[s]));
      m[s][PRA]->Add(infile);
      // ...and link it to TUPLE.
      m[s][TUPLE]->AddFriend(m[s][PRA],"pra");
    }
    
    // "analysis" tree
    m[s][ANALYSIS] = new TChain(Form("a%s",treeNames[s]));
    m[s][ANALYSIS]->Add(compfile);
    m[s][TUPLE]->AddFriend(m[s][ANALYSIS],"a");
    
    // and finally, "recon" tree
    m[s][RECON] = new TChain(Form("r%s",treeNames[s]));
    m[s][RECON]->Add(compfile);
    m[s][TUPLE]->AddFriend(m[s][RECON],"r");
  }
  
  // for convenience, assign shortcuts:
  // [d]ata, [h]ydrogen, [fe]rrum (iron), [n]itrogen, [he]lium
  
  TChain *d = m[0][TUPLE];
  TChain *h = m[1][TUPLE];
  TChain *fe = m[2][TUPLE];
  TChain *n = m[3][TUPLE];
  TChain *he = m[4][TUPLE];

  
}