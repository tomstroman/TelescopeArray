# kludge-stereo.py
# Thomas Stroman, University of Utah, 2015-05-31
# This code is here for reference. It's some of my earliest work in Python,
# which I embarked upon with two goals: translate an existing Bash script,
# and experiment with an object-oriented approach to an existing analysis
# chain.
# This monolithic code is only marginally easier to modify than the
# Bash script it replaced. I plan to write a new stereo analysis script
# that makes use of modules and the additional Python experience I've
# acquired since producing this, but I'm adding this to my code repository
# for reference (and will probably be able to reuse many of the functions).

import os
import sys
import glob
import re
import time

class night(object):
  """
  Class night
  """
  def __init__(self, nightpath):
    """
    Constructor for night class
    """

    self.__status = 0
    self.__abspath = os.path.abspath(nightpath)
    self.__geocal,self.__model,self.__dstsrc,self.__ymd = (
        self.__abspath.split('/')[-4:] )
    self.__relpath = '/'.join(self.__abspath.split('/')[-4:])
    self.__asciidir = self.__abspath + '/ascii/{0}-{1}'.format(
        tpname,mdname )
    self.__fullydone = self.__asciidir + '/COMPLETE'

    self.getDirectories()
    self.__nsites = self.countSites()
    self.__downlist = {}
    self.__nMatches = {}
    self.__matchlist = {}
    self.__matchlistcontent = {}
    self.__clflist = {}
    self.__nclf = {}
    self.__dstdone = {}
    
  @property  
  def ymd(self):
    return self.__ymd

  @property  
  def model(self):
    return self.__model

  @property  
  def dstsrc(self):
    return self.__dstsrc
  
  @property
  def geocal(self):
    return self.__geocal
    
  @property
  def nmatches(self):
    print self.__matchlist
    return self.__nMatches
    
  @property
  def nclf(self):
    return self.__nclf
  
    
  @property
  def printDirectories(self):
    print 'Absolute path: ' + self.__abspath
    print 'Output directory: ' + self.__outdir
    print 'Data source directory: '+self.__datadir
    print self.__sitedir
    return self.__nsites

  @property  
  def complete(self):
    return os.path.exists(self.__fullydone)
    
  def getDirectories(self):
    self.__outdir = stereoRoot + '/' + self.__relpath
    
    if self.__dstsrc == 'nature':
      self.__srcdir = fdplaneDataDir
      self.__datadir = ( stereoRoot + 
          '/' + self.__geocal+'/tafd-data/'+self.__ymd )
    else:
      self.__srcdir = '/'.join(self.__outdir.split('/')[0:-1])
      self.__datadir = self.__outdir
    
    self.__sitedir = {}
    
  @property
  def nsites(self):
    return self.__nsites
    
  def countSites(self):
    nsites = 0
    for siteid in siteids:
      sitedir=self.__srcdir + ( 
          '/{0}/{1}'.format(sitename[siteid],self.__ymd) if          
          self.__dstsrc == 'nature' else 
          '/{0}/trump/{1}'.format(self.__ymd,sitename[siteid]) )
      #print 'Checking for ' + sitedir
      if os.path.exists(sitedir):
        self.__sitedir[sa[siteid]] = sitedir
        nsites += 1      
    return nsites
  
  def createDownList(self,site):
    def createBRLRDownList(site):
      dstfiles = ' '.join(
          sorted(glob.glob(self.__sitedir[site]+'/*.down.dst.gz')))
      dump = os.popen('{0} -{1}plane {2}'.format(dstdump,site,dstfiles),'r')
      n = {}
      for line in dump.readlines():
        if 'Part' in line:
          sline = line.split()
          t = hms2sec(sline[1])
          p = int(sline[4])
          if p not in n:
            n[p] = 0
          n[p] += 1
          e = int(sline[6])
          continue
        elif 'Angular' in line:
          l = line.split()[-1]
          buf.append([t,l,p,n[p]-1,e])
      dump.close()
          
    def createMDDownList():
      for dstfile in sorted(
          glob.glob(self.__sitedir['md'] + '/*.down.dst.gz')):      
        pp = os.path.basename(dstfile)[12:14]
        dump = os.popen('{0} -hraw1 -stpln {1}'.format(dstdump,dstfile),'r')
        n = 0
        new_event = False
        for line in dump.readlines():
          if 'stat' in line:
            t = (hms2sec(line.split()[3]) + 43200) % 86400
            new_event = True
          elif 'tracklength' in line and new_event:  
            l = line.split()[-1]
            n += 1
            buf.append([t,l,pp,n-1,n])
            new_event = False
        dump.close()
            
    buf = [] # save results to in-memory buffer; write all at once later
    if site == 'md':
      createMDDownList()
    else:
      createBRLRDownList(site)        
      
    # now open and write the complete file all at once  
    dl = open(self.__downlist[site],'w')
    for b in buf:
      dl.write('{0:.9f} {1} {2} {3} {4}\n'.format(b[0],b[1],b[2],b[3],b[4]))
    dl.close()
    

  def prepMono(self):
    for site in self.__sitedir:
      self.__downlist[site] = ( 
          self.__sitedir[site] + 
          '/downlist-{0}-{1}.txt'.format(self.__ymd,sa.index(site)) )
      if not os.path.exists(self.__downlist[site]):
        print "Creating " + self.__downlist[site]
        self.createDownList(site)
    
  def getMatches(self):
    def scan2DownFiles():
      print matches
      dl0 = open(self.__downlist[psites[inps][0]],'r').readlines()      
      dl1 = open(self.__downlist[psites[inps][1]],'r').readlines()
      
      k = 0
      for line0 in dl0:
        t0 = float(line0.split()[0])
        l = k
        for line1 in dl1[k:]:
          l += 1
          t1 = float(line1.split()[0])
          if abs(t0 - t1) < stereoCoincidenceWindow:
            k = l
            buf.append(' '.join([line0.strip(),line1.strip()]))
            break
          if (t1 - t0) > 2*stereoCoincidenceWindow:
            break    
    
    def scan2MatchFiles():
      print matches
      
      bmmatch = open(self.__matchlist['bm'],'r').readlines()      
      lmmatch = open(self.__matchlist['lm'],'r').readlines()

      
      k = 0
      for bmline in bmmatch:
        mline=' '.join(bmline.split()[5:10])
        l = k
        for lmline in lmmatch[k:]:
          l += 1
          if mline in lmline:
            k = l
            buf.append(
                ' '.join([' '.join(bmline.split()[0:5]),lmline.strip()]))
            break
            
    def removeTriples(pair,triples):
      buf = open(self.__matchlist[pair],'r').readlines()
      
      for triple in triples:
        t = triple.split()
        #print '{0} {1}'.format(pair,psites[pair])
        i0 = 5*sa.index(psites[pair][0])
        i1 = 5*sa.index(psites[pair][1])                
        event0 = ' '.join(t[i0:i0+5])
        event1 = ' '.join(t[i1:i1+5])
        line = event0 + ' ' + event1 + '\n'
        try:
          buf.remove(line)
          self.__matchlistcontent[pair].remove(line)
        except:
          print 'failed to remove {0} from {1}'.format(line,buf)
      
      fm = open(self.__matchlist[pair],'w')
      for b in buf:
        fm.write(b)
      fm.close()
    
    for inps in nps:

      odir = self.__datadir + '/' + inps
      matches = odir + '/matches.txt'

      if os.path.exists(matches):
        #print 'Found ' + matches
        self.__matchlist[inps] = matches
        self.__matchlistcontent[inps] = open(matches,'r').readlines()
        self.__nMatches[inps] = len(self.__matchlistcontent[inps])
        continue

      if inps in nps[0:-1]:
        if not (psites[inps][0] in self.__downlist and
                psites[inps][1] in self.__downlist):
          continue
        self.__matchlist[inps] = matches
        buf = []
        
        scan2DownFiles()
        
        os.system('mkdir -p ' + odir)
        
        fm = open(matches,'w')
        self.__matchlistcontent[inps] = []
        for b in buf:
          self.__matchlistcontent[inps].append(b + '\n')
          fm.write(b + '\n')
        fm.close()
        self.__nMatches[inps] = len(self.__matchlistcontent[inps])
        
      else:
        if self.__nsites != 3:
          continue
        
        os.system('mkdir -p ' + odir)
        self.__matchlist[inps] = matches
        noTriples = False
        self.__matchlistcontent[inps] = []        
        for pair in nps[0:-1]:
          if pair not in self.__nMatches or self.__nMatches[pair] == 0:
            noTriples = True
            self.__nMatches[inps] = 0
            open(matches,"w").close()
            break
        else:
          # search the BRM/MD list for events also in LR/MD
          buf = []
           
          scan2MatchFiles()
          
          fm = open(matches,'w')
          
          for b in buf:
            fm.write(b + '\n')
            self.__matchlistcontent[inps].append(b + '\n')
          fm.close()
          self.__nMatches[inps] = len(self.__matchlistcontent[inps])
          for pair in nps[0:-1]:
            self.__nMatches[pair] -= self.__nMatches['blm']
            removeTriples(pair,buf)

  def removeCLF(self):
    #print 'About to search match lists (qty: {0}) for CLF'.format(len(self.__matchlist))
    for pair in self.__matchlist:
      self.__clflist[pair] = os.path.dirname(self.__matchlist[pair])+'/rejectclf.txt'

      # if the file exists, count its lines
      try: 
        self.__nclf[pair] = len(open(self.__clflist[pair]).readlines())
        #print 'Found '+self.__clflist[pair]

      except IOError: 
      # file does not exist, so let's create it
        matches = open(self.__matchlist[pair],'r').readlines()
        buf = []
        
        for line in matches:        
          if isCLF(line.split()[0]):
            buf.append(line)
            
        for line in buf:    
          matches.remove(line)
           
        fm = open(self.__matchlist[pair],'w')
        for m in matches:
          fm.write(m)
        fm.close()
        
        fc = open(self.__clflist[pair],'w')
        for b in buf:
          fc.write(b)
        fc.close()
        
        self.__nclf[pair] = len(buf)
        self.__nMatches[pair] -= self.__nclf[pair]
  
  def getEventFiles(self):    
    def populatePositions(matchlist):
      matchnum = 0      
      for line in open(matchlist,'r').readlines():
        i0 = 0
        for site in psites[inps]:
          sline = line.split()[i0:i0+5]
          indst = self.__sitedir[site] + ( 
              '/y{0}m{1}d{2}p{3:02d}.down.dst.gz'.format(
                  self.__ymd[0:4],self.__ymd[4:6],self.__ymd[6:8],
                  int(sline[2])) )
          event = [inps,'{0}-{1:05d}'.format(site,matchnum)]
          evpos = int(sline[3])
          try:
            positions[indst][evpos] = event
          except KeyError:
            positions[indst] = {evpos: event}
          i0 += 5
        matchnum += 1      
    
    def splitDST(dst):
      odir = os.path.dirname(dst)
      outputbase = odir+'/tmpdst'
      wlist = odir + '/wantlist-' + os.path.basename(dst) + '.txt'
      fwlist = open(wlist,'w')
      outnum = 0
      cmd = []
      for pos in sorted(positions[dst]):
        fwlist.write('{0}\n'.format(pos)) 
        source = '{0}-{1:05d}.dst.gz'.format(outputbase,outnum)
        destination = '{0}/{1}/{2}.dst.gz'.format( self.__datadir,
            positions[dst][pos][0], positions[dst][pos][1] )
        cmd.append('mv {0} {1}'.format(source, destination))
        outnum += 1
      fwlist.close()      
      os.system(dstsplit + ' -w {0} -ob {1} {2}'.format(wlist,outputbase,dst))
      for c in cmd:
        os.system(c)    
      os.remove(wlist)
      
      
    positions = {}    
    for inps in self.__matchlist:
      self.__dstdone[inps] = (
          os.path.dirname(self.__matchlist[inps]) + '/dstdone.txt' )
      if os.path.exists(self.__dstdone[inps]):
        continue
      populatePositions(self.__matchlist[inps])  
    for dst in sorted(positions):
      splitDST(dst)    
    for inps in self.__dstdone:
      open(self.__dstdone[inps],'w').close()
      
  def getStereoGeometry(self):
    def isFlash(dst):
      sigma = [[],[]] # bad tubes, good tubes      
      for line in os.popen(
          dstdump + ' +brplane +lrplane ' + dst,
          'r' ).readlines():
        sline = line.split()
        if len(sline) != 21:
          continue
        sigma[int(sline[18]) == 1].append(float(sline[16]))        
      sigma[1].sort(reverse=True)
      #print sigma
      nGood = len(sigma[1])
      try:
        maxGood = sigma[1][0]      
      except IndexError:
        return False
      nHigherBad = 0
      for bad in sigma[0]:
        nHigherBad += (bad > maxGood)        
      return (nHigherBad > nGood)    
      
    def runMDPlane(dst):
      bn = os.path.basename(dst)
      os.system('{0} -geo {1} -d {2} {3} > {4}.out 2> {4}.err'.format(
          mdplane, geo[sa.index('md')], txtdir, dst,
          txtdir + '/' + re.sub('dst.gz','pln',bn) ))

      mdpdst = re.sub('dst','down.dst',bn)
      os.system('mv {0}/{1} {2}'.format(txtdir,mdpdst,dst))
      if self.__dstsrc == 'nature':
        os.system('cp {0} {1}/{2}'.format(dst,self.__datadir,inps))      
      
    def runSTPlane(dst0,dst1,i0,i1):
      bn = txtdir + '/' + re.sub('dst.gz','spln',os.path.basename(dst0)) 
      os.system('{0} {1} {2} {3} {4} > {5}.out 2> {5}.err'.format(
          stplane, dst0, dst1, geo[sa.index(psites[inps][i0])],
          geo[sa.index(psites[inps][i1])],  bn ))
      return bn
      
    def renameGeometry(outbn,pair,dst0,dst1):        
      for txt in ['out','err']:
        os.system('mv {0}.{1} {2}.{1}'.format(
            outbn, txt, re.sub('spln',pair+'.spln',outbn) ))
      for dst in [dst0,dst1]:
        spln = re.sub('dst','spln.dst',dst)
        os.system('mv {0} {1}'.format(
            spln, re.sub('spln',pair+'.spln',spln) ))        


        
              
    for inps in self.__dstdone:
      odir = self.__outdir + '/' + inps
      stpdone = odir + '/stpdone.txt'
      
      if os.path.exists(stpdone):
        continue
      txtdir = odir + '/output'
      
      if self.__dstsrc == 'nature':
        os.system('mkdir -p ' + odir)
        for dst in sorted(glob.glob(self.__datadir + '/' + 
            inps + '/*[0-9].dst.gz' )):
          os.system('cp -v {0} {1}'.format(dst,odir))
      
      os.system('mkdir -p ' + txtdir)
      
      dst0s = glob.glob('{0}/{1}-*[0-9].dst.gz'.format(odir, 
          psites[inps][0] ))
      
      #print dst0s
      
      for dst0 in sorted(dst0s):
        dst1 = os.path.dirname(dst0) + '/' + re.sub(
            psites[inps][0],psites[inps][1],os.path.basename(dst0) )
        if isFlash(dst0) or isFlash(dst1):
          print 'flash detected; skipping ' + dst0
          continue

        if psites[inps][1] == 'md':
          runMDPlane(dst1)
            
        outbn = runSTPlane(dst0,dst1,0,1)
        
        if inps == 'blm':      
          renameGeometry(outbn,'bl',dst0,dst1)
          
          dst2 = re.sub(psites[inps][0],psites[inps][2],dst0)
          runMDPlane(dst2)
          
          renameGeometry(runSTPlane(dst0,dst2,0,2),'bm',dst0,dst2)
      
          renameGeometry(runSTPlane(dst1,dst2,1,2),'lm',dst1,dst2)
          
        print dst0
        
      if self.__dstsrc == 'nature':
        for origdst in glob.glob(odir + '/*[0-9].dst.gz'):
          os.remove(origdst)
          
      open(stpdone,'w').close()    
  
  def sanityCheck(self):
    def checkDuration(dst,pair):
      duration = [] # expect 4 entries
      for line in os.popen('{0} {1} -stplane {2}'.format(
          dstdump, dumpbanks[pair], dst )).readlines():
        if 'uration' in line:
          duration.append(float(line.split()[-1]))
      try:
        p = duration[0]*duration[1]/(duration[2]*duration[3])
      except ZeroDivisionError:
        print 'Warning: bad durations in ' + dst
        p = 0
      return [p,(duration[2] > 0 and duration[3] > 0 and p > 0.5)]
      
    def getBestGeometry():
      sdpa = {} 
      for pair in nps[0:-1]:
        splnout = txtdir + '/{0}-{1}.{2}.spln.out'.format(
            psites[pair][0], evnum, pair )
        for line in open(splnout,'r').readlines():
          if 'n dot n' in line:
            angle = float(line.split()[-1])
            sdpa[pair] = [angle, abs(angle - 90.)]
            break

      bestpair = 'bl'
      bestsdpa = sdpa['bl'][0]
      bestdist = sdpa['bl'][1]

      if not sdpa['bl'][0] < maxBLsdpa:
        for pair in ['bm','lm']:
          if sdpa[pair][1] < bestdist:
            bestsdpa = sdpa[pair][0]
            bestdist = sdpa[pair][1]
            bestpair = pair
      #print sdpa
      #print '{0} {1} {2}'.format(bestpair,bestsdpa,bestdist)
      return bestpair      
      
    def buildTripleSTPLANE():
      rmfiles = [beststplane] # temporary files to create and remove
      stripcmd = dststrip
      for line in os.popen(dstlist + ' ' + dst0best,'r').readlines():
        if ',' in line:
          for bank in line.split():
            if 'stplane' not in bank:
              stripcmd += ' -{0}'.format(bank.split(',')[0])
      os.system(stripcmd + ' {0} -f -o {1}'.format(dst0best,beststplane))
      tempdst = {}
      srcpair = {'br': 'bl', 'lr': 'bl', 'md': 'bm'}
      gooddst = {}

      
      for site in sa:
        tempdst[site] = odir + '/{0}-{1}-temp.dst.gz'.format(site,evnum)
        gooddst[site] = odir + '/{0}-{1}.spln.dst.gz'.format(site,evnum)
        stdsts.append(gooddst[site])
        cmd = dststrip + ( ' -stplane -f -o {0} ' +
            '{1}/{2}-{3}.{4}.spln.dst.gz' ).format(
                tempdst[site], odir, site, evnum, srcpair[site] ) 
        print cmd
        os.system(cmd )
      ibest = nps.index(bestpair)
      os.system(spectator + ' {0} {1} {2}'.format(beststplane, 
          geo[ibest],'{0}/{1}/{2}-{3}.dst.gz'.format(
              self.__datadir,inps,sa[ibest],evnum ) ))
      specout = re.sub('dst','3pln.dst',beststplane)
      rmfiles.append(specout)
      for site in sa:
        os.system(dstsum + ' -f -o {0} {1} {2}'.format(
            gooddst[site],tempdst[site],specout ))
        rmfiles.append(tempdst[site])
      
      for rmfile in rmfiles:
        os.remove(rmfile)
      
    print ( 'Will check for sane event geometry here.' +
            ' Also choose best geometry when 3 sites involved.')

    for inps in self.__dstdone:
      odir = self.__outdir + '/' + inps
      sanedone = odir + '/sanedone.txt'      
      if os.path.exists(sanedone):
        continue
      
      txtdir = odir + '/output'
      dst0s = glob.glob('{0}/{1}-*spln.dst.gz'.format(odir, 
          psites[inps][0] ))
      for dst0 in sorted(dst0s):
        dst1 = os.path.dirname(dst0) + '/' + re.sub(
            psites[inps][0],psites[inps][1],os.path.basename(dst0) )

        if inps != 'blm':
          ratio,good = checkDuration(dst0,inps)
          stdsts = [dst0, dst1]
        else:
          bn = os.path.basename(dst0)
          if '.bl.' not in bn: # don't want to triple the work needlessly
            continue
          evnum = bn[3:8]
          beststplane = odir + '/st-{0}.dst.gz'.format(evnum)

         
          bestpair = getBestGeometry()
          dst0best = odir + '/{0}-{1}.{2}.spln.dst.gz'.format(
              psites[bestpair][0],evnum,bestpair )
          ratio,good = checkDuration(dst0best,bestpair)
          stdsts = []
          buildTripleSTPLANE()
          
        if good:  
          for line in os.popen(dstdump + ' -stplane ' + stdsts[0],
              'r' ).readlines():
            if 'Zenith' in line:
              zenith = float(line.split()[-1])
              break
          if (zenith < maxstzen):
            print ('Advancing {0} (ratio: {1} is good and zenith:' +
                '{2} is good' ).format(stdsts[0],ratio,zenith)
            for dst in stdsts:
              os.system('mv {0} {1}'.format(
                  dst, re.sub('spln','spln.sane',dst) ))
          else:
            print 'Rejecting {0}: bad zenith: {1}'.format(stdsts[0],zenith)
        else:
          print 'Rejecting {0}: bad ratio: {1}'.format(stdsts[0],ratio)
      
      open(sanedone,'w').close()
      
  def reconstructProfiles(self,retry_missing=False):
    def reconstructProfile(dst):
      def reconstructMDProfile(dst):
        outdst = dst.replace('sane.dst','sane.{0}-pfst.dst'.format(mdname))
        if os.path.exists(outdst):
          return 0
        hctimdst = dst.replace('sane.dst','sane.hctim.dst')
        cmd = hctim + ' ' + dst + ' ' + hctimdst
        os.system(cmd)


        tout = txtdir + '/{0}.{1}-pfst.out'.format(bn[0:-7],mdname)
        terr = tout.replace('pfst.out','pfst.err')
        cmd = ('mosrun -q40 -b -l -m3072 -e {0} -det 34 -db -fit 3 ' + 
            '-o {1} {2} > {3} 2> {4} &' ).format(
            stpfl,outdst,hctimdst,tout,terr )
        #print cmd
        os.system(cmd)
        return 1
        
        
      def reconstructBRLRProfile(dst,site):
        outdst = dst.replace('sane.dst','sane.{0}-tbst.dst'.format(tpname))
        if os.path.exists(outdst):
          return 0
        evnum = bn[3:8]        
        partpos = 2 + 5*psites[inps].index(site)
        matchline = self.__matchlistcontent[inps][int(evnum)]
        pedfile = fdpedpath + '/{0}/{1}/y{2}m{3}d{4}p{5:02d}'.format(
            sitename[sa.index(site)],self.__ymd,
            self.__ymd[0:4],self.__ymd[4:6],self.__ymd[6:8],
            int(matchline.split()[partpos]) ) + '.ped.dst.gz'
        if not os.path.exists(pedfile):
          pedfile = caldir + '/fdped/{0}/y{1}m{2}d{3}.ped.dst.gz'.format(
              sitename[sa.index(site)],
              self.__ymd[0:4], self.__ymd[4:6], self.__ymd[6:8] )
              
        gainfile = caldir + '/fdpmt_gain/pmtGainDSTBank.{0}.dst.gz'.format(
            self.__ymd[0:6] )
        
        mirfile = caldir + '/fdmirror_ref/mirrorDSTBank.{0}.dst.gz'.format(
            self.__ymd[0:4] )

        tout = txtdir + '/{0}.{1}-tbst.out'.format(bn[0:-7],tpname)
        terr = tout.replace('tbst.out','tbst.err')
        cmd = ('mosrun -q40 -b -l -m3072 -e {0} -o {7} -st -raw {1} -geo {2} ' +
            '-force_{3} -pmtcal {4} -pmtgain {5} -mirref {6} ' +
            '{8} > {9} 2> {10} &').format(fdtp, rawindex, 
                geo[sa.index(site)], site, pedfile, gainfile, mirfile,
                outdst, dst, tout, terr )
        #print cmd
        os.system(cmd)
        return 1

               
                
      site = os.path.basename(dst)[0:2]
      bn = os.path.basename(dst)
      if site == 'md':        
        self.__submitted += reconstructMDProfile(dst)
      else:
        self.__submitted += reconstructBRLRProfile(dst,site)
      

    print 'Reconstruct profiles here.'
    self.__submitted = 0
    for inps in self.__dstdone:
      odir = self.__outdir + '/' + inps
      profdone = odir + '/profdone-{0}-{1}.txt'.format(tpname,mdname)
      if os.path.exists(profdone) and not retry_missing:
        continue
      txtdir = odir + '/output'
      dst0s = glob.glob(odir + '/{0}*.spln.sane.dst.gz'.format(
          psites[inps][0] ))
      for dst0 in sorted(dst0s):
        suffix = os.path.basename(dst0)[2:]
        for site in psites[inps]:
          dst = odir + '/{0}{1}'.format(site,suffix)
          reconstructProfile(dst)
    
      open(profdone,'w').close()
    if self.__submitted > 0:
      print "Submitted {0} job(s) to queue; re-run when complete.".format(
          self.__submitted )
      sys.exit()
      
  def dumpASCII(self):
    def checkRunning(dst):
      for line in runningnow:
        if dst in line:
          return [line.split()[i] for i in [0,4]]
      else:
        return False
    def dumpEvent(dst0):
      def outputPresent(dst):
        if site == 'md':
          outdst = dst.replace('sane.dst','sane.{0}-pfst.dst'.format(mdname))
          tout = txtdir + '/{0}.{1}-pfst.out'.format(bn[0:-7],mdname)
          terr = tout.replace('pfst.out','pfst.err')                    
        else:
          outdst = dst.replace('sane.dst','sane.{0}-tbst.dst'.format(tpname))
          tout = txtdir + '/{0}.{1}-tbst.out'.format(bn[0:-7],tpname)
          terr = tout.replace('tbst.out','tbst.err')
        present = [ os.path.exists(outdst),
                    os.path.exists(tout),
                    os.path.exists(terr) ]
        #print present
        if present != [1,1,1]:
          runpid = checkRunning(outdst)
          if runpid > 0:
            print '{0} is being produced by PID {1}; skipping event'.format(
                os.path.basename(outdst),runpid )
          else:
            print 'Error: missing output files from profile reconstruction.'
            if not present[0]:
              print outdst
            if not present[1]:
              print tout
            if not present[2]:
              print terr
            if retry_missing:
              print 'Retrying reconstruction on ' + dst
              self.reconstructProfiles(retry_missing=True)

          
          return False
        #print 'Found the output.'
        nfail = 0
        outEvents = -1
        if site == 'md':
          for line in open(terr,'r').readlines():
            if 'Events successfully processed' in line:
              outEvents = int(line.split()[0])
        else:
          for line in open(terr,'r').readlines():
            if 'not found' in line:
              nfail += 1
            if 'Events out' in line:
              outEvents = int(line.split()[-1])
              
        if outEvents != 1:
          print 'Error! Failed output count verification in ' + terr
          return False
        if nfail > 0:
          print 'Warning! Not-found error in ' + terr
          return False
        
        return outdst
        
      def mergeOutputs(dst):  
        # check whether a BR-LR merge is necessary.
        # use numeric site indices and the structure of "sa"
        for i in [0,1]:
          if sa[i] not in dst:
            # the other site must be present to have gotten this far.
            out = dst[sa[1-i]]
            break
        else:
          out = odir + '/st-{0}.{1}-tbst.dst.gz'.format(evnum,tpname)
          if not os.path.exists(out):
            cmd = eventmerge + ' {0} {1} {2}'.format(dst['br'],dst['lr'],out)
            os.system(cmd)
        
        if 'md' in dst:
          united = out.replace('.dst','.md.dst')
          if not os.path.exists(united):
            stripcmd = dststrip
            for line in os.popen(dstlist + ' ' + dst['md'],'r').readlines():
              if ',' in line:
                for bank in line.split():
                  if 'prfc' not in bank and 'hcbin' not in bank:
                    stripcmd += ' -{0}'.format(bank.split(',')[0])
            prfc = odir + '/prfc-temp.dst.gz'                        
            os.system(stripcmd + ' {0} -f -o {1}'.format(dst['md'],prfc)) 
            
            stripcmd = dststrip
            psource = dst['md'].replace(mdname + '-pfst.','')
            for line in os.popen(dstlist + ' ' + psource,'r').readlines():
              if ',' in line:
                for bank in line.split():
                  if 'fdplane' not in bank:
                    stripcmd += ' -{0}'.format(bank.split(',')[0])
            plane = odir + '/plane-temp.dst.gz'
            os.system(stripcmd + ' {0} -f -o {1}'.format(psource,plane))
            
            cmd = dstsum + ' -f -o {0} {1} {2} {3}'.format(
                united,out,plane,prfc )
            os.system(cmd)
            
            os.remove(prfc)
            os.remove(plane)
        else:
          united = out          
        return united  
        
      suffix = os.path.basename(dst0)[2:]
      #print suffix
      evnum = suffix[1:6]  
      dst = {}
      for site in psites[inps]:
        #print site
        dst[site] = odir + '/{0}{1}'.format(site,suffix)
        bn = os.path.basename(dst[site])
        #print dst[site]
        dst[site] = outputPresent(dst[site])
        if not dst[site]:
          del dst[site]
          return False    

      eventfile = mergeOutputs(dst)
      print eventfile     
      core = 'n{0}.{1}.{2}-{3}'.format(
          nps.index(inps),os.path.basename(eventfile)[0:8],tpname,mdname )
      txtprefix = self.__asciidir + '/' + core
      txttuple = txtprefix + '.tuple.txt'
      txtprof = txtprefix + '.prof.txt'
      if not (os.path.exists(txttuple) and os.path.exists(txtprof)):
        os.system('{0} {1} > {2}'.format(dumpst,eventfile,txttuple))
        os.system('{0} {1} > {2}'.format(dumpster,eventfile,txtprof))
      
      return True
      
    print 'Dump to ASCII files here.'
    """ 
    Steps to completion:
    1. Verify all expected output files are present.
    2. If missing, check for running processes.
    3. Combine relevant output files
    4. Dump to profile and tuple files
    """
    #runningnow = os.popen('mosq listall','r').readlines()
    
    os.system('mkdir -p ' + self.__asciidir)
    

              
    complete = True
    for inps in self.__dstdone:
      odir = self.__outdir + '/' + inps
      dumpdone = odir + '/dumpdone-{0}-{1}-{2}.txt'.format(
        dumprevision,tpname,mdname)
      if os.path.exists(dumpdone):
        continue
      txtdir = odir + '/output'
      finished = True
      

      
      dst0s = glob.glob(odir + '/{0}*.spln.sane.dst.gz'.format(
          psites[inps][0] ))
          
      for dst0 in sorted(dst0s):
        finished *= dumpEvent(dst0)
      
      if finished:
        open(dumpdone,'w').close()
      complete *= finished
      
    if complete:
      open(self.__fullydone,'w').close()
