class Player(object):
    """represents a player"""
    def __init__(self, username, level=0, note=""):
        self.score = 0
        self.username = username
        self.level = level
        self.note = note
        self.wrong_songs = []
        self.correct_songs = []

    def __repr__(self):
        return "Player('%s', %d, '%s')" % (self.username,
                                           self.level, self.note)
