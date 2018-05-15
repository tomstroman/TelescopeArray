import logging
import os
import subprocess as sp

def compile_fdtp(stereo_run, cwd, destination):
    dedx_model = stereo_run.params.dedx_model
    cmd_shell = ['make clean']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd_shell = ['make -j4']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp bin/fdtubeprofile.run {}'.format(destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)

# run newly compiled fdtubeprofile, check for correct DEDX_MODEL
    exe_out = sp.Popen([destination], stderr=sp.PIPE)
    assert 'main(): DEDX_MODEL {}\n'.format(dedx_model) in exe_out.stderr.read()
