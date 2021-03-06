import logging
import os
import subprocess as sp


def modify_trump(cwd, stereo_run):
    dedx_model = stereo_run.params.dedx_model
    change = os.path.join(cwd, 'inc', 'constants.h')
    original = change + '.original'

    cmd = 'cp {} {}'.format(change, original)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)

    with open(change, 'r') as origfile:
        orig_lines = origfile.readlines()

        buf = ''
        for line in orig_lines:
            if line.startswith('#define DEDX_MODEL'):
                buf += '#define DEDX_MODEL {} // set by script\n'.format(dedx_model)
            else:
                buf += line

    with open(change, 'w') as newfile:
        newfile.write(buf)

    return {change: original}


def compile_trump(stereo_run, cwd, destination):
    dedx_model = stereo_run.params.dedx_model

    cmd_shell = ['make realclean']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd_shell = ['make -j4']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp bin/trump.run {}'.format(destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)

# run newly compiled TRUMP, check for correct DEDX_MODEL
    exe_out = sp.Popen([destination], stdout=sp.PIPE)
    assert 'This version built using DEDX_MODEL {}\n'.format(dedx_model) in exe_out.stdout.read()
