import logging
import os
import subprocess as sp

from collections import OrderedDict

from compile_dump import compile_dump_tuples, compile_dump_profs
from compile_trump import compile_trump
from compile_fdtp import compile_fdtp
from compile_mc2k12 import compile_mc2k12
from compile_stpfl import compile_stpfl


base_reqs = OrderedDict()
base_reqs['trump'] = 'trump.run'
base_reqs['mc2k12'] = 'mc2k12_main'
base_reqs.update({
    'fdtp':  'fdtubeprofile.run',
    'stpfl': 'stpfl12_main',
    'dump_tuples': 'dumpst.run',
    'dump_profs' : 'dumpster2.run',
    'dump_meta'  : 'dumpst-rootformat.txt',
})


use_recon = ['fdtp']
use_mdrecon = ['stpfl']

TAHOME = os.getenv('TAHOME')
save_files = {
    'dump_profs': {
        'base' : None,
        'files': [],
    },
    'dump_tuples': {
        'base' : None,
        'files': [],
    },
    'trump': {
        'base'  : os.path.join(TAHOME, 'trump'),
        'files' : [
            'inc/constants.h',
            'inc/control.h',
        ]
    },
    'fdtp': {
        'base'  : os.path.join(TAHOME, 'fdtubeprofile'),
        'files' : [],
    },
}

compiler_map = {
    'dump_profs' : (None, compile_dump_profs),
    'dump_tuples': (None, compile_dump_tuples),
    'fdtp': (save_files['fdtp']['base'], compile_fdtp),
    'mc2k12': (None, compile_mc2k12),
    'stpfl': (None, compile_stpfl),
    'trump': (save_files['trump']['base'], compile_trump),
}


def get_base_reqs(stereo_run):
    items = []
    for name, filename in base_reqs.items():
        if name in use_recon:
            filename = stereo_run.recon + '-' + filename
        elif name in use_mdrecon:
            filename = stereo_run.mdrecon + '-' + filename
        items.append((name, filename))
    return items

def prepare_executable(stereo_run, name, destination, src_dir=None):
    assert name in base_reqs.keys()
    logging.info('compiling %s and copying to %s', name, destination)
    if name in compiler_map:
        cwd, compiler = compiler_map[name]
        compiler(stereo_run, cwd, destination)
    else:
        logging.warn('Creating unusable exe: %s. This WILL cause errors.', name)
        cmd = 'touch {}'.format(destination)
        output = sp.check_output(cmd.split(), stderr=sp.STDOUT)

    if src_dir is not None and name in save_files:
        for save_file in save_files[name]['files']:
            src = os.path.join(save_files[name]['base'], save_file)
            dest = location = os.path.join(
                src_dir,
                os.path.basename(destination),
                save_file,
            )
            cmd = 'mkdir -p {}'.format(os.path.dirname(dest))
            sp.check_output(cmd.split())
            cmd = 'cp {} {}'.format(src, dest)
            sp.check_output(cmd.split())
            assert os.path.exists(dest)

