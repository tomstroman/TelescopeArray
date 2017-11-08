# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os

from glob import glob

from make_evt import make_evt
from run_trump import run_trump


def simulate_night(trump_path, geo_files):
    print trump_path
    assert os.path.isdir(trump_path), 'Not a directory: {}'.format(trump_path)

    num_configs = len(glob(os.path.join(trump_path, '*.conf')))
    if num_configs == 1:
        is_mono = True
    elif num_configs == 2:
        is_mono = False
    else:
        raise Exception('{} TRUMP configurations found (expecting either 1 or 2)'.format(num_configs))

    rts = run_trump(trump_path, is_mono, geo_files)
    prep_md_sim(rts)
    run_md_sim()



def prep_md_sim(rts):
    _make_evt(rts)
    make_in()
    prepare_path()

def run_md_sim():
    generate_mc2k12_mc()
    split_md_output()
    run_pass2()
    run_pass3()



def _make_evt(rts):
    evt = rts.replace('.rts', 'p00.txt_md.evt')
    make_evt(rts, evt)

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
    rtdata = os.getenv('RTDATA')
    assert rtdata
    parser = argparse.ArgumentParser()
    parser.add_argument('trump_path')
    parser.add_argument('-geobr', default=os.path.join(rtdata, 'fdgeom', 'geobr_joint.dst.gz'))
    parser.add_argument('-geolr', default=os.path.join(rtdata, 'fdgeom', 'geolr_joint.dst.gz'))
    args = parser.parse_args()
    geo_files = {
        'br': args.geobr,
        'lr': args.geolr,
    }
    simulate_night(args.trump_path, geo_files)
