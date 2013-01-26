import database

class Artist:
    def __init__(self, index):
        self.index = index

class Track:
    def __init__(self, release, index):
        self.release = release
        self.index = index

class Release:
    def __init__(self, index):
        data, aid, sales, posted = database.get_release(index)
        if not data:
            data, sales, ntracks, posted = discogs.get_release(index)
        self.tracks = []
        self.artists = []
        self.data = data
        self.sales = sales
        self.posted = posted
        for i in range(ntracks):
            self.tracks.append(Track(self, i))

  
