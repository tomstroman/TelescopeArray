from services.stereo_run import StereoRun
from utils import log
import logging

def make_stereo_happen(console_mirror=False):
    log_name = log.set_up_log(console_mirror=console_mirror)
    if not console_mirror:
        print 'Logging to', log_name

    logging.info("stereo happening now")
    logging.debug("Begin validating stereo arguments")

    run = StereoRun()
    run.prepare_stereo_run()
    run.stereo_run()

    return run

if __name__ == '__main__':
    run = make_stereo_happen(console_mirror=True)

