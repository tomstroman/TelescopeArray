# step.py
# Thomas Stroman, University of Utah, 2016-11-27
# Standardized list of steps for stereo-processing

class Step(object):
    counter = 0
    def __init__(self, name, function):
        self.name = name
        self.function = function
        self.id = Step.counter
        Step.counter += 1

    def ex(self, *args, **kwargs):
        try:
            return self.function(*args, **kwargs)
        except TypeError:
            print 'Error: no callable function for', self

    def __repr__(self):
        return 'Step {0}: {1} (calls function {2})'.format(self.id, self.name,
                self.function)

def foo(*args, **kwargs):
    """
    Placeholder function.
    """
    pass

steps = [Step('run_timecorr', foo),
         Step('run_tama', foo),
         Step('run_fdplane', foo),
         Step('get_mdps3', foo),
         Step('find_matches', foo),
         Step('remove_clf', foo),
         Step('isolate_events', foo),
         Step('run_stplane', foo),
         Step('perform_sanity_check', foo),
         Step('reconstruct_profiles', foo),
         Step('dump_ascii', foo),
         ]
