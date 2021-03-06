# get_fdmean.py
# Thomas Stroman, University of Utah, 2017-02-05
# Call TAMA with the '-m' flag to extract FDMEAN banks for a specific data part and mirror,
# then apply calibration to the data and output in a usable format.

import os
import sys
import argparse

# Set up default directory and connect to database with part information
default_output = os.path.join('/raidscratch', 'tstroman', 'tama')
assert os.path.isdir(default_output)

TSTA = os.getenv('TSTA')
assert TSTA is not None
sys.path.append(os.path.join(TSTA, 'pro'))

from db.database_wrapper import DatabaseWrapper
from utils import _timecorr_path, _camlist
raw_db = DatabaseWrapper(os.path.join(TSTA, 'pro', 'db', 'fadc_data.db'))

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('part', help='11-digit part code (YYYYMMDDPPS) e.g. 20080709200', type=int)
parser.add_argument('-c', '--camera', help='Which camera to use; if blank, use all available.', type=int, default=-1)
parser.add_argument('-d', '--output_dir', help='Output location; default: {}'.format(default_output), default=default_output)
parser.add_argument('-f', '--force_rebuild', help='Rebuild FDMEAN file even if it exists in specified location', action='store_true')
args = parser.parse_args()
part = args.part
output = args.output_dir
force_rebuild = args.force_rebuild

# Retrieve part info from database and validate result
dbpart = raw_db.retrieve('SELECT p.daqcams, p.site, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.part11={}'.format(part))

assert len(dbpart) == 1
daqcams, site, ctdprefix = dbpart[0]
print ctdprefix

camlist = _camlist(daqcams)

if args.camera in camlist:
    cams = [args.camera]
else:
    cams = camlist
if args.camera != -1 and cams[0] != args.camera:
    print '!!! Warning !!! Requested camera not found.'
print 'Using camera(s):', cams

# Locate the timecorr file and copy to destination, and prepare logs directory
origtcfile = _timecorr_path(part)
tcfile = os.path.join(output, os.path.basename(origtcfile))
if not os.path.exists(tcfile) or force_rebuild:
  assert os.path.exists(origtcfile)
  cmd = 'cp -v {} {}'.format(origtcfile, output)
  os.system(cmd)

logdir = os.path.join(output, 'logs')
os.system('mkdir -p {}'.format(logdir))

# Read the number of triggers in the raw data files
assert os.path.exists(tcfile)
with open(tcfile, 'r') as tc:
    tclines = tc.readlines()
num_triggers = len(tclines)
print num_triggers

# Loop over raw data files, organized in 256-trigger chunks, with TAMA calls
outfiles = []
for trigset in range(0, num_triggers, 256):
    t7 = '{:07}'.format(trigset)
    ctd = '{}-{}-{}.d.bz2'.format(ctdprefix, site, t7)
    outfile = os.path.basename(ctd).replace('DAQ', 'FDMEAN').replace('d.bz2', 'dst.gz')
    if len(cams) == 1:
        outfile = outfile.replace('-{}-{}.dst.gz'.format(site, t7), '-{}-{:x}-{}.dst.gz'.format(site, cams[0], t7))
    outfile_path = os.path.join(output, outfile)
    outfiles.append(outfile_path)
    if os.path.exists(outfile_path) and not force_rebuild:
        continue
    stdout = os.path.join(logdir, outfile.replace('.dst.gz', '.stdout'))
    stderr = stdout.replace('.stdout', '.stderr')
    cmd = '$TAHOME/tama/bin/tama.run -m -o {} {} '.format(outfile_path, ctd)
    for cam in cams:
        cmd += ctd.replace('ctd', 'camera{:02}'.format(cam)).replace('-{}-{}.d.bz2'.format(site, t7), 
                '-{}-{:x}-{}.d.bz2 '.format(site, cam, t7))
    cmd += '> {} 2> {}'.format(stdout, stderr)
    print ctd
    os.system(cmd)

# Concatenate the output files into a single file
combined_outfile = outfiles[0][:-len('-1234567.dst.gz')] + '.dst.gz'
print combined_outfile
cmd = 'dstcat -o {} '.format(combined_outfile) + ' '.join(outfiles)
if not os.path.exists(combined_outfile) or force_rebuild:
    os.system(cmd)
assert os.path.exists(combined_outfile)

# Call calibration C code (compile if necessary)
calibrate_exe = 'calibrate.run'
calibrate_c = 'calibrate.c'
if not os.path.exists(calibrate_exe):
    print '{} not found. Attempting to compile using comments in {}'.format(calibrate_exe, calibrate_c)
    with open(calibrate_c, 'r') as cc_file:
        cc = cc_file.readlines()
    for line in cc:
        if line.startswith('gcc -'):
            print line
            os.system(line)

assert os.path.exists(calibrate_exe)

calibrated_outfile = combined_outfile.replace('.dst.gz', '-calibrated.txt')
if not os.path.exists(calibrated_outfile) or force_rebuild:
    cmd = '{} {} {} {}'.format(calibrate_exe, combined_outfile, args.camera, calibrated_outfile)
    os.system(cmd)

os.system('gzip {}'.format(calibrated_outfile))
print calibrated_outfile + '.gz'
