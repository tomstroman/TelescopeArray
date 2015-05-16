import os
import re
import subprocess as sp

from ta_common import ta
from ta_common import tabin
from ta_common import util

locdbfile = '../daqDB/locations-20141104.txt'

def assess_tama(daqID,rebuild=0,locdb=None):
  '''
  For a given part (uniquely identifed by daqID), determine whether
  to run TAMA. 
  
  If rebuild is nonzero, run TAMA to generate new output
  if possible. rebuild=1 means run TAMA for all files; rebuild=2 means
  attempt to skip good files and only rebuild problematic ones.
  
  if the locations database is already in memory, it can be passed in as an
  argument; otherwise, it will be loaded each time this is called.
  
  Return type/value varies depending on actions taken. I haven't decided
  exactly how yet.
  '''
  
  if not locdb:
    locdb = util.read_loc_db(locdbfile)
  
  daq_tuple = locdb.get(daqID,False)
  
  if not daq_tuple:
    print 'No files found for part ' + daqID
    return None
  
  tcfile = util.timecorr(daqID)
  ecfile = util.get_ecf(daq_tuple)
  
  if tama_complete(daqID,tcfile,ecfile) and not rebuild:
    return False    
    
  daq0 = daq_tuple[0]
  print 'This function will eventually run tama on files related to ' + daq0
  

  
  
  ymd = daqID[0:8]
  part = daqID[8:10]
  site = int(daqID[10])
  

  
  timecorr = util.timecorr(daqID)
      
    
  
  return None

def tama_complete(daqID,tcfile,ecfile):
  '''
  Look in the permanent location for TAMA output from part specified
  by daqID. 
  
  Return True if everything meets expectations.
  Return False if further processing may be needed.
  '''
  ymd = daqID[0:8]
  part = daqID[8:10]
  site = int(daqID[10])  
  
  final_tama = '{0}{1}/{2}/{3}'.format(ta.tama,site,ta.sitenames[site],ymd)
  
  # Quit now if permanent output location doesn't exist
  if not os.path.exists(final_tama):
    return False
  
  final_timecorr = final_tama + '/' + tcfile
  final_ecounts = final_tama + '/' + ecfile 
  
    
  
  # count lines in the timecorr file or return False
  try:
    with open(final_timecorr) as tcf:
      ntrig_ctd = len(tcf.readlines())
  except IOError:
    return False
    
  # add up triggers listed in the eventcounts file or return False  
  ntrig_dst = 0
  bad_segments = []
  try:
    with open(final_ecounts) as ecf:
      ec = ecf.readlines()
      for line in ec:
        l = line.split()
        ntrig_dst += int(l[1])
        if l[-1]=='1':
          bad_segments.append(l[0])
  except IOError:
    return False      
  
  # return True if they match, or else report on mismatch and return False.
  if ntrig_ctd == ntrig_dst:
    print '{0} in {1} is complete (triggers: {2})'.format(
        daqID,final_tama,ntrig_ctd )
    return True
  else:
    print 'Warning! Part {0} mismatch. Expected {1}, found {2}.'.format(
        daqID,ntrig_ctd,ntrig_dst )
    print 'Segments marked as bad:'
    for seg in bad_segments:
      print seg
    return False

  # end of tama_complete  
  
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
  
  #end of validate_raw
