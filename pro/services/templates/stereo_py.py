import logging
import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)
meta_template_file = os.path.join(__location__, 'stereo_py_meta_template.txt')

standard_replacements = {
    '_META_REPLACE_TPNAME_' : 'ghl70x60',
    '_META_REPLACE_MDNAME_' : 'mdghl70x60',
    '_META_REPLACE_ATMOS_'  : '$RTDATA/atmosphere/gdas.dst.gz',
    '_META_REPLACE_DUMPREVISION_' : '2d',
    '_META_REPLACE_STEREOROOT_' : '/scratch/tstroman/stereo',
    '_META_REPLACE_FDPLANEDATADIR_' : '/scratch/tstroman/mono/fdplane_cal1.4_joint_20141014',
    '_META_REPLACE_GEOBR_'  : '$RTDATA/fdgeom/geobr_joint.dst.gz',
    '_META_REPLACE_GEOLR_'  : '$RTDATA/fdgeom/geolr_joint.dst.gz',
    '_META_REPLACE_GEOMD_'  : '$RTDATA/fdgeom/geomd_20131002.dst.gz',
    '_META_REPLACE_FDPED_'  : '/scratch1/fdpedv',
}


def build_stereo_py():
    with open(meta_template_file, 'r') as meta_template_in:
        meta_template = meta_template_in.read()
    logging.info('%s contains %s newlines', meta_template_file, meta_template.count('\n'))
