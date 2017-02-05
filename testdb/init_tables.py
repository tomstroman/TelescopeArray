#!/usr/local/bin/python
import sqlite3

import static_data

from tables import tables, table_names

def init():
    with sqlite3.connect('test.db') as con:
        cur = con.cursor()

        sql = 'SELECT name FROM sqlite_master WHERE type="table"'
        cur.execute(sql)
        rows = cur.fetchall()
        dbtables = [table[0] for table in rows]


        for table, details in tables:
            if table in dbtables:
                print 'Table {0} exists. Deleting...'.format(table)
                cur.execute('DROP TABLE {0}'.format(table))
            
            print 'Creating table {0}'.format(table)
            sql = 'CREATE TABLE {0}({1});'.format(table, details)
            cur.execute(sql)
            
        
        sql = 'INSERT INTO Sites VALUES(?, ?, ?, ?)'
        cur.executemany(sql, static_data.sites)
        
        sql = 'INSERT INTO FileErrors VALUES(?, ?)'
        cur.executemany(sql, static_data.file_errors)

if __name__ == '__main__':
    init()
