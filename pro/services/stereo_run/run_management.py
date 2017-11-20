import logging
import os

def find_or_create_base_run(stereo_run, supplied_name):
    """
    Find any StereoRun(s) matching the simulation *parameters* (FDPlaneConfig and Model),
    and check against the supplied name, otherwise attempt to create one.
    """
    db = stereo_run.db
    params = stereo_run.params

    sql = 'SELECT name, path FROM StereoRuns WHERE fdplaneconfig=\"{0}\" AND model=\"{1}\"'.format(
            params.fdplane_config,
            params.model,
    )
    logging.debug('sql: %s', sql)

    matching_runs = db.retrieve(sql)

    name_match_paths = []
    for name, path in matching_runs:
        logging.info('found base StereoRun %s at path %s', name, path)
        if name == supplied_name:
            name_match_paths.append(path)

    if len(name_match_paths) == 1:
        logging.info('One name-match found; using %s', name_match_paths[0])
        return name_match_paths[0]

    if not supplied_name:
        if len(matching_runs) == 1:
            name, path = matching_runs[0]
            logging.warn('No name supplied but one matching StereoRun: path=%s', path)
            return path
        logging.error('%s matching StereoRuns %s no name supplied.',
            len(matching_runs),
            'and' if not len(matching_runs) else 'but'
        )
        raise Exception('No StereoRun')

    path = os.path.join(supplied_name, params.model)
    logging.info('No name-matching StereoRuns found. Attempting to create StereoRun with name=%s, path=%s',
        supplied_name,
        path
    )
    try:
        db.insert_row('INSERT INTO StereoRuns VALUES(?, ?, ?, ?)',
            (supplied_name, path, params.fdplane_config, params.model)
        )
        return path
    except Exception as err:
        logging.error('Failed to create StereoRun. Error: %s', err)

def find_or_create_specific_run(stereo_run):
    base_run = stereo_run.base_run
    db = stereo_run.db
    params = stereo_run.params

    run_name = params.name
    is_mc = params.is_mc
    if is_mc:
        sql = 'SELECT name, species FROM MCStereoRuns WHERE stereorun_path=\"{0}\"'.format(base_run)
    else:
        sql = 'SELECT name FROM DataStereoRuns WHERE stereorun_path=\"{0}\"'.format(base_run)
    logging.debug('sql: %s', sql)

    matching_runs = db.retrieve(sql)
    for row in matching_runs:
        if row[0] == run_name:
            logging.info('Found a matching specific run for %s', run_name)
            return run_name

    logging.info('No matching specific runs found. Attempting to create %s with is_mc=%s', run_name, is_mc)
    try:
        if is_mc:
            db.insert_row('INSERT INTO MCStereoRuns VALUES(?, ?, ?)', (run_name, base_run, params.species))
        else:
            db.insert_row('INSERT INTO DataStereoRuns VALUES(?, ?)', (run_name, base_run))
        return run_name
    except Exception as err:
        logging.error('Failed to create specific run. Error: %s', err)
