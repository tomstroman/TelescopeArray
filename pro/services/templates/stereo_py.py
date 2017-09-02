import copy
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


def build_stereo_py(new_replacements=None):
    with open(meta_template_file, 'r') as meta_template_in:
        meta_template = meta_template_in.read()

    replacements = copy.deepcopy(standard_replacements)
    if new_replacements is not None:
        replacements.update(new_replacements)

    for placeholder, replacement in replacements.items():
        meta_template = meta_template.replace(placeholder, replacement)

    return meta_template
