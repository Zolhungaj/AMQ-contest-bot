from player import Player
from song import Song
import time

class Lobby:
    def remove_player(self, username, reason):
        return


class GameLobby(Lobby):
    """represents the lobby"""
    def __init__(self, driver, players=[], round=0):
        self.round = round
        self.total_rounds = -1
        self.last_round = round - 1
        self.players = [p for p in players if p is not None]
        self.player_count = 0
        for p in self.players:
            if p.note == "":
                self.player_count += 1
        self.time = -1
        self.song_list = []
        self.driver = driver
        self.answer = False
        self.results = False
        self.playback = False
        self.last_song = None

    def remove_player(self, username, reason):
        for p in self.players:
            if p.username == username and p.note == "":
                p.note = "[%s in round %d]" % (reason, self.round)
                self.player_count -= 1

    def add_player(self, username):
        self.players.append(Player(username))
        player_count += 1

    def scan_lobby(self):
        hider = self.driver.find_element_by_id("qpAnimeNameHider")
        if "hide" not in hider.get_attribute("class"):
            playround = True
        else:
            playround = False
        self.round = int(
            self.driver.find_element_by_id("qpCurrentSongCount").text)
        self.total_rounds = int(
            self.driver.find_element_by_id("qpTotalSongCount").text)
        if playround:
            hider_text = self.driver.find_element_by_id("qpHiderText").text
            if hider_text == "Answers":
                self.answer = True
                self.playback = False
            elif hider_text == "":
                self.answer = False
                # self.playback = True
            elif "Loading" in hider_text:
                pass
            else:
                self.answer = False
                self.playback = False
                self.time = int(hider_text)
        elif self.round > self.last_round:
            self.playback = True
            self.last_round = self.round
            anime_name = self.driver.find_element_by_id("qpAnimeName").text
            song_name = self.driver.find_element_by_id("qpSongName").text
            artist = self.driver.find_element_by_id("qpSongArtist").text
            song_type = self.driver.find_element_by_id("qpSongType").text
            link = self.driver.find_element_by_id("qpSongVideoLink").get_attribute("href")
            song = Song(anime_name, song_name, artist, song_type, link)
            self.song_list.append(song)
            self.last_song = song
            for player in self.players:
                for n in range(5):
                    status = self.driver.find_element_by_id("qpAvatar-%s" % player.username)
                    if "disabled" in status.get_attribute("class"):
                        self.remove_player(player.username, "Left the game")
                    answer = status.find_element_by_class_name("qpAvatarAnswerText").text
                    correct = status.find_element_by_class_name("qpAvatarAnswerContainer")
                    score = status.find_element_by_class_name("qpAvatarPointText").text
                    if "rightAnswer" in correct.get_attribute("class"):
                        player.correct_songs.append([song, answer])
                    elif "wrongAnswer" in correct.get_attribute("class"):
                        player.wrong_songs.append([song, answer])
                    else:
                        print("ye mystical race condition has been solved")
                        time.sleep(0.2)
                        continue
                    break
                player.score = int(score)

    def scan_lobby_many(self):
        hider = self.driver.find_element_by_id("qpAnimeNameHider")
        if "hide" not in hider.get_attribute("class"):
            playround = True
        else:
            playround = False
        self.round = int(
            self.driver.find_element_by_id("qpCurrentSongCount").text)
        self.total_rounds = int(
            self.driver.find_element_by_id("qpTotalSongCount").text)
        if playround:
            hider_text = self.driver.find_element_by_id("qpHiderText").text
            if hider_text == "Answers":
                self.answer = True
                self.playback = False
            elif hider_text == "":
                self.answer = False
                # self.playback = True
            elif "Loading" in hider_text:
                pass
            else:
                self.answer = False
                self.playback = False
                self.time = int(hider_text)
        elif self.round > self.last_round:
            self.playback = True
            self.last_round = self.round
            anime_name = self.driver.find_element_by_id("qpAnimeName").text
            song_name = self.driver.find_element_by_id("qpSongName").text
            artist = self.driver.find_element_by_id("qpSongArtist").text
            song_type = self.driver.find_element_by_id("qpSongType").text
            link = self.driver.find_element_by_id("qpSongVideoLink").get_attribute("href")
            song = Song(anime_name, song_name, artist, song_type, link)
            self.song_list.append(song)
            self.last_song = song
            containers = self.driver.find_elements_by_class_name("qpAvatarContainer")
            for element in containers:
                answer_container = element.find_element_by_class_name("qpAvatarAnswerContainer")
                for i in range(5):
                    if "rightAnswer" in answer_container.get_attribute("class"):
                        correct = True
                    elif "wrongAnswer" in answer_container.get_attribute("class"):
                        correct = False
                    else:
                        print("ye mystical race condition has been solved")
                        time.sleep(0.2)
                        continue
                    break
                score = int(element.find_element_by_class_name("qpAvatarPointText").text)
                level = int(element.find_element_by_class_name("qpAvatarLevelText").text)
                name_container = element.find_element_by_class_name("qpAvatarNameContainer")
                name = name_container.find_element_by_tag_name("span").text
                player = self.get_player(name)
                if not player:
                    continue
                answer = element.find_element_by_class_name("qpAvatarAnswerText").text
                if correct:
                    player.correct_songs.append([song, answer])
                else:
                    player.wrong_songs.append([song, answer])
                if "disabled" in element.get_attribute("class"):
                    self.remove_player(name, "Left the game")
                player.score = score

    def get_player(self, name):
        for p in self.players:
            if p.name == name and p.note == "":
                return p
        return None

    def verify_players(self):
        actual_players = []
        for p in self.players:
            try:
                self.driver.find_element_by_id("qpAvatar-%s" % p.username)
                actual_players.append(p)
            except Exception:
                pass
        self.players = actual_players
        self.player_count = 0
        for p in self.players:
            if p.note == "":
                self.player_count += 1

    def active_players(self):
        return [p for p in self.players if p.note == ""]

    def all_players(self):
        return self.players

    def __repr__(self):
        out = "GameLobby(["
        for p in self.players:
            out += repr(p) + ", "
        out += "], %d)" % (self.round)
        return out


