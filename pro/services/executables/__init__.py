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
            'inc/constants.h',
            'inc/control.h',
        ]
    },
}

def prepare_executable(stereo_run, name, destination, src_dir=None):
    assert name in base_reqs.keys()
    logging.info('compiling %s and copying to %s', name, destination)
    if name in compiler_map:
        compiler_map[name](stereo_run, destination)
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

def compile_trump(stereo_run, destination):
    dedx_model = stereo_run.params.dedx_model
    cwd = save_files['trump']['base']
    change = os.path.join(cwd, 'inc', 'constants.h')
    original = change + '.original'

    cmd = 'cp {} {}'.format(change, original)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)

    with open(change, 'r') as origfile:
        orig_lines = origfile.readlines()

        buf = ''
        for line in orig_lines:
            if line.startswith('#define DEDX_MODEL'):
                buf += '#define DEDX_MODEL {} // set by script'.format(dedx_model)
            else:
                buf += line

    with open(change, 'w') as newfile:
        newfile.write(buf)

    cmd_shell = ['make realclean']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd_shell = ['make']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp bin/trump.run {}'.format(destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)

# run newly compiled TRUMP, check for correct DEDX_MODEL
    exe_out = sp.Popen([destination], stdout=sp.PIPE)
    assert 'This version built using DEDX_MODEL {}\n'.format(dedx_model) in exe_out.stdout.read()

# cleanup -- TODO: add this to a list for cleanup AFTER source-code copying
    cmd = 'mv {} {}'.format(original, change)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)

compiler_map = {
    'trump': compile_trump
}
