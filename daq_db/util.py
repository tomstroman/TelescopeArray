def daqID(daq_str, site_str):
  '''
  Given a numeric daq code (normally "yymmddpp") and site ("s"),
  obtained from 6-sigma parts listed in daq-ctrl/*.log file,
  return 11-digit DAQ ID string ("yyyymmddpps").
  '''
  daq = int(daq_str)
  if daq < 1000000:
    daq += 7000000
    
  if daq < 2000000000:
    daq += 2000000000
    
  return str(daq) + site_str
  
def cams(daqline):
  '''
  Given a begin-part line from a daq-ctrl/*.log file, compute the unique
  numerical representation of the combination of cameras present.
  Let each camera represent one bit in a 12-bit unsigned integer, with the
  bit set to 1 if the camera is present, and absent otherwise.
  
  Return the decimal representation of the resulting integer.
  '''
  
  try:
    combo = sum([2**int(camID) for camID in daqline.split()[2:-5]])
  except ValueError:
    print "Error. Offending line:"
    print daqline
    combo = -1
  
  return combo
  
  
def ymd8(ymd):
  '''
  from a string beginning yYYYYmMMdDD, 
  return 8-digit integer YYYYMMDD
  '''
  
  year = ymd[1:5]
  month = ymd[6:8]
  day = ymd[9:11]
  try:
    intymd = int(year + month + day)
  except ValueError:
    # test for a special case
    if year == '200y':
      print 'Warning: replacing "200y" with "2007"' 
      return ymd8(ymd.replace(year,'2007'))
    
    intymd = ymd8_desperate(ymd)
    
    if not intymd:
      print 'Error: expected string beginning yYYYYmMMdDD'
      print '(where YYYY, MM, DD are integers)'
      print 'Offending entry:'
      print ymd

  return intymd
  
def ymd8_desperate(ymd):
  '''
  This is the "desperate mode" for the ymd8 function. We will grab
  every numeric digit in the string, and if it looks like an 8-digit date,
  we will treat it as such.
  '''
  numstr = ''.join(s for s in ymd if s.isdigit())
  
  if len(numstr) == 8 and numstr[0:2] == '20':
    print 'Warning: inferring {0} from {1}'.format(numstr,ymd)
    return int(numstr)
  else:
    return None
  
def getCamList(cams):
  '''
  Convert bitmask (cams) to list of flags, or return None argument
  '''
  if cams == None:
    return None
  return [(cams >> i) & 1 for i in range(0,12)]  