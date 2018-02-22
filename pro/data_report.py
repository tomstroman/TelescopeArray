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


MAX_DATE = 20171201
db_wiki = 'db/tafd_status.db'
db_fadc = 'db/fadc_data.db'

site_to_site_id = {
    'brm' : 0,
    'lr'  : 1,
    'md'  : 2,
}

YMDPS = re.compile('(\d{4})(\d{2})(\d{2})(\d{2})(\d)')
TIMECORRS = {
    '0': '/tama_{4}/black-rock/{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt',
    '1': '/tama_{4}/long-ridge/{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt',
}
DSTS = {
    '0': '/tama_{4}/black-rock/{0}{1}{2}/{5}-{4}-0000000.dst.gz',
    '1': '/tama_{4}/long-ridge/{0}{1}{2}/{5}-{4}-0000000.dst.gz',
}
FDPEDS = {
    '0': '/scratch1/fdpedv/black-rock/{0}{1}{2}/y{0}m{1}d{2}p{3}.ped.dst.gz',
    '1': '/scratch1/fdpedv/long-ridge/{0}{1}{2}/y{0}m{1}d{2}p{3}.ped.dst.gz',
}

# status system: characterize progress of a given night or part numerically, with
# higher numbers representing further processing. Negative numbers are used to
# indicate parts that are known to have problems and *cannot* be processed to
# the corresponding positive number. Nights or parts with negative statuses in
# whatever database field ends up holding them will be ignored.
class Status(object):
    def __init__(self):
        pass

night_statuses = Status()
night_statuses.WIKI_EXISTS = 0 # Wiki indicates detector may have run

night_statuses.LOG_EXISTS = 1 # log file found
night_statuses.LOG_MISSING = -1 # log file missing from disk and cannot be corrected

night_statuses.SIXSIGMA = 2 # log file includes data parts at 6-sigma threshold or higher
night_statuses.NO_SIXSIGMA = -2 # log file shows no data parts of scientific merit

night_statuses.DAQ_EXISTS = 3 # any data for this night exists (may be incomplete)
night_statuses.DAQ_MISSING = -3 # no data can be found for this night

night_statuses.DAQ_COMPLETE = 4 # data exists for all parts listed in log (includes parts terminated early)
night_statuses.DAQ_INCOMPLETE = -4 # data missing for at least some parts

night_statuses.FDPED_EXISTS = 5 # FDPED data summary has been generated and is in the expected location
night_statuses.FDPED_FAILURE = -5 # FDPED generation fails and cannot be corrected

part_statuses = Status()

part_statuses.LOG_EXISTS = 0 # A log file claims this part was requested during operation

part_statuses.DAQ_EXISTS = 1
part_statuses.DAQ_MISSING = -1 # no data can be found for this part

part_statuses.TIMECORR_EXISTS = 2 # timecorr file is found in the expected location
part_statuses.TIMECORR_FAILURE = -2 # timecorr generation fails and cannot be corrected

part_statuses.DST_EXISTS = 3 # DST files are found in the expected location
part_statuses.DST_FAILURE = -3 # DST generation fails and cannot be corrected

part_statuses.FDPED_EXISTS = 4
part_statuses.FDPED_FAILURE = -4

part_statuses.CALIBRATION_COMPLETE = 5 # FDPlane processing mentions no "missing" pedestal, gain, or reflectance errors
part_statuses.CALIBRATION_INCOMPLETE = -5 # calibration permanently unavailable for some or all of data part


