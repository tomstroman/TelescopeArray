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
import glob
import subprocess as sp
from ta_common import ta
from ta_common import util
from ta_common import tabin

def get_matched_events(night):
  '''
  Perform the entire process of time-matching events, classifying by site
  combination, removing some contaminants, and extracting data files,
  according to information in a Night object.
  
  Return True if successful, False otherwise.
  '''
  
  find_matches(night)
  for matchlist in night.lists['match'].values():
    if not os.path.exists(matchlist):
      print('Error: missing ' + matchlist)
      return False

  remove_clf(night)
  for clflist in night.lists['clf'].values():
    if not os.path.exists(clflist):
      print('Error: missing ' + clflist)
      return False
  
  get_event_dsts(night)
  return True
  
  
  
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
    print('Generating ' + matchlist)
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
  if 0 in [len(m) for m in night.data['match']]:
    return buf
    
  # If an event occurs in two matchlists, we assume it's in the third one.
  # Search the two that are likely to be shortest: namely, the lists involving
  # the Middle Drum detector. If an MD event shows up in both lists, it's a 
  # triple.
  m1 = night.data['match']['bm'].split('\n')
  m2 = night.data['match']['lm'].split('\n')
  
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
    t = night.data['match']['bl'].replace(' '.join([b,l]) + '\n','')
    night.data['match']['bl'] = t
    
    # remove from bm
    t = night.data['match']['bm'].replace(' '.join([b,m]) + '\n','')
    night.data['match']['bm'] = t
    
    # remove from lm
    t = night.data['match']['lm'].replace(' '.join([l,m]) + '\n','')
    night.data['match']['lm'] = t
  
  return buf
  
def remove_clf(night):
  '''
  Scan a list of time-matched events for CLF-compatible timestamps and remove
  them from the list, writing them instead to a list of CLF events that won't
  be processed.
  '''

  night.lists['clf'] = {}
  night.data['clf'] = {}
    
  for comb,match in night.data['match'].items():
    clflist = os.path.join(night.dirs['st'][comb],'rejectclf.txt')
    night.lists['clf'][comb] = clflist
    
    if False not in [night.retry[s] < 2 for s in ta.psites[comb]]:
      try:
        night.data['clf'][comb] = open(clflist).read()
        continue
      except IOError as e:
        if 'No such file or directory' in e:
          pass
        else:
          raise e
    
    print('Generating ' + clflist)
    to_remove = []
    for line in match.split('\n')[:-1]:
      if True in [util.is_clf(float(line.split()[i])) for i in [0,5]]:
        to_remove.append(line + '\n')
        
    buf = ''.join(to_remove)
    night.data['clf'][comb] = buf
    with open(clflist,'w') as out:
      out.write(buf)
      
    if len(to_remove) > 0:
      matchlist = night.lists['match'][comb]
      print('Pruning ' + matchlist)
      
      for line in to_remove:
        t = night.data['match'][comb].replace(line,'')
        night.data['match'][comb] = t
      
      with open(matchlist,'w') as out:
        out.write(night.data['match'][comb])
    
    
def get_event_dsts(night):
  '''
  Invoke the dstsplit command to extract single-event DST files from
  the parent collections. To keep I/O to a minimum, identify requests from
  each site combination, and handle bookkeeping behind the scenes to make sure
  the extracted events end up with the correct paths and filenames.
  '''
  existing = {}
  for comb,odir in night.dirs['st'].items():
    existing[comb] = sorted(glob.glob(os.path.join(odir,'??-?????.dst.gz')))
  
  
  # determine which events are requested, and by which combination,
  # and with what final number
  survey_dst_files(night)
  
  
  
  # loop over identified files, running dstsplit once per file
  # and then renaming the output
  for in_dst in sorted(night.data['pos'].keys()):
        
    buf = ''
    outnum = 0
    odir = os.path.dirname(in_dst)
    obase = os.path.join(odir,'tmpdst')
    
    # each file produced will be moved individually; save the commands here
    mv_cmd = []
    
    for pos,event in sorted(night.data['pos'][in_dst].items()):
      comb,num = event
      
      outdst = os.path.join(night.dirs['st'][comb],num + '.dst.gz')
      site = num[0:2]
      # unless retry is requested, skip existing files
      if outdst in existing[comb] and night.retry[site] < 2:
        continue
      
      buf += '{0}\n'.format(pos)
      dstsplit_output = obase + '-{0:05d}.dst.gz'.format(outnum)
      mv_cmd.append('mv {0} {1}'.format(dstsplit_output,outdst))
      outnum += 1
      
    # make sure we still want something from this file
    if len(buf) == 0:
      continue
    
    print('Splitting {0} into event files (count: {1})'.format(
        os.path.basename(in_dst),outnum))
        
    wlist = os.path.join(odir,'wantlist-' + os.path.basename(in_dst) + '.txt')
    with open(wlist,'w') as outw:
      outw.write(buf.strip()) # a trailing \n may cause segfault
    
    cmd = [tabin.dstsplit,'-w',wlist,'-ob',obase,in_dst]
    split = sp.Popen(cmd,stdout=sp.PIPE,stderr=sp.PIPE)
      
    out = split.stdout.read()
    err = split.stderr.read()
    
    no_remove = False
    if out != 'Reading DST file: ' + in_dst + '\n':
      print('Warning! Anomalous stdout when splitting:')
      no_remove = True
      print(out)
      
    if err != tabin.dststderr:
      print('Warning! Anomalous stderr when splitting:')
      no_remove = True
      print(err)
      
    os.system(';'.join(mv_cmd))
    
    if not no_remove:
      os.remove(wlist)
    
def survey_dst_files(night):
  '''
  Add to a "positions" dict from a matchlist, with each key being a file,
  and each value being itself a dict of event position and an event tuple,
  itself consisting of the site combination and the output event number.
  '''
  
  y,m,d = [night.ymd[a:b] for (a,b) in [(0,4),(4,6),(6,8)]]
  
  # nested dict for positions, by file then by number
  night.data['pos'] = {}
  
  for comb,matchlist in night.data['match'].items():
    counter = 0
    for line in matchlist.split('\n')[:-1]:
      i0 = 0 # select 5 fields in line starting from here
      for sa in ta.psites[comb]:
        s_event = line.split()[i0:i0+5]
        
        # infer the filename of the parent DST
        in_dst = os.path.join(night.dirs['mono'][sa],
            'y{0}m{1}d{2}p{3:02d}.down.dst.gz'.format(y,m,d,int(s_event[2])))
            
        # for correctly naming the output  
        event = (comb,'{0}-{1:05d}'.format(sa,counter))
        
        # where within the part is it?
        ev_pos = int(s_event[3])
        
        try:
          night.data['pos'][in_dst][ev_pos] = event
        except KeyError:
          night.data['pos'][in_dst] = {ev_pos: event}
        i0 += 5 # prepare to start from a different place in the same line
      
      counter += 1
  
  
      
    