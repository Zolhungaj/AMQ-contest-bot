import sqlite3
import math


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
        username TEXT UNIQUE NOT NULL,
        truename TEXT NOT NULL
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
        c.execute("""CREATE TABLE IF NOT EXISTS game(
        id INTEGER PRIMARY KEY,
        song_count INTEGER,
        player_count INTEGER,
        time TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS gametoplayer(
        game_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        result INTEGER,
        miss_count INTEGER,
        position INTEGER,
        PRIMARY KEY(game_id, player_id),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS gameplayertomissed(
        game_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        ordinal INTEGER,
        answer TEXT,
        PRIMARY KEY(game_id, player_id, ordinal),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS gameplayertocorrect(
        game_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        ordinal INTEGER,
        answer TEXT,
        PRIMARY KEY(game_id, player_id, ordinal),
        FOREIGN KEY(game_id) REFERENCES game(id),
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS elo(
        player_id INTEGER PRIMARY KEY,
        rating INTEGER NOT NULL,
        FOREIGN KEY(player_id) REFERENCES player(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS elodiff(
        game_id INTEGER NOT NULL,
        player_id INTEGER NOT NULL,
        rating_change INTEGER NOT NULL,
        PRIMARY KEY(game_id, player_id),
        FOREIGN KEY(player_id) REFERENCES player(id),
        FOREIGN KEY(game_id) REFERENCES game(id)
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
            '<system>',
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
            (?),
            ?
            )""", (username.lower(), username,))
        except sqlite3.IntegrityError as e:
            return None
        self.conn.commit()
        return self.get_player_id(username)

    def get_player_id(self, username):
        if username is None:
            return None
        username = username.lower()
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

    def get_player_username(self, player_id):
        c = self.conn.cursor()
        c.execute("""SELECT username FROM player WHERE id=(?)""", (player_id,))
        result = c.fetchone()
        c.close()
        if result is None:
            return None
        else:
            return result[0]

    def get_player_truename(self, player_id):
        c = self.conn.cursor()
        c.execute("""SELECT truename FROM player WHERE id=(?)""", (player_id,))
        result = c.fetchone()
        c.close()
        if result is None:
            return None
        else:
            return result[0]

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
            self.conn.execute("""INSERT INTO moderator VALUES(
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

    def get_song_id(self, song):
        res = self.conn.execute("""
        SELECT id FROM song
        WHERE
                anime = ?
            AND
                type = ?
            AND
                title = ?
            AND
                artist = ?
            AND
                link = ?
        """, (song.anime, song.type, song.name, song.artist, song.link,))
        return res.fetchone()

    def get_or_create_song_id(self, song):
        res = self.get_song_id(song)
        if res is None:
            self.conn.execute("""
            INSERT INTO song VALUES(
            NULL,
            ?,
            ?,
            ?,
            ?,
            ?)
            """, (song.anime, song.type, song.name, song.artist, song.link,))
            res = self.get_song_id(song)
            self.conn.commit()
        return res[0]

    def create_game(self, song_count, player_count):
        self.conn.execute("""
        INSERT INTO game VALUES(
        NULL,
        ?,
        ?,
        DATETIME('now')
        )""", (song_count, player_count,))
        res = self.conn.execute("""
        SELECT id FROM game
        ORDER BY id DESC
        LIMIT 1""")
        self.conn.commit()
        return res.fetchone()[0]

    def add_song_to_game(self, game_id, song, ordinal):
        song_id = self.get_or_create_song_id(song)
        self.conn.execute("""
        INSERT INTO gametosong VALUES(
        ?,
        ?,
        ?
        )""", (game_id, song_id, ordinal))
        self.conn.commit()

    def get_all_ratings(self):
        res = self.conn.execute("""
        SELECT DISTINCT(g.player_id), rating
        FROM gametoplayer g
        INNER JOIN elo e
        ON e.player_id = g.player_id
        ORDER BY rating DESC""")
        return res.fetchall()

    def get_total_games(self):
        res = self.conn.execute("""
        SELECT count(*) FROM game""")
        return res.fetchone()[0]

    def get_player_game_count(self, player_id):
        res = self.conn.execute("""
        SELECT count(*) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        return res.fetchone()[0]

    def get_player_win_count(self, player_id):
        res = self.conn.execute("""
        SELECT count(*) FROM gametoplayer
        WHERE player_id = ?
        AND position = 1""", (player_id,))
        return res.fetchone()[0]

    def get_player_hit_count(self, player_id):
        res = self.conn.execute("""
        SELECT SUM(result) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        hit = res.fetchone()
        if hit is None:
            return 0
        else:
            return hit[0]

    def get_player_miss_count(self, player_id):
        res = self.conn.execute("""
        SELECT SUM(miss_count) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        miss = res.fetchone()
        if miss is None:
            return 0
        else:
            return miss[0]

    def get_player_song_count(self, player_id):
        res = self.conn.execute("""
        SELECT SUM(result) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        hit = res.fetchone()
        res = self.conn.execute("""
        SELECT SUM(miss_count) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        miss = res.fetchone()
        if hit is None and miss is None:
            return 0
        elif hit is None:
            return miss[0]
        elif miss is None:
            return hit[0]
        else:
            return hit[0]+miss[0]

    def get_player_hit_rate(self, player_id):
        res = self.conn.execute("""
        SELECT SUM(result) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        hit = res.fetchone()
        res = self.conn.execute("""
        SELECT SUM(miss_count) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        miss = res.fetchone()
        if hit is None or miss is None:
            return "0.00%"
        else:
            return "%3.2f%%" % (hit[0]/(miss[0]+hit[0])*100)

    def get_player_hit_miss_ratio(self, player_id):
        res = self.conn.execute("""
        SELECT SUM(result) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        hit = res.fetchone()
        res = self.conn.execute("""
        SELECT SUM(miss_count) FROM gametoplayer
        WHERE player_id = ?""", (player_id,))
        miss = res.fetchone()
        if hit is None or miss is None:
            return "0:0"
        elif hit[0] == 0 and miss[0] == 0:
            return "0:0"
        elif hit[0] == miss[0]:
            return "1:1"
        elif hit[0] > 0 and miss[0] == 0:
            return "1:0"
        elif hit[0] == 0 and miss[0] > 0:
            return "0:1"
        elif hit[0] > miss[0]:
            return "%3.2f:1" % (hit[0]/miss[0])
        elif hit[0] < miss[0]:
            return "1:%3.2f" % (miss[0]/hit[0])

    def get_elo(self, player_id):
        res = self.conn.execute("""
        SELECT rating FROM elo
        WHERE player_id = ?""", (player_id,))
        return res.fetchone()

    def get_or_create_elo(self, player_id):
        res = self.get_elo(player_id)
        if res is None:
            default_elo = 1400
            self.conn.execute("""
            INSERT INTO elo VALUES(
            ?,
            ?
            )""", (player_id, default_elo))
            res = self.get_elo(player_id)
        return res[0]

    def update_elo(self, game_id, player_id, diff):
        elo = self.get_or_create_elo(player_id)
        if diff > 0:
            diff = math.ceil(diff)
        else:
            diff = int(diff)
        self.conn.execute("""
        UPDATE elo
        SET rating = ?
        WHERE player_id = ?
        """, (elo+diff, player_id,))
        self.conn.execute("""
        INSERT INTO elodiff VALUES(
        ?,
        ?,
        ?
        )""", (game_id, player_id, diff,))
        self.conn.commit()

    def get_result_leaderboard_player_id(self, top=10):
        res = self.conn.execute("""
        SELECT DISTINCT(player_id), result
        from gametoplayer
        order by result desc
        limit ?""", (top,))
        return res.fetchall()

    def get_result_leaderboard_truename(self, top=10):
        res = self.conn.execute("""
        SELECT DISTINCT(truename), result
        from player
        join gametoplayer
        on player_id=id
        order by result desc
        limit ?""", (top,))
        return res.fetchall()

    def record_game(self, song_list, players):
        game_id = self.create_game(len(song_list), len(players))
        counter = 0
        song_list_with_ordinal = {}
        for s in song_list:
            self.add_song_to_game(game_id, s, counter)
            song_list_with_ordinal[str(s)] = counter
            counter += 1
        for p in players:
            player_id = self.get_or_create_player_id(p.username)
            correct_songs = len(p.correct_songs)
            missed_songs = len(p.wrong_songs)
            position = 1
            for p2 in players:
                if len(p2.correct_songs) > correct_songs:
                    position += 1
            self.conn.execute("""
            INSERT into gametoplayer VALUES(
            ?,
            ?,
            ?,
            ?,
            ?
            )""", (game_id, player_id, correct_songs, missed_songs, position,))
            for s in p.correct_songs:
                ordinal = song_list_with_ordinal[str(s[0])]
                self.conn.execute("""
                INSERT into gameplayertocorrect VALUES(
                ?,
                ?,
                ?,
                ?
                )""", (game_id, player_id, ordinal, s[1]))
            for s in p.wrong_songs:
                ordinal = song_list_with_ordinal[str(s[0])]
                self.conn.execute("""
                INSERT into gameplayertomissed VALUES(
                ?,
                ?,
                ?,
                ?
                )""", (game_id, player_id, ordinal, s[1]))
        player_id_elo_score = []
        for p in players:
            player_id = self.get_or_create_player_id(p.username)
            elo = self.get_or_create_elo(player_id)
            correct_songs = len(p.correct_songs)
            player_id_elo_score.append((player_id, elo, correct_songs,))
        k = 32
        k2 = int(k*2/len(players))
        for p, elo1, correct_songs in player_id_elo_score:
            diff = 0
            for p2, elo2, correct_songs2 in player_id_elo_score:
                diff2 = 0
                ex1 = 1/(1+10**((elo2-elo1)/400))
                ex2 = 1/(1+10**((elo1-elo2)/400))
                if correct_songs == correct_songs2:
                    s1 = 0.5
                elif correct_songs < correct_songs2:
                    s1 = 0
                else:
                    s1 = 1
                diff2 = (s1 - ex1) * k2
                diff += diff2
            if diff > k:
                diff = k
            if diff < -k:
                diff = -k
            self.update_elo(game_id, p, diff)
        self.conn.commit()


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