def data_report(reset=False, console_mirror=False, check_wiki_log=False):
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

    sql = 'SELECT count() FROM NightStatus WHERE status={} AND site<2'.format(night_statuses.WIKI_EXISTS)
    num_wiki = db.retrieve(sql)[0][0]
    logging.info('FADC FD runs in state WIKI_EXISTS: %s', num_wiki)

    db.attach(db_fadc, 'FDDB')
    sql = 'SELECT n.date, n.site FROM NightStatus AS n JOIN FDDB.Runnights AS r ON n.date=r.date AND n.site=r.site WHERE n.status={}'.format(night_statuses.WIKI_EXISTS)
    rows = db.retrieve(sql)
    if rows:
        logging.info('Log files found for %s FD runs; promoting status', len(rows))
        db.update_rows('UPDATE NightStatus SET status={} WHERE date=? AND site=?'.format(night_statuses.LOG_EXISTS), tuple(rows))

    sql = 'SELECT count() FROM NightStatus WHERE status={} AND site<2'.format(night_statuses.LOG_EXISTS)
    num_log = db.retrieve(sql)[0][0]
    logging.info('FADC FD runs in state LOG_EXISTS: %s', num_log)

    sql = 'SELECT n.date, n.site FROM FDDB.Parts AS p JOIN NightStatus AS n ON n.date=p.date AND n.site=p.site WHERE p.daqsigma=6.0 AND n.status={}'.format(night_statuses.LOG_EXISTS)
    rows = db.retrieve(sql)
    unique_rows = set(rows)
    if unique_rows:
        logging.info('Six-sigma parts in LOG_EXISTS: %s in %s runs; promoting status', len(rows), len(unique_rows))
        db.update_rows('UPDATE NightStatus SET status={} WHERE date=? AND site=?'.format(night_statuses.SIXSIGMA), tuple(unique_rows))

    sql = 'SELECT count() FROM NightStatus WHERE status={} AND site<2'.format(night_statuses.SIXSIGMA)
    num_six = db.retrieve(sql)[0][0]
    logging.info('FADC FD runs in state SIXSIGMA: %s', num_six)

    sql = 'SELECT n.date, n.site FROM FDDB.Filesets AS f JOIN FDDB.Parts AS p ON p.part11=f.part11 JOIN NightStatus AS n ON n.date=p.date AND n.site=p.site WHERE p.daqsigma=6.0 AND n.status={}'.format(night_statuses.SIXSIGMA)
    rows = db.retrieve(sql)
    unique_rows = set(rows)
    if unique_rows:
        logging.info('Filesets in SIXSIGMA: %s in %s runs; promoting status', len(rows), len(unique_rows))
        db.update_rows('UPDATE NightStatus SET status={} WHERE date=? AND site=?'.format(night_statuses.DAQ_EXISTS), tuple(unique_rows))

    sql = 'SELECT date, site FROM NightStatus WHERE status={} AND site<2'.format(night_statuses.DAQ_EXISTS)
    any_daq_exists = db.retrieve(sql)
    logging.info('FADC FD runs in state DAQ_EXISTS: %s', len(any_daq_exists))

    sql = 'SELECT n.date, n.site FROM FDDB.Parts AS p LEFT OUTER JOIN FDDB.Filesets AS f ON p.part11=f.part11 JOIN NightStatus AS n ON p.date=n.date AND p.site=n.site WHERE n.status={} AND p.daqsigma=6.0 AND f.ctdprefix IS NULL'.format(night_statuses.DAQ_EXISTS)
    rows = db.retrieve(sql)
    complete_rows = set(any_daq_exists) - set(rows)
    if complete_rows:
        logging.info('DAQ found for all parts on %s DAQ_EXISTS runs; promoting status', len(complete_rows))
        db.update_rows('UPDATE NightStatus SET status={} WHERE date=? AND site=?'.format(night_statuses.DAQ_COMPLETE), tuple(complete_rows))

    sql = 'SELECT date, site FROM NightStatus WHERE status={} AND site<2'.format(night_statuses.DAQ_COMPLETE)
    all_daq_exists = db.retrieve(sql)
    logging.info('FADC FD runs in state DAQ_COMPLETE: %s', len(all_daq_exists))

    sql = 'SELECT f.part11, f.date, f.part, f.site from FDDB.Parts AS f WHERE f.daqsigma=6.0 AND f.part11 NOT IN (SELECT part11 FROM PartStatus)'
    new_parts = db.retrieve(sql)
    if new_parts:
        logging.info('Found %s new 6-sigma part(s); adding to status DB with status LOG_EXISTS', len(new_parts))
        for part11, date, part, site in new_parts:
            try:
                db.insert_row('INSERT INTO PartStatus VALUES(?, ?, ?, ?, ?)', (part11, date, part, site, part_statuses.LOG_EXISTS))
            except Exception as err:
                logging.error('Error adding %s: %s', part11, err)

    sql = 'SELECT part11 FROM PartStatus WHERE status={}'.format(part_statuses.LOG_EXISTS)
    logged_parts = db.retrieve(sql)
    logging.info('Six-sigma parts in state LOG_EXISTS: %s', len(logged_parts))

    sql = 'SELECT part11 FROM FDDB.Filesets WHERE part11 IN ({})'.format(sql)
    rows = db.retrieve(sql)
    if rows:
        logging.info('DAQ found for %s LOG_EXISTS part(s); promoting status', len(rows))
        db.update_rows('UPDATE PartStatus SET status={} WHERE part11=?'.format(part_statuses.DAQ_EXISTS), tuple(rows))

    sql = 'SELECT part11 FROM PartStatus WHERE status={}'.format(part_statuses.DAQ_EXISTS)
    daq_parts = db.retrieve(sql)
    logging.info('Six-sigma parts in state DAQ_EXISTS: %s', len(daq_parts))

    timecorr_found = set()
    for part11, in daq_parts:
        timecorr = _timecorr_file(part11)
        logging.info('Searching for %s', timecorr)
        if os.path.exists(timecorr):
            timecorr_found.add((part11,))
    if timecorr_found:
        logging.info('Found timecorr for %s DAQ_EXISTS part(s); promoting status', len(timecorr_found))
        db.update_rows('UPDATE PartStatus SET status={} WHERE part11=?'.format(part_statuses.TIMECORR_EXISTS), tuple(timecorr_found))

    sql = 'SELECT f.part11, f.ctdprefix FROM FDDB.Filesets AS f WHERE f.part11 IN (SELECT part11 FROM PartStatus WHERE status={}) ORDER BY f.part11'.format(part_statuses.TIMECORR_EXISTS)
    tc_parts = db.retrieve(sql)
    logging.info('Six-sigma parts in state TIMECORR_EXISTS: %s', len(tc_parts))

    dst0_found = set()
    for part11, ctd_prefix in tc_parts:
        dst0 = _dst0_file(part11, ctd_prefix)
        logging.info('Searching for %s', dst0)
        if os.path.exists(dst0):
            dst0_found.add((part11,))
    if dst0_found:
        logging.info('Found dst0 for %s TIMECORR_EXISTS part(s); promoting status', len(dst0_found))
        db.update_rows('UPDATE PartStatus SET status={} WHERE part11=?'.format(part_statuses.DST_EXISTS), tuple(dst0_found))

    sql = 'SELECT part11 FROM PartStatus WHERE status={} ORDER BY part11'.format(part_statuses.DST_EXISTS)
    dst_parts = db.retrieve(sql)
    logging.info('Six-sigma parts in state DST_EXISTS: %s', len(dst_parts))

    fdped_found = set()
    for part11, in dst_parts:
        fdped = _fdped_part_file(part11)
        logging.info('Searching for %s', fdped)
        if os.path.exists(fdped):
            fdped_found.add((part11,))
    if fdped_found:
        logging.info('Found fdped for %s DST_EXISTS part(s); promoting status', len(fdped_found))
        db.update_rows('UPDATE PartStatus SET status={} WHERE part11=?'.format(part_statuses.FDPED_EXISTS), tuple(fdped_found))

    sql = 'SELECT part11 FROM PartStatus WHERE status={}'.format(part_statuses.FDPED_EXISTS)
    fdped_parts = db.retrieve(sql)
    logging.info('Six-sigma parts in state FDPED_EXISTS: %s', len(fdped_parts))


