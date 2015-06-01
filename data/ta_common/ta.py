# A number of constants and other useful information for use in other scripts.
import os
t0 = 2454282.5 # Julian date of 2007-07-01 00:00:00.0 UTC

sites = ['brm','lr','md','tale']
sitenames = ['black-rock','long-ridge','middle-drum','tale']




# absolute-path prefix for permanent storage of various programs' output
tama = '/tama_' 

fdped = '/scratch1/fdpedv'

fdplane = '/scratch/tstroman/mono/fdplane_cal1.4_joint_20141014'

localtama = '/scratch1/tama'

fdgeom = os.getenv('RTDATA') + '/fdgeom'
geo = [fdgeom + '/geo' + i + '.dst.gz' for 
    i in ['br_joint','lr_joint','md_20131002']]
    
stereo_roots = [i+'/tstroman/stereo' for i in ['/scratch','/hangar']]