# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import shutil
import subprocess as sp

from distutils import spawn as distutils__spawn
from glob import glob
from math import log10

FIELDS = [
    'event',
    'species',
    'ymd',
    'sec',
    'logE',
    'xcore',
    'ycore',
    'vx',
    'vy',
    'vz',
    'x0',
    'lambda',
    'xmax',
    'logNmax',
]

DIRECT_FIELDS = {
    'event': 0,
    'species': 3,
    'logE': 11,
    'xcore': 12,
    'ycore': 13,
    'vx': 15,
    'vy': 16,
    'vz': 17,
    'x0': 18,
    'lambda': 19,
    'xmax': 20,
}
def simulate_night(trump_path):
    print trump_path
    assert os.path.isdir(trump_path), 'Not a directory: {}'.format(trump_path)
    run_trump(trump_path)
    prep_md_sim()
    run_md_sim()


def run_trump(trump_path):
    rts = generate_trump_mc(trump_path)
    try:
        rts_to_ROOT(rts)
    except AssertionError: # this is not a critical step and can be fixed later
        print 'Warning! No ROOT file generated.'
    split_fd_output()
    run_fdplane()

def prep_md_sim():
    make_evt()
    make_in()
    prepare_path()

def run_md_sim():
    generate_mc2k12_mc()
    split_md_output()
    run_pass2()
    run_pass3()


def generate_trump_mc(trump_path, regenerate=False):
    '''
    Locate the TRUMP executable and configuration files.
    Run TRUMP (this may take minutes or hours).
    Find the .rts file and move it to trump_path.

    Return the final location of the .rts file.
    '''

    confs = glob(os.path.join(trump_path, '*.conf'))
    assert 0 < len(confs) <= 2, '{} configurations found (expecting either 1 or 2)'.format(len(confs))

    path_tokens = trump_path.split(os.path.sep)
    trump_exe = os.path.sep.join(path_tokens[:-4] + ['bin', 'trump.run'])
    assert os.path.exists(trump_exe), 'TRUMP not found at {}'.format(trump_exe)

    output = os.path.join(trump_path, 'trump.out')

    if regenerate or not os.path.exists(output):
        cmd = '{} *.conf &> {}'.format(trump_exe, output)
        sp.check_output(cmd, shell=True, cwd=trump_path)

        rts_files = glob(os.path.join(trump_path, '*', '*.rts'))
        if len(rts_files) <> 1:
            print 'Zero or multiple RTS files found:', rts_files

        bn = os.path.basename(rts_files[0])
        rts = os.path.join(trump_path, bn)

        if os.path.exists(rts):
            os.remove(rts)
        shutil.move(rts_files[0], trump_path)
    else:
        rts = glob(os.path.join(trump_path, '*.rts'))[0]

    return rts

def rts_to_ROOT(rts):
    rts_parser_exe = os.path.join(os.getenv('TAHOME'), 'trump', 'bin', 'rtsparser.run')
    rts_to_root_exe = rts_parser_exe.replace('rtsparser.run', 'rts2root.C')
    for exe in [rts_parser_exe, rts_to_root_exe]:
        assert os.path.exists(exe), 'Not found: {}'.format(exe)
    assert distutils__spawn.find_executable('root'), 'ROOT appears not to be installed'

    cmd = '{rtsparser} -Etslpcgu {rts}'.format(rtsparser=rts_parser_exe, rts=rts)
    output = sp.check_output(cmd, shell=True)
    lines = output.split('\n')[:-1]

    buf = ''
    last_event = None
    for line in lines:
        text, last_event = _format_line(line, last_event)
        buf += text

    temp_file = '{}.txt'.format(rts)
    with open(temp_file, 'w') as rts_txt:
        rts_txt.write(buf)

    cmd = 'root -l -q "{0}(\\"{1}\\")"'.format(rts_to_root_exe, temp_file)
    sp.check_output(cmd, shell=True)
    os.remove(temp_file)

def _format_line(line, last_event):
    d = _get_dict(line)
    if d['event'] == last_event:
        return '', last_event

    buf = ' '.join([d[f] for f in FIELDS])
    buf += '\n'
    return buf, d['event']

def _get_dict(line):
    s = line.split()
    d = {
        'ymd' : ''.join(s[4:7]),
        'sec' : '{sec}.{nanosec}'.format(
            sec=3600*int(s[7]) + 60*int(s[8]) + int(s[9]),
            nanosec=s[10],
        ),
        'logNmax' : '{0:.5}'.format(log10(float(s[21]))),
    }


    d.update({field: s[index] for field, index in DIRECT_FIELDS.items()})
    return d



def split_fd_output():
    pass

def run_fdplane():
    pass


def make_evt():
    pass

def make_in():
    pass

def prepare_path():
    pass


def generate_mc2k12_mc():
    pass

def split_md_output():
    pass

def run_pass2():
    pass

def run_pass3():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trump_path')
    args = parser.parse_args()
    simulate_night(args.trump_path)
