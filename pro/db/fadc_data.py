# fadc_data.py
# Thomas Stroman, University of Utah, 2016-11-28
# Storage of information for Telescope Array FADC data processing


import sqlite3

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
        

