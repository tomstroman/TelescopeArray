# TelescopeArray
This repository is for code that I develop as part of my workflow
in performing research on the Telescope Array Experiment.

##data

I store and process TA data on a computing cluster at the University of Utah.
The software environment on the cluster puts constraints on my development
workflow. In practice, this means that some of the code can only be tested
*after* deploying it to the cluster, which explains the frequency of "bugfix"
commits to this repository during development of new features.

###data/ta\_common

Common code shared by various other projects listed below. 
*This code must be made available in the path*, for example, via
a symlink from site-packages. If this location changes from one
revision to the next, it will be necessary to update the path or
symlink manually.

###data/daqDB 

daqDB is a set of scripts that check the data from certain telescope stations,
which is organized into "DAQ parts." 
 
##analysis

This code is used to do science with processed data. Some of it is in Python,
but much more of it is in ROOT (essentially C++), a particle physics tool
developed by CERN.
