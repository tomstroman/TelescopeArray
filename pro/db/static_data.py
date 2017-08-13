# static_data.py
# Thomas Stroman, University of Utah, 2016-11-28
# Constants and other static data as needed for Telescope Array analysis

table_data = {}

# ('Sites', 'id INTEGER PRIMARY KEY, shortname TEXT, name TEXT, longname TEXT'),
sites = (
    (0, 'br', 'black-rock', 'Black Rock Mesa'),
    (1, 'lr', 'long-ridge', 'Long Ridge'),
    (2, 'md', 'middle-drum', 'Middle Drum'),
)
table_data['Sites'] = sites

# ('GeometrySets', 'name TEXT PRIMARY KEY, description TEXT')
geometry_sets = (
    ('joint', 'Thomas-Tokuno joint geometry (BR-LR), Thomas geometry (MD)'),
)
table_data['GeometrySets'] = geometry_sets

# ('SiteGeometry', 'dstfile TEXT PRIMARY KEY, site INTEGER REFERENCES Sites, geometryset TEXT REFERENCES GeometrySets, dstUniqID INTEGER DEFAULT NULL')
site_geometry = (
    ('geobr_joint.dst.gz', 0, 'joint', 1391197084),
    ('geolr_joint.dst.gz', 1, 'joint', 1391197084),
    ('geomd_20131002.dst.gz', 2, 'joint', 1388788818),
)
table_data['SiteGeometry'] = site_geometry

# ('Calibrations', 'version TEXT PRIMARY KEY')
calibrations = (
    ('1.4',),
)
table_data['Calibrations'] = calibrations

# ('FDPlaneConfigs', 'name TEXT PRIMARY KEY, path TEXT, calibration TEXT REFERENCES Calibrations, geometryset TEXT REFERENCES GeometrySets')
fdplane_configs = (
    ('joint_cal1.4', '/scratch/tstroman/stereo/joint_cal1.4/tafd-data', '1.4', 'joint'),
)
table_data['FDPlaneConfigs'] = fdplane_configs

# ('Models', 'name TEXT PRIMARY KEY, propername TEXT, dedx_model INTEGER')
models = (
    ('qgsjet01c', 'QGSJET-01c', 14),
    ('qgsjetii-03', 'QGSJET-II-03', 13),
    ('qgsjetii-04', 'QGSJET-II-04', 15),
    ('sibyll', 'SIBYLL 2.1', 16),
    ('epos-lhc', 'EPOS LHC', 12),
)
table_data['Models'] = models

# ('Species', 'corsika_id INTEGER PRIMARY KEY, name TEXT')
species = (
    (14, 'proton'),
    (5626, 'iron'),
    (402, 'helium'),
    (1407, 'nitrogen'),
)
table_data['Species'] = species

# ('Showlibs', 'model TEXT REFERENCES Models, species INTEGER REFERENCES Species, dstfile TEXT PRIMARY KEY')
showlibs = (
    ('qgsjet01c', 14, 'tas-qgsjet01c-prot.dst.gz'),
    ('qgsjet01c', 5626, 'tas-qgsjet01c-iron.dst.gz'),
    ('qgsjetii-03', 14, 'tas-qgsjetii-03-prot.dst.gz'),
    ('qgsjetii-03', 5626, 'tas-qgsjetii-03-iron.dst.gz'),
    ('qgsjetii-04', 14, 'tas-qgsjetii-04-prot.dst.gz'),
    ('qgsjetii-04', 5626, 'tas-qgsjetii-04-iron.dst.gz'),
    ('sibyll', 14, 'tas-sibyll-prot.dst.gz'),
    ('sibyll', 5626, 'tas-sibyll-iron.dst.gz'),
    ('epos-lhc', 14, 'tas-epos-lhc-prot.dst.gz'),
    ('epos-lhc', 5626, 'tas-epos-lhc-iron.dst.gz'),
)
table_data['Showlibs'] = showlibs

