# tafd_analysis.py
# Thomas Stroman, University of Utah, 2016-11-27
# Define metadata for Telescope Array analysis and store in sqlite3 database.


import sqlite3
import json

from fadc_data import retrieve
default_dbfile='tafd_analysis.db'

from database_wrapper import DatabaseWrapper

db = DatabaseWrapper(default_dbfile)

default_properties=(('ROOTPATH', '/scratch/tstroman/stereo/'),                    
                    ('ANALYSIS', 'gdas_j14t'),
                    ('DESCRIPTION', 'GDAS atmosphere, "joint" geometry, calibration 1.4, correct molecular atmosphere lookup'),
                    ('DATAPATH', '/scratch/tstroman/stereo/joint_cal1.4/tafd-data/'),
                    )


def report(db=db):
    """
    Print a list of the information in the Properties table.
    """
    properties = {name: value for name, value in db.retrieve('SELECT name, value FROM Properties')}

    print json.dumps(properties, sort_keys=True, indent=2)


def init(dbfile=db.db, properties=default_properties):
    with sqlite3.connect(dbfile) as con:
        cur = con.cursor()
        cur.execute('DROP TABLE IF EXISTS Properties')
        cur.execute('CREATE TABLE Properties(name TEXT PRIMARY KEY, value TEXT)') 
    
        cur.executemany('INSERT INTO Properties VALUES(?, ?)', properties)
    
    
if __name__ == '__main__':
    report()
