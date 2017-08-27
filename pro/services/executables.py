import logging
import os
import subprocess as sp


base_reqs = {
    'trump': 'trump.run',
    'fdtp':  'fdtubeprofile.run',
    'stpfl': 'stpfl12_main',
    'dump_tuples': 'dumpst.run',
    'dump_profs' : 'dumpster2.run',
    'dump_meta'  : 'dumpst-rootformat.txt',
}

save_files = {
    'trump': {
        'base'  : os.path.join(os.getenv('TAHOME'), 'trump'),
        'files' : [
            'bin/trump.c',
        ]
    },
}

def prepare_executable(name, destination, src_dir=None):
    assert name in base_reqs.keys()
    logging.info('compiling %s and copying to %s', name, destination)
    if name in compiler_map:
        compiler_map[name]()
    else:
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

def compile_trump(dedx_model=13):
    cwd = save_files['trump']['base']
    change = os.path.join(cwd, 'inc', 'constants.h')
    original = change + '.original'

    cmd = 'cp {} {}'.format(change, original)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)

    cmd_shell = ['make realclean']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd_shell = ['make']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'mv {} {}'.format(original, change)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)

compiler_map = {
    'trump': compile_trump
}
