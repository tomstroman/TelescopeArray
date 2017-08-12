import logging
import sys
def set_up_log(name=None, console_mirror=False):
    if name is None:
        name = "log.txt"

    logformat = '%(asctime)s %(levelname)s %(funcName)s: %(message)s'
    logging.basicConfig(filename=name, format=logformat, level=logging.DEBUG)
    if console_mirror:
        root = logging.getLogger()
        h = logging.StreamHandler(sys.stderr)
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter(logformat))
        root.addHandler(h)
    logging.info("Began logging to %s", name)
    return name

