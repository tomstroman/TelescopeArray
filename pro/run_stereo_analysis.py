# run_stereo_analysis.py
# Thomas Stroman, University of Utah, 2016-12-05
# Main supervisory executable for an entire stereo analysis.
# TODO: Documentation!
import logging
import os
import shutil
import subprocess

from datetime import datetime
from glob import glob

from db.database_wrapper import DatabaseWrapper
from db import tafd_analysis
from prep_fadc.raw_to_dst import _command
from process_night import process_night
from step import steps
from stereo import simulation

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

def _setup_run_get_dates(stereo_run, analysis_db, modelsource, model, source, disregard_ignore=False):
    properties = {name: value for name, value in analysis_db.retrieve("SELECT name, value FROM Properties")}
    print "Analysis properties retrieved from database:"
    print properties

    ignore_nights = {d: 'ignored: '+r for d,r in analysis_db.retrieve("SELECT date, reason FROM StereoIgnoreNights WHERE modelsource='{}'".format(modelsource))}

    if disregard_ignore:
        logging.warn('Nights that would normally be ignored: %s', len(ignore_nights))
        ignore_nights = {} 

    dates = sorted(list(set(stereo_run.dates) - set(ignore_nights.keys())))

    logging.info('Unique nights not ignored: %s', len(dates))

    date_status = {date: 'unstarted' for date in dates}
    date_status.update(ignore_nights)

    properties.update(temp_properties)
    simulation.prep_directories_for_simulation(properties, model, source)

    trump_template = None
    if stereo_run.params.is_mc:
        trump_template = stereo_run.trump_template
        assert os.path.exists(trump_template)
        assert os.path.exists(stereo_run.log_path)

    mosq = _get_mosix_jobs()


    params = {'model': model, 'source': source, 'is_mc': trump_template, 'path': stereo_run.run_path, 'mosq': mosq}

    return date_status, params


def run(stereo_run, dbfile='db/tafd_analysis.db'):
    # Initialization
    model = stereo_run.params.model
    source = stereo_run.specific_run
    modelsource = _modelsource(model, source)    
    dbfile = os.path.join(stereo_run.base_path, 'tafd_analysis.db')
    if not os.path.exists(dbfile):
        data_path = os.path.join(stereo_run.rootpath, stereo_run.params.fdplane_config, 'tafd-data')
        base_properties = (
            ('ROOTPATH', stereo_run.rootpath),
            ('ANALYSIS', stereo_run.name),
            ('DESCRIPTION', 'GDAS atmosphere, "joint" geometry, calibration 1.4, correct molecular atmosphere lookup'),
            ('DATAPATH', data_path),
        )

        tafd_analysis.init(
            dbfile=dbfile,
            properties=base_properties,
        )

    print """
    **** run_stereo_analysis ****
    **** model: {0}
    **** source: {1}
    **** DB: {2}
    """.format(model, source, dbfile)


    analysis_db = DatabaseWrapper(dbfile)

    date_status, params = _setup_run_get_dates(stereo_run, analysis_db, modelsource, model, source)
    mosq_age = datetime.utcnow()


    dates = sorted([d for d in date_status.keys()])

    for date in dates:
        now = datetime.utcnow()
        if (now - mosq_age).total_seconds() > mosq_poll_interval:
            print 'Updating mosq list'
            mosq = _get_mosix_jobs()
            mosq_age = now
            params['mosq'] = mosq

        try:
            #date_status[date] = process_night(date, params, start_code='prep_trump_sim')
            #date_status[date] = process_night(date, params, end_code='run_tama')
            logging.warn('Not actually processing date %s', date)
            continue # TODO: remove
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
