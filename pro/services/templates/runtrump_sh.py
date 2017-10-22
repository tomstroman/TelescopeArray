import copy
import logging
import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)
meta_template_file = os.path.join(__location__, 'runtrump_sh_meta_template.txt')

standard_replacements = {
}


def build_runtrump_sh(new_replacements=None):
    with open(meta_template_file, 'r') as meta_template_in:
        meta_template = meta_template_in.read()

    replacements = copy.deepcopy(standard_replacements)
    if new_replacements is not None:
        replacements.update(new_replacements)

    for placeholder, replacement in replacements.items():
        meta_template = meta_template.replace(placeholder, replacement)

    return meta_template
