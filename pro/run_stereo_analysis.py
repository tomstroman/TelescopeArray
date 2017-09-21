# run_stereo_analysis.py
# Thomas Stroman, University of Utah, 2016-12-05
# Main supervisory executable for an entire stereo analysis.
# TODO: Documentation!
import logging
from db.database_wrapper import DatabaseWrapper
import os
from process_night import process_night
from step import steps
from prep_fadc.raw_to_dst import _command
from datetime import datetime
import subprocess

# hard-code these here, for now:
model = 'qgsjetii-03'
#source = 'mc-proton'
source = 'nature'
#source = 'mc-iron0'

event_interval = 5.0 # average seconds between events
# TODO: use database for these
temp_properties = {'DTIME': str(event_interval),
                   'GEOMETRY': os.path.join(os.getenv('RTDATA'), 'fdgeom', 'geoREPLACE_GEO_joint.dst.gz'),
                   'ELIMITS': '17.7 21.5',
                   'SPECTRUM_NBREAK': '3',
                   'SPECTRUM_EBREAK': '17.52 18.65 19.75',
                   'SPECTRUM_SLOPES': '2.99 3.25 2.81 5.1'
                   }

ignorable_night_reasons = ['no TRUMP conf found', 'analysis complete']

from stereo import simulation

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

def _modelsource(model, source):
    return ''.join([i for i in model+source if i.isalnum()])

def _setup_run_get_dates(analysis_db, modelsource):
    properties = {name: value for name, value in analysis_db.retrieve("SELECT name, value FROM Properties")}
    print "Analysis properties retrieved from database:"
    print properties

    ignore_nights = {d: 'ignored: '+r for d,r in analysis_db.retrieve("SELECT date, reason FROM StereoIgnoreNights WHERE modelsource='{}'".format(modelsource))}

    # TEMPORARY - DEBUGGING:
    print '\nNights that would normally be ignored:', len(ignore_nights)
    ignore_nights = {} 
    # TEMPORARY PART FINISHED!


    rootpath = properties['ROOTPATH']
    dates_file = os.path.join(rootpath, 'list-of-dates')

    dates_file += '-all-lr-20170301.txt'

    print 'Reading list of stereo nights (YYYYMMDD) from master list:', dates_file
    try:
        with open(dates_file, 'r') as stream:
            dates = [int(d) for d in stream.readlines()]
        print 'Attempting to perform analysis on {} nights.'.format(len(dates))
    except IOError:
        print 'Error: could not read', dates_file
        return None, None

    dates = sorted(list(set(dates) - set(ignore_nights.keys())))

    print 'Unique nights not ignored:', len(dates)

    properties.update(temp_properties)
    simulation.prep_directories_for_simulation(properties, model, source)
    # this part is going to be a bit of a kludge for now --
    # eventually generate the needed paths and templates, but
    # today we just fail loudly if they haven't been created

    modelpath = os.path.join(rootpath, properties['ANALYSIS'], model)

    analysispath = os.path.join(modelpath, source)
    print 'checking for', analysispath
    assert os.path.isdir(analysispath)

    binpath = os.path.join(modelpath, 'bin')
    assert os.path.isdir(binpath)



    date_status = {date: 'unstarted' for date in dates}
    date_status.update(ignore_nights)

    is_mc = source.startswith('mc')
    trump_template = None
    if is_mc:
        trump_template = os.path.join(analysispath, 'yYYYYmMMdDD.fd.conf')
        assert os.path.exists(trump_template)
        assert os.path.exists(os.path.join(analysispath, 'logs'))

    mosq = _get_mosix_jobs()


    params = {'model': model, 'source': source, 'is_mc': trump_template, 'path': analysispath, 'mosq': mosq}

    return date_status, params


def run(dbfile='db/tafd_analysis.db'):
    # Initialization
    modelsource = _modelsource(model, source)    
    print """
    **** run_stereo_analysis ****
    **** model: {0}
    **** source: {1}
    **** DB: {2}
    """.format(model, source, dbfile)

    logging.warn("In run_stereo_analysis - and exiting!")
    return

    analysis_db = DatabaseWrapper(dbfile)

    date_status, params = _setup_run_get_dates(analysis_db, modelsource)
    mosq_age = datetime.utcnow()

    #dates = dates[-3:]
    #dates = dates[:3]
    #dates = [20160206, 20160207]
    #dates = [20151104]
    #dates = [20161109]
    #dates = []
    dates = sorted([d for d in date_status.keys() if str(d).startswith('20160')])

    for date in dates:
        now = datetime.utcnow()
        if (now - mosq_age).total_seconds() > mosq_poll_interval:
            print 'Updating mosq list'
            mosq = _get_mosix_jobs()
            mosq_age = now
            params['mosq'] = mosq

        try:
            #date_status[date] = process_night(date, params, start_code='prep_trump_sim')
            date_status[date] = process_night(date, params, end_code='run_tama')
        except Exception as e:
            date_status[date] = 'exception'
            print e
            #raise

        if date_status[date] in ignorable_night_reasons:
            print 'This date will be ignored in future runs.'
            analysis_db.insert_row('INSERT INTO StereoIgnoreNights VALUES(?, ?, ?)', (date, date_status[date], modelsource))

    return date_status, params

def report(date_status):
    print 'Result of analysis on {} nights:'.format(len(date_status))
    status_dates = {}
    for date, status in date_status.items():
        try:
            status_dates[status].append(date)
        except KeyError:
            status_dates[status] = [date]
    for status, dates in status_dates.items():
        print "Status '{}': {} night(s)".format(status, len(dates))

    print 'Returning "status_dates" dict for more details.'
    return status_dates

def erase_mosout(nights, params):
    """
    Given a list of nights -- e.g., all with a particular status --
    remove Mosix signature of those nights from the analysis.
    """
    if isinstance(nights, int):
       nights = [nights]
    path = params['path']
    for night in nights:
        mosout = os.path.join(path, 'logs', 'trump-{}.mosout'.format(night))
        print 'Removing', mosout
        os.remove(mosout)

stereo_dirs = ['bl', 'bm', 'lm', 'blm']
def erase_stereo(nights, params):
    """
    Given a list of nights -- e.g., all with a particular status --
    remove stereo processing of those nights from the analysis.
    """
    from glob import glob
    import shutil
    if isinstance(nights, int):
       nights = [nights]
    path = params['path']

    for night in nights:
        night_dir = os.path.join(path, str(night))
        dirs = glob(os.path.join(night_dir, '[abl]*'))
        for d in dirs:
            base = os.path.basename(d)
            if base in stereo_dirs or base.startswith('ascii'):
                print 'removing', d
                shutil.rmtree(d)
        downlists =  glob(os.path.join(night_dir, 'trump', '*', 'downlist-{}-*.txt'.format(night)))
        for d in downlists:
            print 'removing', d
            os.remove(d)
        #print night, dirs

if __name__ == '__main__':
    date_status, params = run()
    status_dates = report(date_status)




