# prep_data.py
# Thomas Stroman, University of Utah 2018-01-24
# Run TAMA on raw FADC telescope data to produce DST files.

import argparse
import logging
import os
import re

from db.database_wrapper import DatabaseWrapper

from prep_fadc.raw_to_dst import _call_timecorr
from utils import log, _camlist

FADC_DB = 'db/fadc_data.db'
TAMA_EXE = os.path.join(os.getenv('TAHOME'), 'tama', 'bin', 'tama.run')
EXPECTED_TAMA_STDERR = 2


class PrologError(Exception):
    pass


class MissingOutputError(Exception):
    pass


class Part(object):
    def __init__(self, part11):
        self.part11 = part11
        s11 = str(part11)
        self.year = s11[:4]
        self.month = s11[4:6]
        self.day = s11[6:8]
        self.part = s11[8:10]
        self.site = s11[10]

        self.ymd = s11[:8]
        self.yymmdd = 'y{}m{}d{}'.format(self.year, self.month, self.day)
        self.timecorr = '{}p{}_site{}_timecorr.txt'.format(self.yymmdd, self.part, self.site)
        self.tama_code = s11[2:10]

    def __repr__(self):
        return str(self.part11)


class TamaRun(object):
    def __init__(self, part, trigset, outdir):
        self.part = part
        self.trigset = trigset
        self.outdir = outdir
        self.cmd_template = '{tama_exe} -o {output_dst} -r {tama_code} {ctd_file} {cam_files} > {stdout} 2> {stderr}'
        self.files = None

    def build_cmd(self, ctd_prefix, daq_cams):
        ctd_file = ctd_prefix + '-{}-{:07}.d.bz2'.format(self.part.site, self.trigset)
        output_dst = os.path.join(
            self.outdir,
            '{}-{}-{:07}.dst.gz'.format(
                os.path.basename(ctd_prefix),
                self.part.site,
                self.trigset,
            ),
        )
        stdout, stderr, prolog = (output_dst.replace('.dst.gz', suffix) for suffix in ['.out', '.err', '.prolog'])
        cam_file_template = ctd_prefix.replace('/ctd/', '/camera{0:02}/') + '-{0}-{{0:x}}-{1:07}.d.bz2'.format(self.part.site, self.trigset)
        cam_files = ' '.join([cam_file_template.format(c) for c in _camlist(daq_cams)])

        self.files = {
            'dst' : output_dst,
            'out' : stdout,
            'err' : stderr,
            'log' : prolog,
        }

        self.cmd = self.cmd_template.format(
            tama_exe=TAMA_EXE,
            output_dst=output_dst,
            tama_code=self.part.tama_code,
            ctd_file=ctd_file,
            cam_files=cam_files,
            stdout=stdout,
            stderr=stderr
        )

        return self.cmd, self.files

    def __repr__(self):
        if self.files is not None:
            return 'tama.run({})'.format(os.path.basename(self.files['dst']))
        return 'tama.run({}, {:07})'.format(part, trigset)


def process_subpart(part=None, trigset=None, outdir=os.curdir, console_mirror=False):
    log_name = log.set_up_log(name='process.log', console_mirror=console_mirror)
    logging.info('Logging to %s', log_name)
    if part is None or trigset is None:
        logging.error('No part and/or trigset specified!')
        raise ValueError

    part = Part(part)
    outdir = os.path.join(outdir, part.site, part.ymd)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    tama_run = TamaRun(part, trigset, outdir)

    logging.info('Processing part %s trigset %07d, output to %s', part, trigset, outdir)
    ctd_prefix, daq_cams = _get_db_info(part, trigset)

    timecorr_file = os.path.join(outdir, part.timecorr)
    if not os.path.exists(timecorr_file):
        logging.info('Creating %s', timecorr_file)
        _call_timecorr(part.site, outdir, ctd_prefix)

    cmd, files = tama_run.build_cmd(ctd_prefix, daq_cams)
    logging.debug('TAMA command: %s', cmd)
    logging.info('Please wait; creating %s', files['dst'])
    os.system(cmd)

    logging.info('Validating output')
    if not all([os.path.exists(f) for f in files.values()]):
        logging.error('Missing expected output from %s', tama_run)
        raise MissingOutputError

    stderr = open(files['err'], 'r').readlines()
    logging.info('Lines of stderr: expected=%s, actual=%s', len(stderr), EXPECTED_TAMA_STDERR)

    try:
        prolog = open(files['log'], 'r').read()
        prolog_data = dict([tuple(r.split()) for r in re.findall('[A-Z]+_[A-Z]+ \d+', prolog)[-4:]])
        logging.info('Prolog report: read=%s, kept=%s, bytes=%s',
            prolog_data['TAMA_READ'],
            prolog_data['TAMA_KEPT'],
            prolog_data['BYTES_OUT'],
        )
    except Exception as err:
        logging.error('Encountered error reading prolog: %s', err)
        raise PrologError

    return prolog_data


def _get_db_info(part, trigset):
    db = DatabaseWrapper(FADC_DB)
    sql = 'SELECT f.ctdprefix, p.daqtrig, p.daqcams FROM Filesets AS f JOIN Parts AS p ON f.part11=p.part11 WHERE f.part11={}'.format(part)
    rows = db.retrieve(sql)
    if len(rows) != 1:
        logging.error('No unique Fileset found for part11=%s', part)
        raise ValueError("FilesetNotFound")

    ctd_prefix, daq_triggers, daq_cams = rows[0]
    logging.info('ctd_prefix: %s', ctd_prefix)
    if not 0 <= trigset < daq_triggers:
        logging.error('Requesting triggers from %d but DAQ reports %d', trigset, daq_triggers)
        raise ValueError("TriggerOutOfBounds")
    return ctd_prefix, daq_cams



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--part', type=int, help="11-digit part code (yyyymmddpps)")
    parser.add_argument('-t', '--trigset', type=int, help="trigger set (multiple of 256)")
    parser.add_argument('-o', '--outdir', help="location for output")
    args = parser.parse_args()
    assert not args.trigset % 256, 'trigset must be a multiple of 256!'
    process_subpart(args.part, args.trigset, args.outdir, console_mirror=True)
