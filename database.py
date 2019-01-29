import sqlite3


class Database:

    def __init__(self, database_file):
        self.database_file = database_file
        self.conn = sqlite3.connect(database_file)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.start()
        self.initalize_base()

    def start(self):
        c = self.conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL
        );""")
        c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY,
        player_id INTEGER,
        time TEXT,
        content TEXT,
        FOREIGN KEY(player_id) REFERENCES players(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS banned(
        player_id INTEGER PRIMARY KEY,
        reason TEXT,
        banner INTEGER NOT NULL,
        FOREIGN KEY(player_id) REFERENCES players(id),
        FOREIGN KEY(banner) REFERENCES players(id)
        );""")
        c.execute("""CREATE TABLE IF NOT EXISTS elo(
        player_id INTEGER PRIMARY KEY,
        rating INTEGER NOT NULL,
        FOREIGN KEY(player_id) REFERENCES players(id)
        )""")
        c.execute("""CREATE TABLE game(
        id INTEGER PRIMARY KEY
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS gametoplayer(
        game_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        result INTEGER,
        position INTEGER,
        PRIMARY KEY(game_id, player_id),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS song(
        id INTEGER PRIMARY KEY,
        anime TEXT,
        type TEXT,
        title TEXT,
        artist TEXT,
        link TEXT
        )""")
        c.execute("""CREATE TABLE gametosong(
        game_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        ordinal INTEGER NOT NULL,
        PRIMARY KEY(game_id, ordinal),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(song_id) REFERENCES song(id)

        )""")
        c.close()
        self.conn.commit()

    def initalize_base(self):
        try:
            self.conn.execute("""INSERT INTO players VALUES(
            0,
            '<System>'
            );""")
        except Exception as e:
            print("base initialize failed")
        self.conn.commit()

    def create_player(self, username):
        # id = get_player_id(username)  # check if player already exists
        # if id is not None:
        #    return id
        try:
            self.conn.execute("""INSERT INTO players VALUES(
            NULL,
            (?)
            )""", (username,))
        except sqlite3.IntegrityError as e:
            return None
        self.conn.commit()
        return self.get_player_id(username)

    def get_player_id(self, username):
        c = self.conn.cursor()
        c.execute("""SELECT id FROM players WHERE username=(?)""", (username,))
        result = c.fetchone()
        c.close()
        if result is None:
            return None
        else:
            return result[0]

    def get_or_create_player_id(self, username):
        player_id = self.get_player_id(username)
        if player_id is None:
            player_id = self.create_player(username)
        return player_id

    def save_message(self, username, message):
        player_id = self.get_or_create_player_id(username)
        self.conn.execute("""
        INSERT INTO messages VALUES(
        NULL,
        (?),
        DATETIME('now'),
        (?)
        )""", (player_id, message,))
        self.conn.commit()

    def ban_player(self, username, reason=None, banner=None):
        player_id = self.get_or_create_player_id(username)
        if banner is None:
            banner_id = 0
        else:
            banner_id = self.get_or_create_player_id(banner)
        self.conn.execute("""
        INSERT INTO banned VALUES(
        (?),
        (?),
        (?)
        )""", (player_id, reason, banner_id,))

    def ban_readable(self, username=None, banner=None):
        query = """
        SELECT p.username, b.reason, p2.username
        FROM banned AS b
        JOIN players p
            ON p.id = b.player_id
        JOIN players p2
            ON p2.id = b.banner
        """
        if username is not None:
            if banner is not None:
                query += "WHERE p.username = ? AND p2.username = ?;"
                return self.conn.execute(query, (username, banner,)).fetchall()
            else:
                query += "WHERE p.username = ?;"
                return self.conn.execute(query, (username,)).fetchall()
        elif banner is not None:
            query += "WHERE p2.username = ?;"
            return self.conn.execute(query, (banner,)).fetchall()
        else:
            return self.conn.execute(query+";").fetchall()


if __name__ == "__main__":
    # a basic test of the functions
    database = Database(":memory:")
    assert database.get_player_id("player1") is None
    assert database.create_player("player1") == 1
    assert database.get_or_create_player_id("player2") == 2
    assert database.get_or_create_player_id("player2") == 2
    assert database.get_player_id("player2") == 2
    database.save_message("player3", "message1")
    database.ban_player("player4")
    database.ban_player("player3", "reason1", "player2")
    print(database.ban_readable())
    print(database.ban_readable("player4"))
    print(database.ban_readable(banner="player2"))
    print(database.conn.execute(input()).fetchall())
