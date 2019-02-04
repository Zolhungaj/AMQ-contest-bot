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

        c.execute("""CREATE TABLE IF NOT EXISTS player(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL
        );""")
        c.execute("""CREATE TABLE IF NOT EXISTS message(
        id INTEGER PRIMARY KEY,
        player_id INTEGER,
        time TEXT,
        content TEXT,
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS banned(
        player_id INTEGER PRIMARY KEY,
        reason TEXT,
        banner INTEGER NOT NULL,
        FOREIGN KEY(player_id) REFERENCES player(id),
        FOREIGN KEY(banner) REFERENCES player(id)
        );""")
        c.execute("""CREATE TABLE IF NOT EXISTS elo(
        player_id INTEGER PRIMARY KEY,
        rating INTEGER NOT NULL,
        FOREIGN KEY(player_id) REFERENCES player(id)
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
        c.execute("""CREATE TABLE IF NOT EXISTS gametosong(
        game_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        ordinal INTEGER NOT NULL,
        PRIMARY KEY(game_id, ordinal),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(song_id) REFERENCES song(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS valour(
        player_id INTEGER PRIMARY KEY,
        surplus INTEGER NOT NULL,
        referer_id INTEGER,
        FOREIGN KEY(player_id) REFERENCES player(id),
        FOREIGN KEY(referer_id) REFERENCES player(id)
        )
        """)
        c.execute("""CREATE TABLE IF NOT EXISTS administrator(
        player_id INTEGER PRIMARY KEY,
        source INTEGER,
        FOREIGN KEY(player_id) REFERENCES player(id),
        FOREIGN KEY(source) REFERENCES player(id)
        )
        """)
        c.execute("""CREATE TABLE IF NOT EXISTS moderator(
        player_id INTEGER PRIMARY KEY,
        source INTEGER,
        FOREIGN KEY(player_id) REFERENCES player(id),
        FOREIGN KEY(source) REFERENCES player(id)
        )
        """)
        c.close()
        self.conn.commit()

    def initalize_base(self):
        try:
            self.conn.execute("""INSERT INTO player VALUES(
            0,
            '<System>'
            );""")
        except Exception as e:
            pass
        try:
            self.conn.execute("""INSERT INTO administrator VALUES(
            0,
            0
            );""")
        except Exception as e:
            pass
        try:
            self.conn.execute("""INSERT INTO moderator VALUES(
            0,
            0
            );""")
        except Exception as e:
            pass
        self.conn.commit()

    def create_player(self, username):
        # id = get_player_id(username)  # check if player already exists
        # if id is not None:
        #    return id
        try:
            self.conn.execute("""INSERT INTO player VALUES(
            NULL,
            (?)
            )""", (username,))
        except sqlite3.IntegrityError as e:
            return None
        self.conn.commit()
        return self.get_player_id(username)

    def get_player_id(self, username):
        c = self.conn.cursor()
        c.execute("""SELECT id FROM player WHERE username=(?)""", (username,))
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
        INSERT INTO message VALUES(
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
        self.conn.commit()

    def unban_player(self, username):
        player_id = self.get_player_id(username)
        self.conn.execute("""
        DELETE FROM banned
        WHERE player_id = ?
        """, (player_id,))
        self.conn.commit()

    def ban_readable(self, username=None, banner=None):
        query = """
        SELECT p.username, b.reason, p2.username
        FROM banned AS b
        JOIN player p
            ON p.id = b.player_id
        JOIN player p2
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

    def add_administrator(self, username, source=None):
        self.add_moderator(username, source)
        player_id = self.get_or_create_player_id(username)
        source_id = self.get_player_id(source) or 0
        try:
            self.conn.execute("""INSERT INTO administrator VALUES(
            ?,
            ?
            )""", (player_id, source_id,))
        except Exception:
            return False
        self.conn.commit()
        return True

    def remove_administrator(self, username):
        player_id = self.get_player_id(username)
        self.conn.execute("""DELETE FROM administrator
        WHERE player_id = ?""", (player_id,))
        self.conn.commit()

    def is_administrator(self, username):
        res = self.conn.execute("""
        SELECT *
        FROM administrator
        WHERE player_id = ?""", (self.get_player_id(username),))
        return res.fetchone() is not None

    def add_moderator(self, username, source=None):
        player_id = self.get_or_create_player_id(username)
        source_id = self.get_player_id(source) or 0
        try:
            self.conn.execute("""INSERT INTO administrator VALUES(
            ?,
            ?
            )""", (player_id, source_id,))
        except Exception:
            return False
        self.conn.commit()
        return True

    def remove_moderator(self, username):
        player_id = self.get_player_id(username)
        self.conn.execute("""DELETE FROM moderator
        WHERE player_id = ?""", (player_id,))
        self.conn.commit()

    def is_moderator(self, username):
        res = self.conn.execute("""
        SELECT *
        FROM moderator
        WHERE player_id = ?""", (self.get_player_id(username),))
        return res.fetchone() is not None

    def add_valour(self, username, referer=None):
        if referer is not None:
            if not self.get_valour_surplus(referer) > 0:
                return False
        try:
            self.conn.execute("""INSERT INTO valour VALUES(
            ?,
            2,
            ?
            )""", (self.get_player_id(username), self.get_player_id(referer),))
            self.conn.commit()
            self.change_valour_surplus(referer, -1)
        except Exception:
            return False
        return True

    def has_valour(self, username):
        res = self.conn.execute("""
        SELECT player_id
        FROM valour
        WHERE player_id = ?""", (self.get_player_id(username),))
        return res.fetchone() is not None

    def get_valour_surplus(self, username):
        if self.has_valour(username):
            res = self.conn.execute("""
            SELECT surplus
            FROM valour
            WHERE player_id = ?
            """, (self.get_player_id(username),))
            return res.fetchone()[0]
        else:
            return -1

    def change_valour_surplus(self, username, change):
        new_surplus = self.get_valour_surplus(username) + change
        self.conn.execute("""UPDATE valour
        SET surplus = ?
        WHERE player_id = ?
        """, (new_surplus, self.get_player_id(username),))
        self.conn.commit()

    def valour_readable(self):
        res = self.conn.execute("""
        WITH RECURSIVE record (lvl, player_id, referer_id) AS
        (SELECT 0, v.player_id AS player_id, v.referer_id AS referer_id
            FROM valour v
                WHERE v.referer_id IS NULL
        UNION ALL
        SELECT r.lvl+1, v.player_id, v.referer_id
            FROM record AS r
                JOIN valour v
                    ON r.player_id = v.referer_id)
        SELECT r.lvl, p.username, p2.username
        FROM record AS r
        JOIN player AS p on p.id = r.player_id
        LEFT OUTER JOIN player as p2 on p2.id = r.referer_id
        ORDER BY r.lvl, p.username, p2.username""")
        return res.fetchall()


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
    database.create_player("player9")
    assert database.add_valour("player4")
    assert not database.add_valour("player5")
    assert database.add_valour("player3", "player4")
    assert not database.add_valour("player2", "player1")
    assert database.add_valour("player1", "player3")
    assert database.add_valour("player2", "player4")
    assert not database.add_valour("player6", "player4")
    print(database.valour_readable())
    print(database.ban_readable())
    print(database.ban_readable("player4"))
    print(database.ban_readable(banner="player2"))
    print(database.conn.execute(input()).fetchall())
