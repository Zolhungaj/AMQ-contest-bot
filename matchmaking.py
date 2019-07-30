class Matchmaking:
    pass


class MatchMakingEntry:
    def __init__(self, name, rating, desperation=0):
        self.name = name  # name of the entry
        self.rating = rating  # rating of the entry
        self.desperation = desperation  # measurement of how long they have waited

    def match(self, other):
        return abs(self.rating-other.rating) <= self.desperation

    def increase_desperation(self):
        self.desperation = int(self.desperation*1.1) + 1

    def __repr__(self):
        return "MatchMakingEntry('%s', %d, %d)" % (self.name, self.rating, self.desperation)