def hms2sec(hmstimestr):
  time=hmstimestr.split(':')
  if len(time) != 3:
    return -1
  return 3600*float(time[0]) + 60*float(time[1]) + float(time[2])
  
def isCLF(sectimestr):
  ss,ns = sectimestr.split('.')[0:2]
  s18 = int(ss) % 1800
  return (ns[1:3]=='00' and (s18 < 32 or s18 >= 1797))

retry_missing = False
if 'retry' in sys.argv:
  retry_missing = True
  sys.argv.remove('retry')


  
if len(sys.argv) != 2:
  print "Usage: {0} path/to/night".format(sys.argv[0])
  sys.exit()
#positions = {}
target = os.path.abspath(sys.argv[1])


#model,dstsrc,ymd=target.split('/')[-3:]






## set up
tpname = 'ghdef'
#tpname = 'width0'
#tpname = 'width1'
#mdname = 'mddef'
mdname = 'mdghd'
dumprevision = 1
rawindex = 1
sitename = ['black-rock','long-ridge','middle-drum']
stereoCoincidenceWindow = 0.002 # 2 milliseconds
maxstzen = 82.0
maxBLsdpa = 150.0
siteids = [0,1,2]
sa = ['br','lr','md'] # site abbreviation
nps = ['lm','bm','bl','blm']
psites = ( {'lm': ['lr','md'],'bm': ['br','md'],
    'bl': ['br','lr'],'blm': ['br','lr','md']} )
