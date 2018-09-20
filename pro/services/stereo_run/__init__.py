import logging
import os

from db import stereo_run_db
from db.database_wrapper import DatabaseWrapper
from services import executables
from services.stereo_run_params import StereoRunParams
from services.templates import trump_conf, stereo_py

from . import run_management, directory
import run_stereo_analysis

MASTER_DB_NAME = 'stereo_runs.db'

ENV_VARS = [
    ('rootpath', 'TAFD_STEREO_ROOT'),
    ('rtdata', 'RTDATA'),
    ('tahome', 'TAHOME'),
]

DEFAULT_DATE_LIST_FILE = 'test-date-list.txt'
DEFAULT_DATE_LIST_CONTENTS = '20080401\n'

class StereoRun(object):
    def __init__(self, name=None, model=None, source=None):
        logging.debug("setting up StereoRun")

        self._import_environment()

        self._prepare_database()

        if source == 'nature':
            self.params = StereoRunParams(self, model=model, is_mc=False)
        else:
            try:
                assert source.startswith('mc-') and source.count('-') == 2, 'Invalid source name'
                _, species_name, dtime = source.split('-')
                self.params = StereoRunParams(self, model=model, is_mc=True, species_name=species_name, dtime=dtime)
            except Exception as err:
                logging.error('Error building StereoRunParams: %s', err)
                raise Exception('Invalid source, must be "nature" or "mc-(species)-(dtime)"')
        self.params.skip_md = 'no-middle-drum' in name

        logging.info("Parameters object: %s", self.params)

# TODO: replace this function with runtime arguments
        self._set_hardcoded_variables(name=name)

    def _import_environment(self):
        is_valid_environment = True

        for attr, env in ENV_VARS:
            setattr(self, attr, os.getenv(env))
            if not getattr(self, attr):
                is_valid_environment = False
                logging.error("%s variable not set.", env)

        if not is_valid_environment:
            raise Exception("Missing expected environment variable(s)")

    def _prepare_database(self):
        db_path = os.path.join(self.rootpath, MASTER_DB_NAME)
        if not os.path.exists(db_path):
            stereo_run_db.initialize(db_path)

#            logging.error("No database exists at %s", db_path)
# TODO: prompt user to create
#            raise Exception("Database not found")

        self.db = DatabaseWrapper(db_path)

    def _set_hardcoded_variables(self, name, recon='ghl70x60'):
        vars = [
            ('name', name),
            ('recon', recon),
            ('mdrecon', 'md' + recon),
        ]
        for attr, value in vars:
            setattr(self, attr, value)


    def prepare_stereo_run(self):
        logging.warn("method not yet implemented")
        self.base_run = run_management.find_or_create_base_run(self, self.name)
        self.specific_run = run_management.find_or_create_specific_run(self)

        self.modelsource = ''.join(
            [i for i in self.params.model + self.specific_run if i.isalnum()]
        )
        logging.debug('modelsource value: %s', self.modelsource)
        self._create_directory_structure(self.base_run)
        self._compile_executables()
        self._build_templates()
        logging.info("TODO: generate plan for run, report to user")

    def stereo_run(self, date_list, begin, end):
        self.dates = self._read_date_list(date_list)
        date_status, params = run_stereo_analysis.run(self, begin, end)
        self.status_dates = run_stereo_analysis.report(date_status)

    def _read_date_list(self, date_list):
        try:
            dates = [int(date_list)]
            date_file = 'stdin'
            logging.info('Interpreting %s as a date', date_list)
        except ValueError:
            dates = None

        if dates is None:
            date_file = os.path.join(self.rootpath, date_list)
            if date_list == DEFAULT_DATE_LIST_FILE and not os.path.exists(date_file):
                with open(date_file, 'w') as df:
                    df.write(DEFAULT_DATE_LIST_CONTENTS)

            with open(date_file, 'r') as df:
                dates = sorted(
                    list(
                        set(
                            [int(d) for d in df.readlines()]
                        )
                    )
                )

        logging.info('Read %s night(s) from %s through %s from %s', len(dates), dates[0], dates[-1], date_file)
        return dates

    def _create_directory_structure(self, path=None):
        directory.build_tree(self, path)

    def _compile_executables(self):
        with executables.override_params(stereo_run=self) as exe_service:
            for prog, filename in exe_service.get_base_reqs():
                exe = os.path.join(self.bin_path, filename)
                if not os.path.exists(exe):
                    logging.debug('did not find %s', exe)
                    executables.prepare_executable(self, prog, exe, src_dir=self.src_path)

    def _build_templates(self):
        logging.info('creating templates')

        geometry_replacements = {
            '_META_REPLACE_GEOBR_': self.params.geometry_dsts['br'],
            '_META_REPLACE_GEOLR_': self.params.geometry_dsts['lr'],
            '_META_REPLACE_GEOMD_': self.params.geometry_dsts['md'],
        }

        if self.params.is_mc:
            self.trump_template = trump_conf.render_template(self)
        else:
            self.trump_template = None

        self.stereo_dot_py = os.path.join(self.bin_path, 'stereo.py')
        replacements = {
            '_META_REPLACE_TPNAME_' : self.recon,
            '_META_REPLACE_MDNAME_' : self.mdrecon,
            '_META_REPLACE_STEREOROOT_' : self.rootpath,
        }
        replacements.update(geometry_replacements)

        contents = stereo_py.build_stereo_py(new_replacements=replacements)
        with open(self.stereo_dot_py, 'w') as stpyfile:
            stpyfile.write(contents)
