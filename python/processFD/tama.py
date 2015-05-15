import os
import re
import subprocess as sp

from ta_common import tabin
from ta_common import util


def validate_raw(dst, expected):
  '''
  Check that the TAMA output DST meets expectations about
  the number of included triggers.
  
  Run dstdump on dst, finding lines with times.
  Return the number of such lines, the difference between first and last
  times, the size of the file, 
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
  
  
