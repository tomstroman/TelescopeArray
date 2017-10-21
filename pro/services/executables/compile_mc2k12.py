import logging
import os
import re
import subprocess as sp


def compile_mc2k12(stereo_run, cwd, destination):
    utafd = os.getenv('UTAFD_ROOT_DIR')
    assert os.path.isdir(utafd)

    _confirm_max_date(utafd)

    cmd_shell = ['ssh tstroman@localhost "cd UTAFD/build/std-build/release; make -j4"']
    sp.check_output(cmd_shell, shell=True, stderr=sp.STDOUT, cwd=cwd)

    cmd = 'cp {}/build/std-build/release/bin/mc2k12_main {}'.format(utafd, destination)
    sp.check_output(cmd.split(), stderr=sp.STDOUT, cwd=cwd)

def _confirm_max_date(utafd):
    res_dir = os.getenv('UTAFD_RESOURCES_DIR')
    assert os.path.isdir(res_dir)

    atmos_file = os.path.join(utafd, 'src', 'atmos', 'src', 'utafd_atmosphere.cu')
    with open(atmos_file, 'r') as atmos_in:
        atmos = atmos_in.read()

    dates = re.findall('(?<=db_idate > )[0-9]{8}', atmos)
    assert len(dates) == 1
    max_utafd_date = dates[0]
    logging.info('UTAFD supports dates through %s', max_utafd_date)


    gdas = os.path.join(res_dir, 'required', 'TA_Calib', 'gdas')
    dst_files = sorted([f for f in os.listdir(gdas) if f.endswith('.dst.gz')])
    last_dst = os.path.join(gdas, dst_files[-1])

    # get the last date for which database support exists
    # looks like 'FROM 2017/01/31 19:30:00 TO 2017/01/31 22:30:00\n'
    cmd = 'dstdump -gdas {} | grep FROM | tail -1'.format(last_dst)
    last_line = sp.check_output(cmd, shell=True)
    max_gdas_date = ''.join(re.findall('(?<=TO )([0-9]{4})/([0-9]{2})/([0-9]{2})(?= )', last_line)[0])

    logging.info('GDAS supports dates through %s', max_gdas_date)
