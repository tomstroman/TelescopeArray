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

    
    
data_steps = [Step('run_timecorr', foo),
              Step('run_tama', foo),
              Step('run_fdped', foo),
              Step('run_fdplane', foo),
              Step('get_mdps3', foo),
              ]
    
mc_steps = [Step('verify_data', foo),
            Step('prep_trump_sim', foo),
            Step('run_trump_sim', foo),
            Step('prep_md_sim', foo),
            Step('run_md_sim', foo),
            ]
            
analysis_steps = [Step('verify_source', foo),
                  Step('find_matches', foo),
                  Step('remove_clf', foo),
                  Step('isolate_events', foo),
                  Step('run_stplane', foo),
                  Step('perform_sanity_check', foo),
                  Step('reconstruct_profiles', foo),
                  Step('dump_ascii', foo),
                  ]

steps = data_steps + mc_steps + analysis_steps