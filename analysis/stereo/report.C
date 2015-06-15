/* report.C
 * Thomas Stroman, University of Utah, 2015-06-15
 * ROOT script to generate a predetermined series of figures and arrange
 * them into a collection using the "Beamer" LaTeX presentation format.
 */

{
  // for now, hard-code the input name
  char infile[1024] = "/data/stereo/data/20150615/elko_j1.4.qgsjetii-03.ghdef-mdghd.TupleProf.nature_mc-proton0_mc-proton1_mc-iron0.root";  
  
  char latex_infile[1024];
  // LaTeX version of infile needs to escape the underscores
  int i = 0, k = 0;  
  for (i=0; i<strlen(infile); i++) {
    if (k > 1023) {
      fprintf(stderr,"Error: filename too close to 1024 characters\n");
      k = 1023;
      break;
    }
    if (infile[i] == '_')
      latex_infile[k++] = '\\';    
    latex_infile[k++] = infile[i];
  }
  latex_infile[k] = '\0';
  // the output will just be the input name but 
  // replacing .root with .report.tex
  char report[1024];
  sprintf(report,infile);
  sprintf(&report[strlen(report)-5],".report.tex");
  
  
  int USE_PRA = 0;
  
  gROOT->ProcessLine(".x onemodel.C");
  
  switch (USE_PRA) {
  case 0:
    all += Form("r.ngprof>=2 && weather(ymd) >= 1");
    break;
  case 1:
    all += Form("r.ngprof>=1 && weather(ymd) >= 1");
    break;
  case 2:
    all += Form("weather(ymd) >= 1 && (r.ngprof>=2 || (r.ngprof==1 && r.onepra==1))");
    break;
  }
  
  gROOT->LoadMacro("macro/weather.C+");
  gROOT->LoadMacro("macro/ghwr.C+");
  gROOT->LoadMacro("macro/edmc7.C");

  // open the report .tex file and give it a title page with the input filename
  FILE *rep = fopen(report,"w");
  fprintf(rep,"\\documentclass[aspectratio=169]{beamer}\n");
  fprintf(rep,"\\mode<presentation>\n");
  fprintf(rep,"\\begin{document}\n");
  fprintf(rep,"\\begin{frame}\n");
  fprintf(rep,"\\frametitle{%s}\n",latex_infile);
  fprintf(rep,"\\end{frame}\n");
  
  // TODO: add the output here.
  
  
  // close the report
  fprintf(rep,"\\end{document}\n");
  fclose(rep);
}