# run_stereo_analysis.py
# Thomas Stroman, University of Utah, 2016-12-05
# Main supervisory executable for an entire stereo analysis.
# TODO: Documentation!

from db.database_wrapper import DatabaseWrapper
import os
from process_night import process_night
from step import steps


# hard-code these here, for now:
model = 'qgsjetii-03'
source = 'nature'


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

    # this part is going to be a bit of a kludge for now --
    # eventually generate the needed paths and templates, but
    # today we just fail loudly if they haven't been created
    
    modelpath = os.path.join(rootpath, properties['ANALYSIS'], model)
            
    analysispath = os.path.join(modelpath, source)
    print 'checking for', analysispath
    assert os.path.isdir(analysispath)

    binpath = os.path.join(modelpath, 'bin')
    assert os.path.isdir(binpath)
    
    is_mc = source.startswith('mc')
    if is_mc:
        trump_template = os.path.join(analysispath, 'yYYYYmMMdDD.fd.conf')
        assert os.path.exists(trump_template)

        
    dates=dates[-3:]
    date_status = {date: 'unstarted' for date in dates}
    
    params = {'model': model, 'source': source, 'is_mc': is_mc, 'path': analysispath}

    for date in dates:
        try:
            date_status[date] = process_night(date, params, start_code='prep_trump_sim')
        except Exception:
            date_status[date] = 'exception'

    return date_status

    

def report(date_status):
    print 'Result of analysis on {} nights:'.format(len(date_status))
    aggregate = {}
    for status in date_status.values():
        try:
            aggregate[status] += 1
        except KeyError:
            aggregate[status] = 1
    for status, count in aggregate.items():
        print "Status '{}': {} night(s)".format(status, count)

if __name__ == '__main__':
    date_status = run()
    report(date_status)




