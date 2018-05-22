import logging
import os
import subprocess as sp

from collections import OrderedDict

from compile_dump import compile_dump_tuples, compile_dump_profs
from compile_trump import compile_trump, modify_trump
from compile_fdtp import compile_fdtp
from compile_mc2k12 import compile_mc2k12, modify_utafd
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
UTAFD = os.getenv('UTAFD_ROOT_DIR')
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
    'mc2k12': {
        'base'  : UTAFD,
        'files' : [
            'src/physics/inc/Nerling.cuh',
        ],
    },
}

compiler_map = {
    'dump_profs' : (None, compile_dump_profs),
    'dump_tuples': (None, compile_dump_tuples),
    'fdtp': (save_files['fdtp']['base'], compile_fdtp),
    'mc2k12': (save_files['mc2k12']['base'], compile_mc2k12),
    'stpfl': (None, compile_stpfl),
    'trump': (save_files['trump']['base'], compile_trump),
}

class override_params(object):
    def __init__(self, stereo_run):
        self.stereo_run = stereo_run
        self.model = stereo_run.params.model
        self.recon = stereo_run.recon
        self.mdrecon = stereo_run.mdrecon

    def __enter__(self):
        logging.info('Entering override_model context for model %s', self.model)
        self.changes = self._modify_sources()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging.info('Exiting override_model')
        for updated, original in self.changes.items():
            logging.info('Moving %s to %s', original, updated)
            cmd = 'mv {} {}'.format(original, updated)
            sp.check_output(cmd.split(), stderr=sp.STDOUT)


    def get_base_reqs(self):
        items = []
        for name, filename in base_reqs.items():
            if name in use_recon:
                filename = self.recon + '-' + filename
            elif name in use_mdrecon:
                filename = self.mdrecon + '-' + filename
            items.append((name, filename))
        return items

    def _modify_sources(self):
        changes = OrderedDict()
        changes.update(modify_trump(save_files['trump']['base'], self.stereo_run))
        changes.update(modify_utafd(save_files['mc2k12']['base'], self.stereo_run))
        return changes


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

