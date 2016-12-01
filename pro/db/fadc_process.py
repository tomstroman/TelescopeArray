# fadc_process.py
# Thomas Stroman, University of Utah, 2016-11-30
# Storage of information for Telescope Array FADC data processing.

import sqlite3
import os
from database_wrapper import DatabaseWrapper

from fadc_data import default_dbfile as rawdata_dbfile
rawdb = DatabaseWrapper(rawdata_dbfile)

default_dbfile = 'fadc_process.db'
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





    
