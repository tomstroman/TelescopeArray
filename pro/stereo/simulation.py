# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import shutil
import subprocess as sp

from distutils import spawn as distutils__spawn
from glob import glob

def simulate_night(trump_path):
    print trump_path
    assert os.path.isdir(trump_path), 'Not a directory: {}'.format(trump_path)
    run_trump(trump_path)
    prep_md_sim()
    run_md_sim()


def run_trump(trump_path):
    rts = generate_trump_mc(trump_path)
    rts_to_ROOT(rts)
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

    # TODO: use Python for this since it's failing
    magic_cmd = '''{rtsparser} -Etslpcgu {rts} | gawk '$1 != o {{print $1,$4,$5*10000+$6*100+$7,3600*$8+60*$9+$10 "." $11,$12,$13,$14,$16,$17,$18,$19,$20,$21,log($22)/log(10.)}} {{o=$1}}' > {rts}.txt'''.format(rtsparser=rts_parser_exe, rts=rts)
    print magic_cmd
    sp.check_output(magic_cmd, shell=True)

    cmd = 'root -l -q "{0}(\"{1}.txt\")"'.format(rts_to_root_exe, rts)
    sp.check_output(cmd, shell=True)
    os.remove('{}.txt'.format(rts))





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
