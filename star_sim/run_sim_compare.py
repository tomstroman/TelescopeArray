# run_sim_compare.py
# Thomas Stroman, University of Utah, 2017-02-28
# Automate the multiple steps of star simulation and comparison

import os
import re
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('infile')

args = parser.parse_args()
infile = args.infile


assert os.path.exists(infile)

simfile = infile.replace('calibrated', 'simulated').replace('input', 'output/simulation')

assert os.path.exists(simfile)

pdf = simfile.replace('simulation', 'pdf').replace('-simulated.txt', '-centroid.pdf')

cmd = 'root -l -b -q "compare.C+(\"{0}\", \"{1}\", \"{2}\")"'.format(infile, simfile, pdf)
print cmd