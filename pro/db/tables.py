# tables.py
# Thomas Stroman, University of Utah, 2016-11-28
# Definitions for database tables

fadc_tables = [
        ('Sites', 'id INTEGER PRIMARY KEY, shortname TEXT, name TEXT, longname TEXT'),
        
        ('Downloads', 'path TEXT PRIMARY KEY, site INTEGER REFERENCES Sites'),

        ('Runnights', 'date INTEGER, site INTEGER REFERENCES Sites, download TEXT REFERENCES Downloads, logfile TEXT, PRIMARY KEY (date, site)'),

        ('Parts', 'part11 INTEGER PRIMARY KEY, date INTEGER, part INTEGER, site INTEGER REFERENCES Sites, daqtrig INTEGER, daqcams INTEGER, daqsigma REAL, FOREIGN KEY (date, site) REFERENCES Runnights(date, site)'),

        ('Filesets', 'part11 INTEGER REFERENCES Parts, ctdprefix TEXT PRIMARY KEY'),
        ]






