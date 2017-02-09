# simulate.py
# Thomas Stroman, University of Utah, 2017-02-08
# Given a text file containing output produced by get_fdmean.py, determine
# appropriate arguments and call the TRUMP ray-tracing routines to simulate
# a particular star.

import argparse
from query_stellarium import query

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Name of .txt file with data')
    parser.add_argument('name', help='Name or search string of object to simulate, e.g. "alpha boo"')

    args = parser.parse_args()
    with open(args.filename, 'r') as infile:
        lines = infile.readlines()
    jstart = lines[0].split()[0]
    jend = lines[-1].split()[0]

    dur = int((float(jend) - float(jstart)) * 86400) + 1
    print "Duration, start to finish, in seconds:", dur
    sim_params = query(jstart, args.name)
    print sim_params
    # hard-code some of this; TODO: make it smarter
    cmd = '$TRUMP/bin/star.run -rays 100 -dt 1.0 -q -geo $RTDATA/fdgeom/geobr_joint.dst.gz -mir 2 -o test.txt '

    cmd += '-dur {} '.format(dur)

    for k, v in sim_params.items():
        cmd += '-{} {} '.format(k, v)

    print cmd



