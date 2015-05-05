# updatedb.py
# Thomas Stroman, University of Utah, 2015-05-05
# This is a Python-2 script to supervise the processing of telescope data
# collected by the Telescope Array Experiment in Millard County, Utah.

# The script is to be run from within the TA Data Server ("tadserv") cluster.

# The telescope data is organized into "parts." Prior to running updatedb.py,
# it is necessary to identify the expected parts, and locate the data on disk.
# These tasks are accomplished by running hunt.py, also in this directory.

# The main output of hunt.py is an ASCII database, organized as one part
# per line, with initially three columns but increasing to twelve as
# processing proceeds.

# Each part has a unique label, called daqID, in the form yyyymmddpps
# where yyyymmdd is the date, pp is the part number, and s is the data 
# source (telescope site) ID.

# Several stages of processing are required for each part. Briefly:
# 0. Collect the raw data files.
# 1. Create a list of "triggers" within the part.
# 2. Process the data into "DST" files for use in analysis chain
# 3. Calculate minute-average "pedestals" from DSTs for telescope simulation
# 4. First-stage analysis: Identify "downward" triggers corresponding to
#    scientifically relevant signals
# 5. Quantify triggers for which accurate telescope calibration is unavailable

# Of the twelve columns (database fields), this is how they
# relate to the processing steps above:
# Columns 1-3 come from step 0
# Column 4 comes from step 1
# Columns 5-9 come from step 2
# Columns 10-12 come from steps 3-5 respectively

# This script identifies parts with incomplete processing,
# looks for the output of further processing steps, and updates
# the ASCII database accordingly.

# Under its original design, it does not automatically attempt to
# perform any processing itself. However, I do intend to incorporate
# that functionality into future revisions.

import daq



# hard-coded for testing purposes.
daqdbfile = 'logparts-20141104.txt'

daqdb = {} # this is the database dict
daq.daqdb = daqdb # add daqdb to daq global namespace


# read the ASCII dbfile and populate the database.
for line in open(daqdbfile).readlines():
  l = line.split()
  ll = len(l)
  daqdb[l[0]] = {
      'cams': int(l[1]) if ll > 1 else None,
      'ntrig_log': int(l[2]) if ll > 2 else None,
      'ntrig_ctd': int(l[3]) if ll > 3 else None,
      'nbad_dst': int(l[4]) if ll > 4 else None,
      'ntrig_dst': int(l[5]) if ll > 5 else None,
      'nsec_dst': float(l[6]) if ll > 6 else None,
      'nbytes_dst': int(l[7]) if ll > 7 else None,
      't0': float(l[8]) if ll > 8 else None,
      'nmin_ped': int(l[9]) if ll > 9 else None,
      'ndown': int(l[10]) if ll > 10 else None,
      'nbad_cal': int(l[11]) if ll > 11 else None 
      }

# Make a dict of DAQs       

print 'Generating list of DAQs for incomplete parts. This may take a moment.'

# syntax necessary given installed Python version is 2.6
daqs = dict(
  (daqID, daq.DAQ(daqID)) for daqID in sorted(daqdb) 
  if daqdb[daqID]['nbad_cal'] == None )

# next step in coding: modify daqdb and write it back to disk.