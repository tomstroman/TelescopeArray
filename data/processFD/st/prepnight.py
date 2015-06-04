# prepnight.py
# Thomas Stroman, University of Utah, 2015-06-02
# Given a Night object, prepare it for stereo analysis. This includes:
# 0. Determine where to find "downward" monocular data from each FD site
# 1. Identify active sites this night
# 2. Create lists of downward-event timestamps
# 3. Ensure the output directory exists (create if necessary)

import os
import glob
import subprocess as sp
import re
from ta_common import ta
from ta_common import tabin
from ta_common import util

def prep(night):
  '''
  Perform the monocular-data preparation on one night's data. Return
  True for successful processing, False otherwise.
  '''
  # locate relevant directories
  mono_source(night)
  for key in ['down','data']:
    if not os.path.exists(night.dirs[key]):
      print('Error: missing ' + night.dirs[key])
      return False
      
  # ensure we have enough sites for stereo
  sites = count_sites(night)
  if sites < 2:
    print('Too few active FD sites on {0}; skipping.'.format(night.ymd))
    return False
    
  # make the downward-event lists
  create_downlists(night)
  for downlist in night.lists['down'].values():
    if not os.path.exists(downlist):
      print('Error: missing ' + downlist)
      return False
  
  # create the output directory for this night's stereo analysis
  try:
    os.mkdir(night.dirs['root'])
  except OSError as error:
    if 'File exists' in error:
      pass
    else:
      raise error
    
  return True

  
def mono_source(night):
  '''
  Determine where the processed monocular data is located. If it was produced
  by Monte Carlo simulation, it will be located within an already-existing
  directory for stereo analysis. But if it is real/nature data, it is located
  in a special standard location.
  '''
  
  outd = night.dirs['root']
  
  if night.source == 'nature':
    # 'down' contains mono-analysis output, and downward-event lists
    # should be made here.
    night.dirs['down'] = ta.fdplane

    # 'data' contains matched events, extracted from parent DST files 
    night.dirs['data'] = os.path.join(ta.stereo_root,
        night.calib,'tafd-data',night.ymd)
  else:
    night.dirs['down'] = os.path.pardir(outd)
    night.dirs['data'] = outd
    

def count_sites(night):
  '''
  Identify sites with monocular output available. Add locations to
  night.dirs['mono'] dict and return total.
  '''
  nsites = 0
  night.dirs['mono'] = {}
  
  # loop over site names and corresponding 2-letter abbreviations
  for s,sa in zip(ta.sitenames[:-1],ta.sa[:-1]):
    if night.source == 'nature':
      sitedir = os.path.join(night.dirs['data'],s,night.ymd)
    else:
      sitedir = os.path.join(night.dirs['data'],night.ymd,'trump',s)

    if os.path.exists(sitedir):
      night.dirs['mono'][sa] = sitedir
      nsites += 1
        
  return nsites


def create_BRLR_downlist(path):
  '''
  Given the path to a location of BRPLANE or LRPLANE DST files,
  create the list of downward-event times for stereo-matching.
  Return the list as a string.
  '''
  
  buf = ''
  
  # assemble and execute the dstdump command, capturing stdout and stderr
  dstfiles = sorted(glob.glob(path + '/*.down.dst.gz'))
  cmd = [tabin.dstdump,'-brplane','-lrplane'] + dstfiles
  dump = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
  
  out = dump.stdout.readlines()
  err = dump.stderr.read()

  if err != len(dstfiles) * tabin.dststderr:
    print('Warning! Non-trivial stderr from dstdump:')
    print(err)
    
  # keep track of events in each part, using a dict
  n = {}
  
  for line in out:
    if 'Part' in line:
      s = line.split()
      t = util.hms2sec(s[1])    # time
      p = int(s[4])             # part
      e = int(s[6])             # event code
      try:
        n[p] += 1
      except KeyError:
        n[p] = 1
      continue
    elif 'Angular' in line:
      l = line.split()[-1]      # track length
      buf += '{0:.9f} {1} {2} {3} {4}\n'.format(t,l,p,n[p]-1,e)
  
  return buf

def create_MD_downlist(path):
  '''
  Given the path to a location of HRAW1 and STPLN DST files,
  create the list of downward-event times for stereo-matching.
  Return the list as a string.
  '''
  
  buf = ''
  
  dstfiles = sorted(glob.glob(path + '/*.down.dst.gz'))

  for dst in dstfiles:
    n = 0
    
    # infer the part number PP from the filename yYYYYmMMdDDpPP.down.dst.gz
    pp = os.path.basename(dst)[12:14]
    
    cmd = [tabin.dstdump,'-hraw1','-stpln',dst]
    dump = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)

    out = dump.stdout.readlines()
    err = dump.stderr.read()
    
    if err != tabin.dststderr:
      print('Warning! Non-trivial stderr from dstdump:')
      print(err)
    
    # need to keep track of this to avoid multiple reports
    new_event = False
    for line in out:
      if 'stat' in line:
        # convert from Julian time to UTC time (12h difference)
        t = (util.hms2sec(line.split()[3]) + 43200) % 86400
        new_event = True
      elif 'tracklength' in line and new_event:
        l = line.split()[-1]
        n += 1
        buf += '{0:.9f} {1} {2} {3} {4}\n'.format(t,l,pp,n-1,n)
        new_event = False
        
  return buf 
    
def create_downlists(night):
  '''
  From a Night object, get the paths to individual sites' data
  and construct the downlists; if they exist and retry isn't specified,
  do nothing.
  '''
  night.lists['down'] = {}
  for site,path in night.dirs['mono'].items():
    # the desired output filename
    downlist = os.path.join(path,'downlist-{0}-{1}.txt'.format(
        ta.sa.index(site),night.ymd))    

    night.lists['down'][site] = downlist
    # unless we've specified full retry, don't re-create it
    if os.path.exists(downlist) and night.retry[site] < 2:
      continue
    
    if site == 'md':
      buf = create_MD_downlist(path)
    else:
      buf = create_BRLR_downlist(path)
    print('Writing ' + downlist)  
    
    with open(downlist,'w') as out:
      out.write(buf)
      
    

  
  
  