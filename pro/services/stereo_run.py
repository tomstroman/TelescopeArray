from db.database_wrapper import DatabaseWrapper
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
            logging.error("No database exists at %s", db_path)
# TODO: prompt user to create
            raise Exception("Database not found")

        self.db = DatabaseWrapper(db_path)
        self.params = StereoRunParams()
        logging.info("Parameters object: %s", self.params)

    def prepare_stereo_run(self):
        logging.warn("method not yet implemented")
        logging.info("TODO: get global info from db")
        logging.info("TODO: validate parameters")
        logging.info("TODO: prepare paths")
        logging.info("TODO: compile executables")
        logging.info("TODO: prepare templates from meta-templates")
        logging.info("TODO: generate plan for run, report to user")

    def stereo_run(self):
        logging.warn("method not yet implemented")

class StereoRunParams(object):
    def __init__(self, geocal=None, model=None, source=None):
        self.model = model or 'qgsjetii-03'
        self.source = source or 'mc-proton'
        self.geocal = geocal or 'gdas_j14t'

    def __repr__(self):
        return 'StereoRunParams: geocal={}, model={}, source={}'.format(
            self.geocal,
            self.model,
            self.source,
        )
