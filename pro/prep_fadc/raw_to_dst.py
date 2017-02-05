# raw_to_dst.py
# Thomas Stroman, University of Utah, 2016-11-27
# Functions for preparing DST files from raw Telescope Array FADC data.

import os
import time
import hashlib
import re

from glob import glob

from utils import _command, _ymdps, _timecorr_path, _camlist, get_jstart
from collections import defaultdict

site_names = {'0': 'black-rock', '1': 'long-ridge'}
site_ids = {v: k for k, v in site_names.items()}
import subprocess
tahome = os.getenv('TAHOME')
tama_exe = os.path.join(tahome, 'tama/bin/tama.run')
timecorr_exe = os.path.join(tahome, 'getTimeTable/bin/getTimeTable.run')
dstlist = os.path.join(os.getenv('TADSTBIN'), 'dstlist.run')

scratch = '/raidscratch/tstroman/prep_fadc'
fdped_by_part = '/scratch1/fdpedv'
fdped_by_night = os.path.join(os.getenv('RTDATA'), 'calibration', 'fdped')

if not os.path.exists(scratch):
    os.system('mkdir -p ' + scratch)

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
    cmd = 'rsync -ahP {} {}'.format(source, remote_path)
    print cmd
    out, err = _command(cmd)
    print out.strip().split('\n')[-2]
    assert not err
    final_path = os.path.join(key, tokens[-2], tokens[-1])
    print 'Confirming existence of', final_path
    while not os.path.exists(final_path):
        print 'Waiting 1 second'
        time.sleep(1)

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

def _verify_dst(dst, prolog, out, err, expected_triggers):
    error = False
    try:
        with open(prolog, 'r') as prolog_file:
            prolog_content = prolog_file.read()
        tama_kept = re.findall('(?<=TAMA_KEPT )\d+', prolog_content)
        bytes_out = re.findall('(?<=BYTES_OUT )\d+', prolog_content)
        assert len(tama_kept) == 1
        assert len(bytes_out) == 1
        assert os.stat(dst).st_size == int(bytes_out[0])
        assert int(tama_kept[0]) == expected_triggers
        with open(out, 'r') as out_file:
            out_content = out_file.readlines()
        triglines = [l for l in out_content if l.startswith('trigger')]
        assert len(triglines) == expected_triggers
        times = {}
        for index in [0, -1]:
            hms = triglines[index].split()[5].split(':')
            times[index] = sum([float(hms[i]) * 60**(2-i) for i in range(3)])

        return 'exists', (tama_kept, times[-1] - times[0], bytes_out, int(error))
    except:
        raise
        return _brute_verify_dst(dst, prolog, out, err, expected_triggers)

validate_raw_exe = os.path.join(os.getenv('TAHOME'), 'processFD', 'validate_raw.sh')
def _brute_verify_dst(dst, prolog, out, err, expected_triggers):
    try:
        cmd = '{} {} {}'.format(validate_raw_exe, dst, expected_triggers)
        return 'exists', subprocess.check_output(cmd.split()).strip().split()
    except:
        return 'error', (0, 0, 0, 1)

