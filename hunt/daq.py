# The daq class keeps track of each DAQ part from the BRM and LR telescopes.
# Each part is subject to several processing stages, and the methods in
# this class are able to pick up where any previous processing left off.

import os

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
    
    self.daqID = daqID          # DAQ ID: yyyymmddpps
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
    self.ymd = daqID[0:8]
    self.part = daqID[8:10]
    self.siteID = int(daqID[10])

    # yYYYYmMMdDD
    self.fymd = 'y{0}m{1}d{2}'.format(self.ymd[0:4],self.ymd[4:6],self.ymd[6:8])
    
    # yYYYYmMMdDDpPP
    self.fymdp = self.fymd + 'p' + self.part
    self.sitename = ta.sitenames[self.siteID]

    # a list of twelve elements, 1 if camera is present else 0
    self.camlist = util.getCamList(self.cams)
    
    # Default location on disk of timecorr and TAMA output
    self.tamapath = '{0}{1}/{2}/{3}'.format(
        ta.tama, self.siteID, self.sitename, self.ymd )
    self.tcfile = self.tamapath + '/{0}_site{1}_timecorr.txt'.format(
        self.fymdp, self.siteID )
    
    self.daq0 = None
    
    # Default location on disk of FDPed output
    self.fdpedpath = '{0}/{1}/{2}'.format(ta.fdped,self.sitename,self.ymd)
    self.fdpederr = self.fdpedpath + '/fdped-{0}-{1}.err'.format(
        self.siteID, self.daqID[2:10] )
    
    # Default location on disk of FDPlane output
    self.fdplanepath = '{0}/{1}/{2}'.format(ta.fdplane,self.sitename,self.ymd)
    self.prolog = self.fdplanepath + '/{0}.prolog'.format(self.fymdp)
  
    self.status = self.exam()
  # end of __init__
    
  def exam(self):
    '''
    Find out how much processing has been done on this part by consulting:
    1. the database
    2. the expected output locations of anything not already recorded
       in the database
       
    Update the self.db* variables accordingly 
    and return the number of "finished" columns.
    '''
    if 'daqdb' in globals():
      ncol = self.readDaqDB(daqdb)
      
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
      
      ncol = sum([db[i] != None for i in db.keys()])
      
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
  
  #def checkTAMA(self):
    #'''
    #Look for the timecorr file
  
  
