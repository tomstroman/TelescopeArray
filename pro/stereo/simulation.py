# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import subprocess as sp

from glob import glob

def simulate_night(trump_path):
    print trump_path
    assert os.path.isdir(trump_path), 'Not a directory: {}'.format(trump_path)
    run_trump(trump_path)
    prep_md_sim()
    run_md_sim()


def run_trump(trump_path):
    generate_trump_mc(trump_path)
    rts_to_ROOT()
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


def generate_trump_mc(trump_path):
    confs = glob(os.path.join(trump_path, '*.conf'))
    assert 0 < len(confs) <= 2, '{} configurations found (expecting either 1 or 2)'.format(len(confs))

    path_tokens = trump_path.split(os.path.sep)
    trump_exe = os.path.sep.join(path_tokens[:-4] + ['bin', 'trump.run'])
    assert os.path.exists(trump_exe), 'TRUMP not found at {}'.format(trump_exe)

    cmd = '{} *.conf &> trump.out'.format(trump_exe)
    print cmd
    sp.check_output(cmd, shell=True, cwd=trump_path)
    print 'done'




def rts_to_ROOT():
    pass

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
