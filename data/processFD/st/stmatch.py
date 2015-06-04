# stmatch.py
# Thomas Stroman, University of Utah, 2015-06-04
# These functions handle the identification of stereo events, based on
# matching timestamps within the desired coincidence window. The major
# steps performed here are:
# 1. For each of 3 possible pairs of FD sites (bl, bm, lm), find events
#    with stereo-candidate timestamps.
# 2. Isolate "triple-stereo" events (seen by all three sites) into "blm"
# 3. For all 4 site combinations, remove known artificial sources
# 4. Create individual data files per event per site with common numbering



def scan_2down(down1,down2,window):
  '''
  Given two strings as the entire contents of two "downlist" files,
  find times that match to within the time given by window (in seconds).
  Return a string as the contents of a "matchlist" file.
  
  Known limitation: if 2+ events occur within window of each other
  in the same list, only the first one will be reported.
  '''
  
  window_x2 = window * 2 # will be used frequently
  
  buf = ''
  
  d1 = down1.split('\n')
  d2 = down2.split('\n')
  
  k = 0 # keep track of starting place in down2 as we...
  # loop over lines in down1, looking for matches in d2
  for e1 in d1:
    t1 = float(e1.split()[0])
    l = k # current position in d2
    for e2 in d2[k:]:
      l += 1 
      t2 = float(e2.split()[0])
      if abs(t2 - t1) < window: # we have a match!
        k = l # on next pass, start from event following the match
        buf += '{0} {1}\n'.format(e1,e2)
        break # look for match for next event
      elif (t2 - t1) > window_x2: # we've gone far enough
        break
  
  return buf
