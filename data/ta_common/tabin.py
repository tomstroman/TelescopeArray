import os
tdb = os.getenv('TADSTBIN')

dstdump = tdb + '/dstdump.run'
dstlist = tdb + '/dstlist.run'
dstsplit = tdb + '/dstsplit.run'
# not an executable, but the stderr expected of every(?) dst operation
dststderr = ' $$$ dst_get_block_ : End of input file reached\n'

tahome = os.getenv('TAHOME')
fdplane = tahome + '/fdplane/bin/fdplane.run'
getTimeTable = tahome + '/getTimeTable/bin/getTimeTable.run'
mdplane = tahome + '/fdplane/bin/mdplane.run'
rtsparser = tahome + '/trump/bin/rtsparser.run'
tama = tahome + '/tama/bin/tama.run'



