# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import re
import subprocess as sp

from glob import glob

from prep_md import prep_md_sim
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

    md_in, md_dir = prep_md_sim(rts)

    if md_in is not None:
        run_md_sim(md_in, md_dir)


def run_md_sim(md_in, md_dir):
    generate_mc2k12_mc(md_in, md_dir)
    split_md_output()
    run_pass2()
    run_pass3()


def generate_mc2k12_mc(md_in, md_dir):
    path_tokens = md_dir.split(os.path.sep)
    mc2k12_exe = os.path.sep.join(path_tokens[:-4] + ['bin', 'mc2k12_main'])
    assert os.path.exists(mc2k12_exe), 'mc2k12 not found at {}'.format(mc2k12_exe)

    dst = os.path.join(md_dir, os.path.basename(md_in).replace('.txt_md.in', '.md-sim.dst.gz'))
    outfile = md_in.replace('.txt_md.in', '.utafd.out')

    cmd = '{} -o {} {} &> {}'.format(mc2k12_exe, dst, md_in, outfile)
    print cmd
    sp.check_output(cmd, shell=True)

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
