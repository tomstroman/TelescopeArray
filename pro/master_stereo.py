from utils import log
import logging

def make_stereo_happen(console_mirror=False):
    log_name = log.set_up_log(console_mirror=console_mirror)
    if not console_mirror:
        print 'Logging to', log_name

    logging.info("stereo happening now")
    logging.debug("Begin validating stereo arguments")
    prepare_stereo_run()
    stereo_run()

    return

#TODO: move these out
def prepare_stereo_run():
    logging.warn("not yet implemented")

def stereo_run():
    logging.warn("not yet implemented")

if __name__ == '__main__':
    make_stereo_happen(console_mirror=True)

