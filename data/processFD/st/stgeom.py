# stgeom.py
# Thomas Stroman, University of Utah, 2015-06-04
# Calculate the geometry of stereo events in the FD data. This mainly consists
# of running the stplane executable, with some special preparation beforehand
# in some cases, and a little more analysis in some cases to decide when
# multiple geometries are available.

import os
import glob
import re
from ta_common import ta

def get_stereo_geometries(night):
  '''
  Go through all site combinations and events in night, calculating the
  stereo geometry.
  '''
  for comb,path in night.dirs['st'].items():
    # list all DST files already in the directory:
    all_dsts = sorted(glob.glob(os.path.join(path,'*.dst.gz')))
    
    # list the files corresponding to this combination's "first" site
    pattern = re.compile(ta.psites[comb][0] + '-\d{5}\.dst\.gz')    
    dst0s = [dst in all_dsts if pattern.match(os.path.basename(dst))]
    
    df = ['{0}/{1}-'.format(comb,i) for i in ta.psites[comb]] 
    
    for dst0 in dst0s:
      # all the base DST files for this event:
      event_dst = [dst0.replace(df[0],d) for d in df]
      out_dst = [d.replace('.dst.gz','.spln.dst.gz') for d in event_dst]
      
      # if no retry, and final output already present, move on
      if (False not in [dst in all_dsts for dst in out_dst] and
          False not in [night.retry[s] < 2 for s in ta.psites[comb]):
        continue
      
      # preprocess the MD DST, if present
      try:
        imd = ta.psites[comb].index('md')
        run_mdplane(event_dst[imd])
      except ValueError:
        pass
        
    
    
def run_mdplane(dst):
  pass