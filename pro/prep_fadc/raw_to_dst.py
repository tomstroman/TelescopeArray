# raw_to_dst.py
# Thomas Stroman, University of Utah, 2016-11-27
# Functions for preparing DST files from raw Telescope Array FADC data.

import os
from glob import glob
site_names = {'0': 'black-rock', '1': 'long-ridge'}
site_ids = {v: k for k, v in site_names.items()}
import subprocess
tahome = os.getenv('TAHOME')
tama_exe = os.path.join(tahome, 'tama/bin/tama.run')
timecorr_exe = os.path.join(tahome, 'getTimeTable/bin/getTimeTable.run')
dstlist = os.path.join(os.getenv('TADSTBIN'), 'dstlist.run')

scratch = '/scratch/tstroman/prep_fadc'
if not os.path.exists(scratch):
    os.system('mkdir -p ' + scratch)

def _command(cmd):
    """
    Given a command as though typed in the shell, execute that command and return (stdout, stderr)
    """
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    return p.communicate()

def _get_tama_mounts():
    """
    Make sure remote directories locally known as /tama_0 and /tama_1
    are mounted, and identify their remote location.
    """
    out, err = _command('mount')
    #print out
    mounts = [tuple(line.split()) for line in out.split('\n')[:-1]]
    #tama_mounts = {}
    #for line in mounts:
        #if 'tama' in line:
            
    tama_mounts = {line[2]: line[0] for line in mounts if line[2].startswith('/tama_')}
    assert '/tama_0' in tama_mounts.keys()
    assert '/tama_1' in tama_mounts.keys()
    return tama_mounts
    
tama_mounts =  _get_tama_mounts()
    
from db.fadc_process import _timecorr_path, _ymdps

def _verify_timecorr_exists(part_code):
    """
    Check for the existence of timecorr file in the expected final location.
    """    
    timecorr = _timecorr_path(part_code)
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

def make_timecorr(part_code, daq_pref):
    # build the file in temporary output
    # verify new file was built
    y, m, d, p, s = _ymdps(part_code)


    timecorr = _timecorr_path(part_code)
    print timecorr
    
    rel_dir = os.path.join(site_names[s], '{}{}{}'.format(y, m, d))

    output_dir = os.path.join(scratch, rel_dir)
    
    
    
    os.system('mkdir -p ' + output_dir)

    _call_timecorr(s, output_dir, daq_pref)
    
    new_file = os.path.join(output_dir, os.path.basename(timecorr))

    assert os.path.exists(new_file)
    return new_file    

    
def _sync_to_tama(source):
    """
    Infer destination path from source directory and copy with rsync.
    """
    tokens = source.split(os.path.sep)
    sitename = tokens[-2]
    key = '/tama_' + site_ids[sitename]
    remote_path = os.path.join(tama_mounts[key], sitename)
    cmd = 'rsync -aP {} {}'.format(source, remote_path)
    print cmd
    out, err = _command(cmd)
    
    assert not err

from db.database_wrapper import DatabaseWrapper

def run_timecorr(night, _params):
    db = DatabaseWrapper('db/fadc_data.db')
    parts = db.retrieve('SELECT p.part11, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.date={}'.format(night))
    print 'FADC parts for {}: {}'.format(night, len(parts))
    
    create_attempts = {}
    failures = 0
    for part, ctdprefix in parts:
        try:
            _verify_timecorr_exists(part)
            #print 'timecorr exists for', part
        except AssertionError:
            print 'no timecorr for', part, ctdprefix
            new_timecorr = make_timecorr(part, daq_pref=ctdprefix)
            create_attempts[part] = new_timecorr
    
    if create_attempts:
        for output in set([os.path.dirname(v) for v in create_attempts.values()]):
            _sync_to_tama(output)
    
        for part in create_attempts.keys():
            try:
                _verify_timecorr_exists(part)
            except AssertionError:
                failures += 1
        if failures > 0:
            return 'timecorr failed'
        
    return None



