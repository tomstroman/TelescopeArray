# run_sim_compare.py
# Thomas Stroman, University of Utah, 2017-02-28
# Automate the multiple steps of star simulation and comparison

import os
import re
import argparse

from simulate import get_site_cam

parser = argparse.ArgumentParser()

parser.add_argument('infile')

args = parser.parse_args()
infile = args.infile
all_targets = {
    0: {
        0: {'procyon': ['09013031']},
        1: {'rigel': ['09013021']},
        2: {'jupiter': ['08070920']},
        3: {'bellatrix': ['09013121', '09013026']},
        4: {'castor': ['09013036']},
        5: {'jupiter': ['15041427', '15041423']},
        6: {'deneb': [],
            'capella': []},
        7: {'castor': ['09032726']},
        8: {'epsilon uma': ['09062221']},
        9: {'deneb': ['10120226']},
        10: {'delta dra': []},
        11: {'epsilon uma': []}
        },
    1: {
        0: {'alpha uma': []},
        1: {'gamma dra': []},
        2: {'gamma dra': []},
        3: {'algol': []},
        4: {'vega': []},
        5: {'pollux': []},
        6: {'jupiter': []},
        7: {'jupiter': []},
        8: {'regulus': []},
        9: {'jupiter': []},
        10: {'jupiter': []},
        11: {'jupiter': ['09062209']}
        }
    }

skip_existing = False

targets_by_file = {}
if infile == 'preset':
    skip_existing = True
    infiles = []
    for site, cams in all_targets.items():
        for cam, targets in cams.items():
            for target, partlist in targets.items():
                try:
                    filename = 'input/FDMEAN-{}-{}-{:x}-calibrated.txt'.format(
                            partlist[0], site, cam)
                    print filename
                    targets_by_file[filename] = target
                except IndexError:
                    continue
                infiles.append(filename)
                break # only simulate one target
else:
    infiles = [infile]
    targets_by_file[infile] = 'unknown'

for infile in infiles:
    print infile
    try:
        if not os.path.exists(infile):
            cmd = 'rsync -hPa $TAD:/raidscratch/tstroman/tama/{}.gz input'.format(
                os.path.basename(infile))
            os.system(cmd)
            cmd = 'gunzip input/{}.gz'.format(os.path.basename(infile))
            os.system(cmd)
        assert os.path.exists(infile)

        simfile = infile.replace('calibrated', 'simulated').replace('input', 'output/simulation')
        target = targets_by_file[infile]
        if not os.path.exists(simfile):
            cmd = 'python2 simulate.py {} "{}"'.format(infile, target)
            print cmd
            os.system(cmd)
        assert os.path.exists(simfile)

        sitecam = get_site_cam(infile)
        

        pdf = simfile.replace(
              'simulation', 'pdf').replace(
              '-simulated.txt', '-centroid.pdf').replace(
              'FDMEAN-', 'site{}cam{:02}-{}-'.format(
                    sitecam['site'], sitecam['cam'], target.replace(' ', '_')))

        if not (skip_existing and os.path.exists(pdf)):
            cmd = 'root -l -b -q "compare.C+(\\\"{0}\\\", \\\"{1}\\\", \\\"{2}\\\")"'.format(infile, simfile, pdf)
            print cmd
            os.system(cmd)
    except Exception as err:
        print err