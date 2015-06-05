# stutil.py
# Thomas Stroman, University of Utah, 2015-06-01
# A collection of utility functions used in stereo processing.

# Currently defined:
# some exceptions
# valid(night_path): function to validate processing requests
# Night: class to contain information about night being processed


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
          'exists': None,        # only applies to a specific night
          'bindir': bindir,
          'ymdpath': ''
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
    info['night'] = ymd
    info['ymdpath'] = os.path.join(srcdir,ymd)
    info['exists'] = os.path.exists(info['ymdpath'])    
  else:
    raise BadDate(ymd + ' is not a yyyymmdd date')
  
  return info

  
  
  
class Night(object):
  def __init__(self,info):
    # these need to be defined for __repr__ to work, but will be
    # populated by whatever wants this class
    self.ymd = info['night']
    self.calib = info['calib']
    self.model = info['model']
    self.source = info['source']

    self.rc = [info['fdtp'],info['stpfl']]    
    
    # can't use dict comprehension in Python 2.6
    # right now, each site gets the same retry level, but I want to
    # write the deeper code in a way that can handle sites independently.
    self.retry = dict([(s,info['retry']) for s in ta.sa[:-1]])
    
    self.dirs = {'root': info['ymdpath']}
    self.lists = {}
    self.data = {}
    
    self.errors = []
  
  def __repr__(self):
    return self.dirs['root']
  
  #def get_directories(self):
    '''
    Determine where to look for input and write output.
    '''
    #self.outdir = os.path.join(
  
  #def prep_mono(self):
    #for site in self.sites:
    