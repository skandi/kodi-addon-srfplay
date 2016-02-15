
import playsrf
import http
import os

import urllib
import xbmcgui, xbmcplugin, xbmcaddon, xbmc
from http import fetch


in_url    = sys.argv[0]
in_handle = int(sys.argv[1])
in_params = sys.argv[2]

addon = xbmcaddon.Addon()
# sayHi()

def decodeparams( url):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if url:
        paramPairs = url[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = urllib.unquote( paramSplits[1]).replace( "+", " ")
    return paramDict

def params2url( params):
    params_encoded = dict()
    for k in params.keys():
        if (params[k]):
            params_encoded[k] = params[k].encode( "utf-8")
    return in_url + "?" + urllib.urlencode( params_encoded)

def showMenu( menu):
    for item in menu.entries():

        # look        
        icon = "DefaultFolder.png"
        image = item.image
        if not image:
            image = ""
        li = xbmcgui.ListItem( label=item.title, iconImage=icon, thumbnailImage=image)

        # logic
        if not item.content:
            print( "skipping %s, no content" % item.title)
            continue
        
        params = dict()
        if (item.itemtype == playsrf.MenuEntry.VIDEO):
            if item.info:
                li.setInfo( "video", item.info)
            li.setProperty( "Video", "true")
            params["command"] = "play"
            params["title"] = item.title
            params["id"] = item.content
            dlRunner = "RunPlugin( %s?command=download&id=%s)" % (in_url, item.content)
            li.addContextMenuItems( [ ( "Download...", dlRunner) ])
        elif( item.itemtype == playsrf.MenuEntry.FOLDER):
            menuId, args = item.content
            params = args
            params["command"] = "menu"
            params["menuid"] = str(menuId)
        url = params2url( params)

        xbmcplugin.addDirectoryItem( handle=in_handle, url=url, listitem=li, isFolder=(item.itemtype == playsrf.MenuEntry.FOLDER))
    xbmcplugin.endOfDirectory( handle=in_handle, succeeded=True)

def playVideo( url, title=None, startOffset=0):
    li = xbmcgui.ListItem( title)
    li.setProperty( "IsPlayable", "true")
    li.setProperty( "Video", "true")
    li.setProperty( "startOffset", "%f" % (startOffset))
    xbmc.Player().play( url, li)

def getSetting( id):
    return addon.getSetting( id=id)

def notification( title, message):
    xbmc.executebuiltin( "Notification( " + title + ", " + message + ")")


def downloadm3u8( url):
    dldir = getSetting( "dlpath")
    print repr( dldir)
    if not dldir:
        notification( "Error", "Download directory not configured")
        return

    if not os.path.exists( dldir):
        os.makedirs( dldir)
    filename = url.split("/")[-2].split( ",")[0][0:-1] + ".ts"
    filename = os.path.join( dldir, filename)
    if os.path.exists( filename): return
    
    m3u = http.fetch( url).split( "\n")
    playlists = filter( lambda l: "_av." in l, m3u)
    playlist = playlists[-1]
    if not playlist.startswith( "http://"):
        prefix = "/".join( url.split( "/")[0:-1])
        playlist = prefix +"/" + playlist
    lines = http.fetch( playlist).split( "\n")
    segments = filter( lambda l: not l.startswith( "#") and len(l) > 0, lines)

    idx = 1
    tot = len( segments)
    f = open( filename, "w+")
    xbmc.executebuiltin( "Notification( SRF-Play Addon, Downloading %u segments)" % tot)
    for seg in segments:
        if not seg.startswith( "http://"):
            prefix = "/".join( url.split( "/")[0:-1])
            seg = prefix +"/" + seg
        data = http.fetch( seg)
        f.write( data)
        idx += 1
    size = f.tell() / 1024 / 1024
    f.close()
    xbmc.executebuiltin( "Notification( SRF-Play Addon, Download completed (%u MB))" % size)
    

params = decodeparams( in_params)

if not in_params:
    showMenu( playsrf.getMenu( 0))
    exit(0)

cmd = params["command"]
del params["command"]
if (cmd == "menu"):
    menuid = int(params["menuid"])
    del params["menuid"]
    showMenu( playsrf.getMenu( menuid, params))
elif (cmd == "play"):
    vid = params["id"]
    videourl = playsrf.videoForBroadcast( vid)
    if (videourl):
        playVideo( videourl, params["title"]);
elif (cmd == "download"):
    vid = params["id"]
    videourl = playsrf.videoForBroadcast( vid)
    if (videourl):
        if videourl.startswith( "rtmp://"):
            xbmc.executebuiltin( "Notification( SRF-Play Addon, Can not download RTMP stream)")
            exit(0)

        downloadm3u8( videourl)
    
