import logging
import os
import re
from datetime import datetime

TAMA_EXE = os.path.join(os.getenv('TAHOME'), 'tama', 'bin', 'tama.run')
EXPECTED_TAMA_STDERR = 2


# match a string like "7/28/2017  UT 05:59:55.087354105" followed by the processing time (indicating success)
TIMESTAMP = re.compile('(\d+)\/(\d+)\/(\d{4}) +UT (\d+):(\d{2}):(\d{2}\.\d+).*sec')


class PrologError(Exception):
    pass


class MissingOutputError(Exception):
    pass


def _camlist(daq_cams):
    """
    Get the list of active camera IDs, given daqcams.
    daqcams is a 12-bit unsigned integer where each bit indicates whether
    a camera was active for a given DAQ part.
    """
    return [i for i in range(12) if (daq_cams >> i) % 2]


def _time(timestamp): # works with TIMESTAMP matches
    hour, minute, second = [float(t) for t in timestamp[-3:]]
    return hour*3600 + minute*60 + second


class TamaRun(object):
    def __init__(self, part, trigset, outdir):
        self.part = part
        self.trigset = trigset
        self.outdir = outdir
        self.cmd_template = '{tama_exe} -o {output_dst} -r {tama_code} {ctd_file} {cam_files} > {stdout} 2> {stderr}'
        self.files = None

    def build_cmd(self, ctd_prefix, daq_cams):
        ctd_file = ctd_prefix + '-{}-{:07}.d.bz2'.format(self.part.site, self.trigset)
        output_dst = os.path.join(
            self.outdir,
            '{}-{}-{:07}.dst.gz'.format(
                os.path.basename(ctd_prefix),
                self.part.site,
                self.trigset,
            ),
        )
        stdout, stderr, prolog = (output_dst.replace('.dst.gz', suffix) for suffix in ['.out', '.err', '.prolog'])
        cam_file_template = ctd_prefix.replace('/ctd/', '/camera{0:02}/') + '-{0}-{{0:x}}-{1:07}.d.bz2'.format(self.part.site, self.trigset)
        cam_files = ' '.join([cam_file_template.format(c) for c in _camlist(daq_cams)])

        self.files = {
            'dst' : output_dst,
            'out' : stdout,
            'err' : stderr,
            'log' : prolog,
        }

        self.cmd = self.cmd_template.format(
            tama_exe=TAMA_EXE,
            output_dst=output_dst,
            tama_code=self.part.tama_code,
            ctd_file=ctd_file,
            cam_files=cam_files,
            stdout=stdout,
            stderr=stderr
        )

        return self.cmd, self.files

    def prolog_data(self):
        logging.info('Validating output')
        if not all([os.path.exists(f) for f in self.files.values()]):
            logging.error('Missing expected output from %s', self)
            raise MissingOutputError

        with open(self.files['err'], 'r') as err_file:
            stderr = err_file.readlines()
        logging.info('Lines of stderr: expected=%s, actual=%s', EXPECTED_TAMA_STDERR, len(stderr))

        try:
            with open(self.files['log'], 'r') as log_file:
                prolog = log_file.read()
            prolog_data = dict([tuple(r.split()) for r in re.findall('[A-Z]+_[A-Z]+ \d+', prolog)[-4:]])
            logging.info('Prolog report: read=%s, kept=%s, bytes=%s',
                prolog_data['TAMA_READ'],
                prolog_data['TAMA_KEPT'],
                prolog_data['BYTES_OUT'],
            )
        except Exception as err:
            logging.error('Encountered error reading prolog: %s', err)
            raise PrologError

        with open(self.files['out'], 'r') as out_file:
            stdout = out_file.read()
        times = TIMESTAMP.findall(stdout)

        duration = _time(times[-1]) - _time(times[0])
        prolog_data['DURATION'] = duration

        return prolog_data

    def __repr__(self):
        if self.files is not None:
            return 'tama.run({})'.format(os.path.basename(self.files['dst']))
        return 'tama.run({}, {:07})'.format(part, trigset)


