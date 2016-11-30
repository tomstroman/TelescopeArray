# fadc_data.py
# Thomas Stroman, University of Utah, 2016-11-28
# Storage of information for Telescope Array FADC data processing


import sqlite3
import os
import re
from glob import glob
default_dbfile = 'fadc_data.db'

def report(db=default_dbfile):
    """
    Print a list of tables in the database, with the number of rows in each.
    """
    import json
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
        dbtables = [table[0] for table in cur.fetchall()]

        counts = {}
        for table in dbtables:
            cur.execute('SELECT count() FROM {0}'.format(table))
            counts[table] = cur.fetchall()[0][0]

    print json.dumps(counts, sort_keys=True, indent=2)




def init(db=default_dbfile):
    """
    Create the database tables from scratch (overwriting any existing ones),
    and initialize with static data where appropriate.
    """
    from tables import fadc_tables
    import static_data
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        for table, structure in fadc_tables:
            cur.execute('DROP TABLE IF EXISTS {0}'.format(table))
            cur.execute('CREATE TABLE {0}({1})'.format(table, structure))

        cur.executemany('INSERT INTO Sites VALUES(?, ?, ?, ?)', static_data.sites)
        
def retrieve(sql, db=default_dbfile):
    """
    Execute arbitrary SQL on the specified database, provided the SQL begins
    with 'SELECT ', then return the selected rows.
    """
    assert sql.upper().startswith('SELECT ')

    with sqlite3.connect(db) as con:
        cur = con.cursor()

        cur.execute(sql)
        rows = cur.fetchall()
    return rows

def insert_row(sql, values, db=default_dbfile):
    """
    Execute arbitrary SQL on the specified database, provided the SQL begins
    with 'INSERT INTO '. A tuple is expected for values.
    """
    assert isinstance(values, tuple)
    assert sql.count('?') == len(values)
    assert sql.upper().startswith('INSERT INTO ')
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = 1')
        cur.execute(sql, values)

def insert_rows(sql, all_values, db=default_dbfile):
    """
    Execute arbitrary SQL on the specified database, provided the SQL begins
    with 'INSERT INTO '. A tuple of tuples is expected for all_values.
    """
    assert isinstance(all_values, tuple)
    assert sql.upper().startswith('INSERT INTO ')
    num_v = sql.count('?')
    assert all(isinstance(values, tuple) and len(values) == num_v for values in all_values)
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys = 1')
        cur.executemany(sql, all_values)

def find_new_downloads(db=default_dbfile):
    """
    Locate all paths matching /tadserv*/tafd/*/*/ctd/ and add to the database.
    Return the number of new paths found.
    """
    db_downloads = retrieve('SELECT path, site FROM Downloads', db)
    print 'Downloads already in database:', len(db_downloads)
    tafd_list = sorted(glob('/tadserv*/tafd/'))
    new_downloads = []
    for tafd in tafd_list:
        ctd_list = glob(tafd + '*/*/ctd/')
        for ctd in ctd_list:
            site = int(ctd.split('station')[1][0]) # path contains "station0" or "station1"
            path = ctd[:-4] # truncate "ctd/"
            download = (path, site)
            try:
                db_downloads.remove(download) # This download was in DB already
            except ValueError: # this download is new
                new_downloads.append(download)
    if len(db_downloads):
        print 'Downloads not found in this scan:', [d[0] for d in db_downloads]

    num_new = len(new_downloads)
    if num_new:
        print 'New downloads found in this scan:', num_new    
        insert_rows('INSERT INTO Downloads VALUES(?, ?)', tuple(new_downloads))

    return num_new

def _pick_sameday_log(logs):
    """
    On rare occasion, two logs may exist whose filenames indicate they refer to the same day.
    When that happens, exclude the one with a purely numeric name.
    """
    to_remove = []
    for log in logs:
        logfile = log.split(os.path.sep)[-1]
        if '_' in logfile and 'y' in logfile:
            dirname = os.path.dirname(log)
            ymd = ''.join([c for c in logfile if c.isdigit()])
            ymdlog = os.path.join(dirname, ymd + '.log')
            to_remove.append(ymdlog)
    for r in to_remove:
        try:
            logs.remove(r)
        except ValueError:
            pass
    return logs

