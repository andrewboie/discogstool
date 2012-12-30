import discogs_client as discogs
import pprint
import difflib
import urllib
import hashlib
import base64
import os.path
import util

discogs.user_agent = 'TaggingTool/0.0 andrewboie@gmail.com'

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

def ask_matches(rs):
    i = 1
    for r, t in rs:
        print "%d)" % (i,), str_track(r, t)
        i = i + 1
    while (1):
        s = raw_input("Enter selection, <releaseid>,<trackno>, or - to skip (default=1): ")
        if not s:
            s = "1"
        if s == "-":
            return None
        if "," in s:
            rid, tid = s.split(",")
            try:
                ret = specify_track(rid, int(tid))
            except (ValueError, DiscogsException) as lde:
                print lde
                continue
            return ask_matches([ret])
        if not s.isdigit():
            print "Invalid input, bad form"
            continue
        s = int(s)
        if s < 1 or s > len(rs):
            print "Invalid input, out of range"
            continue
        ret = rs[s - 1]
        break
    return ret

def query_release():
    while (1):
        z = raw_input("Enter <releaseid>,<trackno> or enter to skip: ")
        if z == "":
            return None
        if "," not in z:
            print "Expecting <release>,<track_no> pair"
            continue
        rid, tid = z.split(",")
        try:
            ret = specify_track(rid, int(tid))
        except (ValueError, DiscogsException) as lde:
            print lde
            ret = None
        if ret:
            return [ret]
        print "Error retrieving track"

def lookup_music(af, rechecking=False, hint=None):
    rs = []

    if hint:
        rs = find_release(None, hint)

    if not rs and "comment" in af.keys():
        c = unicode(af["comment"])
        cs = c.split(" ")
        if not rechecking and len(cs) == 2 and cs[1] == "VERIFIED":
            return

        # sniff automagically if release id is in comment field and track number declared
        cmt = af["comment"].split(" ")[0]
        if cmt.isdigit():
            rid = int(cmt)
            if "track" in af.keys():
                try:
                    result, track = specify_track(rid, af["track"][0])
                    print "auto-update with", str_track(result, track)
                    af.update(result, track)
                    return
                except DiscogsException, lde:
                    print lde

            elif "title" in af.keys():
                rs = find_track(rid, af["title"])
            else:
                rls = get_release(rid)
                try:
                    rs = [specify_track(rid,i)
                            for i in range(1, len(rls.tracklist) + 1)]
                except DiscogsException, lde:
                    print lde

    if not rs:
        if "artist" in af.keys() and "title" in af.keys():
            # album can be None, but we need artist/title
            rs = find_release(af["artist"], af["title"], af["album"])
        else:
            # No metadata. Use filename as search term
            rs = find_release(None, af.filename.rsplit(".", 1)[0])
    if not hint:
        print
        print
        print af.filename
        print "metadata: " + " - ".join([unicode(af[i]) for i in
            ["track", "title", "artist", "album"] if i in af.keys()])
    else:
        print hint

    if not rs:
        rs = query_release()

    if rs:
        ret = ask_matches(rs)
        if ret:
            result, track = ret
            print "update with", str_track(result, track)
            af.update(result, track)
