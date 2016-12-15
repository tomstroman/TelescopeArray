# utils.py
# Thomas Stroman, University of Utah, 2016-12-15
# Utilities for use in several functions/modules.

import subprocess

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