class WaitingLobby(Lobby):
    def __init__(self, driver, player_max, players=None):
        self.driver = driver
        self.players = players or [None]*player_max
        self.ready_players = [False]*player_max
        self.player_max = player_max
        self.player_count = len([p for p in self.players if p is not None])

    def scan_lobby(self):
        for n in range(self.player_max):
            element = self.driver.find_element_by_id("lobbyAvatar%d" % n)
            is_player = element.find_element_by_class_name("lobbyAvatarTextContainer")
            if "invisible" in is_player.get_attribute("class"):
                self.players[n] = None
                self.ready_players[n] = False
            else:
                try:
                    level = element.find_element_by_class_name("lobbyAvatarLevel")
                    level = int(level.text)
                    # print(level)
                    name = element.find_element_by_class_name("lobbyAvatarName")
                    username = name.text
                    # print(username)
                    if self.players[n] is None or self.players[n].username != username:
                        self.players[n] = Player(username, level)
                    ready = element.get_attribute("class")
                    if "lbReady" in ready:
                        self.ready_players[n] = True
                    else:
                        self.ready_players[n] = False
                except Exception:
                    self.players[n] = None
                    self.ready_players[n] = False
        self.player_count = len([p for p in self.players if p is not None])

    def scan_lobby_many(self):
        players = []
        ready_players = []
        containers = self.driver.find_elements_by_class_name("lobbyAvatar")
        for element in containers:
            name_container = element.find_element_by_class_name("lobbyAvatarNameContainterInner")
            name = name_container.find_element_by_tag_name("h2").text
            level_container = element.find_element_by_class_name("lobbyAvatarLevelContainer")
            level = int(level_container.find_element_by_tag_name("h3").text)
            ready = "lbready" in element.get_attribute("class")
            players.append(Player(name, level))
            ready_players.append(ready)
        self.players = players
        self.ready_players = ready_players
        self.player_count = len(players)

    def get_unready(self):
        not_ready = []
        for n in range(self.player_max):
            if self.players[n] is not None and not self.ready_players[n]:
                not_ready.append(self.players[n])
        return not_ready

    def all_ready(self):
        return self.get_unready() == []

    def generateGameLobby(self):
        return GameLobby(self.driver, self.players)

    def player_count_fun(self):
        res = 0
        for p in self.players:
            if p is not None:
                res += 1
        return res

    def active_players(self):
        return [p for p in self.players if p is not None]

    def all_players(self):
        return self.active_players()
