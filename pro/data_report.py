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


MAX_DATE = 20161111
db_wiki = 'db/wiki.db'
db_fadc = 'db/fadc_data.db'

site_to_site_id = {
    'brm' : 0,
    'lr'  : 1,
    'md'  : 2,
}

def data_report(reset=False, console_mirror=False):
    log_name = log.set_up_log(name='report_log.txt', console_mirror=console_mirror)
    logging.info('MAX_DATE: %s', MAX_DATE)
    is_db_new = False
    if reset or not os.path.exists(db_wiki):
        logging.warn('Creating new database at %s', db_wiki)
        init_db(db_wiki)
        is_db_new = True

    db = DatabaseWrapper(db_wiki)

    if is_db_new:
        update_from_wiki(db)

    sql = 'SELECT count(), sum(darkhours) FROM Dates'
    nights, dark_hours = db.retrieve(sql)[0]
    logging.info('Database contains %s nights with %s dark hours', nights, dark_hours)
    sql = 'SELECT count(), sum(darkhours) FROM Dates WHERE darkhours > 3.0'
    run_nights, run_darkhours = db.retrieve(sql)[0]
    logging.info('%s nights with > 3.0 dark hours for %s hours', run_nights, run_darkhours)

    db.attach(db_fadc, 'FDDB')
    for site_id in range(3):
        sql = 'SELECT count(), sum(d.darkhours) FROM Dates AS d JOIN Wikilogs AS w ON d.date=w.date WHERE w.site={site_id} AND d.darkhours > 3.0'.format(
            site_id=site_id,
        )
        site_night_count, site_darkhours = db.retrieve(sql)[0]

        logging.info('Site %s has wiki logs for %s nights with %s dark hours (%0.3f of all >3.0-hour nights)',
            site_id, site_night_count, site_darkhours, float(site_darkhours)/float(run_darkhours)
        )

        sql = 'SELECT w.file, d.darkhours FROM Wikilogs AS w JOIN Dates AS d ON d.date=w.date WHERE site={site_id} AND d.date<{max_date}'.format(
            site_id=site_id,
            max_date=MAX_DATE,
        )
        site_nights_hours = db.retrieve(sql)
        site_hours = {night: hours for night, hours in site_nights_hours}
        site_nights = set([row[0] for row in site_nights_hours])

        sql = 'SELECT w.file FROM FDDB.Runnights AS r JOIN Wikilogs AS w ON r.date=w.date AND r.site=w.site WHERE w.site={site_id}'.format(
            site_id=site_id,
        )
        site_fdnights = set([row[0] for row in db.retrieve(sql)])
        logging.info('Site %s has tadserv logs for %s nights', site_id, len(site_fdnights))
        missing_nights = site_nights - site_fdnights

        if site_id == 2:
            continue
        logging.info('Pre-%s nights (hours) missing from tadserv:\n%s',
            MAX_DATE,
            '\n'.join(['{}: {}'.format(night, site_hours[night]) for night in sorted(list(missing_nights))])
        )






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


START_YEAR = 2007
CUTOFF_YEAR = 2018 # will not be included in range()


def update_from_wiki(db):
    existing_rows = [r[0] for r in db.retrieve('SELECT date FROM Dates')]
    for year in range(START_YEAR, CUTOFF_YEAR):
        html = tawiki.get_page(year)
        dark, site_logs = get_dark_hours_logs_by_date(html)

        nights = sorted(dark.keys())
        logging.info('Found %s dark hours for %s night(s) from %s to %s', sum(dark.values()), len(nights), nights[0], nights[-1])
        new_dark_tuples = [(night, dark[night]) for night in nights if night not in existing_rows]

        db.insert_rows('INSERT INTO Dates VALUES(?, ?)', tuple(new_dark_tuples))

        for date, sites in site_logs.items():
            for site in sites:
                try:
                    db.insert_row('INSERT INTO Wikilogs VALUES(?, ?, ?)', 
                        (date, site_to_site_id[site[1]], site[0].lower())
                    )
                except Exception as err:
                    logging.error('Exception: %s executing SQL for %s, %s', err, date, sites)


DARK = re.compile('<td>([0-9]{1,2}\.[0-9]{2})</td>') # matches cells like <td>6.84</td>
LOG = re.compile('y([0-9]{4})m([0-9]{2})d([0-9]{2})\.(?:brm?|lr|md|sd)\.log') # like y2018m01d10.brm.log
TIME = re.compile('\w{3} (\w{3} \d+ \d{4}) \d{2}:\d{2} (?:UT|GMT)') # like Thu Jan 10 2018 05:33 GMT
def get_dark_hours_logs_by_date(html):
    dark = {}
    site_logs = {}
    for line in html.split('\n'):
        if DARK.match(line):
            try:
                date, dark_hours = parse_line(line)
                dark[date] = dark_hours
                sites_with_logs = parse_line_logs(line, date)
                if sites_with_logs:
                    site_logs[date] = sites_with_logs
            except Exception as err:
                logging.error('Error %s when processing line:\n%s', err, line)
    return dark, site_logs


def parse_line(line):
    dark_hours = float(DARK.match(line).groups()[0])
    times = TIME.findall(line)
    if times:
        ymds = [time.strftime('%Y%m%d', time.strptime(t, '%b %d %Y')) for t in times]
        if len(set(ymds)) == 1:
            date = ymds[0]
            return date, dark_hours
        logging.warn('Could not interpret human-readable date; looking for log files\n%s', line)

    logs = LOG.findall(line)
    if logs:
        ymds = [y+m+d for y,m,d in logs]
        if len(set(ymds)) == 1:
            date = ymds[0]
            return date, dark_hours
        raise Exception('Multiple dates! {}'.format(ymds))
    raise Exception('No logs!')


YMD = re.compile('(\d{4})(\d{2})(\d{2})')
def parse_line_logs(line, date):
    file_date = 'Y{}m{}d{}'.format(*YMD.match(date).groups())
    existing_logs = re.findall('title="({}\.(brm|lr|md)\.log)">'.format(file_date), line)
    return existing_logs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', action='store_true')
    args = parser.parse_args()
    data_report(reset=args.reset, console_mirror=True)
