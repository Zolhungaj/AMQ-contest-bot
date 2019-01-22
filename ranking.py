from player import Player
from song import Song

"""
relevant factors to store:
players:
total games
average score
total wins/position

Elo score

High score

games:
results
songs played
players scores
"""


class Ranking:
    def __init__(self, path):
        self.path = path
        self.players = {}  # memoization

    def get_file_path(self, username):
        return self.path+username+".amq"

    def get_player_stats(self, username):
        if username in self.players:
            return self.players[username]
        try:
            file = open(get_file_path(username), "r", encoding="utf-8")
            data = file.read()
            self.players[username] = data
            return data
        except Exception:
            return None
        finally:
            file.close()

    def save_player(self, username, data):
        with open(get_file_path(username), "w", encoding="utf-8") as f:
            f.write(data)
            self.players[username] = data

    def create_default_data(self):
        """returns the default data values"""
        data = ""
        data += "0\n"  # total games
        data += "0\n"  # average score
        data += "0\n"  # average position
        return data

    def create_player(self, username):
        self.save_player(username, self.create_default_data())

    def get_total_games(self, username):
        data = self.get_player_stats(username)
        return int(data.split("\n")[0])

    def get_average_score(self, username):
        data = self.get_player_stats(username)
        return float(data.split("\n")[1])

    def get_average_position(self, username):
        data = self.get_player_stats(username)
        return float(data.split("\n")[2])


class EloRanking(Ranking):
    default_rating = 1200
    k_factor = 12

    def get_elo(self, username):
        data = self.get_player_stats(username)
        return int(data.split("\n")[3])

    def create_default_data(self):
        data = super.create_default_data()
        data += "%d" % self.default_rating  # default Elo ranking
        return data


class HighScoreRanking(Ranking):
    def create_default_data(self):
        data = super.create_default_data()
        data += "0"  # default max score
        return data
