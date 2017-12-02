# boundary-crossing-tracks.py
# Thomas Stroman, University of Utah, 2017-12-01
# Scan through processed data from Telescope Array showers to identify cosmic ray events
# that meet very specific criteria and collect information about a useful subset of PMTs.

import argparse
import subprocess as sp

EVENT_SEPARATOR = 'START OF EVENT'

def dump_and_parse(dst_file):
    cmd = 'dstdump +brplane +lrplane {}'.format(dst_file)
    dump = sp.check_output(cmd, shell=True)
    events = dump.split(EVENT_SEPARATOR)[1:] # first entry is just the filename; skip it
    return events

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dst')
    args = parser.parse_args()
    events = dump_and_parse(args.dst)
