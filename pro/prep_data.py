# prep_data.py
# Thomas Stroman, University of Utah 2018-01-24
# Run TAMA on raw FADC telescope data to produce DST files.

import argparse
import logging
from utils import log


def process_part(part=None, console_mirror=False):
    log_name = log.set_up_log(name='process.log', console_mirror=console_mirror)
    logging.info('Logging to %s', log_name)
    if part is None:
        logging.error('No part specified!')
        return
    logging.info('Processing part %s', part)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--part', type=int, help="11-digit part code (yyyymmddpps)")
    args = parser.parse_args()
    process_part(args.part, console_mirror=True)
