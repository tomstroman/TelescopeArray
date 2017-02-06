# get_fdmean.py
# Thomas Stroman, University of Utah, 2017-02-05
# Call TAMA with the '-m' flag to extract FDMEAN banks for a specific data part and mirror,
# then apply calibration to the data and output in a usable format.

import os
import sys
import argparse

default_output = os.path.join('/raidscratch', 'tstroman', 'tama')
assert os.path.isdir(default_output)

TSTA = os.getenv('TSTA')
assert TSTA is not None
sys.path.append(os.path.join(TSTA, 'pro'))

from db.database_wrapper import DatabaseWrapper
from utils import _timecorr_path, _camlist
raw_db = DatabaseWrapper(os.path.join(TSTA, 'pro', 'db', 'fadc_data.db'))

parser = argparse.ArgumentParser()
parser.add_argument('part', help='11-digit part code (YYYYMMDDPPS) e.g. 20080709200', type=int)
parser.add_argument('-c', '--camera', help='Which camera to use; if blank, use all available.', type=int, default=-1)
parser.add_argument('-d', '--output_dir', help='Output location; default: {}'.format(default_output), default=default_output)
args = parser.parse_args()

part = args.part
output = args.output_dir

dbpart = raw_db.retrieve('SELECT p.daqcams, p.site, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.part11={}'.format(part))

assert len(dbpart) == 1
daqcams, site, ctdprefix = dbpart[0]
print ctdprefix

camlist = _camlist(daqcams)

if args.camera in camlist:
    cams = [args.camera]
else:
    cams = camlist
print 'Using camera(s):', cams
tcfile = _timecorr_path(part)
assert os.path.exists(tcfile)
cmd = 'cp -v {} {}'.format(tcfile, output)
os.system(cmd)

tcfile = os.path.join(output, os.path.basename(tcfile))
with open(tcfile, 'r') as tc:
    tclines = tc.readlines()
num_triggers = len(tclines)
print num_triggers
for trigset in range(0, num_triggers, 256):
    t7 = '{:07}'.format(trigset)
    ctd = '{}-{}-{}.d.bz2'.format(ctdprefix, site, t7)
    outfile = os.path.basename(ctd).replace('DAQ', 'FDMEAN').replace('d.bz2', 'dst.gz')
    outfile_path = os.path.join(output, outfile)
    cmd = '$TAHOME/tama/bin/tama.run -m -o {} {} '.format(outfile_path, ctd)
    for cam in cams:
        cmd += ctd.replace('ctd', 'camera{:02}'.format(cam)).replace('-{}-{}.d.bz2'.format(site, t7), 
                '-{}-{:x}-{}.d.bz2 '.format(site, cam, t7))
    os.system(cmd)

