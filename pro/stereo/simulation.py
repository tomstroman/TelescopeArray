# simulation.py
# Thomas Stroman, University of Utah 2016-12-17
# New code for stereo simulation, either fresh (not replacing previous
# code) or rewritten legacy code.

def prep_directories_for_simulation(properties, model, source):
    """
    Lay the groundwork for a new simulation in the location goverend by
    the properties argument, retrieved from a database.
    """

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
                os.mkdir(d)

    # Data path needs a symlink to appear locally in this analysis
    if not os.path.isdir(tafddata):
        os.symlink(properties['DATAPATH'], tafddata)

    # Binaries need a symlink in RAID
    if not os.path.isdir(binpath):
        os.mkdir(binpath)
    rbinpath = binpath.replace('/scratch/', '/raidscratch/')
    if not os.path.isdir(rbinpath):
        os.symlink(binpath, rbinpath)

    # Source goes in RAID for MC
    if not os.path.isdir(sourcedir):
        if not source.startswith('mc'):
                os.mkdir(sourcepath)
        else:
            raidpath = sourcepath.replace('/scratch/', '/raidscratch/')
            if not os.path.isdir(raidpath):
                os.mkdir(raidpath)
                os.symlink(raidpath, sourcepath)

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


