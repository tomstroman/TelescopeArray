import os
import re
import subprocess as sp

from ta_common import ta
from ta_common import tabin
from ta_common import util

daqdbfile = '../daqDB/logparts-20141104.txt'
locdbfile = '../daqDB/locations-20141104.txt'

def assess_tama(daqID,rebuild=0,locdb=None,daqdb=None):
  '''
  For a given part (uniquely identifed by daqID), determine whether
  to run TAMA. 
  
  If rebuild is nonzero, run TAMA to generate new output
  if possible. rebuild=1 means run TAMA for all files; rebuild=2 means
  attempt to skip good files and only rebuild problematic ones.
  
  if the locations database is already in memory, it can be passed in as an
  argument; otherwise, it may be loaded each time this is called.
  Likewise for the DAQ status database.
  
  Return type/value varies depending on actions taken. I haven't decided
  exactly how yet.
  '''

  # let's begin by checking the DAQ database. Is this part fully finished?
  if not daqdb:
    daqdb = util.read_daq_db(daqdbfile)

  daq = daqdb.get(daqID,{'cams': None})
  if not daq['cams']: # we know nothing about this part
    return None
        
  if ( not rebuild and not daq['nbad_dst'] 
      and daq['ntrig_dst'] == daq['ntrig_log'] ):
    return False # no bad parts and no problems
  
  # we got here, so there may be work to do. Now we figure out where
  # the raw-data source files are.
  if not locdb:
    locdb = util.read_loc_db(locdbfile)
  
  daq_tuple = locdb.get(daqID,False)
  
  if not daq_tuple:
    print 'No files found for part ' + daqID
    return None # this part is not known to exist on disk.
    
  # The part is not known to be complete, but data files exist. Let's see
  # what we need to do.
  
  # first, some metadata.
  ymd = daqID[0:8]
  part = daqID[8:10]
  site = int(daqID[10])  
  sitename = ta.sitenames[site]
  
  final_tama = '{0}{1}/{2}/{3}'.format(ta.tama,site,sitename,ymd)  
  tcfile = final_tama + '/' + util.timecorr(daqID)
  ecfile = final_tama + '/' + util.get_ecf(daq_tuple)
  
  # Perhaps there's nothing for us to do here and the database just
  # needs to be updated:
  if tama_complete(daqID,tcfile,ecfile) and not rebuild:
    return False    

  # having reached this point, we decide what to run.
  daq0 = daq_tuple[0]
  print 'This function will eventually run tama on files related to ' + daq0
  
  # this is where output will go, or might already exist
  tama_outdir = ta.localtama + '/{0}/{1}'.format(sitename,ymd)

  # this will have no effect if the directory already exists.
  os.system('mkdir -p ' + tama_outdir)
  
  # check for timecorr
  tcfile_temp = tama_outdir + '/' + os.path.basename(tcfile)
  tc_exists = os.path.exists(tcfile_temp)
  
  if not tc_exists: # it didn't exist, so let's create it
    tc_exists = get_timecorr(daq_tuple,tcfile_temp)
  
  if not tc_exists: # it still doesn't exist, so we surrender
    return None
  
  # timecorr exists. Let's identify the expected files 
  # for each 256-trigger segment. Also, name of DST output.
  
  infiles,dst = tama_data(daq,daq_tuple,site,tama_outdir)
  
  # generate a dict containing TAMA commands necessary to build this
  # entire part. Do not run it here, but return the dict.
        
  tama_cmd = {}        
  for segment in infiles.keys():
    tama_cmd[segment] = ['mosrun -q -b -l -m320 -e']
    tama_cmd[segment] += [tabin.tama,'-t','-o',dst[segment]]
    tama_cmd[segment] += infiles[segment]
    
  # TODO: check for existing output files if rebuild=2, and
  # remove the corresponding commands from tama_cmd
    
  return tama_cmd

  # end of assess_tama
  
  
def tama_complete(daqID,tcfile,ecfile):
  '''
  Look in the permanent location for TAMA output from part specified
  by daqID. 
  
  Return True if everything meets expectations.
  Return False if further processing may be needed.
  '''
  
  # count lines in the timecorr file or return False
  try:
    with open(tcfile) as tcf:
      ntrig_ctd = len(tcf.readlines())
  except IOError:
    return False
    
  # add up triggers listed in the eventcounts file or return False  
  ntrig_dst = 0
  bad_segments = []
  try:
    with open(ecfile) as ecf:
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
        daqID,os.path.dirname(tcfile),ntrig_ctd )
    return True
  else:
    print 'Warning! Part {0} mismatch. Expected {1}, found {2}.'.format(
        daqID,ntrig_ctd,ntrig_dst )
    print 'Segments marked as bad:'
    for seg in bad_segments:
      print seg
    return False

  # end of tama_complete  
  
  
def get_timecorr(daq_tuple,tcfile):
  '''
  Attempt to run the program that generates the timecorr file
  for a given part. Return True if creation was successful, else False.
  '''
  
  outdir = os.path.dirname(tcfile)
  
  daqID = ''.join([c for c in os.path.basename(tcfile) if c.isdigit()])
  
  site = daqID[10]
  
  
  # goal: extract 
  # /tadserv1/tafd/y2007m11d01/station0/ctd/event-data/DAQ-0110104
  # from 
  # /tadserv1/tafd/y2007m11d01/station0/ctd/event-data/DAQ-0110104-0-0000000.d.bz2
  
  head = '-'.join(daq_tuple[0].split('-')[:-2])
  
  
  cmd = [tabin.getTimeTable,site,outdir,head]
  sp.call(cmd)
  
  if os.path.exists(tcfile):
    return True
  else: 
    print 'Failed to create ' + tcfile
    return False  
  
  # end of get_timecorr
  
  
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

  
def tama_data(daq,daq_tuple,site,tama_outdir):
  '''
  Identify expected input and output data files for TAMA. Input files
  are predicted based on the contents of DAQ and location databases,
  and output DSTs are based on the location specified in ta_common.ta.
  Return infiles/outfiles dicts.
  '''
  files = {}
  dst = {}
  
  # a part is typically thousands of triggers, but stored in segments
  # up to 256 triggers in length.
  segments = ['{0:07d}'.format(i) for i in range(0,daq['ntrig_log'],256)]
  
  # which cameras were involved in the part, according to the log?
  cams = util.get_cam_list(daq['cams'])
  
  for segment in segments:
    # the output file for this segment
    dst[segment] = tama_outdir + '/DAQ-{0}-{1}-{2}.dst.gz'.format(
        daq_tuple[1],site,segment)
    
    # the input files: CTD, plus one for each camera
    ctd = daq_tuple[0][:-13] + segment + '.d.bz2'
    files[segment] = [ctd]
    files[segment] += [ ctd.replace('ctd','camera{0:02d}'.format(
        i)).replace(segment,'{0:1x}-{1}'.format(i,segment)) 
        for i in range(0,12) if cams[i] ]
  
  
  return files,dst
  # end of tama_data