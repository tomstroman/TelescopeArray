# simulation.py
# Thomas Stroman, University of Utah, 2016-12-10
# Code to wrap simulation preparation and execution, which exists as
# various Bash and Python code I've written previously. This will be
# deprecated eventually.

from prep_fadc.raw_to_dst import _command
import os
from glob import glob
import subprocess

processfd = os.path.join(os.getenv('TAHOME'), 'processFD')
prep_trump_stereo_exe = os.path.join(processfd, 'prep-trump-stereo.py')
runtrump_exe = os.path.join(processfd, 'runtrump.sh')
def verify_data(night, params):
    pass

def prep_trump_sim(night, params):
    """
    Call legacy code to prepare a TRUMP simulation from configuration templates.
    """
    assert 'is_mc' in params
    template = params['is_mc']
    if not template:
        return None

    cmd = '{} {} {}'.format(prep_trump_stereo_exe, template, night)
    output = os.path.join(params['path'], str(night), 'trump', '*.conf')
    if glob(output):
        return None

    out, err = _command(cmd)
    if out:
        print 'prep_trump_sim:'
        print out
    assert not err

def run_trump_sim(night, params):
    """
    Call legacy code that runs TRUMP, uses its output for a tandem MC simulation
    of Middle Drum, and performs initial event reconstruction.
    """
    analysis = params['path']
    trump_path = os.path.join(analysis, str(night), 'trump')

    if not glob(os.path.join(trump_path, '*.conf')):
        return 'no TRUMP conf found'

    moslog = os.path.join(analysis, 'logs', 'trump-{}.mosout'.format(night))

    if os.path.exists(moslog):
        return None

    cmd = 'mosenv -q -J{} -b -l -m320 -e {} {} &> {}'.format(night, runtrump_exe, trump_path, moslog)

    params['mosq'][night] = ('new', None)
    subprocess.Popen(cmd, shell=True)
    return 'added to queue'

def run_md_sim(night, params):
    pass
