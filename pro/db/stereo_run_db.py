# stereo_run_db.py
# Thomas Stroman, University of Utah, 2017-08-12
# Manage stereo simulation and analysis metadata for Telescope Array.

from db.static_data import table_data
from db.tables import stereo_run_tables

import logging
import json
import os
import sqlite3


def initialize(dbfile):
    if os.path.exists(dbfile):
        logging.warn('DELETING and re-initializing stereo run database at %s', dbfile)
    else:
        logging.info('CREATING and initializing stereo run database at %s', dbfile)

    with sqlite3.connect(dbfile) as con:
        cur = con.cursor()

        for table_name, schema in stereo_run_tables:
            cur.execute('DROP TABLE IF EXISTS {0}'.format(table_name))
            cur.execute('CREATE TABLE {0}({1})'.format(table_name, schema))

            data = table_data.get(table_name)
            if data:
                logging.debug("Data for %s: %s", table_name, data)
                num = len(data[0])
                sql = 'INSERT INTO {0} VALUES({1})'.format(table_name, ', '.join(['?']*num))
                logging.debug("Num %s, sql %s", num, sql)
                cur.executemany(sql, data)


