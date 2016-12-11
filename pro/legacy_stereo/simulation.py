# simulation.py
# Thomas Stroman, University of Utah, 2016-12-10
# Code to wrap simulation preparation and execution, which exists as
# various Bash and Python code I've written previously. This will be
# deprecated eventually.

from db.database_wrapper import DatabaseWrapper

analysis_db = DatabaseWrapper('db/tafd_analysis.db')
properties = {name: value for name, value in analysis_db.retrieve("SELECT name, value FROM Properties")}


def verify_data(night):
    pass

def prep_trump_sim(night):
    pass

def run_trump_sim(night):
    pass

def run_md_sim(night):
    pass
