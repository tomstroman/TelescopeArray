# db.py
# Thomas Stroman, University of Utah, 2016-11-30
# Class definition for wrapping an sqlite3 connection with some useful commands.

import sqlite3

class DatabaseWrapper(object):

    def __init__(self, db):
        self.db = db

    def report(self):
        """
        Print a list of tables in the database, with the number of rows in each.
        """
        import json
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()

            cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
            dbtables = [table[0] for table in cur.fetchall()]

            counts = {}
            for table in dbtables:
                cur.execute('SELECT count() FROM {0}'.format(table))
                counts[table] = cur.fetchall()[0][0]

        print json.dumps(counts, sort_keys=True, indent=2)


    def retrieve(self, sql):
        """
        Execute arbitrary SQL on the specified database, provided the SQL begins
        with 'SELECT ', then return the selected rows.
        """
        assert sql.upper().startswith('SELECT ')

        with sqlite3.connect(self.db) as con:
            cur = con.cursor()

            cur.execute(sql)
            rows = cur.fetchall()
        return rows

    def insert_row(self, sql, values):
        """
        Execute arbitrary SQL on the specified database, provided the SQL begins
        with 'INSERT INTO '. A tuple is expected for values.
        """
        assert isinstance(values, tuple)
        assert sql.count('?') == len(values)
        assert sql.upper().startswith('INSERT INTO ')
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = 1')
            cur.execute(sql, values)

    def insert_rows(self, sql, all_values):
        """
        Execute arbitrary SQL on the specified database, provided the SQL begins
        with 'INSERT INTO '. A tuple of tuples is expected for all_values.
        """
        assert isinstance(all_values, tuple)
        assert sql.upper().startswith('INSERT INTO ')
        num_v = sql.count('?')
        assert all(isinstance(values, tuple) and len(values) == num_v for values in all_values)
        with sqlite3.connect(self.db) as con:
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys = 1')
            cur.executemany(sql, all_values)
    
    def __repr__(self):
        return 'DatabaseWrapper for {}'.format(self.db)

