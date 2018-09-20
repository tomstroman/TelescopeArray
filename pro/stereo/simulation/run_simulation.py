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

    # skip the MD simulation if --no_md was specified
    if not geo_files['md']:
        return

    md_in, md_dir = prep_md_sim(rts)

    if md_in is not None:
        run_md_sim(md_in, md_dir)


def run_md_sim(md_in, md_dir):
    dst, outfile = generate_mc2k12_mc(md_in, md_dir)
    filtered_dst = filter_md_output(dst)
    if filtered_dst is None:
        return

    dst2 = run_pass2(filtered_dst, outfile)
    if os.path.getsize(dst2) < 100:
        return
    dst3 = run_pass3(dst2, outfile)


def generate_mc2k12_mc(md_in, md_dir):
    path_tokens = md_dir.split(os.path.sep)
    mc2k12_exe = os.path.sep.join(path_tokens[:-4] + ['bin', 'mc2k12_main'])
    assert os.path.exists(mc2k12_exe), 'mc2k12 not found at {}'.format(mc2k12_exe)

    dst = os.path.join(md_dir, os.path.basename(md_in).replace('.txt_md.in', '.md-sim.dst.gz'))
    outfile = md_in.replace('.txt_md.in', '.utafd.out')

    cmd = '{} -o {} {} &> {}'.format(mc2k12_exe, dst, md_in, outfile)
    print cmd
    sp.check_output(cmd, shell=True)
    return dst, outfile

def filter_md_output(dst):
    cmd = 'dstlist {}'.format(dst)
    output = sp.check_output(cmd, shell=True)
    lines = output.split('\n')[0:]
    events_with_hraw1 = []
    for i, line in enumerate(lines):
        if 'hraw1' in line:
            events_with_hraw1.append(i)
    if not events_with_hraw1:
        return None

    new_dst = dst.replace('.md-sim.dst.gz', '.md.dst.gz')
    want = dst.replace('.md-sim.dst.gz', '.want')
    with open(want, 'w') as wantfile:
        wantfile.write('\n'.join(map(str, events_with_hraw1)))
        wantfile.write('\n')
    cmd = 'dstsplit -w {} -o {} {}'.format(want, new_dst, dst)
    sp.check_output(cmd, shell=True)
    return new_dst



def run_pass2(dst, outfile):
    dst2 = dst.replace('.dst.gz', '.ps2.dst.gz')
# TODO: see if this needs to be made local
    pass2_exe = '/home/tstroman/UTAFD/build/std-build/release/bin/stps2_main'
    cmd = '{} -det 34 -o {} {} >> {} 2>&1'.format(pass2_exe, dst2, dst, outfile)
    sp.check_output(cmd, shell=True)
    return dst2

def run_pass3(dst2, outfile):
    dst3 = dst2.replace('.md.ps2.dst.gz', '.down.dst.gz')
# TODO: see if this needs to be made local
    pass3_exe = '/home/tstroman/UTAFD/build/std-build/release/bin/stpln_main'
    cmd = '{} -det 34 -o {} {} >> {} 2>&1'.format(pass3_exe, dst3, dst2, outfile)
    sp.check_output(cmd, shell=True)
    return dst3

if __name__ == '__main__':
    rtdata = os.getenv('RTDATA')
    assert rtdata
    parser = argparse.ArgumentParser()
    parser.add_argument('trump_path')
    parser.add_argument('-geobr', default=os.path.join(rtdata, 'fdgeom', 'geobr_joint.dst.gz'))
    parser.add_argument('-geolr', default=os.path.join(rtdata, 'fdgeom', 'geolr_joint.dst.gz'))
    parser.add_argument('--no_md', action="store_true")
    args = parser.parse_args()
    geo_files = {
        'br': args.geobr,
        'lr': args.geolr,
        'md': not args.no_md,
    }
    simulate_night(args.trump_path, geo_files)
