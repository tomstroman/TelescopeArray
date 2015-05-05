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
daqs = dict((daqID, daq.DAQ(daqID)) for daqID in sorted(daqdb) if daqdb[daqID]['nbad_cal'] != None)

