import logging
import os
import subprocess as sp

def _both(path):
    # Some files are physically in the rootpath, while others are physically
    # on a RAID-0 volume (striped across 4 disks) for performance. Directories are
    # symlinked.
    return [path, path.replace('/scratch/', '/raidscratch/')]

def build_tree(stereo_run, path=None):
    rootpath = stereo_run.rootpath
    # If root paths are missing, don't even try to run.
    for p in _both(stereo_run.rootpath):
        assert os.path.isdir(p)

    stereo_run.analysis_path = os.path.join(stereo_run.rootpath, stereo_run.name)
    base_run = path if path is not None else stereo_run.base_run

    full_path = os.path.join(stereo_run.rootpath, base_run)
    assert stereo_run.analysis_path in full_path

    stereo_run.base_path = full_path

    # These directories need to exist on main and RAID
    for path in [stereo_run.analysis_path, stereo_run.base_path]:
        for p in _both(path):
            if not os.path.isdir(p):
                logging.info('Creating directory: %s', p)
                os.mkdir(p)

    # Real night-sky data is preprocessed once and shared by multiple analyses,
    # so we can symlink its true location here.
    stereo_run.tafd_data = os.path.join(stereo_run.analysis_path, 'tafd-data')
    if not os.path.isdir(stereo_run.tafd_data):
        true_data_path = os.path.join(stereo_run.rootpath, stereo_run.params.fdplane_config, 'tafd-data')
        logging.info('Symlinking %s to point to night-sky data at %s', stereo_run.tafd_data, true_data_path)
        os.symlink(true_data_path, stereo_run.tafd_data)


    # These directories will exist in one place only, and be symlinked in the other.
    stereo_run.bin_path = os.path.join(full_path, 'bin')
    main, raid = _both(stereo_run.bin_path)
    if not os.path.isdir(main):
        os.mkdir(main)
    if not os.path.isdir(raid):
        os.symlink(main, raid)
    assert os.path.realpath(raid) == main

    stereo_run.run_path = os.path.join(full_path, stereo_run.specific_run)
    main, raid = _both(stereo_run.run_path)
    if stereo_run.params.is_mc:
        if not os.path.isdir(raid):
            os.mkdir(raid)
        if not os.path.isdir(main):
            os.symlink(raid, main)
        assert os.path.realpath(main) == raid
    else:
        if not os.path.isdir(main):
            os.mkdir(main)

    stereo_run.src_path = os.path.join(full_path, 'src')
    stereo_run.log_path = None

    paths = [stereo_run.src_path]
    if stereo_run.params.is_mc:
        stereo_run.log_path = os.path.join(stereo_run.run_path, 'logs')
        paths.append(stereo_run.log_path)

    for path in paths:
        if not os.path.isdir(path):
            logging.info('Creating path: %s', path)
            os.mkdir(path)
        assert os.path.isdir(path)

