# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os
import re

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

    num_md_events = prep_md_sim(rts)

    if num_md_events > 0:
        run_md_sim()



def prep_md_sim(rts):
    evt, num_events = _make_evt(rts)
    if num_events > 0:
        make_in(evt)
        prepare_path()
    return num_events

def run_md_sim():
    generate_mc2k12_mc()
    split_md_output()
    run_pass2()
    run_pass3()



def _make_evt(rts):
    evt = rts.replace('.rts', 'p00.txt_md.evt')
    num_events = make_evt(rts, evt)
    return evt, num_events

def make_in(evt):
    md_in = evt.replace('txt_md.evt', 'txt_md.in')
# get YYYYMMDD from yYYYYmMMdDDp00.txt_md.evt
    ymd = ''.join(
        re.findall(
            'y([0-9]{4})m([0-9]{2})d([0-9]{2})p00\.txt_md\.evt',
            os.path.basename(evt)
        )[0]
    )
    in_contents  = 'output file:  ./foo.out\n'
    in_contents += '            setNr:  {}00\n'.format(ymd)
    in_contents += '           use DB:  YES\n'
    in_contents += '            iseed:  -8111111\n'
    in_contents += '         detector:  ta_md.conf\n'
    in_contents += '     shift origin:  NO\n'
    in_contents += '             nevt:  1\n'
    in_contents += '       event type:  MC_SHOWER\n'
    in_contents += ' \n'
    with open(md_in, 'w') as infile:
        infile.write(in_contents)
    print 'created', md_in


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
