# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os


def simulate_night(trump_path):
    run_trump()
    prep_md_sim()
    run_md_sim()
    print trump_path
    assert os.path.isdir(trump_path)


def run_trump():
    generate_trump_mc()
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


def generate_trump_mc():
    pass

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
