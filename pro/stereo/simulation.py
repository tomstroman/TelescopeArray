# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import re
import shutil
import subprocess as sp

from collections import defaultdict
from glob import glob

import utils

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

    run_trump(trump_path, is_mono, geo_files)
    prep_md_sim()
    run_md_sim()


def run_trump(trump_path, is_mono, geo_files):
    rts, new_run = generate_trump_mc(trump_path)
    try:
        utils.rts_to_ROOT(rts)
    except AssertionError: # this is not a critical step and can be fixed later
        print 'Warning! No ROOT file generated.'
    site_paths = {}
    for site in ['br', 'lr']:
        site_name = 'black-rock' if site == 'br' else 'long-ridge'
        site_path = os.path.join(trump_path, site_name)
        if os.path.exists(site_path):
            site_paths[site] = site_path
    if is_mono and new_run:
        split_mono_fd_output(site_paths)
    run_fdplane(site_paths, geo_files)

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


    path_tokens = trump_path.split(os.path.sep)
    trump_exe = os.path.sep.join(path_tokens[:-4] + ['bin', 'trump.run'])
    assert os.path.exists(trump_exe), 'TRUMP not found at {}'.format(trump_exe)

    output = os.path.join(trump_path, 'trump.out')

    if regenerate or not os.path.exists(output):
        new_run = True
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
        new_run = False
        rts = glob(os.path.join(trump_path, '*.rts'))[0]


    return rts, new_run

def split_mono_fd_output(site_paths):
    """
    Find the output from the monocular TRUMP simulation and split it
    into one file per "part" by recording the indices of events belonging
    to each part and using "dstsplit" to isolate them.
    """
    for site, site_path in site_paths.items():
        dsts = glob(os.path.join(site_path, '*d??.dst.gz'))
        assert len(dsts) == 1, 'Did not find unique mono DST in {}'.format(site_path)
        dst = dsts[0]
        cmd = 'dstdump -{site}raw {dst}'.format(site=site, dst=dst)
        dump = sp.check_output(cmd, shell=True, stderr=sp.STDOUT)

        events_by_part = defaultdict(list)
        for i, part in enumerate(re.findall('[0-9]+(?=  event_code)', dump)):
            events_by_part[part].append(i)

        eventlist = os.path.join(site_path, 'want')
        for part, events in events_by_part.items():
            with open(eventlist, 'w') as want:
                want.write('\n'.join(map(str, events)))

            output = dst.replace('.dst.gz', 'p{}.dst.gz'.format(part))
            cmd = 'dstsplit -w {} -o {} {}'.format(eventlist, output, dst)
            sp.check_output(cmd, shell=True)

        break


def run_fdplane(site_paths, geo_files):
    for site, site_path in site_paths.items():
        dsts = glob(os.path.join(site_path, '*p??.dst.gz'))
        geo = geo_files[site]
        for dst in dsts:
            base_dst = os.path.basename(dst)
            out = base_dst.replace('dst.gz', 'fdplane.out')
            cmd = '$TAHOME/fdplane/bin/fdplane.run -geo {} -output 1000 {} &> {}'.format(geo, base_dst, out)
            sp.check_output(cmd, shell=True, cwd=site_path)
        junk_dsts = glob(os.path.join(site_path, '*d??.dst.gz'))
        for dst in junk_dsts:
            os.remove(dst)

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
