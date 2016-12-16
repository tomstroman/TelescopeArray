# step.py
# Thomas Stroman, University of Utah, 2016-11-27
# Standardized list of steps for stereo-processing

class Step(object):
    counter = 0
    names = {}
    
    def __init__(self, name, function):
        assert name not in Step.names.keys()
        self.name = name
        self.function = function
        self.id = Step.counter
        Step.names[name] = self.id
        Step.counter += 1

    def ex(self, *args, **kwargs):
        try:
            return self.function(*args, **kwargs)
        except TypeError:
            print 'Error: invalid call for', self

    def __repr__(self):
        return 'Step {0}: {1} (calls function {2})'.format(self.id, self.name,
                self.function)

def foo(*args, **kwargs):
    """
    Placeholder function.
    """
    pass

from prep_fadc import raw_to_dst
from legacy_stereo import simulation, analysis
    
data_steps = [Step('run_timecorr', raw_to_dst.run_timecorr),
              Step('run_tama', foo),
              Step('run_fdped', foo),
              Step('run_fdplane', foo),
              Step('get_mdps3', foo),
              ]
    
mc_steps = [Step('verify_data', simulation.verify_data),
            Step('prep_trump_sim', simulation.prep_trump_sim),
            Step('run_trump_sim', simulation.run_trump_sim),
            Step('prep_md_sim', foo),
            Step('run_md_sim', foo),
            Step('verify_sim', simulation.verify_sim),
            ]
            
analysis_steps = [Step('verify_source', foo),
                  Step('find_matches', foo),
                  Step('remove_clf', foo),
                  Step('isolate_events', foo),
                  Step('run_stplane', foo),
                  Step('perform_sanity_check', foo),
                  Step('reconstruct_profiles', foo),
                  Step('dump_ascii', analysis.analyze_and_dump),
                  ]

steps = data_steps + mc_steps + analysis_steps
