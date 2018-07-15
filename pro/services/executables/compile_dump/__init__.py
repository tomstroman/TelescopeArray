import logging
import os
import subprocess as sp

COMPILER_SYNTAX_START = '/* Syntax for compiling:'
COMPILER_SYNTAX_END = '*/'

def compile_dump_profs(stereo_run, cwd, destination):
    template_name = 'dumpster2_template.c'
    _compile_template(template_name, stereo_run, destination)

def compile_dump_tuples(stereo_run, cwd, destination):
    template_name = 'dumpst_template.c'
    dedx_model = stereo_run.params.dedx_model
    db_vars = stereo_run.db.retrieve('SELECT p_mec_a0, p_mec_a1, p_mec_a2 FROM Models WHERE dedx_model={}'.format(dedx_model))[0]
    replacements = {
        '_META_REPLACE_MEC_A0_': str(db_vars[0]),
        '_META_REPLACE_MEC_A1_': str(db_vars[1]),
        '_META_REPLACE_MEC_A2_': str(db_vars[2]),
    }
    _compile_template(template_name, stereo_run, destination, replacements)

def _compile_template(template_name, stereo_run, destination, replacements=None):
    source_template = os.path.join(os.path.dirname(__file__), template_name)
    with open(source_template, 'r') as c_source_file:
        source = c_source_file.read()

    if replacements is not None:
        print 'Replacements:', replacements
        for placeholder, value in replacements.items():
            source = source.replace(placeholder, value)

    cmds = []
    is_command = False
    for line in source.split('\n'):
        if line == COMPILER_SYNTAX_START:
            is_command = True
            continue
        if line == COMPILER_SYNTAX_END:
            break
        if is_command:
            cmds.append(line)

    logging.info('Commands for compiling %s: %s', template_name, cmds)
    logging.info('Destination: %s', destination)
    source_file = os.path.join(stereo_run.bin_path, template_name.replace('_template', ''))
    with open(source_file, 'w') as c_source_file:
        c_source_file.write(source)

    for cmd in cmds:
        sp.check_output(cmd, shell=True, cwd=stereo_run.bin_path, stderr=sp.STDOUT)

    assert os.path.exists(destination)
