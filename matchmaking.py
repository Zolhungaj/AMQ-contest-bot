class Matchmaking:
    def __init__(self, target, entries=[]):
        self.target = target
        self.entries = entries

    def add(self, name, rating, desperation=0):
        if name not in [entry.name for entry in self.entries]:
            self.entries.append(MatchmakingEntry(name, rating, desperation))

    def remove(self, name):
        self.entries = [entry for entry in self.entries if entry.name != name]

    def match(self):
        if not self.active():
            return None
        for entry in self.entries:
            result = [entry]
            sorted_list = sorted([other for other in self.entries if other.name != entry.name], key=lambda other: abs(entry.rating-other.rating))
            for other in sorted_list:
                if other.name == entry.name:
                    continue
                if entry.match(other):
                    result.append(other)
                if len(result) == target:
                    return [res.name for res in result]
            entry.increase_desperation()
        return None

    def count(self):
        return len(entries)

    def active(self):
        return self.count() >= self.target()

    def __str__(self):
        ret = "Matchmaking: {\n"
        count = 0
        for entry in self.entries:
            ret += "%d: %s,\n"
        ret += "}"
        return ret


class MatchmakingEntry:
    def __init__(self, name, rating, desperation=0):
        self.name = name  # name of the entry
        self.rating = rating  # rating of the entry
        self.desperation = desperation  # measurement of how long they have waited

    def match(self, other):
        return abs(self.rating-other.rating) <= self.desperation

    def increase_desperation(self):
        self.desperation = int(self.desperation*1.1) + 1

    def __repr__(self):
        return "MatchmakingEntry('%s', %d, %d)" % (self.name, self.rating, self.desperation)

    def __str__(self):
        return '{ "name": "%s", "rating": %d, "desperation": %d }' % (self.name, self.rating, self.desperation)


if __name__ == "__main__":
    matchmaking = Matchmaking(int(input("target\n")))
    while True:
        name = input("name: ")
        rating = input("rating: ")
        if name == "":
            break
        matchmaking.add(name, int(rating))
    while matchmaking.active():
        print(matchmaking)
        match = matchmaking.match()
        if match:
            print(match)
            input()
            for name in match:
                matchmaking.remove(name)
