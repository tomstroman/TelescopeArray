# run-stereo-trump.py
# Thomas Stroman, University of Utah, 2015-05-28
# This script calls the TRUMP detector simulation program with any
# configuration files found in the location passed as the first argument.
# That program may take several hours to finish.

# Upon completion, this script performs some operations on the output,
# including data processing and, if a second argument requests it,
# the preparation and execution of a subsequent simulation using UTAFD.

# If running this script with MOSIX, use "mosenv" instead of "mosrun."
# Otherwise the os.system call to ROOT will fail.

import os
import sys
import glob
import subprocess
import re
import math as m

from ta_common import ta
from ta_common import tabin

if len(sys.argv) == 1:
  print 'Usage: python',__file__,'/path/to/config_location [-no_md]'
  print '  assumes that config_location contains the .conf file(s)'
  print '  by default, we attempt to kick off UTAFD MD simulation'
  print '  upon completion of TRUMP. Suppress with -no_md'
  sys.exit()

# make sure TRUMP executable exists
confloc = os.path.abspath(sys.argv[1])
binloc = '/'.join(confloc.split('/')[:-3]) + '/bin'

trump = binloc + '/trump.run'
if not os.path.exists(trump):
  print 'Error: trump.run not found in ' + binloc
  sys.exit()

# change working directory to confloc and run TRUMP
try:  
  os.chdir(confloc)
except OSError: # NOTE: in python3, possibly a FileNotFoundError
  print 'Error:',confloc,'not found'
  sys.exit()

  
# count the configurations present
nconf = len(glob.glob('*.conf'))
  
outfile = 'trump.out'

# This may take hours.
# (this approach causes outfile to be written so we can check progress)
os.system(trump + ' *conf &> ' + outfile)


# TRUMP created .rts files somewhere, depending on which sites were present.
# Move them here.
os.system('mv */*.rts .')

for rts in glob.glob('*.rts'): # should only be one
  cmd = [tabin.rtsparser,'-Etslpcgu',rts]  
  out = subprocess.Popen(cmd,stdout=subprocess.PIPE).stdout
  
  # manipulate some lines and skip repeated events
  last_shower = '-1'
  buf = ''
  for line in out.readlines():
    l = line.split()    
    if l[0] == last_shower:
      continue
    
    fl = [float(f) for f in l]
    
    # shower number, species, YMD
    outline = '{0} {1} {2} '.format(l[0],l[3],''.join(l[4:7]))
    # UTC time with ns precision
    outline += '{0}.{1} '.format(3600*fl[7]+60*fl[8]+fl[9],l[10])
    # log10 Energy/eV, x-y core position, shower axis vector
    outline += '{0} {1} {2} {4} {5} {6} '.format(*fl[11:18])    
    # Gaisser-Hillas parameters: X0, Lambda, Xmax, log10 Nmax
    outline += '{0} {1} {2} {3}\n'.format(fl[18],fl[19],fl[20],m.log10(fl[21]))
    
    buf += outline
    
    last_shower = l[0]
  rts_txt = rts + '.txt'  
  with open(rts_txt,'w') as txt:
    txt.write(buf)
    
  cmd = 'root -l -q "$TRUMP/bin/rts2root.C(\\"' + rts_txt + '\\")"'
  os.system(cmd)
  os.system('rm ' + rts_txt)
  
  # these will be replaced with Python code soon but for now call Bash
  os.system('$TAHOME/processFD/prepmdsim.sh ' + rts)
  os.system('$TAHOME/processFD/runmdsim.sh *.txt_md.in')
  
for sa,siteid in {'br': 0, 'lr': 1}.items():
  site = ta.sitenames[siteid]
  if not os.path.exists(site):
    continue
  os.chdir(os.path.abspath(site))
  
  # if this was the only site run by TRUMP, then all "parts" are mashed 
  # together into one DST file. We need to split the file up by part.
  if nconf == 1:
    dst = glob.glob('*d??.dst.gz')[0]
    cmd = [tabin.dstdump,'-{0}raw'.format(sa),dst]
    # run dstdump to extract part numbers of stored events
    out = subprocess.Popen(cmd,stdout=subprocess.PIPE).stdout.read()
    parts = re.findall('(?<=part )\d*',out)
    
    # find first occurrence of a part and number of occurrences;
    # these are arguments to dstsplit
    for s in set(parts):
      first = parts.index(s)
      count = parts.count(s)
      outdst = dst.replace('.dst.gz','p{0}.dst.gz'.format(s))
      cmd = tabin.dstsplit + ' -s {0} -n {1} -o {2} {3}'.format(
          first, count, outdst, dst)
      os.system(cmd)
    #os.system('rm ' + dst)
  for dst in sorted(glob.glob('*p??.dst.gz')):
    cmd = ' '.join([tabin.fdplane,'-geo ',ta.geo[siteid],'-output 1000',
        dst,'&>',dst.replace('dst.gz','fdplane.out')])
    os.system(cmd)
  os.chdir(os.path.pardir)
  
  