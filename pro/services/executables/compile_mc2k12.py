import logging
import os
import re
import subprocess as sp

NERLING_COEFF = re.compile('(?:^ +const real_t )(c\d)(?= =)')
def modify_utafd(cwd, stereo_run):
    dedx_model = stereo_run.params.dedx_model
    db_coeffs = stereo_run.db.retrieve('SELECT c1, c2, c3, c4, c5, name FROM Models WHERE dedx_model={}'.format(dedx_model))[0]
    coeffs = {
        'c1': db_coeffs[0],
        'c2': db_coeffs[1],
        'c3': db_coeffs[2],
        'c4': db_coeffs[3],
        'c5': db_coeffs[4],
    }
    model_name = db_coeffs[5]

    change = os.path.join(cwd, 'src', 'physics', 'inc', 'Nerling.cuh')
    original = change + '.original'

    cmd = 'cp {} {}'.format(change, original)
    sp.check_output(cmd.split(), stderr=sp.STDOUT)
    with open(change, 'r') as origfile:
        orig_lines = origfile.readlines()

        buf = ''
        for line in orig_lines:
            coeff_assignment = NERLING_COEFF.findall(line)
            if coeff_assignment:
                c = coeff_assignment[0]
                buf += '    const real_t {} = {}; // set by script for model {} ({})\n'.format(
                    c,
                    coeffs[c],
                    dedx_model,
                    model_name,
                )
            else:
                buf += line

    with open(change, 'w') as newfile:
        newfile.write(buf)

    return {change: original}

# other possible files to modify:
# src/mc2k10/src/ghform.f
# src/stpfl12/src/stpfl_fit_mod_plane.cxx
# src/physics/inc/PhysicsService.cuh


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