def _get_paths_to_logs(db_downloads):
    """
    The same log file can be found in multiple downloads. Assemble a dict with
    log files as keys, and the value is a list of paths to each log file.
    """
    paths_to_log = {}
    print 'Getting paths to logs.'
    for download, site in db_downloads:
        normal_log = os.path.join(download, 'daq-ctrl/y*_*.log')
        alt_log = os.path.join(download, 'daq-ctrl/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].log')
        logs = sorted(glob(normal_log) + glob(alt_log))
        logs = _pick_sameday_log(logs)
        for log in logs:
            sitelog = '{}:{}'.format(site, os.path.basename(log))
            try:
                paths_to_log[sitelog].append(log)
            except KeyError:
                paths_to_log[sitelog] = [log]
    return paths_to_log

def _filter_incomplete_logs(orig_logs):
    """
    Recursive. Looks through orig_logs to confirm that multiple files
    are actually copies of the same content. If this is true, 
    return the original list. Whitespace and non-"part" lines
    are ignored, but if multiple distinct part sets are defined by files of the same name,
    we keep the longest set(s), removing everything shorter. Then we call this
    function again on the reduced set.
    """
    logfile = os.path.basename(orig_logs[0])
    all_parts = {l: '\n'.join(re.findall('.*\|.*\|.*\|.*\|', open(l, 'r').read())) for l in orig_logs}
    unique_part_data = set(all_parts.values())
    if len(unique_part_data) == 1:
        return orig_logs, all_parts.values()[0].count('|')
    else:
        count = len(orig_logs)
        print 'WARNING: Multiple unique log files matching', logfile
        maxcounts = max([p.count('|') for p in unique_part_data])
        for part_data in unique_part_data:
            matching_files = [k for k,v in all_parts.items() if v==part_data]
            print '{0}:'.format(part_data), matching_files
            if part_data.count('|') < maxcounts:
                for f in matching_files:
                    print 'Removing', f
                    orig_logs.remove(f)
        if len(orig_logs) < count:            
            return _filter_incomplete_logs(orig_logs)
        else:
            raise Exception("Different logs, same part count!")

def _find_ctd_and_log(chron_logs, skip=False):
    """
    For a set of logs, find the actual download that contains the files from the logged night.
    Start by checking the downloads where the logs were found. If files are in none of them,
    do a brute-force search. If brute-force search turns up multiple matches, inspect the log
    to count parts, figure out which location contains the most matching files, and choose it.
    """
    ymd = ''.join([c for c in os.path.basename(chron_logs[0]) if c.isdigit()])

    if skip:
        return None, chron_logs[0], ymd

    for log in chron_logs:
        download, logfile = log.split('/daq-ctrl/')
        ctd = download + '/ctd/event-data'
        ctds = glob(ctd + '/DAQ-' + ymd[2:] + '*.d.bz2')
        if len(ctds) > 0:
            print ctd, log
            return ctd, log, ymd            
    else:
        print 'No CTD found for {} in {} location(s) searched. Comprehensive search now...'.format(logfile, len(chron_logs))
        site = log.split('station')[1][0]

        normal_ctd = '/tadserv*/tafd/*/*/ctd/event-data/DAQ-{}??-{}-*.d.bz2'.format(ymd[2:], site)
        alt_ctd = '/tadserv*/tafd/*/*/ctd/event-data/DAQ-0{}??-{}-*.d.bz2'.format(ymd[4:], site)

        ctds = glob(normal_ctd) + glob(alt_ctd)
        
        if len(ctds) == 0:
            print 'Still no files found! Giving up.'
            ctd = chron_logs[0].split('daq-ctrl/')[0] + 'ctd/event-data'
            return ctd, chron_logs[0], ymd
        
        downloads = [ctd.split('ctd/')[0] for ctd in ctds]
        if len(set(downloads)) > 1:
            print 'Found multiple matching downloads:', set(downloads)
            allparts = re.findall('.*\|.*\|.*\|.*\|', open(log, 'r').read())
            
            part_ids = [p.split()[0][-2:] for p in allparts]
            filecount = {d: sum([len(glob('{}/ctd/event-data/DAQ-*{}{}-{}-*.d.bz2'.format(d, ymd[4:], p, site))) for p in part_ids]) for d in list(set(downloads))}
            
            sorted_filecount = sorted(filecount.items(), key=lambda x: x[1], reverse=True)
            print 'Matching file counts; choosing largest:', sorted_filecount
            ctd = sorted_filecount[0][0] + 'ctd/event-data'
            return ctd, chron_logs[0], ymd
        
        
        ctd = downloads[0] + 'ctd/event-data'
        print 'All possibly matching files found in single location; inferring', ctd
        return ctd, chron_logs[0], ymd

