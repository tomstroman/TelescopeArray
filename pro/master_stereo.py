import argparse
import logging

from services.stereo_run import StereoRun, DEFAULT_DATE_LIST_FILE
from step import Step
from utils import log

def make_stereo_happen(
        console_mirror=False,
        date_list=None,
        name=None,
        begin=None,
        end=None,
    ):
    log_name = log.set_up_log(console_mirror=console_mirror)
    if not console_mirror:
        print 'Logging to', log_name

    logging.info("stereo happening now")

    run = StereoRun(name)
    run.prepare_stereo_run()
    run.stereo_run(date_list, begin, end)

    return run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='test')
    parser.add_argument('-d', '--date_list', default=DEFAULT_DATE_LIST_FILE)
    parser.add_argument('--begin', default='prep_trump_sim')
    parser.add_argument('--end', default=None)
    args = parser.parse_args()
    for step in [args.begin, args.end]:
        if step is not None:
            assert step in Step.names.keys()

    run = make_stereo_happen(
        console_mirror=True,
        name=args.name,
        date_list=args.date_list,
        begin=args.begin,
        end=args.end,
    )
