# run_stereo_analysis.py
# Thomas Stroman, University of Utah, 2016-12-05
# Main supervisory executable for an entire stereo analysis.
# TODO: Documentation!

from db.database_wrapper import DatabaseWrapper
import os
from process_night import process_night
from step import steps
from prep_fadc.raw_to_dst import _command
from datetime import datetime
import subprocess

# hard-code these here, for now:
model = 'qgsjetii-03'
source = 'mc-proton0'

mosq_poll_interval = 15 # seconds
def _get_mosix_jobs():
    """
    Obtain a list of queued/running mosix jobs and return a dict with
    job IDs as keys, and lists of (process name, status) as values.
    """
    mosq = subprocess.check_output('mosq -j listall'.split())
    jobs = {}
    for line in mosq.strip().split('\n')[1:]:
        l = line.split()
        pid, pri, jobid = [l[i] for i in [0, 4, 5]]
        jobid = int(jobid)
        try:
            jobs[jobid].append((pid, pri))
        except KeyError:
            jobs[jobid] = [(pid, pri)]

    return jobs

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
    trump_template = None
    if is_mc:
        trump_template = os.path.join(analysispath, 'yYYYYmMMdDD.fd.conf')
        assert os.path.exists(trump_template)
        assert os.path.exists(os.path.join(analysispath, 'logs'))

    #dates = dates[-3:]
    #dates = dates[:30]
    date_status = {date: 'unstarted' for date in dates}
    
    mosq = _get_mosix_jobs()
    mosq_age = datetime.utcnow()

    params = {'model': model, 'source': source, 'is_mc': trump_template, 'path': analysispath, 'mosq': mosq}

    for date in dates:
        now = datetime.utcnow()
        if (now - mosq_age).total_seconds() > mosq_poll_interval:
            print 'Updating mosq list'
            mosq = _get_mosix_jobs()
            mosq_age = now
            params['mosq'] = mosq

        try:
            date_status[date] = process_night(date, params, start_code='prep_trump_sim')
        except Exception:
            date_status[date] = 'exception'

    return date_status

def report(date_status):
    print 'Result of analysis on {} nights:'.format(len(date_status))
    aggregate = {}
    exceptions = []
    for date, status in date_status.items():
        if status == 'exception':
            exceptions.append(date)
        try:
            aggregate[status] += 1
        except KeyError:
            aggregate[status] = 1
    for status, count in aggregate.items():
        print "Status '{}': {} night(s)".format(status, count)
    if exceptions:
        print 'List of dates generating exceptions:'
        print exceptions

if __name__ == '__main__':
    date_status = run()
    report(date_status)




