# hunt.py
# Thomas Stroman, University of Utah, 2015-05-04
# This is a Python-2 script to locate and assess telescope data collected
# by the Telescope Array Experiment in Millard County, Utah.

# The script is to be run from within the TA Data Server ("tadserv") cluster.

# The basic operation follows 3 main steps:
# 1. It consults a members-only wiki to populate a list of nights
#    when specific telescope stations were collecting data.
# 2. Next, it scans all available storage volumes for nightly run logs.
#    From those logs, identify "DAQ parts," continuous periods of operation
#    by a single telescope station within a given night.
# 3. Scan available storage looking for "CTD" data files, and match those 
#    files to the parts expected from the log files.

# The output of the script is two ASCII files:
#       logparts-YYYYMMDD.txt
#       locations-YYYYMMDD.txt
# where YYYYMMDD is the date on which this script was run. As written, 
# subsequent runs on the same calendar date will overwrite existing runs.


import os
import time
import glob
import copy

# custom modules
import ta       # general TA information
import util     # utility code
import tawiki   # functions for scraping wiki pages


# get today's date, for use in filenames
ymd = time.strftime('%Y%m%d')

# the main output: ASCII database
dbfile = 'logparts-{0}.txt'.format(ymd)
locfile = 'locations-{0}.txt'.format(ymd)

# check wiki to learn which log files to expect at brm and lr sites
runnights = {'brm': [], 'lr': []}

for year in range(2007,int(ymd[0:4])+1):
  print 'Scanning for active log files in the wiki page for {0}'.format(year)
  html = tawiki.getPage(year)
  for site in runnights:
    runnights[site] += tawiki.findLogDates(html,site)

for site in runnights:
  runnights[site].sort()
  print 'Wiki log entries for {0}: {1} from {2} through {3}'.format(
      site,len(runnights[site]),runnights[site][0],runnights[site][-1] )

# Remove nights from this list as log files are found.
# At the end, any nights remaining on here may represent missing data.
unclaimed_nights = copy.deepcopy(runnights)


# Collect all the .log files
# Note: this assumes a common directory structure for all data months
logs = glob.glob('/tadserv*/tafd/*/*/daq-ctrl/*.log')

# dict of all parts according to log files
logdaqdb = {}


for log in logs:
  site = log.split('station')[1][0] # first character after word "station"
  
  #print log
  for line in open(log).readlines():
    if '6.0' not in line: # this identifies 6-sigma DAQ parts
      continue
    l = line.split()
    daqID = util.daqID(l[0],site)
    
    # how the files are named depends on the date.
    daqFileCode = 'DAQ-{0}-{1}'.format(
        '0'+l[0] if int(l[0]) < 10000000 else l[0],site)
        
    daqinfo = (int(l[-2]),util.cams(line),log,daqFileCode)
    
    logymd = int(daqID[0:8])
    # add this daqID information to logdaqdb
    try:
      logdaqdb[daqID].append(daqinfo)
    except KeyError:
      logdaqdb[daqID] = [daqinfo]
    
    # remove this night-site from unclaimed_nights
  try:
    unclaimed_nights[ta.sites[int(site)]].remove(logymd)
  except ValueError:
    pass
  
    

print 'Number of logs parsed: {0}, describing {1} parts'.format(
    len(logs),len(logdaqdb) ) 
print 'Number of unclaimed nights remaining:'
for site in ta.sites[0:2]:
  print '{0}: {1}'.format(site,len(unclaimed_nights[site]))

    
# Now we want to check for consistency: does the same part appear in multiple files,
# and if so, do they all report the same information?
conflicts = []
for daqID in sorted(logdaqdb):
  if len(logdaqdb[daqID]) == 1:
    continue
  nunique = (len(set([num[0] for num in logdaqdb[daqID]])),
             len(set([num[1] for num in logdaqdb[daqID]])) )  
  if nunique != (1,1):
    conflicts.append(daqID)
    print 'Error! Conflicting DAQ metadata for part ' + daqID
    print logdaqdb[daqID]
    
print 'Conflicts found: {0}'.format(len(conflicts))


# now we collect the locations of bz2 files.
# Organize them into a dict of dicts resembling the directory structure.
tsbz2 = {}
# Also, for each part, list the files.
partbz2 = {}


for ts in glob.glob('/tadserv*'):
  tsID = ts.split('tadserv')[-1]
  tsbz2[tsID] = {}
  for month_path in glob.glob('{0}/tafd/*'.format(ts)):
    month = month_path.split('/')[-1]
    tsbz2[tsID][month] = sorted(glob.glob(
        '{0}/*/ctd/event-data/*.bz2'.format(month_path) ))
    
    for bz2 in tsbz2[tsID][month]:
      daqFileCode = bz2.split('/')[-1][0:-14]
      try:
        partbz2[daqFileCode].append(bz2)
      except KeyError:
        partbz2[daqFileCode] = [bz2]
    

# We know what parts are listed in the logs, and what files exist on disk.
# Can we match them up?

errors = []

daqdb = {}
locate = {}
for daqID in sorted(logdaqdb.keys()):
  entry = logdaqdb[daqID][0]
  expected_ctd = 1 + entry[0] // 256
  try:
    num_ctd = len(partbz2[entry[3]])
  except KeyError:
    num_ctd = 0
  
  if num_ctd != expected_ctd:
    errors.append('{0} expected {1} but found {2}.'.format(daqID,expected_ctd,num_ctd))
    if num_ctd > 0 and not partbz2[entry[3]][0].endswith('0000000.d.bz2'):
      errors[-1] += ' First file: ' + partbz2[entry[3]][0]
    if num_ctd > expected_ctd:
      errors[-1] += ' Files may exist in multiple locations.'

  daqdb[daqID] = (entry[1],entry[0])
  try:
    locate[daqID] = partbz2[entry[3]][0]
  except KeyError:
    locate[daqID] = None
  
  
# write the output files.

fdbfile = open(dbfile,'w')
flocfile = open(locfile,'w')
for daqID in sorted(daqdb.keys()):
  fdbfile.write('{0} {1} {2}\n'.format(daqID,daqdb[daqID][0],daqdb[daqID][1]))
  if locate[daqID]: # if no data was found, don't include part here
    flocfile.write('{0} {1}\n'.format(daqID,locate[daqID]))
  
fdbfile.close()
flocfile.close()

