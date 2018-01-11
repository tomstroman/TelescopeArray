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
import re
import time

from db.database_wrapper import DatabaseWrapper
from utils import log, tawiki


db_wiki = 'db/wiki.db'


def data_report(reset=False, console_mirror=False):
    log_name = log.set_up_log(name='report_log.txt', console_mirror=console_mirror)
    if reset or not os.path.exists(db_wiki):
        logging.warn('Creating new database at %s', db_wiki)
        init_db(db_wiki)

    db = DatabaseWrapper(db_wiki)

    update_from_wiki(db)

    sql = 'SELECT count() FROM Dates'
    nights = db.retrieve(sql)[0][0]
    logging.info('Database contains %s nights', nights)


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


def update_from_wiki(db):
    for year in [2007]:
    #for year in range(2009, 2018):
        html = tawiki.get_page(year)
        dark = get_dark_hours_by_date(html)

        nights = sorted(dark.keys())
        logging.info('Found dark hours for %s night(s) from %s to %s', len(nights), nights[0], nights[-1])


DARK = re.compile('<td>([0-9]{1,2}\.[0-9]{2})</td>') # matches cells like <td>6.84</td>
LOG = re.compile('y([0-9]{4})m([0-9]{2})d([0-9]{2})\.(?:brm?|lr|md|sd)\.log') # like y2018m01d10.brm.log
TIME = re.compile('\w{3} (\w{3} \d+ \d{4}) \d{2}:\d{2} (?:UT|GMT)') # like Thu Jan 10 2018 05:33 GMT
def get_dark_hours_by_date(html):
    dark = {}
    for line in html.split('\n'):
        if DARK.match(line):
            try:
                date, dark_hours = parse_line(line)
                dark[date] = dark_hours
            except Exception as err:
                logging.error('Error %s when processing line:\n%s', err, line)
    return dark


def parse_line(line):
    dark_hours = DARK.match(line).groups()[0]
    times = TIME.findall(line)
    if times:
        ymds = [time.strftime('%Y%m%d', time.strptime(t, '%b %d %Y')) for t in times]
        if len(set(ymds)) == 1:
            date = ymds[0]
            return date, dark_hours

    logging.warn('Could not interpret human-readable date; looking for log files')
    logs = LOG.findall(line)
    if logs:
        ymds = [y+m+d for y,m,d in logs]
        if len(set(ymds)) == 1:
            date = ymds[0]
            return date, dark_hours
        raise Exception('Multiple dates! {}'.format(ymds))
    raise Exception('No logs!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', action='store_true')
    args = parser.parse_args()
    data_report(reset=args.reset, console_mirror=True)
