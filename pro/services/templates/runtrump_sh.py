import copy
import logging
import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)
meta_template_file = os.path.join(__location__, 'runtrump_sh_meta_template.txt')

standard_replacements = {
    '_META_REPLACE_PREPMD_': '$TAHOME/processFD/prepmdsim.sh',
    '_META_REPLACE_RUNMD_': '$TAHOME/processFD/runmdsim.sh',
    '_META_REPLACE_GEOBR_'  : '$RTDATA/fdgeom/geobr_joint.dst.gz',
    '_META_REPLACE_GEOLR_'  : '$RTDATA/fdgeom/geolr_joint.dst.gz',
}


def build_runtrump_sh(new_replacements=None):
    with open(meta_template_file, 'r') as meta_template_in:
        meta_template = meta_template_in.read()

    replacements = copy.deepcopy(standard_replacements)
    if new_replacements is not None:
        replacements.update(new_replacements)

    for placeholder, replacement in replacements.items():
        meta_template = meta_template.replace(placeholder, replacement)

    assert '_META_REPLACE_' not in meta_template
    return meta_template
