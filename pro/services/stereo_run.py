from db import stereo_run_db
from db.database_wrapper import DatabaseWrapper
from services.stereo_run_params import StereoRunParams
import logging
import os
import subprocess as sp

MASTER_DB_NAME = 'stereo_runs.db'

class StereoRun(object):
    def __init__(self, name=None):
        logging.debug("setting up StereoRun")
        self.rootpath = os.getenv('TAFD_STEREO_ROOT')
        if not self.rootpath:
            logging.error("TAFD_STEREO_ROOT variable not set.")
            raise Exception("TAFD_STEREO_ROOT variable not set.")

        db_path = os.path.join(self.rootpath, MASTER_DB_NAME)
        if not os.path.exists(db_path):
            stereo_run_db.initialize(db_path)

#            logging.error("No database exists at %s", db_path)
# TODO: prompt user to create
#            raise Exception("Database not found")

        self.db = DatabaseWrapper(db_path)
        self.params = StereoRunParams(self.db)
        logging.info("Parameters object: %s", self.params)
        self.name = name

    def prepare_stereo_run(self):
        logging.warn("method not yet implemented")
        self.base_run = self._find_or_create_base_run(self.name)

        self._validate_directory_structure()
        logging.info("TODO: prepare paths")
        logging.info("TODO: compile executables")
        logging.info("TODO: prepare templates from meta-templates")
        logging.info("TODO: generate plan for run, report to user")

    def stereo_run(self):
        logging.warn("method not yet implemented")

    def _find_or_create_base_run(self, supplied_name=None):
        """
        Find any StereoRun(s) matching the simulation *parameters* (FDPlaneConfig and Model),
        and check against the supplied name, otherwise attempt to create one.
        """
        sql = 'SELECT name, path FROM StereoRuns WHERE fdplaneconfig=\"{0}\" AND model=\"{1}\"'.format(
                self.params.fdplane_config,
                self.params.model,
        )
        logging.debug('sql: %s', sql)

        matching_runs = self.db.retrieve(sql)

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

        path = os.path.join(supplied_name, self.params.model)
        logging.info('No name-matching StereoRuns found. Attempting to create StereoRun with name=%s, path=%s',
            supplied_name,
            path
        )
        try:
            self.db.insert_row('INSERT INTO StereoRuns VALUES(?, ?, ?, ?)',
                (supplied_name, path, self.params.fdplane_config, self.params.model)
            )
            self._create_directory_structure(path)
            return path
        except Exception as err:
            logging.error('Failed to create StereoRun. Error: %s', err)

    def _validate_directory_structure(self):
        self.full_path = os.path.join(self.rootpath, self.base_run)
        logging.debug('Full path to base StereoRun: %s', self.full_path)
        assert os.path.isdir(self.full_path)
        self.bin_path = os.path.join(self.full_path, 'bin')
        assert os.path.isdir(self.bin_path)

    def _create_directory_structure(self, path=None):
        base_run = path if path is not None else self.base_run
        full_path = os.path.join(self.rootpath, base_run)
        bin_path = os.path.join(full_path, 'bin')
        for path in [full_path, bin_path]:
            cmd = 'mkdir -p {}'.format(path)
            logging.info('Creating %s', path)
            logging.debug('cmd: %s', cmd)
            try:
                output = sp.check_output(cmd.split(), stderr=sp.STDOUT)
                logging.debug('output: %s', output)
            except Exception as err:
                logging.error("Exception during directory creation: %s", err)
                raise
            if output:
                raise Exception('Unexpected stdout/stderr')


