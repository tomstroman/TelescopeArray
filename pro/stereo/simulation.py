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
    rootpath = properties['ROOTPATH']
    analysispath = os.path.join(rootpath, properties['ANALYSIS'])
    tafddata = os.path.join(analysispath, 'tafd-data')
    modelpath = os.path.join(analysispath, model)
    binpath = os.path.join(modelpath, 'bin')
    sourcepath = os.path.join(modelpath, source)

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
