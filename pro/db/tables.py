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

fadc_process_tables = [
        ('Parts', 'part INTEGER PRIMARY KEY, daqcams INTEGER NOT NULL, daqtrig INTEGER NOT NULL, ctdtrig INTEGER DEFAULT NULL, badcount INTEGER DEFAULT NULL, dsttrig INTEGER DEFAULT NULL, dstseconds REAL DEFAULT NULL, bytes INTEGER DEFAULT NULL, jstart REAL DEFAULT NULL, pedminutes INTEGER DEFAULT NULL, downcount INTEGER DEFAULT NULL, badcalcount INTEGER DEFAULT NULL'),
        ]




