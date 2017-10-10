import os
import re
import sys

print sys.argv

conv_1mev_to_50kev = (1.0 - 0.05*0.045) / (1.0 - 0.045)

rtsf = sys.argv[1]
if not os.path.exists(rtsf):
    print 'not found: {0}'.format(rtsf)
    sys.exit(0)

evtfile = sys.argv[2]
evt = open(evtfile, 'w')

print '{0} is open for writing'.format(evtfile)
rbname = os.path.basename(rtsf)
ymd = rbname[1:5] + rbname[6:8] + rbname[9:11]

mdontfile = '{0}/tstroman/md-ontimes.txt'.format(os.getenv('HOME'))
with open(mdontfile, 'r') as mdont:
    matches = []
    mdontime = mdont.readlines()
    for line in mdontime:
        if line[0:8] == ymd:
            matches.append(line)

print 'found {0} part(s) (of {3}) on {1} in {2}'.format(
    len(matches), ymd, mdontfile, len(mdontime)
)
if len(matches)==0:
    exit(0)

rtss = os.popen('$TRUMP/bin/rtsparser.run -gluyspect -trigger {0}'.format(rtsf))
oldt = ""
n = 0
events = rtss.readlines()
print 'Simulation event count: {0}'.format(len(events))
for event in events:
    field = re.split('[\s]+', event.strip())
    if field[2] != '2' or field[0] == oldt:
        continue

    oldt = field[0]
    hour = float(field[7])
    minute = float(field[8])
    second = float(field[9])
    ns = float(field[10])

    t = hour*3600 + minute*60 + second + 1e-9*ns

    for match in matches:
        lpart = match.split()
        if float(lpart[2]) <= t < float(lpart[3]):
            part = lpart[0][8:10]
            break
        else:
            continue
    # event number, species, ontime flag
    evt.write('{0} {1} 1\n'.format(n, 1 if field[3] == '14' else 2))

    # UTC date YYYYMMDD, second of UTC day, millisecond, nanosecond
    evt.write('{0} {1} {2} {3}\n'.format(
        ymd, int(t), int(t * 1000), int(ns)
    ))

    s = -1.0 * (float(field[12]) * float(field[15]) +
        float(field[13]) * float(field[16])
    )

    # components of Rp vector (from CLF?)
    evt.write('{0} {1} {2}\n'.format(
        float(field[12]) + s*float(field[15]),
        float(field[13]) + s*float(field[16]),
        s*float(field[17])
    ))

    # components of shower axis unit vector
    evt.write('{0} {1} {2}\n'.format(field[15], field[16], field[17]))

    # energy, X0, Xmax, Nmax(50 KeV), Lambda
    evt.write('{0} {1} {2} {3} {4}\n'.format(
        1e-18*float(field[11]),
        field[20],
        field[22],
        1e-9*float(field[23])*conv_1mev_to_50kev,
        field[21]
    ))
    n += 1

evt.close()
print 'Wrote {0} event{1}.'.format(n, '' if n == 1 else 's')
if n == 0:
    os.remove(evtfile)
