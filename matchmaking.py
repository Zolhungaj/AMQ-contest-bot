class Matchmaking:
    def __init__(self, target, entries=[]):
        self.target = target
        self.entries = entries

    def add(self, name, rating, desperation=0):
        if name not in [entry.name for entry in entries]:
            self.entries.append(MatchMakingEntry(name, rating, desperation))

    def remove(self, name):
        self.entries = [entry for entry in self.entries if entry.name != name]

    def match(self):
        for entry in self.entries:
            result = [entry]
            for other in self.entries:
                if other.name == entry.name:
                    continue
                if entry.match(other):
                    result.append(other)
                if len(result) == target:
                    return [res.name for res in result]
            entry.increase_desperation()
        return None


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
