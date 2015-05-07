// Tom Stroman, University of Utah, 2015-05-07
// ROOT script for generating graphical reports on DAQ data.
// This will ignore empty DAQ parts or parts with incomplete processing.
// So far, no tasks are performed beyond reading the file into memory, for
// exploration via the interactive interpreter.

{
  infile = "logparts-20141104.txt";
  format = "daqID/l:cams/i:tlog:tctd:nbad:ndst:nsec/F:nbyte/l:jt0/F:nmin/i:ndown:badcal";
  
  TTree *data = new TTree();
  data->SetMarkerStyle(kFullDotSmall);
  data->ReadFile(infile,format);
  
}
   