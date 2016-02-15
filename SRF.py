
IL     = "http://il.srf.ch/integrationlayer/1.0/ue/srf"
BASEURL = "http://www.srf.ch"
PLAYER = BASEURL + "/player/tv"
    
def extractImage( json):
    if "Image" in json:
        return json["Image"]["ImageRepresentations"]["ImageRepresentation"][0]["url"] + "/scale/width/640"
    elif "AssetSet" in json and "Show" in json["AssetSet"] and "Image" in json["AssetSet"]["Show"]:
        return json["AssetSet"]["Show"]["Image"]["ImageRepresentations"]["ImageRepresentation"][0]["url"] + "/scale/width/640"
    return ""
