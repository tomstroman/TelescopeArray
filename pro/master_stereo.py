import argparse
import logging

from services.stereo_run import StereoRun, DEFAULT_DATE_LIST_FILE
from step import Step, STEPS
from utils import log

def make_stereo_happen(
        console_mirror=False,
        date_list=None,
        model=None,
        name=None,
        source=None,
        begin=None,
        end=None,
        geo=None,
        salt_overrides=None,
    ):
    log_name = log.set_up_log(console_mirror=console_mirror)
    if not console_mirror:
        print 'Logging to', log_name

    logging.info("stereo happening now")

    run = StereoRun(name, model, source, geo, salt_overrides)
    run.prepare_stereo_run()
    run.stereo_run(date_list, begin, end)

    return run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='test')
    parser.add_argument('-d', '--date_list', default=DEFAULT_DATE_LIST_FILE)
    parser.add_argument('-m', '--model', default='qgsjetii-03')
    parser.add_argument('-s', '--source', default='mc-proton-180')
    parser.add_argument('--geobr', default='geobr_joint.dst.gz')
    parser.add_argument('--geolr', default='geolr_joint.dst.gz')
    parser.add_argument('--geomd', default='geomd_20131002.dst.gz')
    parser.add_argument('--begin', default=STEPS.PREP_TRUMP_SIM)
    parser.add_argument('--end', default=None)
    parser.add_argument('--override_salt_geocal', default=None)
    parser.add_argument('--override_salt_model', default=None)
    parser.add_argument('--override_salt_source', default=None)
    args = parser.parse_args()
    for step in [args.begin, args.end]:
        if step is not None:
            assert step in Step.names.keys()

    geo = {
        'br': args.geobr,
        'lr': args.geolr,
        'md': args.geomd,
    }
    salt_overrides = {
        'geocal': args.override_salt_geocal,
        'model': args.override_salt_model,
        'source': args.override_salt_source,
    }
    run = make_stereo_happen(
        console_mirror=True,
        name=args.name,
        source=args.source,
        date_list=args.date_list,
        model=args.model,
        begin=args.begin,
        end=args.end,
        geo=geo,
        salt_overrides=salt_overrides,
    )
