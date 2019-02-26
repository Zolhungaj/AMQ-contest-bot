class Song:
    def __init__(self, anime, name, artist, type, link):
        self.anime = anime
        self.name = name
        self.artist = artist
        self.type = type
        self.link = link

    def __repr__(self):
        return "Song('%s', '%s', '%s', '%s', '%s')" % (self.anime,
                                                       self.name,
                                                       self.artist,
                                                       self.type,
                                                       self.link)

    def __str__(self):
        return "%s:[%s] %s「%s」by: %s" % (self.anime, self.link,
                                         self.type, self.name,
                                         self.artist)

    def __format__(self):
        return self.__str__()
