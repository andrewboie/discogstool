import discogs_client as discogs
import pprint
import difflib
import urllib
import hashlib
import base64
import os.path
import util

discogs.user_agent = 'TaggingTool/0.0'

class DiscogsException(Exception):
    pass


def str_track(rel, tid):
    t = rel.tracklist[tid - 1]
    if t["artists"]:
        art =  " ".join([unicode(i) for i in t["artists"]]) + " - " + t["title"]
    else:
        art = t["title"]
    if t["position"]:
        pos = str(tid) + " " + t["position"]
    else:
        pos = str(tid)
    
    return u"#%s \"%s\" - %s" % (pos, art, rel)

def release_filter(rel):
    if not isinstance(rel, discogs.Release):
        return False
    for f in rel.data["formats"]:
        if f["name"] == "Vinyl":
            return True
    return False

def specify_track(rid, trackno):
    release = discogs.Release(rid)
    try:
        # reference it so queries are made
        data = release.data
    except discogs.HTTPError:
        raise DiscogsException("invalid release id")
    if trackno - 1 not in range(len(release.tracklist)):
        raise DiscogsException("bad track number")
    return (release, trackno)

def find_track(rid, title):
    release = discogs.Release(rid)
    rs = []
    i = 1

    # check for exact match first
    for t in release.tracklist:
        if title == t["title"]:
            rs.append((release, i))
        i = i + 1

    if rs:
        return rs

    i = 1
    for t in release.tracklist:
        cm = difflib.get_close_matches(title, [t["title"]])
        if cm:
            rs.append((release, i))
        i = i + 1
    return rs

def get_release(rid):
    return discogs.Release(rid)

def find_release(artist, title, album=None):
    rlist = []
    try:
        if not artist:
            query = title
        elif album:
            query = "%s %s" % (artist, album)
        else:
            query = "%s %s" % (artist, title)
        s = discogs.Search(query)
        rs = [i for i in s.results()[:15] if release_filter(i)]
    except discogs.HTTPError:
        return []

    # if album name was provided, filter out non-matching
    if album:
        for r in rs:
            rt = r.data["title"]
            if not difflib.get_close_matches(album, [rt]):
                rs.remove(r)

    for r in rs:
        for i in range(len(r.data["tracklist"])):
            t = r.data["tracklist"][i]["title"]
            cm = difflib.get_close_matches(title, [t])
            if cm:
                rlist.append((r, i + 1))
    if not rlist:
        for r in rs:
            for i in range(len(r.data["tracklist"])):
                rlist.append((r, i + 1))

    return rlist

def fetch_image(release):
    d = release.data
    if "images" not in d:
        return None
    uri = d["images"][0]["uri"]
    hashuri = base64.b64encode(uri)
    if os.path.exists(util.userfile(hashuri)):
        imgdata = open(util.userfile(hashuri)).read()
    else:
        imgdata = urllib.urlopen(uri).read()
        open(util.userfile(hashuri), "wb").write(imgdata)
    return imgdata


