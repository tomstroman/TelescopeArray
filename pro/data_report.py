# data_report.py
# Thomas Stroman, University of Utah 2018-01-07
# A program to report on the possibility, existence, availability, and status of data
# on a night-by-night basis from the Telescope Array experiment from the perspective
# of a specific data storage server ("tadserv") and compute cluster ("sithlord").

# The "source of truth" for *possibility* of data is the lunar calendar: if the moon
# is above the horizon, no data can be taken. In a more specific sense, the number of
# moonless nighttime hours (between the end of astronomical twilight after dusk and the
# beginning of astronomical twilight before dawn) is calculated for each day on the
# Telescope Array wiki, and for each date in the past, we also have records of any
# attempt to collect data. So the wiki is the source of truth for possibility.

# The source of truth for *existence* of data is its presence on any disk in tadserv.
# The raw data, straight from the telescopes, is stored there, but with no guarantee of
# high availability; sometimes a system containing a subset of the data is down for maintenance.
# So the *availability* of the data is more fluid, potentially varying from one report to another.

# The *status* of data indicates whether it has undergone the basic processing to promote it to
# the DST framework used by all the analysis code.

import argparse
import logging
import os

from db.database_wrapper import DatabaseWrapper
from utils import log


db_wiki = 'db/wiki.db'


def data_report(reset=False, console_mirror=False):
    log_name = log.set_up_log(name='report_log.txt', console_mirror=console_mirror)
    if reset or not os.path.exists(db_wiki):
        logging.warn('Creating new database at %s', db_wiki)
        init_db(db_wiki)


def init_db(dbfile):
    import sqlite3
    from copy import copy
    from db.tables import fd_daq_tables
    from db import static_data
    with sqlite3.connect(dbfile) as con:
        cur = con.cursor()

        for table, structure in fd_daq_tables:
            cur.execute('DROP TABLE IF EXISTS {0}'.format(table))
            cur.execute('CREATE TABLE {0}({1})'.format(table, structure))

        cur.executemany('INSERT INTO Sites VALUES(?, ?, ?, ?)', static_data.sites)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', action='store_true')
    args = parser.parse_args()
    data_report(reset=args.reset, console_mirror=True)
