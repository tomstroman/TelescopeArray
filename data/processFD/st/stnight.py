# stnight.py
# Thomas Stroman, University of Utah, 2015-06-01
# A collection of routines and class definition for stereo processing.

import os
from ta_common import ta

class BadStereoRoot(Exception):
  pass

class InvalidPath(Exception):
  pass

class MissingBinDir(Exception):
  pass


def valid(night_path):
  '''
  Check that the supplied path meets all the requirements for stereo
  analysis and either return an info tuple or raise an exception.
  '''
  abspath = os.path.abspath(night_path)
  
  # All nights are expected to be in stereo_root
  for root in ta.stereo_roots:
    if abspath.startswith(root):
      stereo_root = root
      break
  else:
    raise BadStereoRoot(abspath + "doesn't start with one of {0}".format(
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
  if not os.path.exists(bindir)):
    raise MissingBinDir(bindir + ' does not exist')
  
  