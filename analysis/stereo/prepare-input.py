# prepare-input.py
# Thomas Stroman, University of Utah, 2015-05-18
# This script reads one or more ASCII files produced by stereo-data processing
# and produces "ROOT Trees" for use with ROOT analysis programs.

# USAGE: Run this script in the directory where the ASCII files are located.

# We don't produce the trees directly, but produce ROOT scripts tailored to the
# specific filenames and inferred contents. We then run the scripts and attempt
# to verify that the output exists as expected.

# There are three types of ASCII output to be interpreted:
# 1. Data tuples, identified by ".tuple.txt" in the filename
# 2. Data profiles, identified by ".prof.txt"
# 3. Third-party profile-quality assessment, identified by ".prof.PRA.txt"

# Typically the first two types will be present. The third one (PRA) is the 
# output of "pattern-recognition analysis" algorithms developed by a colleague
# and applied to the data-profile files on a separate timetable, and as such,
# these files may not be present, especially for recently processed data.

# Some files may need to be combined or otherwise manipulated.

# Conventions established by convenience early in the development of analysis
# have a nasty habit of persisting in perpetuity. Some examples of that may
# appear below.

import os
import glob

etuples = sorted(glob.glob('dumpst2.*.tuple.txt'))

# expected filename format:
# dumpst2.(calib).(model).(source).(recon).tuple.txt
# only (calib) may contain periods.

# source contains exactly one of these words, but possibly extra characters.
# values are the abbreviation used in some existing ROOT programs.
species = {'nature': 'f',
           'mc-proton': 'g',
           'mc-iron': 'h',
           'mc-nitro': 'n',
           'mc-helium': 'he'}

# Contents of files and corresponding filename hints
names = {'Tuple': 'tuple', 'Prof': 'prof', 'PRA': 'prof.PRA'}

# Write this header (a string used by ROOT to interpret colums)
# to the PRA files.
pra_head = 'ymd:brid:lrid:mdid:btube:ltube:mbin:bstat:lstat:mstat:'
pra_head += 'bpra:lpra:mpra\n'

# Let's find out what kinds of information we have.

groups = {}

def format_pra(inl):
  '''
  Helper function to reformat "PRA" input files by combining
  four lines of input into one line of output. Takes a list
  as an argument and returns a list with 1/4 the elements.
  '''
  outbuf = []
  # Just replace newlines with spaces for first three inputs
  for i in range(0,len(inl),4):
    line = inl[i].replace('\n',' ')
    line += inl[i+1].replace('\n',' ')
    line += inl[i+2].replace('\n',' ')
    line += inl[i+3]
    outbuf.append(line)  
  return outbuf

  
# begin the main routine  
  
for etuple in etuples:  
  info = etuple.split('dumpst2.')[-1]
  fields = info.split('.')
  model,source,recon = fields[-5:-2]
  calib = '.'.join(fields[:-5])
  spec = [i for i in species if i in source][0]
  
  tag = '__'.join([calib,model,spec,recon])
  
  # files with common calib, model, spec, and recon 
  # will need to be combined.
  try:
    groups[tag].append((etuple,source))
  except KeyError:
    groups[tag] = [(etuple,source)]
  

# loop over all items in groups, combining files as needed,
# and preparing the list of files to process in ROOT.

to_process = {}

for tag,files in groups.items():

  to_process[tag] = []
  
  fields = tag.split('__')
  calib,model,recon = [fields[i] for i in [0,1,3]]
  
  
  infiles = []
  sources = []
  present = {contents: False for contents in names}
  
  for f in sorted(files,key=lambda i: i[0]):
    infiles.append(f[0])
    sources.append(f[1])

    # this is deliberately crude: the presence of any one file
    # guarantees that we'll attempt to combine all of them.

    for contents,name in names.items():
      fname = f[0].replace('tuple',name)
      if os.path.exists(fname):
        present[contents] = fname
    
  l = len(files)
  if l == 1:    # No combination is necessary
    to_process[tag] += [present[i] for i in present if present[i]]
    continue
    
    
  # We will separately combine tuple, prof, and PRA files.
  # Behavior for each type is slightly different. But rather than
  # reformatting PRA files here, now we just combine them and save
  # that step for later.
  
  
  
  for contents,name in names.items():
    
    if not present[contents]:
      continue
    
    outfile = '.'.join([calib,model,recon,contents,'_'.join(sources)])
    outfile += '.combined{0}.txt'.format(name)
    print('Now writing ' + outfile)
    
    present[contents] = outfile
    
    with open(outfile,'w') as outf:
      # tuple and PRA files will use this:
      skip_head = False 

      # assemble the output file in memory as list of lines
      outbuf = []
      
      for ftuple in infiles: 
        f = ftuple.replace('tuple',name)
        with open(f,'r') as infile:
          print('Reading from ' + f)
          inl = infile.readlines()
          
          # type-dependent behavior now
          if contents == 'Tuple':
            # pretty easy: concatenate but skip the first lines of
            # subsequent input files
            if not skip_head:
              outbuf.append(inl[0])
              skip_head = True
            for line in inl[1:]:
              outbuf.append(line)
          
          else: # prof or PRA files
            # easiest case: just concatenate
            outbuf += inl


      print('Writing {0} lines.'.format(len(outbuf)))
      outf.write('\n'.join(outbuf) + '\n')
      
  to_process[tag] += [present[i] for i in present if present[i]]

# now we know which files contain the information we want. Let's 
# group them according to the intermediate ROOT output (prior to
# final combination). We will group multiple sources (species).

root_batches = {}
for tag,files in to_process.items():
  tags = tag.split('__')
  
  # form tag from calib, model, recon
  cmr = '__'.join([tags[i] for i in [0,1,3]])
  
  for infile in files:
    sp = [species[i] for i in species if i in infile][0]
  
    try:
      root_batches[cmr][sp] = infile
    except KeyError:
      root_batches[cmr] = {sp: infile}
      
  
  

#'TTree *{0} = new TTree();\n'
#'{0}->ReadFile("{1}");\n'
#'TFile e("{0}");\n'




