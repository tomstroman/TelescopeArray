#!/usr/local/bin/python
import sys
import os
import time
import re
import subprocess as sp
from collections import defaultdict

narg = len(sys.argv)

if (narg==1):
    print("Usage: {0} path_to_analysis/with/calibration/model/dstsrc".format(sys.argv[0]))
    sys.exit(0)

#recon = 'ghdef'
#recon="ghdef-mddef"  
#recon='width0-mddef'

#recon = 'width1-mdghd'
#recon = 'ghdef-mdghd'
#recon = 'ghdef-mdghd2'
#recon = 'ghdef-mdghd3'
#recon = 'ghl60x60-mdghl60x60'
recon = 'ghl70x60-mdghl70x60'
#recon = 'ghl70x100-mdghl70x100'
#recon = 'ghl56x150-mdghl56x150'
#recon = 'ghl60-mdghl60'
#dumpst = os.getenv("TAHOME") + "/ascii/dumpst-rootformat.txt"
#dumpst = 
ymd = time.strftime("%Y%m%d")
  
for path in sys.argv[1:]:
    abspath = os.path.abspath(path)
    dumpst = os.path.normpath(abspath + '/../bin/dumpst-rootformat.txt')
    if not os.path.exists(dumpst):
        print 'Error: not found: ' + dumpst
        continue
    #print(abspath)
    ds = abspath.split("/") #directory structure
    l = len(ds)
    dstsrc = ds[l-1]
    model = ds[l-2]
    cal = ds[l-3]
    
    #outrel=abspath+"/../ascii/{0}".format(ymd)
    outrel = abspath + "/../ascii2d/{0}".format(ymd)
    out = os.path.abspath(outrel)
    
    if not os.path.exists(out):
        os.makedirs(out)
  
    outTuple = out+"/dumpst2.{0}.{1}.{2}.{3}.tuple.txt".format(cal, model, dstsrc, recon)
    outProf = re.sub("tuple", "prof", outTuple)
    outHist = re.sub("tuple", "hist", outTuple)
    hist_dump = os.path.join(os.path.abspath(os.path.curdir), 'dump_thrown.C')
    print(outTuple)
    print(outProf)
    
    try:
        foutT = open(outTuple, "w")
        foutP = open(outProf, "w")

        fin = open(dumpst, "r")
        for line in fin.readlines():
            foutT.write(line)
        fin.close()
        #print(foutT)
        #print(foutP)
        nnights = 0
        nfiles = 0

        thrown = defaultdict(int)
        for night in sorted(os.listdir(abspath)):
            if night[0] != "2":
                continue
            apath = abspath + "/" + night + "/ascii2d/" + recon
            if not os.path.exists(apath):
                print "{0} doesn't exist".format(apath)
                continue
            sys.stdout.write("\r{0}".format(apath))
            sys.stdout.flush()
            nnights += 1
            for dump in sorted(os.listdir(apath)):
                if dump.endswith("tuple.txt"):
                    #print("would add ({2}) {0} to {1}".format(os.path.basename(dump),os.path.basename(outTuple),night))
                    fdump = open(apath + "/" + dump, "r")
                    for line in fdump.readlines():
                        #print(line)
                        foutT.write(re.sub("(inf|nan)", "0", line))
                    fdump.close()
                    nfiles += 1
                elif dump.endswith("prof.txt"):
                    #print("would add ({2}) {0} to {1}".format(os.path.basename(dump),os.path.basename(outProf),night))
                    fdump = open(apath + "/" + dump, "r")
                    for line in fdump.readlines():
                        foutP.write(re.sub("(inf|nan)", "0", line))
                    fdump.close()
                    #nfiles+=1
            # look for ROOT files for thrown counts
            y, m, d = night[0:4], night[4:6], night[6:8]
            rpath = os.path.join(abspath, night, "trump", "y{}m{}d{}.rts.root".format(y, m, d))
            if os.path.exists(rpath):
                cmd = 'root -l -b -q "{}(\\"{}\\")"'.format(hist_dump, rpath)
                root_exe = sp.Popen(cmd, shell=True, stdout=sp.PIPE)
                for line in root_exe.stdout.readlines():
                    if not line.startswith('BIN'):
                        continue
                    _, bin_center, num_thrown = line.split()
                    thrown[bin_center] += int(num_thrown)

        foutT.close()
        foutP.close()

        if thrown:
            with open(outHist, "w") as out_hist:
                for bin, count in sorted(thrown.items(), key=lambda x: x[0]):
                    out_hist.write("{} {}\n".format(bin, count))
    except Exception as err:
        print("\nError creating {0}".format(outTuple))  
    print("\nRead {0} files from {1} nights.".format(nfiles, nnights))
