import logging
import os

class StereoRunParams(object):
    def __init__(self, stereo_run, is_mc=True, fdplane_config='joint_cal1.4', geometry=None,
            calibration=None, model=None, species=None, species_name=None, name=None, dtime=None):
        self.db = stereo_run.db
        self.stereo_run = stereo_run

# determine the calibration and geometry associated with the source data
        vconfig, vcal, vgeo = self._validate_fdplane_cfg(fdplane_config)
        self.fdplane_config = vconfig

        self.calibration = calibration or vcal
        if self.calibration != vcal:
            logging.warn("using calibration=%s but fdplane_config %s uses calibration=%s", self.calibration, vconfig, vcal)

        self.geometry = geometry or vgeo
        if self.geometry != vgeo:
            logging.warn("using geometry=%s but fdplane_config %s uses geometry=%s", self.geometry, vconfig, vgeo)

        self.geometry_dsts = self._find_geometry_dsts()
        self.model = model or self._pick_model()
        self.dedx_model = self.db.retrieve('SELECT dedx_model FROM Models where name="{}"'.format(self.model))[0][0]

        self.is_mc = is_mc
        if self.is_mc:
            self.species = species or self._pick_species(species_name)
            self.dtime = float(dtime)
        else:
            self.species = None
            self.dtime = None

        self.name = name or self._generate_name()

    def __repr__(self):
        return 'StereoRunParams {}: fdplane={}, model={}, MC species={}, geometry={}'.format(
            self.name,
            self.fdplane_config,
            self.model,
            self.species,
            self.geometry_dsts,
        )

    def _validate_fdplane_cfg(self, config):
        if not config:
            raise Exception(u'Bad config: {0}'.format(config))
        sql = 'SELECT calibration, geometryset FROM FDPlaneConfigs where name="{0}"'.format(config)
        logging.debug("sql: %s", sql)
        fdpcs = self.db.retrieve(sql)
        if not fdpcs:
            logging.error("no FDPlaneConfigs found named %s", config)
            raise Exception

        return config, fdpcs[0][0], fdpcs[0][1]


    def _pick_model(self):
        models = self.db.retrieve('SELECT name, propername, dedx_model FROM Models')
        sorted_models = sorted(models, key=lambda x: x[2])
        for name, propername, dedx_model in sorted_models:
            logging.info('found model: %s ("%s"), dedx_model %s', name, propername, dedx_model)
        # temporary: just pick index 1 (should be qgsjetii-03)
        return sorted_models[1][0]

    def _pick_species(self, species_name=None):
        species = self.db.retrieve('SELECT corsika_id, name FROM Species')
        sorted_species = sorted(species, key=lambda x: x[0])
        for corsika_id, name in sorted_species:
            if name == species_name:
                logging.info('found species: %s ("%s")', corsika_id, name)
                return corsika_id
        raise Exception('Species not found')

    def _generate_name(self):
        if not self.is_mc:
            return "nature"
        species = self.db.retrieve('SELECT name FROM Species WHERE corsika_id={0}'.format(self.species))[0][0]
        return 'mc-{0}'.format(species)

    def _find_geometry_dsts(self):
        dsts_by_site = self.db.retrieve(
            'SELECT S.shortname, G.dstfile FROM SiteGeometry G JOIN Sites S ON G.site=S.ID WHERE G.geometryset="{0}"'.format(
                self.geometry
            )
        )
        dsts = {
            site: os.path.join(
                self.stereo_run.rtdata,
                'fdgeom',
                dst,
            ) for site, dst in dsts_by_site
        }
        assert len(dsts) == 3, 'Invalid number of geometry DSTs found'
        assert all(os.path.exists(dst) for dst in dsts.values()), 'Missing geometry DSTs'
        return dsts
