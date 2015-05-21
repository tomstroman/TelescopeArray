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
  
  // USE_PRA tells the code how to incorporate or ignore the
  // third-party pattern-recognition analysis cuts, if available.
  // USE_PRA = 0: do not use
  //           1: require for all events
  //           2: require for single-profile events
  
  int USE_PRA = 0;
  
  // to save processing time in the future, store one-time analysis results
  // in a complementary file specific to this USE_PRA value. Insert .compN
  // before .root in the input filename to determine the comp filename.
  
  char compfile[1024];
  strcpy(compfile,infile);
  int l = strlen(compfile);
  strcpy(&compfile[l-5],Form(".comp%d.root",USE_PRA));
  
  // load the infile and print its contents.
  TFile *model = new TFile(infile);
  model->GetListOfKeys()->Print();
}