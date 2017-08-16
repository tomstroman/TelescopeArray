from db import stereo_run_db
from db.database_wrapper import DatabaseWrapper
from services.stereo_run_params import StereoRunParams
import logging
import os

MASTER_DB_NAME = 'stereo_runs.db'

class StereoRun(object):
    def __init__(self):
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

    def prepare_stereo_run(self):
        logging.warn("method not yet implemented")
        self.base_run = self._find_or_create_base_run()
        logging.info("TODO: get global info from db")
        logging.info("TODO: validate parameters")
        logging.info("TODO: prepare paths")
        logging.info("TODO: compile executables")
        logging.info("TODO: prepare templates from meta-templates")
        logging.info("TODO: generate plan for run, report to user")

    def stereo_run(self):
        logging.warn("method not yet implemented")

    def _find_or_create_base_run(self):
        sql = 'SELECT name, path FROM StereoRuns WHERE fdplaneconfig=\"{0}\" AND model=\"{1}\"'.format(
                self.params.fdplane_config,
                self.params.model,
        )
        logging.debug('sql: %s', sql)
        runs = self.db.retrieve(sql)
        for name, path in runs:
            logging.info('found base StereoRun %s at path %s', name, path)
        if len(runs) == 0:
            logging.info('No base StereoRuns found')

