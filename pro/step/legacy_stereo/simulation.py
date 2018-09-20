# simulation.py
# Thomas Stroman, University of Utah, 2016-12-10
# Code to wrap simulation preparation and execution, which exists as
# various Bash and Python code I've written previously. This will be
# deprecated eventually.

from prep_fadc.raw_to_dst import _command
import os
from glob import glob
import subprocess
import re
from db.fadc_process import _ymdps

processfd = os.path.join(os.getenv('TAHOME'), 'processFD')
prep_trump_stereo_exe = os.path.join(processfd, 'prep-trump-stereo.py')
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
    if not params['is_mc']:
        return None

    geometry_dsts = params['stereo_run'].params.geometry_dsts
    analysis = params['path']
    trump_path = os.path.join(analysis, str(night), 'trump')

    if not glob(os.path.join(trump_path, '*.conf')):
        return 'no TRUMP conf found'

    moslog = os.path.join(analysis, 'logs', 'trump-{}.mosout'.format(night))

    if os.path.exists(moslog):
        with open(moslog, 'r') as mos:
            moslog_content = mos.read()
        if 'MOSRUN: Lost communication' not in moslog_content:
            return None
        else:
            os.remove(moslog)

    cmd = 'mosenv -q -J{night} -b -l -m320 -e python $TSTA/pro/stereo/simulation/run_simulation.py {trump_path} -geobr {geobr} -geolr {geolr} {no_md} &> {moslog}'.format(
        night=night,
        trump_path=trump_path,
        geobr=geometry_dsts['br'],
        geolr=geometry_dsts['lr'],
        no_md='--no_md' if params['stereo_run'].params.skip_md else '',
        moslog=moslog,
    )

    params['mosq'][night] = ('new', None)
    subprocess.Popen(cmd, shell=True)
    return 'added to queue'

def run_md_sim(night, params):
    pass

def verify_sim(night, params):
    """
    Inspect the output from a simulation and ensure completion and self-consistency.
    """
    if not params['is_mc']:
        return None

    analysis = params['path']
    trump_path = os.path.join(analysis, str(night), 'trump')
    moslog_file = os.path.join(analysis, 'logs', 'trump-{}.mosout'.format(night))

    # verify that TRUMP ran and produced output log
    trump_log = os.path.join(trump_path, 'trump.out')

    y, m, d, p, s = _ymdps(night*1000 + 2)

    ymd = 'y{}m{}d{}'.format(y, m, d)
    md_evt = os.path.join(trump_path, '{}p00.txt_md.evt'.format(ymd))
    if not os.path.exists(trump_log):
        return 'TRUMP output missing'

    with open(moslog_file, 'r') as outf:
        moslog = outf.read()

    if not moslog:
        return 'Mosix output empty'

    skip_md = 'Simulation event count: 0' in moslog or 'found 0 part(s)' in moslog or params['stereo_run'].params.skip_md

    with open(trump_log, 'r') as outf:
        try:
            outf.seek(-256, 2)
        except IOError:
            pass # seek operation failure leaves us at beginning of file
        trump_out = outf.read()

    if '***** END CRITERIA MET : Trump will now exit' not in trump_out:
        return 'TRUMP incomplete'

    trigline = re.findall('(?<=triggering FD site:  )(\d:\d+) ?(\d:\d+)?', trump_out)
    fdtrig = dict([map(int, t.split(':')) for t in trigline[0] if t])

    tmax = sum(fdtrig.values())

    if tmax == 0:
        print 'No TRUMP triggers!'
        assert skip_md, 'skip_md not set'
        return 'no TRUMP triggers'

    if not skip_md:
        md_out = os.path.join(trump_path, '{}p00.utafd.out'.format(ymd))
        if not os.path.exists(md_out): # TODO: better verification
            return 'MD output missing'
