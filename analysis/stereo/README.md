#analysis/stereo

Code in this directory is specifically for analyzing the output of the
"stereo" data processing sequence, which runs on a University of Utah
computing cluster. When that output is downloaded to a system where it will
be analyzed, the various Python and ROOT scripts here form the building
blocks of the analysis.

##Main routines

These are the programs that can be run from the command line. 
Files not described here, such as those in the "macro" directory,
 are supplemental.

###prepare-input.py

Code that runs once, supervising the conversion of ASCII-formatted data
from the processing cluster into faster ROOT-formatted data to be used
by the analysis routines.

###onemodel.C

ROOT code that loads a single output file (from prepare-input.py) into
an interactive ROOT session for easy exploration and assessment. Although
the comments indicate where to add code for convenience, it's a good idea
to copy this routine to a new file before modifying it.