planebank = {'br': 'BRPLANE', 'lr': 'LRPLANE', 'md': 'FDPLANE'}
stereoRoot = '/scratch/tstroman/stereo'


fdplaneDataDir = '/scratch/tstroman/mono/fdplane_cal1.4_joint_20141014'
geo = ( ['$RTDATA/fdgeom/geobr_joint.dst.gz',
         '$RTDATA/fdgeom/geolr_joint.dst.gz',
         '$RTDATA/fdgeom/geomd_20131002.dst.gz'] )
dumpbanks = { 'bl': '-brplane -lrplane',
              'bm': '-brplane -fdplane',
              'lm': '-lrplane -fdplane'}         

caldir = os.getenv('RTDATA') + '/calibration/cal_1.4'
fdpedpath = '/scratch1/fdpedv'
altfdpedpath = caldir + '/fdped'              

tahome = os.getenv('TAHOME')
tadstbin = os.getenv('TADSTBIN')
exe = []
dstdump = tadstbin + '/dstdump.run'
exe.append(dstdump)
dstsplit = tadstbin + '/dstsplit.run'
exe.append(dstsplit)
dstlist = tadstbin + '/dstlist.run'
exe.append(dstlist)
dststrip = tadstbin + '/dststrip.run'
exe.append(dststrip)
dstsum = tadstbin + '/dstsum.run'
exe.append(dstsum)
stplane = tahome + '/stplane/bin/stplane.run'
exe.append(stplane)
mdplane = tahome + '/fdplane/bin/mdplane.run'
exe.append(mdplane)
spectator = tahome + '/stplane/bin/spectator.run'
exe.append(spectator)  
eventmerge = tahome + '/eventmerge/bin/eventmerge.run'
exe.append(eventmerge)
hctim = tahome + '/stplane/bin/export_hctim.run'
exe.append(hctim)
#stpfl = os.getenv('HOME') + ('/zz/UTAFD-LowGain/LowGain/build/std-build/' +
    #'bin/stpfl12_main')
