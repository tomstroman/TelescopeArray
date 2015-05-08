import urllib2
import time

import ta
import util
try:
   # Private HTTP credentials for the wiki.
  from auth_ta import tawiki_username, tawiki_password
except ImportError:
  print 'Warning: module auth_ta is not present.'
  tawiki_username = ''
  tawiki_password = ''
  
  
  



def getPage(year):
  '''
  Download the "run logs and signups" MediaWiki page for the requested year 
  and return the HTML as a string.  
  '''
  this_year = int(time.strftime('%Y'))
  if not (year >= 2007 and year <= this_year):
    print 'Error: year must be between [2007,{0}]'.format(this_year)
    return None
  
  wiki = 'http://www.telescopearray.org/tawiki/index.php'
  tadurl = wiki + '/{0}_Run_Signups'.format(year)

  # this authentication procedure is based on the HOWTO
  # at https://docs.python.org/2/howto/urllib2.html
  
  authwiki = urllib2.HTTPPasswordMgrWithDefaultRealm()
  
  authwiki.add_password( None, wiki, 
      tawiki_username, tawiki_password )
      
  handler = urllib2.HTTPBasicAuthHandler(authwiki)    
  opener = urllib2.build_opener(handler)
  
  return opener.open(tadurl).read()

  
  
  
def findLogDates(html,site):
  '''
  Scrape the wiki HTML returned by getPage() and find instances of
  links to .log files that exist corresponding to the specified site.
  Extract a date from each file's name and return a list of dates in
  yyyymmdd format.
  
  Assumptions: 
  0. The log filename is yYYYYmMMdDD.SITE.log
  1. The log filename occurs within <a></a> inside a <td></td>
  2. No other text appears inside the <a></a>
  3. A wiki page does not exist for log files on non-existent run nights
  
  '''

  if site not in ta.sites:
    print 'Error: site must be one of:'
    print ta.sites
    return None
    
  ending = '{0}.log'.format(site)
  dates = []  
  for line in html.split('\n'):
    for td in line.split('</td>'):
      if ending not in td:
        continue
      for anchor in td.split('</a>'):
        if anchor.endswith(ending):
          if 'page does not exist' not in anchor:
            dates.append(util.ymd8(anchor.split('>')[-1]))
        
  return dates      
