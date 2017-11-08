import os
import re
from make_evt import make_evt

def prep_md_sim(rts):
    evt, num_events = _make_evt(rts)
    if num_events > 0:
        md_in = make_in(evt)
        md_dir = prepare_path(evt)
    else:
        md_in = None
        md_dir = None
    return md_in, md_dir

def _make_evt(rts):
    evt = rts.replace('.rts', 'p00.txt_md.evt')
    num_events = make_evt(rts, evt)
    return evt, num_events

def make_in(evt):
    md_in = evt.replace('txt_md.evt', 'txt_md.in')
# get YYYYMMDD from yYYYYmMMdDDp00.txt_md.evt
    ymd = ''.join(
        re.findall(
            'y([0-9]{4})m([0-9]{2})d([0-9]{2})p00\.txt_md\.evt',
            os.path.basename(evt)
        )[0]
    )
    in_contents  = 'output file:  ./foo.out\n'
    in_contents += '            setNr:  {}00\n'.format(ymd)
    in_contents += '           use DB:  YES\n'
    in_contents += '            iseed:  -8111111\n'
    in_contents += '         detector:  ta_md.conf\n'
    in_contents += '     shift origin:  NO\n'
    in_contents += '             nevt:  1\n'
    in_contents += '       event type:  MC_SHOWER\n'
    in_contents += ' \n'
    with open(md_in, 'w') as infile:
        infile.write(in_contents)
    print 'created', md_in
    return md_in

def prepare_path(evt):
    md_dir = os.path.join(os.path.dirname(evt), 'middle-drum')
    if not os.path.isdir(md_dir):
        os.mkdir(md_dir)
    return md_dir

