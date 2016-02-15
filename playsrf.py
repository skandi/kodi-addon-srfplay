
import SRF
import http

import time
import calendar
import xbmc, xbmcplugin
import sys
from datetime import date, timedelta


def dayname( weekday):
    days = [ "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return days[weekday]

def monthname( month):
    months = [ "Januar", "Februar", "M&auml;rz", "April", "Mail", "Juni",
               "Juli", "August", "September", "Oktober", "November", "Dezember"]
    return months[month]

class MenuEntry:
    (UNDEFINED,
     FOLDER,
     VIDEO,
     EXTENDER) = range(4)

    itemtype = UNDEFINED
    
    def __init__( self, itype, title, content=None, image=None, info=None):
        self.itemtype = itype
        self.title = http.decode( title)
        self.content = content
        self.image = image
        self.info = info

class Menu:
    def entries( self):
        pass

class MenuEmpfehlungen( Menu):
    def entries( self):
        json = http.fetchJSON( SRF.IL + "/video/editorialPlayerPicks.json")
        videos = json["Videos"]["Video"]
        for video in videos:
            metadata = video["AssetMetadatas"]["AssetMetadata"][0]
            myid = metadata["id"]
            title = metadata["title"]
            image = SRF.extractImage( video)
            
            yield( MenuEntry( MenuEntry.VIDEO, title, myid, image))


class MenuLive( Menu):
    def entries( self):
        programmurl = SRF.BASEURL + "/programm/tv/channel/"
        channels = (
            ("SRF 1",    "srf-1",    "c4927fcf-e1a0-0001-7edd-1ef01d441651" ),
            ("SRF 2",    "srf-2",    "c49c1d64-9f60-0001-1c36-43c288c01a10" ),
            ("SRF info", "srf-info", "c49c1d73-2f70-0001-138a-15e0c4ccd3d0" ),
        )
        
        for ch in channels:
            (title, url_suffix, id) = ch
            yield( MenuEntry( MenuEntry.VIDEO, title, id))
        
class MenuSearch( Menu):
    def entries( self):
        kb = xbmc.Keyboard( "", "Search...", False)
        kb.doModal()
        if (kb.isConfirmed()):
            
            print "input: %s" % kb.getText()
        
class MenuAssetSet( Menu):
    def __init__( self, args):
        self.id = args["id"]
    
    def entries( self):
        json = http.fetchJSON( SRF.IL + "/assetSet/listByAssetGroup/" + self.id + ".json")
        assetset = json["AssetSets"]["AssetSet"]
        for asset in assetset:
            if not "Video" in asset["Assets"]: continue
            video = asset["Assets"]["Video"][0]
            vid = video["id"]
            title = asset["title"]
            image = SRF.extractImage( video)
            metadata = video["AssetMetadatas"]["AssetMetadata"][0]
            info = { "title": metadata["title"] }
            if "description" in metadata: info["plot"] = metadata["description"]
            yield( MenuEntry( MenuEntry.VIDEO, title, vid, image, info=info))
        

class MenuSendungenAZ( Menu):
    def entries( self):
        json = http.fetchJSON( SRF.IL + "/tv/assetGroup/editorialPlayerAlphabetical.json")
        shows = json["AssetGroups"]["Show"]
        for show in shows:
            title = show["title"]
            vid = show["id"]
            image = SRF.extractImage( show)
            
            yield( MenuEntry( MenuEntry.FOLDER, title, (menu2key( MenuAssetSet), { "id": vid }), image))

class MenuVerpasst( Menu):
    def entries( self):
        day = date.fromtimestamp( time.time())

        for x in range(0, 10):
            fmt = "%s, %%d. %s %%Y" % (dayname( day.weekday()), monthname( day.month-1))
            title = day.strftime( fmt)
            yield( MenuEntry( MenuEntry.FOLDER, title, (menu2key( MenuDay), { "day": day.strftime( "%Y-%m-%d")})))
            day = day - timedelta( days=1)
        
        for x in range( day.year, 1999, -1):
            title = "%d" % x
            yield( MenuEntry( MenuEntry.FOLDER, title, (menu2key( MenuCalendar), { "year": title})))

class MenuCalendar( Menu):
    def __init__(self, args):
        self.args = args
        
    def entries( self):
        if not "month" in self.args:
            for x in range( 1, 13):
                title = "%s %s" % (monthname( x-1), self.args["year"])
                self.args["month"] = "%02d" % x
                yield( MenuEntry( MenuEntry.FOLDER, title, (menu2key( MenuCalendar), self.args)))
        else:
            month = int(self.args["month"])
            numdays = calendar.monthrange( int(self.args["year"]), month)[1]
            for x in range( 1, numdays+1):
                title = "%02d. %s %s" % (x, monthname(month-1), self.args["year"])
                day   = "%s-%s-%02d" % (self.args["year"], self.args["month"], x)
                yield( MenuEntry( MenuEntry.FOLDER, title, (menu2key( MenuDay), { "day": day})))

            


class MenuDay( Menu):
    def __init__( self, args):
        self.day = args["day"]
    
    def entries( self):
        json = http.fetchJSON( SRF.IL + "/video/episodesByDate.json", { "day": self.day})
        videos = json["Videos"]["Video"]
        for video in videos:
            id = video["id"]
            assetSet = video["AssetSet"]
            metadata = video["AssetMetadatas"]["AssetMetadata"][0]
            time = assetSet["publishedDate"][11:16]
            title = "%s - %s" % (time, assetSet["Show"]["title"])
            image = SRF.extractImage( video)
            info = { "title": metadata["title"] }
            if "description" in metadata: info["plot"] = metadata["description"]
            yield( MenuEntry( MenuEntry.VIDEO, title, id, image, info=info))


class MenuMain( Menu):
    def entries( self):
# work in progress
#        yield( MenuEntry( MenuEntry.FOLDER, "Search...", (menu2key( MenuSearch), {})))
        yield( MenuEntry( MenuEntry.FOLDER, "Sendungen A-Z", (menu2key( MenuSendungenAZ), {})))
        yield( MenuEntry( MenuEntry.FOLDER, "Sendung verpasst?", (menu2key( MenuVerpasst), {})))
        yield( MenuEntry( MenuEntry.FOLDER, "Empfehlungen", (menu2key( MenuEmpfehlungen), {})))

menus = (
    MenuMain,
      MenuEmpfehlungen,
      MenuSendungenAZ,
        MenuAssetSet,
      MenuVerpasst,
        MenuCalendar,
          MenuDay,
)

menukeys = range( len( menus))
menumap = dict( zip( menukeys, menus))

def menu2key( menuClass):
    for key,menu in menumap.iteritems():
        if menu == menuClass:
            return key
    return 0

def key2menu( key):
    return menumap[key]
    
def getMenu( key, args=None):
    menuClass = key2menu( key)
    if (args): return menuClass( args)
    else: return menuClass()

def getUserStream( playlist):
    # check of HD
    q = xbmcplugin.getSetting( int(sys.argv[1]), "quality")
    print "quality '%s'" % q
    for stream in playlist:
        if stream["@quality"] == "HD":
            return stream["text"]
        
    # use SD
    for stream in playlist:
        if stream["@quality"] == "SD":
            return stream["text"]
    return None

def videoForBroadcast( id):
    json = http.fetchJSON( SRF.IL + "/video/play/" + id + ".json")
    playlists = json["Video"]["Playlists"]["Playlist"]
    for playlist in playlists:
        if playlist["@protocol"] == "HTTP-HLS":
            return getUserStream( playlist["url"])
        elif playlist["@protocol"] == "RTMP":
            for quali in { "HQ", "MQ", "LQ"}:
                for url in playlist["url"]:
                    if url["@quality"] == quali:
                        return url["text"]
    return None;

def ask( stack):
    menu = stack.pop()

    key = 1
    listing = {}
    print "  0) Back"
    for entry in menu.entries():
        listing[key] = entry
        print "%3d) %s" % (key, entry.getTitle())
        
        key = key+1
    val = raw_input( "select number: ")
    sel = int(val)
    
    if sel in listing.keys():
        entry = listing[sel]
        type = entry.getType()
        content = entry.getContent()
        if (type == MenuEntry.FOLDER):
            key, args = content
            stack.append( menu)
            stack.append( getMenu( key, args))
        elif (type == MenuEntry.VIDEO):
            print ( "should play: %s" % content)


if __name__ == '__main__':
    stack = []
    stack.append( MainMenu())
    
    while len( stack):
        ask( stack)
