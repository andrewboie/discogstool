import mutagen
import sys
import pprint
import urllib
import libdiscogs as discogs

tag_map = {
    "MP3" : {
        "album" : "TALB",
        "artist" : "TPE1",
        "bpm" : "TBPM",
        "title" : "TIT2",
        "year" : "TDRC",
        "comment" : "COMM::'eng'",
        "genre" : "TCON",
        "image" : "APIC",
        "track" : "TRCK",
        "label" : "TPUB",
        },
    "MP4" : {
        "album" : "\xa9alb",
        "artist" : "\xa9ART",
        "bpm" : "tmpo",
        "title" : "\xa9nam",
        "year" : "\xa9day",
        "comment" : "\xa9cmt",
        "genre" : "\xa9gen",
        "image" : "covr",
        "track" : "trkn",
        "label" : "\xa9lab",
    }
}

rev_tag_map = {}
for k,v in tag_map.iteritems():
    rev_tag_map[k] = {}
    for k2,v2 in tag_map[k].iteritems():
        rev_tag_map[v2] = k2

uni_flag = "\xa9"


class AudioFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.extension = filename[-3:].upper()
        self.obj = mutagen.File(filename)
        if not self.obj:
            raise Exception("mutagen couldn't open " + filename)
        self.extension = self.obj.__class__.__name__

    def __getitem__(self, key):
        try:
            i = self.obj.tags[tag_map[self.extension][key]]
        except KeyError:
            return None
        while isinstance(i, list):
            i = i[0]
        if key == "track":
            if self.extension == "MP3":
                i = str(i).split("/")
                if len(i) == 1:
                    i.append(0)
                i = tuple([int(x) for x in i])
        elif key == "bpm":
            i = int(str(i))
        elif key == "image":
            i = u"<binary>"
        else:
            i = unicode(i)
        return i

    def update(self, release, track):
        d = release.data
        t = release.tracklist[track - 1];
        self["album"] = d["title"]
        if t["artists"]:
            self["artist"] = " ".join([unicode(i) for i in t["artists"]])
        else:
            self["artist"] = " ".join([unicode(i) for i in release.artists])
        if t["title"] == "Untitled":
            self["title"] = "%s %s" % (d["title"], t["position"])
        else:
            self["title"] = t["title"]
        self["year"] = release.released
        self["comment"] = unicode(release._id) + u" VERIFIED"
        self["label"] = " / ".join([i._id for i in release.labels])
        self["track"] = (track, len(release.tracklist))
        if "image" not in self.keys() and "images" in d:
            self["image"] = [discogs.fetch_image(release)]
        self.save()

    def __setitem__(self, key, value):
        mkey = tag_map[self.extension][key]
        if self.extension == "MP3":
            clazz = getattr(mutagen.id3, mkey[:4])
            if mkey == "COMM::'eng'":
                value = clazz(encoding=0, desc=u"", lang='eng', text=value)
            else:
                if mkey == "APIC":
                    # FIXME
                    return
                elif mkey == "TRCK":
                    if value[1]:
                        value = "%d/%d" % value
                    else:
                        value = str(value[0])
                value = clazz(encoding=0, text=value)
        elif self.extension == "MP4":
            if mkey == "trkn":
                value = [value]
        self.obj.tags[mkey] = value

    def save(self):
        self.obj.save()

    def keys(self):
        ok = self.obj.tags.keys()
        ret = []
        for k,v in tag_map[self.extension].iteritems():
            if v in ok:
                ret.append(k)
        return ret

    def __str__(self):
        ret = {}
        for k in self.keys():
            ret[k] = self[k]
        return repr(ret)


# debugging only
def main():
    for filename in sys.argv[1:]:
        af = AudioFile(filename)
        print filename
        for k in af.keys():
            if k not in ["image"]:
                print "%s: '%s'" % (k, af[k])

if __name__ == "__main__":
    main()
