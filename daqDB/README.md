# daqDB
Code to oversee the first few processing steps of raw data.

Main routines:
hunt.py: locate raw data on disk, and produce ASCII database.

updatedb.py: look for evidence of completed processing stages, and update
the ASCII database produced by hunt.py

visROOT/visualize.C: a ROOT script (root.cern.ch) to generate plots and
other metadata analyses for the data parts identified by hunt.py.

