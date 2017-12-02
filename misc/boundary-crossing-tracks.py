# boundary-crossing-tracks.py
# Thomas Stroman, University of Utah, 2017-12-01
# Scan through processed data from Telescope Array showers to identify cosmic ray events
# that meet very specific criteria and collect information about a useful subset of PMTs.

import argparse
import re
import subprocess as sp

from collections import defaultdict


EVENT_SEPARATOR = 'START OF EVENT'

SDPQ_MIN = 80.0
SDPQ_MAX = 100.0
SDPQ_REGEX = re.compile('(?<=SDP theta, phi: )[0-9\.]*(?= )')

# match a 21-field line of text (with some fields known) and retrieve specific fields
# roughly analogous to awk '(NR==21 && $18==1 && $19==1) {print $4, $6, $8, $9, $17}'
PMT_REGEX = re.compile(' *\d+ \[ cam +(\d+) tube +(\d+) \] +([\d\.]+) +([\d\.]+) +.* +([\d\.]+) +1 +1 +\d+ +\d+')

SIGMA_MIN = 6.0


def dump_and_parse(dst_file):
    cmd = 'dstdump +brplane +lrplane {}'.format(dst_file)
    dump = sp.check_output(cmd, shell=True)
    events = dump.split(EVENT_SEPARATOR)[1:] # first entry is just the filename; skip it
    for event in events:
        is_good, row_times = process(event)
        if is_good:
            print 'Good event with {} tubes'.format(len(row_times))
        else:
            print 'Bad event'

def process(event):
    matches = re.findall(SDPQ_REGEX, event)
    try:
        assert len(matches) == 1
        sdp_theta = float(matches[0])
        print 'sdp_theta:', sdp_theta
        assert SDPQ_MIN < sdp_theta < SDPQ_MAX

        good_tubes = re.findall(PMT_REGEX, event)
        boundary_tubes = defaultdict(list)
        for tube in good_tubes:
            cam, pmt, npe, time, sigma = [f(n) for f,n in zip([int, int, float, float, float], tube)]
            if sigma > SIGMA_MIN:
                row = (16 if (cam % 2 == 0) else 0) + (pmt % 16) # based on camera geometry
                if 13 <= row < 19:
                    boundary_tubes[row].append((npe, time))
        print 'boundary_tubes:', boundary_tubes.keys()
        assert len(boundary_tubes) == 6

        row_times = {
            row: weighted_average(npe_times) for row, npe_times in boundary_tubes.items()
        }
        return True, row_times

    except AssertionError:
        return False, None

def weighted_average(npe_times):
    if len(npe_times) == 1:
        return npe_times[1]

    numerator = sum([npe*time for npe, time in npe_times])
    denominator = sum([npe for npe, time in npe_times])
    return numerator / denominator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dst')
    args = parser.parse_args()
    events = dump_and_parse(args.dst)
