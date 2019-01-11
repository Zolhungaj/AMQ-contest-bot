class Song:
    def __init__(self, anime, name, artist, type):
        self.anime = anime
        self.name = name
        self.artist = artist
        self.type = type

    def __repr__(self):
        return "Song('%s', '%s', '%s', '%s')" % (self.anime,
                                                 self.name,
                                                 self.artist,
                                                 self.type)
