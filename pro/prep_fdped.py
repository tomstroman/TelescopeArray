import argparse
import logging
import os
import re

from utils import log

FDPED_BIN = os.path.join(os.getenv('TAHOME'), 'fdped', 'bin', 'fdped.run')
FDPED_OUT = '/scratch1/fdpedv'
YMDPS = re.compile('(\d{4})(\d{2})(\d{2})(\d{2})(\d)')
TIMECORRS = {
    '0': '/tama_{4}/black-rock/{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt',
    '1': '/tama_{4}/long-ridge/{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt',
}
DSTS = {
    '0': '/tama_{4}/black-rock/{0}{1}{2}/DAQ-*{2}{3}-{4}-*.dst.gz',
    '1': '/tama_{4}/long-ridge/{0}{1}{2}/DAQ-*{2}{3}-{4}-*.dst.gz',
}
FDPEDS = {
    '0': '/scratch1/fdpedv/black-rock/{0}{1}{2}/y{0}m{1}d{2}p{3}.ped.dst.gz',
    '1': '/scratch1/fdpedv/long-ridge/{0}{1}{2}/y{0}m{1}d{2}p{3}.ped.dst.gz',
}

def run_fdped(part11):
    logging.info('part: %s', part11)

    format_kwargs = _files(part11)
    timecorr = format_kwargs['timecorr']
    if not os.path.exists(timecorr):
        logging.error('Timecorr does not exist: %s', timecorr)
        raise Exception

    outdir = os.path.dirname(format_kwargs['peddst'])
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    cmd = '{fdped} -o {peddst} -t {timecorr} {dsts} > {out} 2> {err}'.format(
        fdped=FDPED_BIN,
        **format_kwargs
    )
    logging.info('cmd: %s', cmd)
    os.system(cmd)
    peddst = format_kwargs['peddst']
    out = format_kwargs['out']
    err = format_kwargs['err']
    if not all([os.path.exists(f) for f in peddst, out, err]):
        if os.path.exists(err):
            with open(err) as stderr:
                fdped_err = stderr.read()
            if fdped_err.strip().endswith('DELETE'):
                logging.info('Rejected FDPED for %s', part11)
                return
        logging.error('Missing output for %s', part11)
        raise Exception
    else:
        logging.info('Success - TODO: further validation')





def _files(part11):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    peddst, timecorr, dsts = [f[s].format(y, m, d, p, s) for f in FDPEDS, TIMECORRS, DSTS]
    out = os.path.join(os.path.dirname(peddst), 'fdped-{4}-{0}{1}{2}{3}.out'.format(y[2:], m, d, p, s))
    err = out.replace('.out', '.err')
    return {
        'peddst': peddst,
        'timecorr': timecorr,
        'dsts': dsts,
        'out': out,
        'err': err,
    }


def _dst0_file(part11, ctd_prefix):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    daq_code = os.path.basename(ctd_prefix)
    return DSTS[s].format(y, m, d, p, s, daq_code)


def _fdped_part_file(part11):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    return FDPEDS[s].format(y, m, d, p, s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--part', default=None)
    parser.add_argument('-l', '--log', default='fdped.log', help='name of log file')
    args = parser.parse_args()
    log_name = log.set_up_log(name=args.log, console_mirror=True)
    run_fdped(args.part)

