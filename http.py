__all__ = [ "decode", "fetch" ]

import re
import gzip
import urllib, urllib2, HTMLParser
import simplejson
import StringIO

entitydict = { "E4": u"\xE4", "F6": u"\xF6", "FC": u"\xFC",
               "C4": u"\xE4", "D6": u"\xF6", "DC": u"\xDC",
               "2013": u"\u2013"}

def log( msg):
    msg = msg.encode( "latin-1")
    print "### %s" % msg
#    xbmc.log("### %s" % msg, level=xbmc.LOGNOTICE)

def decode( s):
    try:
        h = HTMLParser.HTMLParser()
        s = h.unescape( s)
        for k in entitydict.keys():
            s = s.replace( "&#x" + k + ";", entitydict[k])
    except UnicodeDecodeError:
        pass
        
    return s

def fetch( url, args={}, hdrs={}, post=False):
    log( "http.fetch(%s): %s" % ("POST" if post else "GET", url))
    if args: log( " -> args: %s" % args)
    if post:
        req = urllib2.Request( url, urllib.urlencode( args), hdrs)
    else:
        url = url + "?" + urllib.urlencode( args)
        req = urllib2.Request( url, None, hdrs)
        req.add_header( "User-Agent", "Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0")
        req.add_header( "Accept-Encoding", "gzip")
    response = urllib2.urlopen( req)
    encoding = re.findall("charset=([a-zA-Z0-9\-]+)", response.headers['content-type'])
    text = response.read()
    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO.StringIO( text)
        f = gzip.GzipFile(fileobj=buf)
        text = f.read()

    if len(encoding):
        print( repr( encoding))
        responsetext = unicode( text, encoding[0] );
    else:
        responsetext = text
    response.close()

    return responsetext

def fetchJSON( url, args={}, hdrs={}, post=False):
    text = fetch( url, args, hdrs, post);
    return simplejson.loads( text)