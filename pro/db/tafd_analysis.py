# tafd_analysis.py
# Thomas Stroman, University of Utah, 2016-11-27
# Define metadata for Telescope Array analysis and store in sqlite3 database.


import sqlite3
import json

default_dbfile='tafd_analysis.db'

default_properties=(('ROOTPATH', '/scratch/tstroman/stereo/'),                    
                    ('ANALYSIS', 'gdas_j14t'),
                    ('DESCRIPTION', 'GDAS atmosphere, "joint" geometry, calibration 1.4, correct molecular atmosphere lookup'),
                    ('DATAPATH', '/scratch/tstroman/stereo/joint_cal1.4/tafd-data/'),
                    )


def report(db=default_dbfile):
    """
    Print a list of the information in the Properties table.
    """
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        cur.execute('SELECT name, value FROM Properties')
        properties = {name: value for name, value in cur.fetchall()}

    print json.dumps(properties, sort_keys=True, indent=2)


def init(db=default_dbfile, properties=default_properties):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute('DROP TABLE IF EXISTS Properties')
        cur.execute('CREATE TABLE Properties(name TEXT PRIMARY KEY, value TEXT)') 
    
        cur.executemany('INSERT INTO Properties VALUES(?, ?)', properties)
    
    
if __name__ == '__main__':
    report()