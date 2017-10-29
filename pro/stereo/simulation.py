# simulation.py
# Thomas Stroman, University of Utah 2017-10-28
# Replace runtrump.sh, prepmdsim.sh, runmdsim.sh

import argparse
import os


def simulate_night(trump_path):
    print trump_path
    assert os.path.isdir(trump_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trump_path')
    args = parser.parse_args()
    simulate_night(args.trump_path)

