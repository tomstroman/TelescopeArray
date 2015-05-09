# The daq class keeps track of each DAQ part from the BRM and LR telescopes.
# Each part is subject to several processing stages, and the methods in
# this class are able to pick up where any previous processing left off.

import os
import gzip

import ta
import util

class DAQ():
  def __init__(self,daqID):
    '''
    Instantiate this DAQ part as fresh (unprocessed).
    Subsequent methods will populate these fields.
    '''
    # These are the 12 columns of processing output.
    # Their default state is "None" until successful processing
    # provides a different number or failure indication.
    
    self.daqID = daqID            # DAQ ID: yyyymmddpps
    self.dbcams = None            # bitmask for cameras present
    self.dbntrig_log = None       # number of triggers in .log file
    self.dbntrig_ctd = None       # number of triggers found in CTD file
    self.dbnbad_dst = None        # number of bad DAQ DST files (post-TAMA)
    self.dbntrig_dst = None       # number of triggers in DAQ DST files
    self.dbnsec_dst = None        # seconds between first and last DAQ DST trigger
                                  # (summed over all DAQ DST files) - NOT ontime!!!
    self.dbnbytes_dst = None      # total bytes in all DAQ DST files
    self.dbt0 = None              # time of first trigger, in days since
                                  # 2007-07-01 00:00:00 UTC
    self.dbnmin_ped = None        # number of minutes in pedestal file (FDPED)
    self.dbndown = None           # number of "downward" events in FDPlane output
    self.dbnbad_cal = None        # number of events with bad calibration
    
    # Everything beyond this point is all helper information.
    
    self.errors = []
    
    self.ymd = daqID[0:8]
    self.part = daqID[8:10]
    self.siteID = int(daqID[10])

    # yYYYYmMMdDD
    self.fymd = 'y{0}m{1}d{2}'.format(self.ymd[0:4],self.ymd[4:6],self.ymd[6:8])
    
    # yYYYYmMMdDDpPP
    self.fymdp = self.fymd + 'p' + self.part
    self.sitename = ta.sitenames[self.siteID]

    # a list of twelve elements, 1 if camera is present else 0
    self.camlist = util.getCamList(self.dbcams)
    
    # Default location on disk of timecorr and TAMA output
    self.tamapath = '{0}{1}/{2}/{3}'.format(
        ta.tama, self.siteID, self.sitename, self.ymd )
    self.tcfile = self.tamapath + '/{0}_site{1}_timecorr.txt'.format(
        self.fymdp, self.siteID )

    self.t0 = None
    
    self.daq0 = None
    
    # Default location on disk of FDPed output
    self.fdpedpath = '{0}/{1}/{2}'.format(ta.fdped,self.sitename,self.ymd)
    self.fdpederr = self.fdpedpath + '/fdped-{0}-{1}.err'.format(
        self.siteID, self.daqID[2:10] )
    
    # Default location on disk of FDPlane output
    self.fdplanepath = '{0}/{1}/{2}'.format(ta.fdplane,self.sitename,self.ymd)
    self.prolog = self.fdplanepath + '/{0}.prolog'.format(self.fymdp)
    self.perr = self.prolog.replace('.prolog','.pln.err')
  
    self.updated = False
    
    self.status = self.exam()
  # end of __init__
  
  def __str__(self):
    s = self.daqID
    if self.dbcams != None:
      s += ' {0}'.format(self.dbcams)
    if self.dbntrig_log != None:
      s += ' {0}'.format(self.dbntrig_log)
    if self.dbntrig_ctd != None:
      s += ' {0}'.format(self.dbntrig_ctd)      
    if self.dbnbad_dst != None:
      s += ' {0}'.format(self.dbnbad_dst)
    if self.dbntrig_dst != None:
      s += ' {0}'.format(self.dbntrig_dst)
    if self.dbnsec_dst != None:
      s += ' {0}'.format(self.dbnsec_dst)
    if self.dbnbytes_dst != None:
      s += ' {0}'.format(self.dbnbytes_dst)
    if self.dbt0 != None:
      s += ' {0}'.format(self.dbt0)
    if self.dbnmin_ped != None:
      s += ' {0}'.format(self.dbnmin_ped)
    if self.dbndown != None:
      s += ' {0}'.format(self.dbndown)
    if self.dbnbad_cal != None:
      s += ' {0}'.format(self.dbnbad_cal)
      
    return s
  
  def exam(self):
    '''
    Find out how much processing has been done on this part by consulting:
    1. the database
    2. the expected output locations of anything not already recorded
       in the database
       
    Return the number of *new* columns.
    '''
    
    ncol = self.readDaqDB(daqdb)
      
    dbncol = ncol
                
    if ncol == 3:
      ncol += self.checkTimecorr()
    
    if ncol == 4 and self.dbntrig_ctd != 0:
      ncol += self.checkDST()
    
    if ncol == 9:
      ncol += self.checkFDPED()
    
    if ncol == 10:
      ncol += self.checkFDPLANE()
      
    if ncol == 11:
      ncol += self.checkCalib()
    
    if ncol > dbncol:
      self.updated = self.updateDaqDB(daqdb)
    
    return ncol
    
  # end of exam(self)
  
  def readDaqDB(self,daqdb):
    '''
    Look for this part's entry in the database, and copy its values.
    The number of non-None columns will be returned.
    '''
    ncol = 0
    
    if self.daqID in daqdb.keys():            
      db = daqdb[self.daqID]
      
      ncol = 1 + sum([db[i] != None for i in db.keys()])
      
      self.dbcams = db['cams']
      self.dbntrig_log = db['ntrig_log']
      self.dbntrig_ctd = db['ntrig_ctd']
      self.dbnbad_dst = db['nbad_dst']
      self.dbntrig_dst = db['ntrig_dst']
      self.dbnsec_dst = db['nsec_dst']
      self.dbnbytes_dst = db['nbytes_dst']
      self.dbt0 = db['t0']
      self.dbnmin_ped = db['nmin_ped']
      self.dbndown = db['ndown']
      self.dbnbad_cal = db['nbad_cal']
      
      
    return ncol
  
  # end of readDaqDB(self,daqdb)
  
  def updateDaqDB(self,daqdb):
    '''
    Look for this part's entry in the database, and update its values.
    Returns True if successful, False otherwise.
    '''
    
    try:
      db = daqdb[self.daqID]
      db['cams'] = self.dbcams
      db['ntrig_log'] = self.dbntrig_log
      db['ntrig_ctd'] = self.dbntrig_ctd
      db['nbad_dst'] = self.dbnbad_dst
      db['ntrig_dst'] = self.dbntrig_dst
      db['nsec_dst'] = self.dbnsec_dst
      db['nbytes_dst'] = self.dbnbytes_dst
      db['t0'] = self.dbt0
      db['nmin_ped'] = self.dbnmin_ped
      db['ndown'] = self.dbndown
      db['nbad_cal'] = self.dbnbad_cal
    except KeyError:
      self.errors.append(__name__ + '(): daqID no longer exists in database???')
      return False

    return True
    
  # end of updateDaqDB(self,daqdb)
  
  def checkTimecorr(self):
    '''
    Look for the timecorr file in its expected location. If it exists,
    count the number of lines and store it to self.dbntrig_ctd.
    Return the number of updated db elements (1 or 0).
    '''
    try:
      tc = open(self.tcfile).readlines()
    except IOError:
      self.errors.append(__name__ + '(): Could not read ' + self.tcfile)
      return 0
      
    self.dbntrig_ctd = len(tc)
    
    # here we also want to get the value for future use in
    # self.dbt0, but for legacy reasons we don't update db at this stage.
    try:
      ymdhms = self.ymd + ''.join(tc[0].split()[2:5])
      self.t0 = util.jtime(util.splitymdhms(ymdhms)) - ta.t0
    except IndexError:
      self.errors.append(__name__ + '(): Failed to identify t0 from' + 
          self.tcfile)
      self.t0 = None
      
    return 1
    
  # end of checkTimecorr(self)
  
  def checkDST(self):
    '''
    Look for evidence of DST files in their expected location.
    The evidence sought is an "eventcounts" file produced by an independent
    routine that inspects the DST files themselves and prints a report.
    
    Gather information from the eventcounts file and modify
    self.[dbnbad_dst, dbntrig_dst, dbnsec_dst, dbnbytes_dst, dbt0],
    and return the number of updated db elements (5 or 0).
    '''
    try:
      self.daq0 = locdb[self.daqID][0]
    except KeyError:
      self.errors.append(__name__ + 
          '(): daqID not found in location database')
      return 0
      
    ecf = self.tamapath + '/eventcounts-{0}.txt'.format(locdb[self.daqID][1])
    
    try:
      ec = open(ecf).readlines()
    except IOError:
      self.errors.append(__name__ + '(): could not find ' + ecf)
      return 0
      
    # need to initialize these to a non-None type so += will work.
    self.dbnbad_dst = 0
    self.dbntrig_dst = 0
    self.dbnsec_dst = 0.
    self.dbnbytes_dst = 0      
    
    for line in ec:
      l = line.split()
      self.dbnbad_dst += int(l[4])
      self.dbntrig_dst += int(l[1])
      self.dbnsec_dst += float(l[2])
      self.dbnbytes_dst += int(l[3])
      
    if self.t0 == None:
      self.checkTimecorr()
    
    self.dbt0 = self.t0
      
    return 5
    
  # end of checkDST(self)
    
  def checkFDPED(self):
    '''
    Look for evidence that FDPed processing stage has been run on this part.
    The evidence sought is the stderr output from the FDPed executable.
    
    If the stderr contains either "DELETE" or "KEEP," 
    update self.dbnmin_ped with the resulting number of minutes (0 or >0, 
    respectively). If neither is found, or the stderr is absent, keep None.
    
    Return the number of updated db elements.
    '''
    
    try:
      pederr = open(self.fdpederr).readlines()
    except IOError:
      self.errors.append(__name__ + '(): could not read ' + self.fdpederr)
      return 0
      
    for line in pederr[::-1]: #expected line should be at end
      if 'minutes' in line:
        break
    else:
      self.errors.append(__name__ + '(): no "minutes" line in ' + 
          self.fdpederr)
      return 0
      
    if 'DELETE' in line:
      self.dbnmin_ped = 0
    elif 'KEEP' in line:
      # this is necessary for the rare case of triple-digit minutes.
      # e.g. "[109 minutes" instead of "[ 58 minutes"
      self.dbnmin_ped = int(line.split('[')[1].split()[0])
    else:
      self.errors.apend(__name__ + 
          '(): "minutes" line contains neither KEEP nor DELETE')
      return 0
      
    return 1
  
  # end of checkFDPED(self)
  
  def checkFDPLANE(self):
    '''
    Look for evidence that FDPlane processing stage has been run on this part.
    The evidence sought is the prolog output from the FDPlane executable.
    
    If the prolog contains the word "valid" (expected on the last line), 
    the first number following valid is the number of triggers processed,
    and the second line is the number of "downward" events. Assign the latter
    to self.dbndown and return 1. Otherwise return 0.
    '''
    try:
      prolog = open(self.prolog).readlines()
    except IOError:
      self.errors.append(__name__ + '(): could not read ' + self.prolog)
      return 0
      
    for line in prolog[::-1]:
      if 'valid' in line:
        self.dbndown = int(line.split()[-1])
        return 1
    else:
      self.errors.append(__name__ + '(): no "valid" line in ' + self.prolog)
      return 0
      
  # end of checkFDPLANE(self)

  def checkCalib(self):
    '''
    Look for the presence of uncalibrated events after running FDPlane.
    Such events are indicated in the stderr output from FDPlane, and are
    indicated by the word "found" per event, or by the word "aborting" in
    some cases.
    
    The stderr output may be compressed (gzip).
    
    Set self.dbnbad_cal to the number of occurrences of "found" or "abort"
    and return 1. If the output is missing, return 0 and don't touch
    self.dbnbad_cal.
    '''
    
    try: 
      perr = open(self.perr).read()
    except IOError:
      gzperr = self.perr + '.gz'
      if os.access(gzperr,os.R_OK):
        perr = gzip.open(gzperr).read()
      else:
        self.errors.append(__name__ + 
            '(): could not read either unzipped or gzipped ' + self.perr)
        return 0
        
    self.dbnbad_cal = perr.count('found') + perr.count('abort')
    return 1
    
  #end of checkCalib(self)
  