import os
import re
import subprocess as sp

from ta_common import tabin
from ta_common import util

locdbfile = '../daqDB/locations-20141104.txt'

def validate_raw(dst, expected):
  '''
  Check that the TAMA output DST meets expectations about
  the number of included triggers.
  
  Run dstdump on dst, finding lines with times.
  Return the number of such lines, the difference between first and last
  times, the size of the file, and whether the file had any problems.
  '''

  try:
    size = os.path.getsize(dst)
  except OSError:
    print 'File appears not to exist: ' + dst
    return None
    
  
  # run dstdump on the dst file, saving stdout and stderr separately
  cmd = [tabin.dstdump,'-brtime','-lrtime',dst]
  dump = sp.Popen(cmd,stdout=sp.PIPE,stderr=sp.PIPE)
  
  out = dump.stdout.read()
  err = dump.stderr.readlines()
  
  # count the number of events by counting printed trigger times
  times = re.findall('\d{6}\.\d{9}',out)
  
  # ...and find the difference between first and last events.
  dtimes = util.hms2sec(times[-1]) - util.hms2sec(times[0])
  
  # Look for any messages in stdout other than "End of input file"
  for line in err:
    if 'End of input file' in line:
      err.remove(line)
      break
      
  bad = 1 if len(err) > 0 or (len(times) != expected) else 0
  
  return (len(times),dtimes,size,bad)
  
def run_tama(daqID,locdb=None):
  if not locdb:
    locdb = util.read_loc_db(locdbfile)
  
  daq0 = locdb.get(daqID,False)
  if not daq0:
    print 'No files found for part ' + daqID
  else:
    print 'This function will eventually run tama on files related to ' + daq0
  
  return None
