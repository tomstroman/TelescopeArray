#!/usr/local/bin/python

# process_night.py
# Thomas Stroman, University of Utah, 2016-11-27
# Supervise the stereo processing of a single night from start to finish.

from step import Step, steps


def process_night(night, params, start_code=None, end_code=None):
    """
    Arguments:
    night is an 8-digit integer giving a UTC date in YYYYMMDD format.
    params is a dict.
    If supplied, start_code will override the processing to begin at the specified
    step if it is possible. Otherwise it will begin at the last known
    checkpoint for the night.
    """
    print night
    if night in params['mosq']:
        return 'found in queue'

    if isinstance(start_code, str):
        start_code = Step.names[start_code]

    if isinstance(end_code, str):
        end_code = Step.names[end_code]

    if start_code is None:
        start_code = steps[0].id
    if end_code is None:
        end_code = steps[-1].id

    #print 'Processing {} from {} through {}'.format(night, steps[start_code], steps[end_code])


    for step in steps:
        if not start_code <= step.id <= end_code:
            continue
        result = step.ex(night, params)
        if result is not None:
            return result

    return 'end reached'

if __name__ == '__main__':
    process_night(0)





