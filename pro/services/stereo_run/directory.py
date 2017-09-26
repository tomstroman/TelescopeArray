import logging
import os
import subprocess as sp

def build_tree(stereo_run, path=None):
    base_run = path if path is not None else stereo_run.base_run
    full_path = os.path.join(stereo_run.rootpath, base_run)
    stereo_run.base_path = full_path
    stereo_run.bin_path = os.path.join(full_path, 'bin')
    stereo_run.run_path = os.path.join(full_path, stereo_run.specific_run)
    stereo_run.src_path = os.path.join(full_path, 'src')
    stereo_run.log_path = None

    paths = [full_path, stereo_run.bin_path, stereo_run.run_path, stereo_run.src_path]
    if stereo_run.params.is_mc:
        stereo_run.log_path = os.path.join(stereo_run.run_path, 'logs')
        paths.append(stereo_run.log_path)

    for path in paths:
        cmd = 'mkdir -p {}'.format(path)
        logging.info('Verifying path exists: %s', path)
        logging.debug('cmd: %s', cmd)
        try:
            output = sp.check_output(cmd.split(), stderr=sp.STDOUT)
            logging.debug('output: %s', output)
        except Exception as err:
            logging.error("Exception during directory creation: %s", err)
            raise
        if output:
            raise Exception('Unexpected stdout/stderr')
        assert os.path.isdir(path)

