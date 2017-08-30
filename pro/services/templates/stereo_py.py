import logging
import os

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)
meta_template_file = os.path.join(__location__, 'stereo_py_meta_template.txt')

def build_stereo_py():
    with open(meta_template_file, 'r') as meta_template_in:
        meta_template = meta_template_in.read()
    logging.info('%s contains %s newlines', meta_template_file, meta_template.count('\n'))
