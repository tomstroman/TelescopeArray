# prepnight.py
# Thomas Stroman, University of Utah, 2015-06-02
# Given a Night object, prepare it for stereo analysis. This includes:
# 0. Determine where to find "downward" monocular data from each FD site
# 1. Identify active sites this night
# 2. Ensure the output directory exists (create if necessary)
# 3. Create lists of downward-event timestamps

import os
import glob
import subprocess as sp
import re
from ta_common import ta
from ta_common import tabin
from ta_common import util

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
  
  # assemble and execute the dstdump command, capturing stdout and stderr
  dstfiles = sorted(glob.glob(path + '/*.down.dst.gz'))
  cmd = [tabin.dstdump,'-brplane','-lrplane'] + dstfiles
  dump = sp.Popen(cmd,stderr=sp.PIPE,stdout=sp.PIPE)
  
  out = dump.stdout.readlines()
  err = dump.stderr.read()

  # keep track of events in each part, using a dict
  n = {}
  
  buf = ''
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

  