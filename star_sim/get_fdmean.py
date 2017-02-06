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

dbpart = raw_db.retrieve('SELECT p.daqcams, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.part11={}'.format(part))

assert len(dbpart) == 1
daqcams, ctdprefix = dbpart[0]

camlist = _camlist(daqcams)

if args.camera in camlist:
    cams = [args.camera]
else:
    cams = camlist
print cams
tcfile = _timecorr_path(part)
assert os.path.exists(tcfile)
cmd = 'cp -v {} {}'.format(tcfile, output)
print cmd
#os.system(cmd)


