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


stereo_run_tables = [
    ('Sites', 'id INTEGER PRIMARY KEY, shortname TEXT, name TEXT, longname TEXT'),

    ('Models', 'name TEXT PRIMARY KEY, propername TEXT, dedx_model INTEGER'),

    ('Species', 'corsika_id INTEGER PRIMARY KEY, name TEXT'),

    ('GeometrySets', 'name TEXT PRIMARY KEY, description TEXT'),

    ('SiteGeometry', 'dstfile TEXT PRIMARY KEY, site INTEGER REFERENCES Sites, geometryset TEXT REFERENCES GeometrySets, dstUniqID INTEGER DEFAULT NULL'),

    ('Calibrations', 'version TEXT PRIMARY KEY'),

    ('FDPlaneConfigs', 'name TEXT PRIMARY KEY, path TEXT, calibration TEXT REFERENCES Calibrations, geometryset TEXT REFERENCES GeometrySets'),

    ('StereoRuns', 'name TEXT, path TEXT PRIMARY KEY, fdplaneconfig TEXT REFERENCES FDPlaneConfigs, model TEXT REFERENCES Models'),

    ('MCStereoRuns', 'name TEXT, stereorun_path TEXT REFERENCES StereoRuns, species INTEGER REFERENCES Species, PRIMARY KEY (stereorun_path, name)'),

    ('DataStereoRuns', 'name TEXT DEFAULT "nature", stereorun_path TEXT REFERENCES StereoRuns, PRIMARY KEY (stereorun_path, name)'),

    ('Showlibs', 'model TEXT REFERENCES Models, species INTEGER REFERENCES Species, dstfile TEXT PRIMARY KEY'),
]

fd_daq_tables = [
    ('Dates', 'date INTEGER PRIMARY KEY, darkhours REAL DEFAULT 0'),

    ('Sites', 'id INTEGER PRIMARY KEY, shortname TEXT, name TEXT, longname TEXT'),

    ('NightStatus', 'date INTEGER REFERENCES Dates, site INTEGER REFERENCES Sites, wikilog TEXT PRIMARY KEY, status INTEGER NOT NULL'),

    ('PartStatus', 'part11 PRIMARY KEY, date INTEGER REFERENCES Dates, part INTEGER, site INTEGER REFERENCES Sites, status INTEGER NOT NULL'),
]
