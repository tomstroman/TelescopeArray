# simulation.py
# Thomas Stroman, University of Utah 2016-12-17
# New code for stereo simulation, either fresh (not replacing previous
# code) or rewritten legacy code.
import os

def prep_directories_for_simulation(properties, model, source):
    """
    Lay the groundwork for a new simulation in the location goverend by
    the properties argument, retrieved from a database.
    """
    print 'Checking directory structure'
    # Location, location, location
    # Some files are physically in the rootpath, while others are physically
    # on a RAID-0 volume (striped across 4 disks) for performance. Directories are
    # symlinked.
    rootpath = properties['ROOTPATH']
    analysispath = os.path.join(rootpath, properties['ANALYSIS'])
    tafddata = os.path.join(analysispath, 'tafd-data')
    modelpath = os.path.join(analysispath, model)
    binpath = os.path.join(modelpath, 'bin')
    sourcepath = os.path.join(modelpath, source)

    # If root paths are missing, don't even try to run.
    for p in [rootpath, rootpath.replace('/scratch/', '/raidscratch/')]:
        assert os.path.isdir(p)

    # If analysis and model don't exist yet, create them.
    for p in [analysispath, modelpath]:
        for d in [p, p.replace('/scratch/', '/raidscratch/')]:
            if not os.path.isdir(d):
                print 'Creating directory:', d
                os.mkdir(d)

    # Data path needs a symlink to appear locally in this analysis
    if not os.path.isdir(tafddata):
        print 'Symlinking tafd-data directory'
        os.symlink(properties['DATAPATH'], tafddata)

    # Binaries need a symlink in RAID
    if not os.path.isdir(binpath):
        print 'Creating diretory:', binpath
        os.mkdir(binpath)
    rbinpath = binpath.replace('/scratch/', '/raidscratch/')
    if not os.path.isdir(rbinpath):
        print 'Symlinking bin directory'
        os.symlink(binpath, rbinpath)

    is_mc = source.startswith('mc')

    # Source goes in RAID for MC
    if not os.path.isdir(sourcepath):
        if not is_mc:
            print 'Creating directory:', sourcepath
            os.mkdir(sourcepath)
        else:
            raidpath = sourcepath.replace('/scratch/', '/raidscratch/')
            if not os.path.isdir(raidpath):
                print 'Creating and symlinking directory:', raidpath
                os.mkdir(raidpath)
                os.symlink(raidpath, sourcepath)

    if is_mc:
        logpath = os.path.join(sourcepath, 'logs')
        if not os.path.isdir(logpath):
            print 'Creating directory:', logpath
            os.mkdir(logpath)

        conf_template = os.path.join(sourcepath, 'yYYYYmMMdDD.fd.conf')
        if not os.path.exists(conf_template):
            _render_template(properties, model, source, conf_template)

def _render_template(properties, model, source, template):
    base_conf = os.path.join(properties['ROOTPATH'], 'trump-conf-template.txt')
    species = _get_species(source)
    showlib = _get_showlib(model, species)
    replacements = {
            '__ANALYSIS__': properties['ANALYSIS'],
            '__MODEL__': model,
            '__SOURCE__': source,
            '__GEOFILE_REPLACEABLE__': properties['GEOMETRY'],
            '__SPECIES__': str(species),
            '__SHOWLIB__': showlib,
            '__ELIMITS__': properties['ELIMITS'],
            '__SPECTRUM_NBREAK__': properties['SPECTRUM_NBREAK'],
            '__SPECTRUM_EBREAK__': properties['SPECTRUM_EBREAK'],
            '__SPECTRUM_SLOPES__': properties['SPECTRUM_SLOPES'],
            '__DTIME__': properties['DTIME']
            }
    with open(base_conf, 'r') as conf_file:
        conf = conf_file.read()

    for placeholder, replacement in replacements.items():
        assert conf.count(placeholder) == 1
        conf = conf.replace(placeholder, replacement)

    assert conf.count('__') == 0 # didn't miss any

    with open(template, 'w') as template_file:
        template_file.write(conf)

    assert os.path.exists(template)



def _get_species(source):
    assert source.startswith('mc')
    # CORSIKA particle number codes
    species_map = {'proton': 14, 'iron': 5626}
    if 'proton' in source:
        return species_map['proton']
    elif 'iron' in source:
        return species_map['iron']
    else:
        raise ValueError('Unrecognized species: {}'.format(source))

def _get_showlib(model, species):
    species_name = {14: 'prot', 5626: 'iron'}
    showlib_path = os.path.join(os.getenv('RTDATA'), 'showlib')
    showlib_file = 'tas-{}-{}.dst.gz'.format(model, species_name[species])
    showlib = os.path.join(showlib_path, showlib_file)
    assert os.path.exists(showlib)
    return showlib

def prep_support_files(binpath):
    """
    Verify that every file needed by stereo code exists.
    """
    recon = 'ghl70x60'
    files = [
            'trump.run', # TRUMP executable, compiled with DEDX_MODEL
            ''
        ]

    pass