def _timecorr_file(part11):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    return TIMECORRS[s].format(y, m, d, p, s)


def _dst0_file(part11, ctd_prefix):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    daq_code = os.path.basename(ctd_prefix)
    return DSTS[s].format(y, m, d, p, s, daq_code)


def _fdped_part_file(part11):
    y, m, d, p, s = YMDPS.findall(str(part11))[0]
    return FDPEDS[s].format(y, m, d, p, s)


def extra_code(db):
    sql = 'SELECT count(), sum(darkhours) FROM Dates'
    nights, dark_hours = db.retrieve(sql)[0]
    logging.info('Database contains %s nights with %s dark hours', nights, dark_hours)
    sql = 'SELECT count(), sum(darkhours) FROM Dates WHERE darkhours > 3.0'
    run_nights, run_darkhours = db.retrieve(sql)[0]
    logging.info('%s nights with > 3.0 dark hours for %s hours', run_nights, run_darkhours)

    for site_id in range(2):
        sql = 'SELECT count(), sum(d.darkhours) FROM Dates AS d JOIN NightStatus AS w ON d.date=w.date WHERE w.site={site_id} AND d.darkhours > 3.0'.format(
            site_id=site_id,
        )
        site_night_count, site_darkhours = db.retrieve(sql)[0]

        logging.info('Site %s has wiki logs for %s nights with %s dark hours (%0.3f of all >3.0-hour nights)',
            site_id, site_night_count, site_darkhours, float(site_darkhours)/float(run_darkhours)
        )

        sql = 'SELECT w.wikilog, d.darkhours FROM NightStatus AS w JOIN Dates AS d ON d.date=w.date WHERE site={site_id} AND d.date<{max_date}'.format(
            site_id=site_id,
            max_date=MAX_DATE,
        )
        site_nights_hours = db.retrieve(sql)
        site_hours = {night: hours for night, hours in site_nights_hours}
        site_nights = set([row[0] for row in site_nights_hours])

        sql = 'SELECT w.wikilog FROM FDDB.Runnights AS r JOIN NightStatus AS w ON r.date=w.date AND r.site=w.site WHERE w.site={site_id}'.format(
            site_id=site_id,
        )
        site_fdnights = set([row[0] for row in db.retrieve(sql)])
        logging.info('Site %s has tadserv logs for %s nights', site_id, len(site_fdnights))
        missing_nights = site_nights - site_fdnights

        if site_id == 2:
            continue
        logging.info('Pre-%s nights (hours) missing from tadserv', MAX_DATE)
        for night in sorted(list(missing_nights)):
            logging.info('%s (%s hours):', night, site_hours[night])
            if check_wiki_log:
                logging.info('log content:\n%s', get_wiki_log_content(night))


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
                    db.insert_row('INSERT INTO NightStatus VALUES(?, ?, ?, ?)',
                        (date, site_to_site_id[site[1]], site[0].lower(), night_statuses.WIKI_EXISTS)
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


LOGTEXT = re.compile('(?<=start content -->\n).*(?=\n<!-- \nNewPP)', flags=re.S)
def get_wiki_log_content(log_file):
    log_html = tawiki.get_log_page(log_file)
    text = LOGTEXT.findall(log_html)
    if text:
        return text[0]
    else:
        return '(could not parse {}'.format(log_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reset', action='store_true')
    parser.add_argument('-w', '--wiki', action='store_true')
    args = parser.parse_args()
    data_report(reset=args.reset, console_mirror=True, check_wiki_log=args.wiki)
