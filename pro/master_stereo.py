from services.stereo_run import StereoRun
from utils import log
import logging

def make_stereo_happen(console_mirror=False, name=None):
    log_name = log.set_up_log(console_mirror=console_mirror)
    if not console_mirror:
        print 'Logging to', log_name

    logging.info("stereo happening now")

    run = StereoRun(name)
    run.prepare_stereo_run()
    run.stereo_run()

    return run

if __name__ == '__main__':
    run = make_stereo_happen(console_mirror=True, name='foo')

