#TelescopeArray production code
Telescope Array (telescopearray.org) is an observatory for detecting
ultra-high-energy cosmic rays, particles of astrophysical origin.

The detectors are located at the experiment site in Utah. Raw data
collected by telescopes at the site is stored on a specialized data
server attached to a computing cluster for processing and analysis.
Much of the code in this repository is tailored to that 
specific computing environment.

Although there are several approaches to interpreting the data
(based on different combinations of detectors and/or detector types)
with differing scientific advantages to each, this code focuses on
the stereoscopic observation of cosmic rays by multiple telescopes,
which requires processing raw telescope data far enough to identify
coincident signals from independent detectors.

The main executable here is in `run_stereo_analysis.py`; a summary
of its operation follows.

Given some configuration, it loads a list of observation nights,
and runs them each through `process_night`. The processing comprises
several steps, in sequence, as defined in `step.py`.

Some SQLite databases are used to track the processing status and
existence of raw data. Relevant utilities, as well as code to 
populate some databases, can be found in the `db` module.

Processing of raw data from the telescopes with FADC-based electronics
is governed by propriety Telescope Array software not stored here, but
wrappers to call this code are in `prep_fadc`.

Legacy code for stereo analysis is called in certain steps from 
`legacy_stereo`. The computationally heavy parts are executed in the
Mosix cluster; this code is written to spawn off those processes and
exit with an incomplete status; on subsequent execution it detects 
the existence of tasks in progress or evidence of their completion,
and continues.

