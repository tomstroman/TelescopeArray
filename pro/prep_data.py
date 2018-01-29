# prep_data.py
# Thomas Stroman, University of Utah 2018-01-24
# Run TAMA on raw FADC telescope data to produce DST files.

import argparse
import logging
import os

from db.database_wrapper import DatabaseWrapper

from prep_fadc.raw_to_dst import _call_timecorr
from prep_fadc.tama_run import TamaRun
from utils import log

FADC_DB = 'db/fadc_data.db'



class Part(object):
    def __init__(self, part11, ctd_prefix, daq_cams, daq_triggers):
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

        self.ctd_prefix = ctd_prefix
        self.daq_cams = daq_cams
        self.daq_triggers = daq_triggers

    def __repr__(self):
        return str(self.part11)


def process_subpart(part, trigset, outdir, skip_run=False):
    tama_run = TamaRun(part, trigset, outdir)


    cmd, files = tama_run.build_cmd(part.ctd_prefix, part.daq_cams)
    #logging.debug('TAMA command: %s', cmd)
    if not skip_run:
        logging.info('Please wait; creating %s', files['dst'])
        os.system(cmd)
    else:
        logging.warn('Skipping execution.')

    return tama_run.prolog_data()


def process_part(part=None, outdir=os.curdir, skip_run=False):
    if part is None:
        logging.error('No part specified!')
        raise ValueError

    ctd_prefix, daq_triggers, daq_cams = _get_db_info(part)
    part = Part(part, ctd_prefix, daq_cams, daq_triggers)

    outdir = os.path.join(outdir, part.site, part.ymd)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    logging.info('Processing part %s output to %s', part, outdir)

    timecorr_file = os.path.join(outdir, part.timecorr)
    if not os.path.exists(timecorr_file):
        logging.info('Creating %s', timecorr_file)
        _call_timecorr(part.site, outdir, ctd_prefix)

    timecorr_lines = len(open(timecorr_file, 'r').readlines())
    logging.info('Trigger counts: daq=%s, ctd=%s', daq_triggers, timecorr_lines)

    event_count_file = os.path.basename(ctd_prefix).replace('DAQ-', 'eventcounts-') + '.txt'
    event_count_file = os.path.join(outdir, event_count_file)
    event_count_buffer = ''
    for trigset in range(0, timecorr_lines, 256):
        expected = min([256, timecorr_lines - trigset])
        logging.info('Processing trigset %07d (expecting %d triggers)', trigset, expected)
        try:
            prolog_data = process_subpart(part, trigset, outdir, skip_run)
            is_error = 1 if int(prolog_data['TAMA_KEPT']) != expected else 0
            event_count_buffer += '{:07} {} {} {} {}\n'.format(
                trigset,
                prolog_data['TAMA_KEPT'],
                prolog_data['DURATION'],
                prolog_data['BYTES_OUT'],
                is_error,
            )
        except Exception as err:
            logging.error(' !!! Failed to process %07d !!!: %s', trigset, err)
            event_count_buffer += '{:07} 0 0 0 1\n'.format(trigset)

    with open(event_count_file, 'w') as ecfile:
        ecfile.write(event_count_buffer)


def process_night(night=None, site=None, outdir=os.curdir, skip_run=False):
    if night is None or site is None:
        logging.error('Missing night and/or site argument')
        raise ValueError
    logging.info('Processing site %s for %s', site, night)
    db = DatabaseWrapper(FADC_DB)
    sql = 'SELECT part11 FROM Parts WHERE date={} AND site={} AND daqsigma>=6.0'.format(night, site)
    parts = [row[0] for row in db.retrieve(sql)]
    logging.info('Number of parts found: %s (codes: %s)', len(parts), ', '.join([str(part)[8:10] for part in parts]))
    for part in parts:
        process_part(part, outdir, skip_run)


def _get_db_info(part):
    db = DatabaseWrapper(FADC_DB)
    sql = 'SELECT f.ctdprefix, p.daqtrig, p.daqcams FROM Filesets AS f JOIN Parts AS p ON f.part11=p.part11 WHERE f.part11={}'.format(part)
    rows = db.retrieve(sql)
    if len(rows) != 1:
        logging.error('No unique Fileset found for part11=%s', part)
        raise ValueError("FilesetNotFound")

    ctd_prefix, daq_triggers, daq_cams = rows[0]
    logging.info('ctd_prefix: %s', ctd_prefix)
    return ctd_prefix, daq_triggers, daq_cams



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--part', type=int, help="11-digit part code (yyyymmddpps)")
    parser.add_argument('-n', '--night', type=int, help="8-digit night (yyyymmdd)")
    parser.add_argument('-s', '--site', type=int, choices=[0,1], help="site: 0 (BRM) or 1 (LR)")
    parser.add_argument('-o', '--outdir', help="location for output")
    parser.add_argument('--skip', action='store_true', help='skip the main TAMA generation and re-check output')
    parser.add_argument('-l', '--log', default='process.log', help='name of log file')
    args = parser.parse_args()
    log_name = log.set_up_log(name=args.log, console_mirror=True)
    if args.part is not None:
        process_part(args.part, args.outdir, args.skip)
    elif args.night is not None and args.site is not None:
        process_night(args.night, args.site, args.outdir, args.skip)
    else:
        logging.error('Missing required arguments')
