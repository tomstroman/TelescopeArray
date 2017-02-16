# simulate.py
# Thomas Stroman, University of Utah, 2017-02-08
# Given a text file containing output produced by get_fdmean.py, determine
# appropriate arguments and call the TRUMP ray-tracing routines to simulate
# a particular star.

import argparse
import os
import re
import sys
from query_stellarium import query

def _get_site_cam(filename):
    m = re.findall('(?<=FDMEAN-[0-9]{8}-)([0-9]+)-([0-9a-f]+)(?=-calibrated.txt)', filename)
    if not len(m):
        return {'site': None, 'cam': None}
    else:
        return {'site': int(m[0][0]), 'cam': int(m[0][1], 16)}
    
site_abbrev = ['br', 'lr']
def _geofile(site):
    return '$RTDATA/fdgeom/geo{}_joint.dst.gz'.format(site_abbrev[site])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Name of .txt file with data')
    parser.add_argument('name', help='Name or search string of object to simulate, e.g. "alpha boo"')
    parser.add_argument('-s', '--site', help='Site ID (0=BRM, 1=LR)', type=int)
    parser.add_argument('-c', '--camera', help='Camera ID (0-11)', type=int)

    args = parser.parse_args()

    if args.site is None or args.camera is None:
        sitecam = _get_site_cam(args.filename)
    else:
        sitecam = {'site': args.site, 'cam': args.camera}

    if None in sitecam.values():
        print 'Error: no site/cam provided and could not obtain from filename'
        sys.exit(1)
    assert sitecam['site'] in range(2)
    assert sitecam['cam'] in range(12)

    with open(args.filename, 'r') as infile:
        lines = infile.readlines()
    jstart = lines[0].split()[0]
    jend = lines[-1].split()[0]

    dur = int((float(jend) - float(jstart)) * 86400) + 1
    print "Duration, start to finish, in seconds:", dur
    sim_params = query(jstart, args.name)

    outfile = args.filename.replace('-calibrated', '-simulated')
    cmd = '$TRUMP/bin/star.run -rays 100 -dt 0.1 -q '
    cmd += '-o {} '.format(outfile)
    cmd += '-geo {} -mir {} '.format(_geofile(sitecam['site']), sitecam['cam'])
    cmd += '-dur {} '.format(dur)

    for k, v in sim_params.items():
        cmd += '-{} {} '.format(k, v)

    print cmd
    os.system(cmd)
    print outfile



