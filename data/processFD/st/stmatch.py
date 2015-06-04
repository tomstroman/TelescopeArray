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

import os
from ta_common import ta

def get_matched_events(night):
  '''
  Perform the entire process of time-matching events, classifying by site
  combination, removing some contaminants, and extracting data files,
  according to information in a Night object.
  
  Return True if successful, False otherwise.
  '''
  
  return find_matches(night)
  
def find_matches(night):
  '''
  Compare downlists by site combination to produce pair-wise matchlists.
  '''
  
  night.lists['match'] = {}
  night.data['match'] = {}
  
  # keep track of lists that are new, for writing to disk
  new = {}
  
  for comb in ta.nps:
    if comb not in night.dirs['st']:
      continue

    matchlist = os.path.join(night.dirs['st'][comb],'matches.txt')
    night.lists['match'][comb] = matchlist
    
    # if no mono site requests a retry, look for existing.
    if False not in [night.retry[s] < 2 for s in ta.psites[comb]]:
      try:
        night.data['match'][comb] = open(matchlist).read()
        continue
      except IOError as e:
        if 'No such file or directory' in e:
          pass
        else:
          raise e
    
    # either it doesn't exist yet or we've requested a retry.
    if comb in ta.nps[:-1]: # 2-way combinations
      down1 = night.data['down'][ta.psites[comb][0]]
      down2 = night.data['down'][ta.psites[comb][1]]
      matches = scan_2down(down1,down2,ta.stereo_coincidence_window)
    else: # for triple-stereo case, we will *remove* events from 2-ways
      matches = isolate_triples(night)
      
    new[comb] = matchlist
    night.data['match'][comb] = matches 

  # finally, write to files if necessary.
  for comb,matchlist in new.items():    
    with open(matchlist,'w') as out:
      out.write(night.data['match'][comb])

  # test that files exist here?
  return True
  
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
  for e1 in d1[:-1]:
    t1 = float(e1.split()[0])
    l = k # current position in d2
    for e2 in d2[k:-1]:
      l += 1 
      t2 = float(e2.split()[0])
      if abs(t2 - t1) < window: # we have a match!
        k = l # on next pass, start from event following the match
        buf += '{0} {1}\n'.format(e1,e2)
        break # look for match for next event
      elif (t2 - t1) > window_x2: # we've gone far enough
        break
  
  return buf

def isolate_triples(night):
  '''
  given a Night object with the three 2-way stereo combinations populated,
  look for events present in all three sites. Remove them from the 2-way
  lists and add them to the 3-way list, which is returned as a string
  formatted for writing to a matchlist.
  
  Known limitation: if the first and third site to see an event are more than
  ta.stereo_coincidence_window apart, the event may be missing from their
  respective matchlist, which could lead to failure to recognize it as triple.
  In practice, the window is much larger than the light-crossing time of the
  largest experiment dimension.
  '''
  buf = ''
  
  # if any pair of sites has no matches, there are no triple matches.
  if 0 in [len(m) for m in night.data['matches']]:
    return buf
    
  # If an event occurs in two matchlists, we assume it's in the third one.
  # Search the two that are likely to be shortest: namely, the lists involving
  # the Middle Drum detector. If an MD event shows up in both lists, it's a 
  # triple.
  m1 = night.data['matches']['bm'].split('\n')
  m2 = night.data['matches']['lm'].split('\n')
  
  k = 0
  for e1 in m1[:-1]:
    md = ' '.join(e1.split()[5:10])
    l = k
    for e2 in m2[k:-1]:
      if md in e2:
        k = l
        buf += ' '.join(e1.split()[0:5] + [e2]) + '\n'
        break
  
  # now we remove the triple matches from the doubles:
  for trip in buf.split('\n'):
    b,l,m = [' '.join(trip.split()[i:i+5]) for i in range(0,15,5)]
    
    # remove from bl
    t = night.data['matches']['bl'].replace(' '.join([b,l]) + '\n','')
    night.data['matches']['bl'] = t
    
    # remove from bm
    t = night.data['matches']['bm'].replace(' '.join([b,m]) + '\n','')
    night.data['matches']['bm'] = t
    
    # remove from lm
    t = night.data['matches']['lm'].replace(' '.join([l,m]) + '\n','')
    night.data['matches']['lm'] = t
  
  return buf