# utils.py
# Thomas Stroman, University of Utah, 2016-12-15
# Utilities for use in several functions/modules.

import subprocess
import os
import datetime

def _ymdps(part):
    """
    Given an 11-digit part code, split it into year, month, day, part, site.
    """
    x = str(part)
    return x[0:4], x[4:6], x[6:8], x[8:10], x[10]


def _command(cmd):
    """
    Given a command as though typed in the shell, execute that command and return (stdout, stderr)
    """
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    return p.communicate()

tama = {'0': '/tama_0/black-rock/', '1': '/tama_1/long-ridge/'}

def _timecorr_path(part):
    y, m, d, p, s = _ymdps(part)
    return os.path.join(tama[s], '{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt'.format(y,m,d,p,s))

def _camlist(daqcams):
    """
    Get the list of active camera IDs, given daqcams.
    daqcams is a 12-bit unsigned integer where each bit indicates whether
    a camera was active for a given DAQ part.
    """
    return [i for i in range(12) if (daqcams >> i) % 2]

j0 = datetime.datetime(2007, 7, 1)
def get_jstart(timecorr, trig=None):
    if trig is None:
        try:
            with open(timecorr, 'r') as tc:
                trig = tc.readlines()[0]
        except:
            print 'Could not get first trigger from', timecorr
            return None
    hh, mm, ss, ns = [int(t) for t in trig.split()[2:6]]
    mus = int(ns/1000)

    basename = os.path.basename(timecorr)
    part11 = ''.join([c for c in basename if c.isdigit()])
    year = int(part11[0:4])
    month = int(part11[4:6])
    day = int(part11[6:8])

    jtrig = datetime.datetime(year, month, day, hh, mm, ss, mus)

    return (jtrig - j0).total_seconds()/86400.
