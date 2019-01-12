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

    def __str__(self):
        return "%s:\n[%s]\n「%s」\nby: %s\n" % (self.anime, self.type, self.name, self.artist)
