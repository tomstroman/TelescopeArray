#!/usr/local/bin/python
# prep-trump-stereo.py
# Thomas Stroman, University of Utah, 2015-05-28
# This script automatically generates configuration files for the TRUMP
# detector simulation program. 

import os
import sys
import re
from hashlib import md5

from ta_common import ta

# expected arguments: config_template, date (as yyyymmdd)

if len(sys.argv) != 3:
    print 'Usage: python', __file__, 'config_template ymd'
    print '  assumes that config_template is located in'
    print '  (overall stereo location)/(calib)/(model)'
    sys.exit()

  
try:
    with open(sys.argv[1]) as config_template:
        conf = config_template.read()
except IOError:
    print 'Error: configuration template', conft, 'does not exist.'
    sys.exit()
  
ymd = sys.argv[2]

# From ymd and conf, we generate the seed for the random-number generator.
# The seed is generated from information on three lines in the template
# that begin with "tstroman-salt-" and also the ymd.
# These four values are joined with spaces and followed by a newline
# before md5-hashing to match the behavior of a Bash script.
# We only use the first eight hex digits of the md5 sum.

csalt = re.findall('(?<=tstroman-salt-).*', conf)
salt = ' '.join([s.split()[1] for s in csalt])
salt += ' ' + ymd + '\n'
seed = str(int(md5(salt).hexdigest()[0:8], 16))

# this string will be used in multiple filenames ahead
fymd = 'y{0}m{1}d{2}'.format(ymd[0:4], ymd[4:6], ymd[6:8])

# TRUMP can run in monocular (one configuration) or stereo mode (two)
orig_conf = conf
for site, siteid in {'br': 0, 'lr': 1}.items():
    sn = ta.sitenames[siteid]

# TRUMP will run for this site iff the pedestal file exists
    ped = os.getenv('RTDATA') + '/calibration/fdped/' + sn
    ped += '/' + fymd + '.ped.dst.gz'

    if not os.path.exists(ped):
        print "Didn't find", ped
        continue

# create the output location
    outdir = os.path.dirname(os.path.abspath(sys.argv[1]))
    outdir += '/' + ymd + '/trump'

    outconf = outdir + '/y{0}m{1}d{2}.{3}.conf'.format(
        ymd[0:4],
        ymd[4:6],
        ymd[6:8],
        site,
    )
  
    dstdir = outdir + '/' + sn
    os.system('mkdir -p ' + dstdir)

# now we specify the values that go in the template's placeholders
    replace_dstfile = sn + '/' + fymd + '.dst.gz'
    replace_site = str(siteid)
    replace_geo = site
    replace_ontime = ped

    conf = orig_conf

    conf = conf.replace('REPLACE_DSTFILE', replace_dstfile)
    conf = conf.replace('REPLACE_SITE', replace_site)
    conf = conf.replace('REPLACE_GEO', replace_geo)
    conf = conf.replace('REPLACE_ONTIME', replace_ontime)
    conf = conf.replace('REPLACE_SEED', seed)

    with open(outconf, 'w') as oc:
        oc.write(conf)
