# run_stereo_analysis.py
# Thomas Stroman, University of Utah, 2016-12-05
# Main supervisory executable for an entire stereo analysis.
# TODO: Documentation!

from db.database_wrapper import DatabaseWrapper
import os

def run(dbfile='db/tafd_analysis.db'):
    analysis_db = DatabaseWrapper(dbfile)

    properties = {name: value for name, value in analysis_db.retrieve("SELECT name, value FROM Properties")}
    print properties
    
    rootpath = properties['ROOTPATH']
    dates_file = os.path.join(rootpath, 'list-of-dates')
    try:
        with open(dates_file, 'r') as stream:
            dates = [int(d) for d in stream.readlines()]
        print 'Attempting to perform analysis on {} nights.'.format(len(dates))
    except IOError:
        print 'Error: could not read', dates_file
        return None






