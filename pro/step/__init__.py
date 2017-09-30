# step.py
# Thomas Stroman, University of Utah, 2016-11-27
# Standardized list of steps for stereo-processing

from utils import Constants

STEPS = Constants(
    RUN_TIMECORR         = 'run_timecorr',
    RUN_TAMA             = 'run_tama',
    RUN_FDPED            = 'run_fdped',
    RUN_FDPLANE          = 'run_fdplane',
    GET_MDPS3            = 'get_mdps3',
    VERIFY_DATA          = 'verify_data',
    PREP_TRUMP_SIM       = 'prep_trump_sim',
    RUN_TRUMP_SIM        = 'run_trump_sim',
    PREP_MD_SIM          = 'prep_md_sim',
    RUN_MD_SIM           = 'run_md_sim',
    VERIFY_SIM           = 'verify_sim',
    VERIFY_SOURCE        = 'verify_source',
    FIND_MATCHES         = 'find_matches',
    REMOVE_CLF           = 'remove_clf',
    ISOLATE_EVENTS       = 'isolate_events',
    RUN_STPLANE          = 'run_stplane',
    PERFORM_SANITY_CHECK = 'perform_sanity_check',
    RECONSTRUCT_PROFILES = 'reconstruct_profiles',
    DUMP_ASCII           = 'dump_ascii',
)


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
    
data_steps = [
    Step(STEPS.RUN_TIMECORR, raw_to_dst.run_timecorr),
    Step(STEPS.RUN_TAMA, raw_to_dst.run_tama),
    Step(STEPS.RUN_FDPED, raw_to_dst.run_fdped),
    Step(STEPS.RUN_FDPLANE, foo),
    Step(STEPS.GET_MDPS3, foo),
]
    
mc_steps = [
    Step(STEPS.VERIFY_DATA, simulation.verify_data),
    Step(STEPS.PREP_TRUMP_SIM, simulation.prep_trump_sim),
    Step(STEPS.RUN_TRUMP_SIM, simulation.run_trump_sim),
    Step(STEPS.PREP_MD_SIM, foo),
    Step(STEPS.RUN_MD_SIM, foo),
    Step(STEPS.VERIFY_SIM, simulation.verify_sim),
]
            
analysis_steps = [
    Step(STEPS.VERIFY_SOURCE, foo),
    Step(STEPS.FIND_MATCHES, foo),
    Step(STEPS.REMOVE_CLF, foo),
    Step(STEPS.ISOLATE_EVENTS, foo),
    Step(STEPS.RUN_STPLANE, foo),
    Step(STEPS.PERFORM_SANITY_CHECK, foo),
    Step(STEPS.RECONSTRUCT_PROFILES, foo),
    Step(STEPS.DUMP_ASCII, analysis.analyze_and_dump),
]

steps = data_steps + mc_steps + analysis_steps
