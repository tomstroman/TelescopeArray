import os
import subprocess as sp

from distutils import spawn as distutils__spawn
from math import log10

FIELDS = [
    'event',
    'species',
    'ymd',
    'sec',
    'logE',
    'xcore',
    'ycore',
    'vx',
    'vy',
    'vz',
    'x0',
    'lambda',
    'xmax',
    'logNmax',
]

DIRECT_FIELDS = {
    'event': 0,
    'species': 3,
    'logE': 11,
    'xcore': 12,
    'ycore': 13,
    'vx': 15,
    'vy': 16,
    'vz': 17,
    'x0': 18,
    'lambda': 19,
    'xmax': 20,
}


def rts_to_ROOT(rts):
    rts_parser_exe = os.path.join(os.getenv('TAHOME'), 'trump', 'bin', 'rtsparser.run')
    rts_to_root_exe = rts_parser_exe.replace('rtsparser.run', 'rts2root.C')
    for exe in [rts_parser_exe, rts_to_root_exe]:
        assert os.path.exists(exe), 'Not found: {}'.format(exe)
    assert distutils__spawn.find_executable('root'), 'ROOT appears not to be installed'

    cmd = '{rtsparser} -Etslpcgu {rts}'.format(rtsparser=rts_parser_exe, rts=rts)
    output = sp.check_output(cmd, shell=True)
    lines = output.split('\n')[:-1]

    buf = ''
    last_event = None
    for line in lines:
        text, last_event = _format_rts_line(line, last_event)
        buf += text

    temp_file = '{}.txt'.format(rts)
    with open(temp_file, 'w') as rts_txt:
        rts_txt.write(buf)

    cmd = 'root -l -q "{0}(\\"{1}\\")"'.format(rts_to_root_exe, temp_file)
    sp.check_output(cmd, shell=True)
    os.remove(temp_file)

def _format_rts_line(line, last_event):
    d = _get_dict(line)
    if d['event'] == last_event:
        return '', last_event

    buf = ' '.join([d[f] for f in FIELDS])
    buf += '\n'
    return buf, d['event']

def _get_dict(line):
    s = line.split()
    d = {
        'ymd' : ''.join(s[4:7]),
        'sec' : '{sec}.{nanosec}'.format(
            sec=3600*int(s[7]) + 60*int(s[8]) + int(s[9]),
            nanosec=s[10],
        ),
        'logNmax' : '{0:.5}'.format(log10(float(s[21]))),
    }


    d.update({field: s[index] for field, index in DIRECT_FIELDS.items()})
    return d
