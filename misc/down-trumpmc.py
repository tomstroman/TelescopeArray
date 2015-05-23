# down-trumpmc.py
# Thomas Stroman, University of Utah, 2015-05-23
# This is essentially a one-time-use script designed to reformat the output
# of another program and teach myself a little more regex.

# The script looks in a hard-coded location for files of a certain type,
# namely the "downward" events identified by fdplane (previously run),
# and then runs a program that produces ASCII output based on the contents
# of those files. The output is searched for the numbers that follow certain
# keywords using look-behind regular expressions, and after some manipulation
# those numbers are printed on a single line per "event" (a single file can
# contain multiple events and so produce multiple lines).

# The resulting file begins with a header of column names separated by colons,
# which can easily be read into ROOT using the TTree::ReadFile method.


import os
import glob
import re
import math

from ta_common import tabin

mcpath = '/tadserv1/tstroman/chpc-mc/sub-20130607'
outfile = '/scratch/tstroman/radarsim/down-events-20080401-20130318.txt'
with open(outfile,'w') as out:
  out.write('epri:xcore:ycore:zcore:ux:uy:uz:rpkm:psi:')
  out.write('zenrad:azmrad:ghx0:ghlambda:ghxmax:ghnmax\n')
  for ymd in sorted(glob.glob(mcpath + '/lr/20*')):
    buf = ''
    for down in sorted(glob.glob(ymd + '/*.down.dst.gz')):
      cmd = tabin.dstdump + ' -trumpmc ' + down
      dump = os.popen(cmd).read()
      
      # Based on the formatting of the TRUMPMC DST bank printout:
      
      # find any number after |Rp|= up until the end of the line
      rp = re.findall('(?<=\|Rp\|=).*',dump)
      
      # find any number after Psi up until the end of the line
      psi = re.findall('(?<=Psi).*',dump)
      
      # pull the shower vector out as a string-encoded tuple,
      # then break it up into a 3-element list    
      # and finally get the float version for a calculation
      sv_str = re.findall('(?<=Shower Vector:).*',dump)    
      sv = [re.sub('[() ]','',s).split(',') for s in sv_str]    
      fsv = [[float(v) for v in s] for s in sv]
      
      core_str = re.findall('(?<=Impact Point \(m\):).*',dump)
      core = [re.sub('[() ]','',s).split(',') for s in core_str]
      
      zenith = [math.acos(-uv[2]) for uv in fsv]
      azimuth = [math.atan2(-uv[1],-uv[0]) for uv in fsv]
      
      epri = re.findall('(?<=Energy:)[\s\d\.]*',dump)
      ghxmax = re.findall('(?<=Xmax)[\s\d\.]*',dump)
      ghx0 = re.findall('(?<=Xo)[\s\d\.]*',dump)
      ghlambda = re.findall('(?<=Lambda).*',dump)
      ghnmax = re.findall('(?<=Nmax)[\s\d\.]*',dump)
    
      for line in zip(epri,core,sv,rp,psi,zenith,
          azimuth,ghx0,ghlambda,ghxmax,ghnmax):
        buf += '{0}'.format(line[0]) # Python 2.6 can't do '{}'
        # time to get clever/lazy
        buf += ''.join([' {{{0}}}'.format(i) for i in range(3)]).format(*line[1])
        buf += ''.join([' {{{0}}}'.format(i) for i in range(3)]).format(*line[2])
        buf += ' {0}'.format(0.001*float(line[3]))
        buf += ''.join([' {{{0}}}'.format(i) for i in range(7)]).format(*line[4:])
        
        buf += '\n'
      
    out.write(buf)  
      
    
    