#exe.append(stpfl)


today = night(target)

if today.complete:
  #print target
  sys.exit()

modelbin = stereoRoot + '/{0}/{1}/bin'.format(today.geocal,today.model)
fdtp = modelbin + '/{0}-fdtubeprofile.run'.format(tpname)
exe.append(fdtp)
dumpst = modelbin + '/dumpst.run'
exe.append(dumpst)
dumpster = modelbin + '/dumpster.run'
exe.append(dumpster)
stpfl = modelbin + '/stpfl12_main'
exe.append(stpfl)

for executable in exe:
  if not os.path.exists(executable):
    print 'Fatal error: {0} does not exist'.format(executable)
    sys.exit()
    
if today.nsites < 2:
  print "Fewer than 2 site directories; exiting"
  sys.exit()
  
today.prepMono()

today.getMatches()

today.removeCLF()   

today.getEventFiles()

today.getStereoGeometry()

today.sanityCheck()

runningnow = os.popen('mosq listall','r').readlines()
# PID is signed short int so mosrun fails if too many processes are queued.
# We can just wait for a while. Try again in a minute.
while len(runningnow) > 28800:
  print 'Too many queued jobs ({0}); waiting 60 seconds.'.format(
      len(runningnow))
  time.sleep(60)
  runningnow = os.popen('mosq listall','r').readlines()
  

today.reconstructProfiles()

today.dumpASCII()
