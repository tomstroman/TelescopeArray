# prep_data.py
# Thomas Stroman, University of Utah 2018-01-24
# Run TAMA on raw FADC telescope data to produce DST files.

import argparse
import logging
import os

from db.database_wrapper import DatabaseWrapper

from prep_fadc.raw_to_dst import _call_timecorr
from utils import log

FADC_DB = 'db/fadc_data.db'
TAMA_EXE = os.path.join(os.getenv('TAHOME'), 'tama', 'bin', 'tama.run')

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

    def __repr__(self):
        return str(self.part11)


def process_subpart(part=None, trigset=None, outdir=os.curdir, console_mirror=False):
    log_name = log.set_up_log(name='process.log', console_mirror=console_mirror)
    logging.info('Logging to %s', log_name)
    if part is None or trigset is None:
        logging.error('No part and/or trigset specified!')
        return

    part = Part(part)
    outdir = os.path.join(outdir, part.site, part.ymd)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    logging.info('Processing part %s trigset %07d, output to %s', part, trigset, outdir)
    ctd_prefix = _get_db_info(part, trigset)

    timecorr_file = os.path.join(outdir, part.timecorr)
    if not os.path.exists(timecorr_file):
        logging.info('Creating %s', timecorr_file)
        _call_timecorr(part.site, outdir, ctd_prefix)


    output_dst = os.path.join(outdir, '{}-{}-{:07}.dst.gz'.format(os.path.basename(ctd_prefix), part.site, trigset))

# TODO: populate all these arguments and run command
    tama_cmd_template = '{tama_exe} -o {output_dst} -r {tama_code} {ctd_file_template} {cam_files_template}'


def _get_db_info(part, trigset):
    db = DatabaseWrapper(FADC_DB)
    sql = 'SELECT f.ctdprefix, p.daqtrig FROM Filesets AS f JOIN Parts AS p ON f.part11=p.part11 WHERE f.part11={}'.format(part)
    rows = db.retrieve(sql)
    if len(rows) != 1:
        logging.error('No unique Fileset found for part11=%s', part)
        raise ValueError("FilesetNotFound")

    ctd_prefix, daq_triggers = rows[0]
    logging.info('ctd_prefix: %s', ctd_prefix)
    if not 0 <= trigset < daq_triggers:
        logging.error('Requesting triggers from %d but DAQ reports %d', trigset, daq_triggers)
        raise ValueError("TriggerOutOfBounds")
    return ctd_prefix



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--part', type=int, help="11-digit part code (yyyymmddpps)")
    parser.add_argument('-t', '--trigset', type=int, help="trigger set (multiple of 256)")
    parser.add_argument('-o', '--outdir', help="location for output")
    args = parser.parse_args()
    assert not args.trigset % 256, 'trigset must be a multiple of 256!'
    process_subpart(args.part, args.trigset, args.outdir, console_mirror=True)
