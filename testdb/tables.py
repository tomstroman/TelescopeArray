tables = [
    ('Sites', 'id INTEGER PRIMARY KEY, shortname TEXT, name TEXT, longname TEXT'),
    
    ('FileErrors', 'id INTEGER PRIMARY KEY, description TEXT'),

    ('Downloads', 'path TEXT PRIMARY KEY, site INTEGER REFERENCES Sites'),
    
    ('Rundates', 'date INTEGER PRIMARY KEY'),
    
    ('Runnights', 'rundate INTEGER REFERENCES Rundates, site INTEGER REFERENCES Sites, download TEXT REFERENCES Downloads, logfile TEXT, PRIMARY KEY (rundate, site)'),
    
    ('Parts', 'rundate INTEGER, part INTEGER, site INTEGER, daqtrig INTEGER, daqsigma REAL, daqcams INTEGER, FOREIGN KEY (rundate, site) REFERENCES Runnights(rundate, site), PRIMARY KEY (rundate, part, site)'), 
    
    ('Filesets', 'rundate INTEGER, part INTEGER, site INTEGER, ctdprefix TEXT PRIMARY KEY, FOREIGN KEY (rundate, part, site) REFERENCES Parts(rundate, part, site)'),
    
    ('Badfiles', 'fileset TEXT REFERENCES Filesets, source TEXT, trigset INTEGER, cause INTEGER REFERENCES FileErrors, PRIMARY KEY(fileset, source, trigset)'),
    
    ('Timecorrs', 'path TEXT PRIMARY KEY, rundate INTEGER, part INTEGER, site INTEGER, ctdtrig INTEGER, FOREIGN KEY (rundate, part, site) REFERENCES Parts(rundate, part, site)'),
    
    #('FadcFiles', 'path TEXT PRIMARY KEY, rundate INTEGER, part INTEGER, site INTEGER, is_good INTEGER, FOREIGN KEY (rundate, part, site) REFERENCES Parts(rundate, part, site)'),
    
    #('CTDFiles', 'path TEXT REFERENCES FadcFiles, trigset INTEGER, PRIMARY KEY (path, trigset)'),
    
    #('CamFiles', 'path TEXT REFERENCES FadcFiles, ctdfile TEXT, trigset INTEGER, camera INTEGER, FOREIGN KEY (ctdfile, trigset) REFERENCES CTDFiles(path, trigset), PRIMARY KEY (ctdfile, trigset, camera)'),
]

table_names = [table[0] for table in tables] 
