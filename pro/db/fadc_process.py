# fadc_process.py
# Thomas Stroman, University of Utah, 2016-11-30
# Storage of information for Telescope Array FADC data processing.

import sqlite3
import os
from database_wrapper import DatabaseWrapper

from fadc_data import default_dbfile as rawdata_dbfile

import utils

rawdb = DatabaseWrapper(rawdata_dbfile)

default_dbfile = 'db/fadc_process.db'
db = DatabaseWrapper(default_dbfile)

def init(dbfile=db.db):
    from tables import fadc_process_tables
    with sqlite3.connect(dbfile) as con:
        cur = con.cursor()
        for table, structure in fadc_process_tables:
            cur.execute('DROP TABLE IF EXISTS {0}'.format(table))
            cur.execute('CREATE TABLE {0}({1})'.format(table, structure))

def import_new_raw_parts():
    db_parts = db.retrieve('SELECT part, daqcams, daqtrig FROM Parts')
    print 'Parts already in processing DB:', len(db_parts)

    new_parts = []
    raw_parts = rawdb.retrieve('SELECT part11, daqcams, daqtrig FROM Parts ORDER BY part11')
    new_parts = set(raw_parts) - set(db_parts)

    db.insert_rows('INSERT INTO Parts (part, daqcams, daqtrig) VALUES (?, ?, ?)', tuple(new_parts))

#tama = {str(siteid): '/tama_{}/{}/'.format(siteid, name) for siteid, name in rawdb.retrieve('SELECT id, name FROM Sites WHERE id<2')}

# hard-coding to avoid issues with database path when importing
tama = {'0': '/tama_0/black-rock/', '1': '/tama_1/long-ridge/'}

def _ymdps(part):
    x = str(part)
    return x[0:4], x[4:6], x[6:8], x[8:10], x[10]

def _timecorr_path(part):
    y, m, d, p, s = _ymdps(part)
    return os.path.join(tama[s], '{0}{1}{2}/y{0}m{1}d{2}p{3}_site{4}_timecorr.txt'.format(y,m,d,p,s))

def _eventcounts_path(part, daq_prefix):
    y, m, d, p, s = _ymdps(part)
    return os.path.join(tama[s], '{0}{1}{2}'.format(y, m, d), daq_prefix.replace('DAQ', 'eventcounts') + '.txt')

def update_parts_with_ctd():
    db_parts_no_ctd = db.retrieve('SELECT part FROM Parts WHERE ctdtrig IS NULL')

    print 'Parts without CTD data:', len(db_parts_no_ctd)
    ctdtrigs = []
    for part, in db_parts_no_ctd:
        timecorr = _timecorr_path(part)
        print timecorr
        try:
            with open(timecorr, 'r') as tcfile:
                tc = tcfile.readlines()
                if len(tc):
                    jstart = utils.get_jstart(timecorr, tc[0])
                else:
                    jstart = None
                ctdtrigs.append((len(tc), jstart, part))
        except IOError:
            continue
        except:
            print 'Error in', timecorr
            continue
    db.update_rows('UPDATE Parts SET ctdtrig=?, jstart=? WHERE part=?', tuple(ctdtrigs))

def _process_eventcounts(eventcounts):
    with open(eventcounts, 'r') as ecfile:
        ec = ecfile.readlines()
    last_trigset = -256
    dsttrig = 0
    dstseconds = 0.0
    dstbytes = 0
    badcount = 0
    for line in ec:
        strigset, strigs, ssec, sbytes, sbad = line.split()
        trigset = int(strigset)

        assert trigset == last_trigset + 256
        last_trigset = trigset

        dsttrig += int(strigs)
        dstseconds += float(ssec)
        dstbytes += int(sbytes)
        badcount += int(sbad)

    return badcount, dsttrig, dstseconds, dstbytes

def update_parts_with_dst():
    with sqlite3.connect(db.db) as con:
        cur = con.cursor()
        cur.execute("ATTACH '{}' AS rdb".format(rawdb.db))
        cur.execute('SELECT p.part, f.ctdprefix FROM Parts AS p JOIN rdb.Filesets AS f ON p.part = f.part11 WHERE p.ctdtrig > 0 AND p.dsttrig IS NULL')
        db_parts_no_dst = cur.fetchall()
        cur.execute("DETACH rdb")

    print 'Parts without DST data:', len(db_parts_no_dst)
    dsts = []
    for part, ctdprefix in db_parts_no_dst:
        eventcounts = _eventcounts_path(part, os.path.basename(ctdprefix))
        print eventcounts
        try:
            badcount, dsttrig, dstseconds, bytes = _process_eventcounts(eventcounts)
            dsts.append((badcount, dsttrig, dstseconds, bytes, part))
        except IOError:
            continue
        except AssertionError:
            print 'Missing triget(s) in', eventcounts
            continue
        except ValueError:
            print 'ValueError in', eventcounts
            continue

    db.update_rows('UPDATE Parts SET badcount=?, dsttrig=?, dstseconds=?, bytes=? WHERE part=?', tuple(dsts))







