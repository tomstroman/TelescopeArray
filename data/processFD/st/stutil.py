# stutil.py
# Thomas Stroman, University of Utah, 2015-06-01
# A collection of utility functions used in stereo processing.

# Currently defined:
# valid(night_path) to validate processing requests


import os
from ta_common import ta

# define a few exceptions that this function can raise
class BadStereoRoot(Exception):
  pass

class InvalidPath(Exception):
  pass

class MissingBinDir(Exception):
  pass

class BadDate(Exception):
  pass

def valid(night_path):
  '''
  Check that the supplied path meets all the requirements for stereo
  analysis and either return an info dict or raise an exception.
  '''
  abspath = os.path.abspath(night_path)
  
  # All nights are expected to be in stereo_root
  for root in ta.stereo_roots:
    if abspath.startswith(root):
      stereo_root = root
      break
  else:
    raise BadStereoRoot(abspath + " doesn't start with one of {0}".format(
        ta.stereo_roots))
  
  # split the remaining path into its directories
  dirs = abspath.replace(stereo_root + '/','').split('/')
    
  # following stereo_root, subsequent directories are:
  # calib
  # model
  # source    
  
  calib,model,source = dirs[0:3]
  
  # verify that this much of a directory already exists AND that
  # the appropriate binaries directory is present:
  
  srcdir = '/'.join([stereo_root,calib,model,source])
  bindir = srcdir[::-1].replace(source[::-1],'bin'[::-1])[::-1]
  # (all those [::-1] just guarantees it replaces RTL)

  if not os.path.exists(srcdir):
    raise InvalidPath(srcdir + ' does not exist')
  if not os.path.exists(bindir):
    raise MissingBinDir(bindir + ' does not exist')
  
  info = {'calib': calib,
          'model': model,
          'source': source,
          'night': '',           # we'll look for this now
          'exists': None         # only applies to a specific night
          }
  
  # see if a specific night has been requested
  try:
    ymd = dirs[3]
  except IndexError:
    # No night specified - default behavior here is to attempt ALL nights!
    info['night'] = 'search'
    return info

  # ymd exists. Validate it as a (probably) real night, based on being an
  # 8-digit integer
  
  isdate = len(ymd) == 8 and len([i for i in ymd if i.isdigit()]) == 8
  
  if isdate:
    info[night] = ymd
    ymdpath = os.path.join(srcdir,ymd)
    info[exists] = os.path.exists(ymdpath)
  else:
    raise BadDate(ymd + ' is not a yyyymmdd date')
  
  return info
    