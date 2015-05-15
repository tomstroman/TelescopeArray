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
  
  
def get_cam_list(cams):
  '''
  Convert bitmask (cams) to list of flags, or return None argument
  '''
  if cams == None:
    return None
  return [(cams >> i) & 1 for i in range(0,12)]  
  
 
def jtime((year, month, day, hour, minute, second)):
  '''
  Given UTC timing information in a six-element tuple,
  such as that returned by split_ymdhms() below,
  return the Julian date via the algorithm on Wikipedia: 
  http://en.wikipedia.org/wiki/Julian_day
  Converting_Julian_or_Gregorian_calendar_date_to_Julian_Day_Number
  '''
  a = (14 - month) // 12
  y = year + 4800 - a
  m = month + 12*a - 3
  jdn = (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
  jdn += (3600*hour + 60*minute + second) / 86400. - 0.5
  return jdn
  

def split_ymdhms(ymdhms):
  '''
  Given a string containing *valid* date and time
  in the order yyyy, mm, dd, HH, MM, ss(.)ssss...,
  interpret only numeric digits. Return six numbers,
  the first five of which are integers and the final may be float.
  '''
  n = ''.join([d for d in ymdhms if (d.isdigit())])
  year = int(n[0:4])
  month = int(n[4:6])
  day = int(n[6:8])
  hour = int(n[8:10])
  minute = int(n[10:12])  
  second = float('.'.join([n[12:14],n[14:]]))

  return (year,month,day,hour,minute,second)
  
def hms2sec(hms):
  '''
  Given a *valid* string of the time in hhmmss.sss... format,
  return the second into the day (0-86399.999...)
  '''
  
  # machinery to parse the string already exists,
  # if any yyyymmdd is prepended to the supplied hms.
  ymdhms = '00000000' + hms
  y,mo,d,h,m,s = split_ymdhms(ymdhms)
  
  return h*3600 + m*60 + s
  
def read_loc_db(locdbfile):
  locdb = {}
  with open(locdbfile) as floc:
    for line in floc.readlines():
      l = line.split()
      daqID = l[0]
      file0 = l[1]
      daq_alias = l[1].split('-')[-3]
      locdb[daqID] = (file0,daq_alias)  

  return locdb