def make_tama(part, daqcams, ctdprefix, params):
    daq_pref = os.path.basename(ctdprefix)
    #print 'tama', part, daq_pref
    timecorr = _timecorr_path(part)


    y, m, d, p, s = _ymdps(part)

    timecorr_lines = open(timecorr, 'r').readlines()
    ctd_triggers = len(timecorr_lines)
    cams = _camlist(daqcams)
    ctd_file_template = ctdprefix + '-{}-{{0:07}}.d.bz2'.format(s)
    cam_file_template = ctdprefix.replace('/ctd/', '/camera{0:02}/') + '-{}-{{0:x}}'.format(s)
    cam_files_template = ' '.join([cam_file_template.format(c) + '-{0:07}.d.bz2' for c in cams])

    rel_dir = os.path.join(site_names[s], '{}{}{}'.format(y, m, d))
    output_dir = os.path.join(scratch, rel_dir)

    eventcounts = os.path.join(output_dir, daq_pref.replace('DAQ-', 'eventcounts-') + '.txt')

    mosix_dir = os.path.join(output_dir, 'mos')
    os.system('mkdir -p ' + mosix_dir)
    os.system('cp {} {}'.format(timecorr, output_dir))

    dst_output_template = os.path.join(output_dir, daq_pref + '-{}-{{0:07}}.dst.gz'.format(s))
    prolog_template = dst_output_template.replace('.dst.gz', '.prolog')
    tama_code = '{}{}{}{}'.format(y[2:], m, d, p)
    stdout_template = os.path.join(mosix_dir,  os.path.basename(dst_output_template).replace('.dst.gz', '.mosout'))
    stderr_template = stdout_template.replace('.mosout', '.moserr')
    cmd_template = 'mosenv -q -J{{1}} -b -l -m3072 -e {} -o {} -r {} {} {} > {} 2> {}'.format(tama_exe, dst_output_template, tama_code, ctd_file_template, cam_files_template, stdout_template, stderr_template)

    file_templates = [dst_output_template,
                      prolog_template,
                      stdout_template,
                      stderr_template]

    ijstart = int(get_jstart(timecorr, timecorr_lines[0]))
    status = defaultdict(list)
    ecountsbuffer = ''
    for trigset in range(0, ctd_triggers, 256):
        jobstring = '{}-{:07}'.format(part, trigset)
        jobid = int(hashlib.md5(jobstring).hexdigest()[-7:], 16)
        assert jobid < 2147483648 # needs to fit inside a 32-bit signed integer

        dst, prolog, out, err = [t.format(trigset) for t in file_templates]
        if jobid in params['mosq']:
            status['found'].append(jobstring)
        elif os.path.exists(prolog):
            expected_triggers = min(256, ctd_triggers - trigset)
            jobstatus, ecline = _verify_dst(dst, prolog, out, err, expected_triggers)

            if jobstatus == 'exists':
                ecountsbuffer += '{:07} {} {} {} {}\n'.format(trigset, *ecline)
                status['exists'].append((jobstring, output_dir))
            elif jobstatus == 'error':
                status['error'].append(jobstring)
        else:
            cmd = cmd_template.format(trigset, jobid)
            print cmd
            status['submitted'].append(jobstring)
            params['mosq'][jobid] = ('new', None)
            subprocess.Popen(cmd, shell=True)
            #break # temporary

    if ecountsbuffer:
        with open(eventcounts, 'w') as ecfile:
            ecfile.write(ecountsbuffer)

    for k, v in status.items():
        print '{}: {}'.format(k, len(v))

    return status

def run_tama(night, params):
    db = DatabaseWrapper('db/fadc_data.db')
    parts = db.retrieve('SELECT p.part11, p.site, p.daqcams, f.ctdprefix FROM Parts AS p JOIN Filesets AS f ON p.part11=f.part11 WHERE p.date={}'.format(night))

    allstatus = {0: defaultdict(list), 1: defaultdict(list)}
    for part, site, daqcams, ctdprefix in parts:
        daq_pref = os.path.basename(ctdprefix)
        try:
            verify_tama_exists(part, daq_pref)
        except AssertionError:
            print 'no TAMA for', part, ctdprefix
            partstatus = make_tama(part, daqcams, ctdprefix, params)
            for k, v in partstatus.items():
                allstatus[site][k] += v

    report = {}
    for site, status in allstatus.items():
        if not status:
            continue

        keys = status.keys()
        if keys == ['exists']:
            out_dir = list(set([v[1] for v in status['exists']]))[0]
            _sync_to_tama(out_dir)
            report[site] = 'success'
            continue

        if 'error' in keys:
            report[site] = 'error'
            continue
        if 'submitted' in keys:
            report[site] = 'submitted to queue'
            continue
        if 'found' in keys:
            report[site] = 'found in queue'
            continue

    if all([r == 'success' for r in report.values()]):
        return None
    return str(report)

def verify_fdped_exists(parts):
    fdped_part_template = os.path.join(fdped_by_part, '{0}', '{1}{2}{3}', 'y{1}m{2}d{3}p{4}.ped.dst.gz')
    fdped_night_template = os.path.join(fdped_by_night, '{0}', 'y{1}m{2}d{3}.ped.dst.gz')
    exists = {}
    for part in parts:
        y, m, d, p, s = _ymdps(part)
        fdped_part = fdped_part_template.format(site_names[s], y, m, d, p)
        exists[p] = os.path.exists(fdped_part)
    fdped_night = fdped_night_template.format(site_names[s], y, m, d)
    exists['night'] = os.path.exists(fdped_night)
    assert all(exists.values())


def run_fdped(night, params):
    db = DatabaseWrapper('db/fadc_data.db')
    parts = db.retrieve('SELECT p.part11, p.site FROM Parts AS p WHERE p.date={}'.format(night))
    print 'checking fdped for', night, len(parts)
    parts_by_site = defaultdict(list)
    for part, site in parts:
        parts_by_site[site].append(part)

    for site, parts_list in parts_by_site.items():
        try:
            verify_fdped_exists(parts_list)
        except AssertionError:
            print 'Missing FDPED for', site, night
