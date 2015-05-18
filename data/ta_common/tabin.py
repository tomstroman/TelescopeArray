import os
tdb = os.getenv('TADSTBIN')

dstdump = tdb + '/dstdump.run'
dstlist = tdb + '/dstlist.run'

tahome = os.getenv('TAHOME')
getTimeTable = tahome + '/getTimeTable/bin/getTimeTable.run'
tama = tahome + '/tama/bin/tama.run'