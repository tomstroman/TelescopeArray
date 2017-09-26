standard_template_name = 'yYYYYmMMdDD.fd.conf'

conf_meta_template = """
# TRUMP CONFIGURATION FILE
#
# FDMC uses a Corsika style steering card system.
#
# Like bash, characters after the '#' symbol in each line are ignored.
#
# This sample defines every parameter by its default, only the file name,  
#   parent directory, and site ID are required.
#
# Please make sure to end your configuration file with a newline character.
#
#        #                   #


# tstroman-salt-geocal  _META_REPLACE_GEOCAL_
# tstroman-salt-model   _META_REPLACE_MODEL_
# tstroman-salt-source  _META_REPLACE_SOURCE_


FILE     REPLACE_DSTFILE        # output file name
PARENT   .                   # parent directory of output file
SITEID   REPLACE_SITE                   # site to use 0=BR, 1=LR, 2=MD
GEOFILE  _META_REPLACE_GEOFILE_

STARTID  1                   # ID number of first trigger
NTRIALS  10000000            # Number of attempts before quitting
NEVENTS  10000000            # Number of events to collect before quitting
SEED     REPLACE_SEED               # initial random number seed

SPECIES  _META_REPLACE_SPECIES_                  # uses Corsika convention 14=p 5626=Fe
SHOWLIB  _META_REPLACE_SHOWLIB_  # path to shower library directory

ENERGY   _META_REPLACE_ENERGY_    # bounds for Energy in log(eV)
NBREAK   _META_REPLACE_NBREAK_    # number of break points in energy spectrum
EBREAK   _META_REPLACE_EBREAK_    # break point energy(ies) in log(eV)
ESLOPE   _META_REPLACE_ESLOPE_    # slope(s) in energy spectrum
LAT      1.0

RP       100.0 40000.0       # bounds for impact parameter Rp in m
PSI      20.0 160.0          # bounds for ang of shower in SD plane in degrees
PHIIMP   -180.0 180.0        # bounds for azm angle to shower track at ground
PHI      -180.0 180.0        # azm direction of shower development in degrees
THETA    0.00 80.0           # zenith angle of shower in degrees

SKYBG    9.00                # night-sky background noise level in 1/(100 ns)

ONTIME   REPLACE_ONTIME  # ontime file
DTIME    _META_REPLACE_DTIME_     # average time between thrown events (seconds)
"""

standard_replacements = {
    '_META_REPLACE_ENERGY_' : '17.7 21.5',
    '_META_REPLACE_NBREAK_' : '3',
    '_META_REPLACE_EBREAK_' : '17.52 18.65 19.75',
    '_META_REPLACE_ESLOPE_' : '2.99 3.25 2.81 5.1',
}