# stereo.py
# Thomas Stroman, University of Utah, 2015-05-31
# This script automates the entire stereo analysis of one night's data,
# whether originating in the physical detectors or Monte Carlo simulation.

# The stereo analysis procedure performed here consists of eight steps:
# 1. Assemble a time-ordered list of events identified as "downward"
#    by the monocular processing routines (previously run)
# 2. Find two-way and three-way coincidences in the event lists from
#    all FD sites ("stereo candidates")
# 3. Remove events with timestamps indicating an artificial origin (the
#    Central Laser Facility, which is a known contaminant in the data)
# 4. Extract stereo-candidate event data from the files containing it
# 5. Compute the stereo-constrained event geometry (air-shower trajectory)
# 6. Check the stereo geometry for physicality ("sanity check")
# 7. Reconstruct the "shower profile" of the event at each observing FD site,
#    using monocular reconstruction but based on the stereo geometry.
# 8. Combine the separate sites' output files and create an ASCII dump of
#    selected event parameters.

# Data organization:

# [date] (yyyymmdd)
# --ascii
# ----[recon] (names like ghdef-mdghd)
# --bl (for events from Black Rock Mesa + Long Ridge)
# --blm (for events from Black Rock Mesa + Long Ridge + Middle Drum)
# --bm (for events from Black Rock Mesa + Middle Drum)
# --lm (for events from Long Ridge + Middle Drum)
# --trump (only if simulation)
# ----black-rock
# ----long-ridge
# ----middle-drum

# The fundamental unit for stereo processing is the "night."
# Any night on which two or more FDs were run may contain stereo events.
# The details of how to process a particular night are inferred from
# its path (i.e., its ancestor directories). 

# The structure is:
# stereo_root/(calib)/(model)/(source)/(date)

# Some code called during analysis is compiled with values specific to
# an analysis (calib and model). This code is stored in
# stereo_root/(calib)/(model)/bin

# Collecting the ASCII output from individual events into large files is 
# similarly organized by model, so the directory structure is
# stereo_root/(calib)/(model)/ascii/(date of aggregation)

import os
import glob
import sys

# local package
from st import stutil
from ta_common import ta

def main(argv):
  '''
  Interpret command-line arguments. More detail to come.
  '''
  
  # check for goal override.
  try:
    igoal = argv.index('-goal')
    goal = int(argv[igoal + 1])
    if goal not in range(0,9):
      print('Error: goal ({0}) out of range.'.format(goal))
      print('Syntax: -goal N')
      print("Values of N: 8: end (default); 1-7: stop early; 0: only report")
      sys.exit()
    
    argv.pop(igoal+1) # remove goal
    argv.pop(igoal) # remove '-goal'
  except ValueError:
    goal = 8
    
  # check for retry request
  try:
    iretry = argv.index('-retry')
    retry_level = int(argv[iretry + 1])
    if retry_level not in range(0,3):
      print('Error: retry_level ({0}) out of range.'.format(retry_level))
      print('Syntax: -retry N')
      print('Values of N: 0: no retry (default); 1: missing only; 2: all')
      sys.exit()
      
    argv.pop(iretry + 1) # remove retry_level
    argv.pop(iretry) # remove '-retry'
  except ValueError:
    retry_level = 0
    
  # check for retry starting point
  try:
    istart = argv.index('-skip')
    retry_after = int(argv[istart + 1])
    if retry_after not in range(0,8):
      print('Error: retry_after ({0}) out of range.'.format(retry_after))
      print('Syntax: -skip N')
      print('Values of N: 0: retry from beginning (default); 1-7: from N')
      sys.exit()
      
    argv.pop(istart + 1) # remove retry_after
    argv.pop(istart) # remove '-skip'
  except ValueError:
    retry_after = 0
  
  if retry_after > 0 and retry_level == 0:
    print('Warning: -skip requested but retry_level>0 not specified.')
    print('Assuming "missing-only" retry (level 1).')
    retry_level = 1
    
  
  # all remaining arguments should be paths to nights.
  status = {}
  for night_path in argv[1:]:
    status[night_path] = process_night(night_path,goal,retry_level,retry_after)
    # in the event a non-night path was given, we may still recover something.
    if status[night_path] not in [True,False]:
      # process_night returned a dict!
      if status[night_path]['night'] == 'search':
        nights = sorted(glob.glob(night_path + '/2*'))
        if len(nights) == 0: # no nights exist yet, but we can create them!
          nights = open(ta.stereo_dates).readlines()
          
      for np in nights:
        np = os.path.join(night_path,np)
        status[np] = process_night(np,goal,retry_level,retry_after)
  
  return status
  
  
def process_night(night_path,goal=8,retry_level=0,retry_after=0):
  '''
  Run the entire processing sequence on data in night_path,
  or only run those steps in between enpoints manually specified via
  these keyword arguments:
  goal = 8: process until complete (default)
         integer in range [1,7]: process through specified task and stop
         0: don't process, just assess stereo candidacy
  retry_level = 0: none (default)
                1: retry missing/failed only
                2: all
  retry_after = 0: retry from beginning (default)
               integer in range [1,7]: final step assumed to be valid
  '''
  
  try:
    info = stutil.valid(night_path)
  except Exception as e:
    print(e)
    return False      
  
  print('Processing ' + night_path)
  
  abspath = os.path.abspath(night_path)
  
  if info['night'] == 'search':
    # let's tell whatever called this to look for some nights.
    return info
  
  
  print(abspath)
  
  
  
  first_step = retry_after if retry_level else 0
  
  if goal not in range(first_step,9):
    return False
  
  
  
  
  if goal == 0:
    return True
  
  # for now, placeholders for each processing step.
  if first_step < 1 <= goal:
    pass
  
  if first_step < 2 <= goal:
    pass
  
  if first_step < 3 <= goal:
    pass
  
  if first_step < 4 <= goal:
    pass
  
  if first_step < 5 <= goal:
    pass
  
  if first_step < 6 <= goal:
    pass
  
  if first_step < 7 <= goal:
    pass
  
  if first_step < 8 <= goal:
    pass
  
  return True


    
if __name__ == '__main__':
  status = main(sys.argv)
