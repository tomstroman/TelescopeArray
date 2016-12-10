# raw_to_dst.py
# Thomas Stroman, University of Utah, 2016-11-27
# Functions for preparing DST files from raw Telescope Array FADC data.

import os
from glob import glob
site_names = {'0': 'black-rock', '1': 'long-ridge'}
import subprocess
tahome = os.getenv('TAHOME')
tama_exe = os.path.join(tahome, 'tama/bin/tama.run')
timecorr_exe = os.path.join(tahome, 'getTimeTable/bin/getTimeTable.run')
dstlist = os.path.join(os.getenv('TADSTBIN'), 'dstlist.run')
scratch = '/scratch/tstroman/'

def _verify_timecorr_exists(part_code):
    """
    Check for the existence of timecorr file in the expected final location.
    """
    part_code=str(part_code)
    ymd, part, site = part_code[0:8], part_code[8:10], part_code[10]

    tama_path = '/tama_{0}/{1}/{2}'.format(site, site_names[site], ymd)
    assert os.path.exists(tama_path)

    timecorr_file = 'y{0}m{1}d{2}p{3}_site{4}_timecorr.txt'.format(ymd[0:4],
            ymd[4:6], ymd[6:8], part, site)
    timecorr = os.path.join(tama_path, timecorr_file)
    assert os.path.exists(timecorr)

def verify_tama_exists(part_code, daq_pref=None):
    """
    Check for the existence of TAMA output in the expected location.
    Arguments:
        part_code is 11-digit part code, yyyymmddpps (8-digit date, 2-digit part, site ID)
        daq_pref is DAQ prefix, assumed to be "DAQ-" + part_code[2:10] unless otherwise specified.

    Returns: nothing, but raises AssertionError in the event of failure.
    """
    part_code=str(part_code)
    ymd, part, site = part_code[0:8], part_code[8:10], part_code[10]

    if daq_pref is None:
        daq_pref = 'DAQ-{0}'.format(part_code[2:10])


    tama_path = '/tama_{0}/{1}/{2}'.format(site, site_names[site], ymd)
    assert os.path.exists(tama_path)

    timecorr_file = 'y{0}m{1}d{2}p{3}_site{4}_timecorr.txt'.format(ymd[0:4],
            ymd[4:6], ymd[6:8], part, site)
    timecorr = os.path.join(tama_path, timecorr_file)
    assert os.path.exists(timecorr)


    dsts = [os.path.basename(d) for d in glob(os.path.join(tama_path, daq_pref) + '*.dst.gz')]
    with open(timecorr, 'r') as tc:
        tc_lines = tc.readlines()
        num_trig = len(tc_lines)
    for trigset in range(0, num_trig, 256):
        dst = '{0}-{1}-{2:07}.dst.gz'.format(daq_pref, site, trigset)
        assert dst in dsts

    eventcounts_file = daq_pref.replace('DAQ-', 'eventcounts-') + '.txt'
    eventcounts = os.path.join(tama_path, eventcounts_file)
    assert os.path.exists(eventcounts)

    with open(eventcounts, 'r') as ec:
        ec_lines = ec.readlines()
        assert len(ec_lines) == len(dsts)

def _command(cmd):
    """
    Given a command as though typed in the shell, execute that command and return (stdout, stderr)
    """
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()

def _call_timecorr(site, output_dir, daq_pref):
    """
    Syntax for timecorr:
    getTimeTable.run siteid output_directory daq_prefix

    Expected console output on success: None
    """
    cmd = '{} {} {} {}'.format(timecorr_exe, site, output_dir, daq_pref)
    out, err = _command(cmd)
    assert not out
    assert not err



def make_timecorr(part_code):
    # build the file in temporary output
    # move the file to permanent location
    # verify
    pass

from db.database_wrapper import DatabaseWrapper

def run_timecorr(night):
    db = DatabaseWrapper('db/fadc_data.db')
    parts = db.retrieve('SELECT p.part11, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.date={}'.format(night))
    print 'FADC parts for {}: {}'.format(night, len(parts))
    for part, ctdprefix in parts:
        try:
            _verify_timecorr_exists(part)
            print 'timecorr exists for', part
        except AssertionError:
            print 'no timecorr for', part
            make_timecorr(part, daq_pref=ctdprefix)




