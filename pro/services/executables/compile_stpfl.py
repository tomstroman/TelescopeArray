import logging
import os
import subprocess as sp


def compile_stpfl(stereo_run, cwd, destination):
    utafd = os.getenv('UTAFD_ROOT_DIR')
    cmd = 'cp {}/build/std-build/release/bin/stpfl12_main {}'.format(utafd, destination)

    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)
