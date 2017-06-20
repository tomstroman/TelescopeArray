# simulate_local.py
# Thomas Stroman, University of Utah 2017-06-01
# Glue code to call localpoint.run and then render.C with common arguments,
# for one-step simulation and visualization of light from a point source
# near a Telescope Array FADC camera box.

import os
import argparse
import subprocess as sp

geo = os.path.join(os.getenv('RTDATA'), 'fdgeom', 'geobr_joint.dst.gz')
outfile = 'output.txt'

parser = argparse.ArgumentParser()
parser.add_argument('-geo', '--geometry', help='Geometry file path', default=geo)
parser.add_argument('-o', '--outfile', help='Filename for raytrace output (.txt)', default=outfile)
parser.add_argument('-dz', help='Distance (meters) along z-axis relative to PMT plane, default=0', type=float, default=0)
parser.add_argument('-xy', nargs=2, help='Offset (meters) in x-y plane relative to axis (X = LEFT, Y = UP), default = 0 0', default=[0, 0], type=float, metavar=('X', 'Y'))
parser.add_argument('-seg', nargs=3, help='Segment reorientation: rotate segment S by AZ degrees RIGHT, ALT degrees UP. Repeatable for multiple segments.', type=float, default=[], metavar=('S', 'AZ', 'ALT'), action='append')
parser.add_argument('-m', '--mir', type=int, default=0, help='Mirror ID (default=0)', choices=range(12))
parser.add_argument('-r', '--rays', type=int, default=1000000, help='Number of rays to simulate (default=1000000)')
parser.add_argument('-t', '--title', default='REPLACE', help='Title to print on canvas (default: outfile name)')


args = parser.parse_args()




trump = os.getenv('TRUMP')
localpoint = os.path.join(trump, 'bin', 'localpoint.run')

assert os.path.exists(localpoint)

geo = args.geometry
outfile = args.outfile
if args.title == 'REPLACE':
    title = os.path.basename(outfile)
else:
    title = args.title


cmd = localpoint + ' -geo {geo} -o {outfile}'.format(geo=geo, outfile=outfile)
cmd += ' -mir {mir}'.format(mir=args.mir)
cmd += ' -rays {rays}'.format(rays=args.rays)
cmd += ' -dz {dz}'.format(dz=args.dz)
cmd += ' -xy {x} {y}'.format(x=args.xy[0], y=args.xy[1])
for fseg, az, alt in args.seg:
    cmd += ' -seg {s} {az} {alt}'.format(s=int(fseg), az=az, alt=alt)
print cmd
trace = sp.check_output(cmd.split(), stderr=sp.STDOUT)
print trace

# set this to '-l -b -q' to generate each PDF without drawing to the screen and then exit.
rootflags = '-l'



cmd = 'root {rootflags} "render.C(\\"{outfile}\\", \\"{title}\\")"'.format(rootflags=rootflags, outfile=outfile, title=title)
os.system(cmd)

