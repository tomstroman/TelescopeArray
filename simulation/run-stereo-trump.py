# run-stereo-trump.py
# Thomas Stroman, University of Utah, 2015-05-28
# This script calls the TRUMP detector simulation program with any
# configuration files found in the location passed as the first argument.
# That program may take several hours to finish.

# Upon completion, this script performs some operations on the output,
# including data processing and, if a second argument requests it,
# the preparation and execution of a subsequent simulation using UTAFD.

import os
import sys
from ta_common import tabin

if len(sys.argv) == 1:
  print 'Usage: python',__file__,'/path/to/config_location'
  print '  assumes that config_location contains the .conf file(s)'
  sys.exit()


confloc = os.path.abspath(sys.argv[1])
binloc = '/'.join(confloc.split('/')[:-3]) + '/bin'

trump = binloc + '/trump.run'
if not os.path.exists(trump):
  print 'Error: trump.run not found in ' + binloc
  sys.exit()

try:  
  os.chdir(confloc)
except OSError: # NOTE: in python3, possibly a FileNotFoundError
  print 'Error:',confloc,'not found'
  sys.exit()
  
