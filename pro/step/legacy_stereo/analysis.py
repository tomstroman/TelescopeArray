# analysis.py
# Thomas Stroman, University of Utah, 2016-12-15
# Code to wrap stereo FADC analysis code, existing as Python code I've
# written previously. This will be deprecated eventually.

import logging
import os
import re
import subprocess

from utils import _command

# This is produced every time we read a DST file. Strip it from stderr.
dst_stderr = ' $$$ dst_get_block_ : End of input file reached\n'

def analyze_and_dump(night, params):
    stereo_exe = params['stereo_run'].stereo_dot_py
    analysis = params['path']
    path = os.path.join(analysis, str(night))

    if not os.path.isdir(path): # path may not exist!
        os.system('mkdir -p {}'.format(path))

    stdout = os.path.join(path, 'stereo_log.out.txt')
    stderr = stdout.replace('out.txt', 'err.txt')
    cmd = 'python {} {} > {} 2> {}'.format(stereo_exe, path, stdout, stderr)
    #print cmd
    #return None
    #out, err = _command(cmd)
    a = subprocess.Popen(cmd, shell=True)
    a.wait()
    out = open(stdout, 'r').read()
    err = open(stderr, 'r').read()

    if 'Fatal error' in out:
        logging.error('Analysis failed for %s', night)
        return 'fatal error in analysis'

    reperr = err.replace(dst_stderr, '')
    if reperr:
        print 'analyze_and_dump: stderr below'
        print reperr
        return 'stderr detected'

    queued = re.findall('Submitted \d+ job\(s\) to queue', out)
    

    if queued:
        print 'analyze_and_dump:', queued[0]
        waitcount = out.count('Too many queued jobs')
        if waitcount:
            print 'WARNING: Spent {} seconds in submission cooldown'.format(waitcount*60)
        return 'Profiles added to queue'

    in_progress_count = out.count('is being produced by PID')
    if in_progress_count:
        print 'Waiting for profile(s) profile from {} event(s).'.format(in_progress_count)
        return 'Profiles found in queue'

    error_count = out.count('Error: missing output files')
    if error_count:
        print 'Missing expected output for {} event(s). For details see: \n{}'.format(error_count, stdout)
        return 'analysis complete with error'

    print 'Complete!'
    return 'analysis complete'