def find_new_runnights(db=default_dbfile):
    """
    Populate the Runnights table from logs in known downloads. Insert one row at a time
    to tolerate interruptions.
    """
    db_runnights = retrieve('SELECT site, logfile FROM Runnights')
    print 'Logfiles already in database:', len(db_runnights)
    db_sitelogs = ['{}:{}'.format(site, os.path.basename(logfile)) for site, logfile in db_runnights]
    db_downloads = retrieve('SELECT path, site FROM Downloads')

    paths_to_logs = _get_paths_to_logs(db_downloads)
    print 'Unique sitelogs:', len(paths_to_logs.keys())

    for sitelog, logs in sorted(paths_to_logs.items()):
        if sitelog in db_sitelogs:
            continue
        try:
            logs, maxcount = _filter_incomplete_logs(logs)
        except:
            print 'Error filtering', sitelog
            continue

        # order the logs by date of download, found in the path after 'tafd'
        chron_logs = sorted(logs, key=lambda x: x.split('tafd')[1])

        try:
            ctd, log, ymd = _find_ctd_and_log(chron_logs, skip=not bool(maxcount))
        except:
            print 'Error finding CTD:', chron_logs[0]

        if ctd is not None:
            download = ctd.split('ctd/')[0]
        elif maxcount==0:
            # log contains no parts
            download = log.split('daq-ctrl')[0]
        else:
            print 'Error: neither empty log nor found data --', log
            continue

        site = int(sitelog[0])
        runnight = (int(ymd), site, download, log)
        insert_row('INSERT INTO Runnights VALUES(?, ?, ?, ?)', runnight)

def _get_parts_by_runnight(db_parts):
    parts_by_runnight = {}
    for date, part, site in db_parts:
        k = (date, site)
        try:
            parts_by_runnight[k].append(part)
        except KeyError:
            parts_by_runnight[k] = [part]

    return parts_by_runnight

def _get_parts_from_log(logfile, date, site):
    parts = []
    partlines = re.findall('.*\|.*\|.*\|.*\|', open(logfile, 'r').read())
    for line in partlines:
        part_id, cameras, sigma, triggers =  [l.strip() for l in line.split('|')][:-1]
        try:
            part = int(part_id[-2:])
            daqcams = sum([2**c for c in map(int, cameras.split())]) # represent 12 cameras as 12 bits
            daqsigma = float(sigma)
            daqtrig = int(triggers)
        except ValueError:
            print 'Error in {} parsing line {}'.format(logfile, line)
            continue
        part11 = 1000*date + 10*part + site
        dbpart = (part11, date, part, site, daqtrig, daqcams, daqsigma)
        if dbpart in parts:
            print 'Warning - skipping repeat  occurrences of', dbpart
            continue
        parts.append(dbpart)
    return parts

def find_new_parts(db=default_dbfile):
    db_parts = retrieve('SELECT date, part, site FROM Parts')
    print 'Parts already in database:', len(db_parts)
    db_parts_by_runnight = _get_parts_by_runnight(db_parts)

    db_runnights = retrieve('SELECT date, site, logfile FROM Runnights')
    for date, site, logfile in db_runnights:
        if (date, site) in db_parts_by_runnight.keys():
            continue
        print logfile
        try:
            logparts = tuple(_get_parts_from_log(logfile, date, site))
        except:
            print 'Error finding parts in', logfile
            continue
        insert_rows('INSERT INTO Parts VALUES(?, ?, ?, ?, ?, ?, ?)', logparts)

def find_filesets(db=default_dbfile):
    db_filesets = retrieve('SELECT part11 FROM Filesets')
    print 'Filesets already in database:', len(db_filesets)

    db_parts = retrieve('SELECT p.part11, r.download FROM Parts AS p JOIN Runnights AS r ON p.date=r.date AND p.site=r.site WHERE p.daqsigma=6.0 ORDER BY p.part11')
    for part11, download in db_parts:
        if (part11,) in db_filesets:
            continue

        ctdpath = os.path.join(download, 'ctd/event-data/')
        daqname = 'DAQ-*{}-{}-???????.d.bz2'.format(str(part11)[4:10], part11 % 10)
        ctd_daqs = glob(os.path.join(ctdpath, daqname))
        if not ctd_daqs:
            print 'No files found for', part11
            continue
        ctdprefix = ctd_daqs[0][:-16]
        fileset = (part11, ctdprefix)
        print fileset
        insert_row('INSERT INTO Filesets VALUES(?, ?)', fileset)

