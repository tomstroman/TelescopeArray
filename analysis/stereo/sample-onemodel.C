/* sample-onemodel.C, 2015-05-21
 * Provide an example for using onemodel.C in the context of code that
 * will override its hard-coded input and do something with its output.
 * In this example, infile and USE_PRA are specified, and then
 * an additional macro is loaded.
 */

{ 
  char infile[1024] = "/data/stereo/data/20150518/gdas_j1.4.qgsjetii-03.ghdef-mddef.TupleProf.nature_mc-proton0_mc-iron0.root";
  int USE_PRA = 0;
  
  gROOT->ProcessLine(".x onemodel.C");
  
  gROOT->LoadMacro("macro/ghwr.C+");
  
  
}