Star simulator

Script to check the optics calibration of Telescope Array
fluorescence detectors (mirror geometry, etc.) by
comparing actual recorded starlight data
with a simulation of the same star at the same time.

Steps to perform comparison for a given telescope mirror:
1. Select a data part with a known, isolated bright star 
2. Run "tama -m" to prepare FDMEAN banks from raw TAFD data
3. Subtract minimum FADC seen in each PMT, and apply calibration
4. Determine comparison start and end time, based on desired binning
5. Identify star and get equatorial coordinates
6. Ray-trace light from star using "TRUMP" telescope simulator
7. Compute signal-weighted centroid and PSF of starlight position on image sensor (data and sim)
8. Compare data and sim as a function of time
9. (Optional) Make graphs and movies to provide additional detail.

Desired visualizations:
* Animation: calibrated image as a function of time (data, sim, and both together)
* Animation: detailed starlight spot moving across image sensor, from simulation

