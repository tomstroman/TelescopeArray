import logging
import os
import subprocess as sp

def compile_fdtp(stereo_run, cwd, destination):
    cmd_shell = ['make clean']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd_shell = ['make -j4']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp bin/fdtubeprofile.run {}'.format(destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)
