# query_stellarium.py
# Thomas Stroman, University of Utah, 2017-02-07
# Extremely special-purpose script, designed to run on a specific virtual machine
# with the host system running Stellarium (stellarium.org), with its remote
# control server interface active and visible to the VM on 192.168.56.1:8090

import httplib
import urllib
import json
import re
import sys

import argparse

def query(jdate, object_name):
    server = '192.168.56.1:8090'
    conn = httplib.HTTPConnection(server)
    try:
      conn.request('GET', '/api/main/status')
      response = conn.getresponse()
    except:
      print 'Stellarium server not detected!'
      sys.exit(1)
      

    # Set the time where we want it and pause it there
    params = urllib.urlencode({'timerate': 0, 'time': jdate})
    conn.request('POST', '/api/main/time', params)
    response = conn.getresponse()
    assert response.status == 200

    # search for the object we want -- and make sure we got results
    params = urllib.urlencode({'str': object_name})
    conn.request('GET', '/api/objects/find', params)
    response = conn.getresponse()
    assert response.status == 200

    results = json.loads(response.read())
    assert len(results)

    print u'Searched for {}; found {}'.format(object_name, results[0])

    # Select the object we found
    params = urllib.urlencode({'target': results[0].encode('utf-8')})
    conn.request('POST', '/api/main/focus', params)
    response = conn.getresponse()
    assert response.status == 200
    print response.read()

    # Get the information about the object
    conn.request('GET', '/api/objects/info')
    response = conn.getresponse()
    assert response.status == 200
    status = response.read()

    # use regex to get right ascension and declination
    a = re.findall("(?<=RA/Dec \(on date\):)(.*)h(.*)m(.*)s/(.*)\xc2\xb0(.*)\'(.*)\"(?=<br>Hour angle)", status)
    assert len(a) == 1
    return a[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('jdate', help='Julian date, e.g. 2451545.000000', type=float)
    parser.add_argument('name', help='search term for object')

    args = parser.parse_args()

    jdate = args.jdate
    object_name = args.name
    
    print query(jdate, object_name)