from db import stereo_run_db
from db.database_wrapper import DatabaseWrapper
from services import executables
from services.stereo_run_params import StereoRunParams
from services.templates import trump_conf, stereo_py
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

        self.rtdata = os.getenv('RTDATA')
        if not self.rtdata:
            logging.error("RTDATA variable not set.")
            raise Exception("RTDATA variable not set.")

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
        self.specific_run = self._find_or_create_specific_run()

        self._create_directory_structure(self.base_run)
        self._compile_executables()
        self._build_templates()
        logging.info("TODO: generate plan for run, report to user")

    def stereo_run(self):
        logging.warn("method not yet implemented")

    def _find_or_create_base_run(self, supplied_name=None):
        """
        Find any StereoRun(s) matching the simulation *parameters* (FDPlaneConfig and Model),
        and check against the supplied name, otherwise attempt to create one.
        """
        assert self.params
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
            return path
        except Exception as err:
            logging.error('Failed to create StereoRun. Error: %s', err)

    def _find_or_create_specific_run(self):
        assert self.base_run

        run_name = self.params.name
        is_mc = self.params.is_mc
        if is_mc:
            sql = 'SELECT name, species FROM MCStereoRuns WHERE stereorun_path=\"{0}\"'.format(self.base_run)
        else:
            sql = 'SELECT name FROM DataStereoRuns WHERE stereorun_path=\"{0}\"'.format(self.base_run)
        logging.debug('sql: %s', sql)

        matching_runs = self.db.retrieve(sql)
        for row in matching_runs:
            if row[0] == run_name:
                logging.info('Found a matching specific run for %s', run_name)
                return run_name

        logging.info('No matching specific runs found. Attempting to create %s with is_mc=%s', run_name, is_mc)
        try:
            if is_mc:
                self.db.insert_row('INSERT INTO MCStereoRuns VALUES(?, ?, ?)', (run_name, self.base_run, self.params.species))
            else:
                self.db.insert_row('INSERT INTO DataStereoRuns VALUES(?, ?)', (run_name, self.base_run))
            return run_name
        except Exception as err:
            logging.error('Failed to create specific run. Error: %s', err)


    def _create_directory_structure(self, path=None):
        base_run = path if path is not None else self.base_run
        full_path = os.path.join(self.rootpath, base_run)
        self.bin_path = os.path.join(full_path, 'bin')
        self.run_path = os.path.join(full_path, self.specific_run)
        self.src_path = os.path.join(full_path, 'src')
        self.log_path = None
        paths = [full_path, self.bin_path, self.run_path, self.src_path]
        if self.params.is_mc:
            self.log_path = os.path.join(self.run_path, 'logs')
            paths.append(self.log_path)

        for path in paths:
            cmd = 'mkdir -p {}'.format(path)
            logging.info('Verifying path exists: %s', path)
            logging.debug('cmd: %s', cmd)
            try:
                output = sp.check_output(cmd.split(), stderr=sp.STDOUT)
                logging.debug('output: %s', output)
            except Exception as err:
                logging.error("Exception during directory creation: %s", err)
                raise
            if output:
                raise Exception('Unexpected stdout/stderr')
            assert os.path.isdir(path)

    def _compile_executables(self):
        for prog, filename in executables.base_reqs.items():
            exe = os.path.join(self.bin_path, filename)
            if os.path.exists(exe):
                logging.debug('found %s', exe)
            else:
                logging.debug('did not find %s', exe)
                executables.prepare_executable(self, prog, exe, src_dir=self.src_path)

    def _build_templates(self):
        logging.info('creating templates')

        showlib = self.db.retrieve('SELECT dstfile FROM Showlibs WHERE model=\"{0}\" AND species={1}'.format(
            self.params.model,
            self.params.species,
        ))[0][0]

        replacements = trump_conf.standard_replacements
        replacements.update({
            '_META_REPLACE_GEOCAL_'  : self.name,
            '_META_REPLACE_MODEL_'   : self.params.model,
            '_META_REPLACE_SOURCE_'  : self.specific_run,
            '_META_REPLACE_GEOFILE_' : os.path.join(
                self.rtdata,
                'fdgeom',
                'geoREPLACE_GEO_{}.dst.gz'.format(self.params.geometry),
            ),
            '_META_REPLACE_SPECIES_' : str(self.params.species),
            '_META_REPLACE_SHOWLIB_' : os.path.join(self.rtdata, 'showlib', showlib),
            '_META_REPLACE_DTIME_'   : str(self.params.dtime),
        })

        meta_template = trump_conf.conf_meta_template
        for key, value in replacements.items():
            logging.debug('Replacing %s with %s', key, value)
            meta_template = meta_template.replace(key, value)

        assert '_META_REPLACE_' not in meta_template

        template = os.path.join(self.run_path, trump_conf.standard_template_name)
        with open(template, 'w') as template_file:
            template_file.write(meta_template)

        stereo_py.build_stereo_py()
