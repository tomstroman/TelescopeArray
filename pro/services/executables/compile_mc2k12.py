import logging
import os
import subprocess as sp


def compile_mc2k12(stereo_run, cwd, destination):
    utafd = os.getenv('UTAFD_ROOT_DIR')
    assert os.path.isdir(utafd)

    cmd_shell = ['ssh tstroman@localhost "cd UTAFD/build/std-build/release; make -j4"']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp {}/build/std-build/release/bin/mc2k12_main {}'.format(utafd, destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)

