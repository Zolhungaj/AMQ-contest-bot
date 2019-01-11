"""
"""
import os

import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import _thread
import subprocess

import datetime

import random

import traceback


class Logger:

    def __init__(self, sys_log="AMQ-bot.log", chat_log="AMQ-bot-chat.log",
                 chat_out_log="AMQ-bot-chat_out.log",
                 event_log="AMQ-bot-events.log"
                 ):
        self.sys_log = sys_log
        self.chat_log = chat_log
        self.chat_out_log = chat_out_log
        self.event_log = event_log

    def log(self, message, logfile):
        """
        logs events to the logfile
        """
        # write timestamp message newline to file
        msg = "[%s]: %s\n" % (
            datetime.datetime.fromtimestamp(
                datetime.datetime.now().timestamp()
            ).isoformat(), message)
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(msg)
        print(msg)

    def sys(self, message):
        self.log(message, self.sys_log)

    def chat(self, message):
        self.log(message, self.chat_log)

    def chat_out(self, message):
        self.log(message, self.chat_out_log)

    def event(self, message):
        self.log(message, self.event_log)


class Song:
    def __init__(self, anime, name, artist, type):
        self.anime = anime
        self.name = name
        self.artist = artist
        self.type = type

    def __repr__(self):
        return "Song('%s', '%s', '%s', '%s')" % (self.anime,
                                                 self.name,
                                                 self.artist,
                                                 self.type)


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


class GameLobby(object):
    """represents the lobby"""
    def __init__(self, round=0, players=[]):
        self.round = round
        self.last_round = round - 1
        self.players = players
        self.player_count = 0
        for p in self.player:
            if p.note == "":
                self.player_count += 1
        self.time = -1
        self.song_list = []

    def remove_player(self, username, reason):
        for p in self.players:
            if p.username == username and p.note == "":
                p.note = "[%s in round %d]" % (reason, self.round)
                player_count -= 1

    def add_player(self, username):
        self.players.append(Player(username))
        player_count += 1

    def scan_lobby(self):
        hider = self.driver.find_element_by_id("qpAnimeNameHider")
        if "hide" in hider.get_attribute("class"):
            playround = True
        else:
            playround = False
        self.round = int(
            self.driver.find_element_by_id("qpCurrentSongCount").innerHTML)
        if playround:
            self.time = int(self.driver.find_element_by_id("qpHiderText").innerHTML)
        elif self.round > self.last_round:
            self.last_round = self.round
            anime_name = self.driver.find_element_by_id("qpAnimeName").innerHTML
            song_name = self.driver.find_element_by_id("qpSongName").innerHTML
            artist = self.driver.find_element_by_id("qpSongArtist").innerHTML
            song_type = self.driver.find_element_by_id("qpSongType").innerHTML
            song = Song(anime_name, song_name, artist, song_type)
            self.song_list.append(song)
            for player in self.players:
                status = self.driver.find_element_by_id("qpAvatar-%s" % player.username)
                if "disabled" in status.get_attribute("class"):
                    self.remove_player(player.username, "Left the game")
                answer = status.find_element_by_class_name("qpAvatarAnswerText").innerHTML
                correct = status.find_element_by_class_name("qpAvatarAnswerContainer")
                score = status.find_element_by_class_name("qpAvatarPointText").innerHTML
                if "rightAnswer" in correct.get_attribute("class"):
                    player.correct_songs.append([song, answer])
                elif "wrongAnswer" in correct.get_attribute("class"):
                    player.wrong_songs.append([song, answer])
                player.score = score

    def __repr__(self):
        out = "GameLobby(%d, [" % (self.round)
        for p in self.players:
            out += repr(p) + ", "
        out += "])"
        return out


class WaitingLobby:
    def __init__(self, driver, player_max, players=None):
        self.driver = driver
        self.players = players or [None]*player_max
        self.ready_players = [False]*player_max
        self.player_max = player_max

    def scan_lobby(self):
        for n in range(self.player_max):
            element = self.driver.find_element_by_id("lobbyAvatar%d" % n)
            is_player = element.find_element_by_class_name("lobbyAvatarTextContainer")
            if "invisible" in is_player.get_attribute("class"):
                self.players[n] = None
            else:
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

    def get_unready(self):
        not_ready = []
        for n in range(self.player_max):
            if self.players[n] is not None and not self.ready_players[n]:
                not_ready.append(self.players[n])
        return not_ready

    def generateGameLobby(self):
        self.scan_lobby()
        return GameLobby(players)

    def player_count(self):
        res = 0
        for p in self.players:
            if p is not None:
                res += 1
        return res


class MessageManager:
    database = {"greeting_player": 3, "kick_chat": 1, "kick_pm": 1,
                "banned_word": 1, "permission_denied": 1,
                "log_chat_out": 1, "something": 1, "hello_world": 1,
                "idle": 1, "get_ready": 1, "scorn_admin": 1, "starting_in": 1}
    langpack = "./langs/"

    def __init__(self, directory="en_UK"):
        self.directory = directory
        self.path = self.langpack + directory + "/"
        # self.database = MessageManager.database

    def get_message(self, name, substitutions=[], number=None):
        filename = name
        try:
            if number is None:
                filename += str(random.choice(range(self.database[name])))
            else:
                if number < self.database[name]:
                    filename += name + str(number)
                else:
                    filename += name + str(self.database[name]-1)
            filename += ".txt"
            with open(self.path + filename) as file:
                base_text = file.read()
            for n in range(len(substitutions)):
                base_text = re.sub("&%d" % (n+1), str(substitutions[n]), base_text)
            return base_text
        except Exception:
            traceback.print_exc()
            return name


class Game:
    chat_pattern = re.compile(r"(?s)<li>(.*?)</li>")
    player_message_pattern = re.compile(
        r'(?s)<img class="backerBadge.*?>.*<span class="gcUserName' +
        r'(?: clickAble" data-original-title="" title=")?">(.*?)</span>(.*)\n')
    player_joined_as_player = re.compile(
        r'<span>(.*?) joined the room.</span><br>')
    player_joined_as_spectator = re.compile(
        r'<span>(.*?) has started spectating.</span><br>')
    player_changed_to_player = re.compile(
        r'<span>(.*?) changed to player</span><br>')
    player_changed_to_spectator = re.compile(
        r'<span>(.*?) changed to spectator</span><br>')
    player_left_pattern = re.compile(
        r'<span>(.*?) has left the game.</span><br>')
    detect_amq_emoji = re.compile(
        r'\n\s<img class="amqEmoji" alt="(.*?)"' +
        r' draggable="false" src=".*?">\n')
    detect_emoji = re.compile(
        r'<img class="emoji" draggable="false" alt=".*?" src="(.*?)">')

    def __init__(self, config_file, admins=[]):
        self.admins = admins
        with open(config_file) as f:
            config = f.read()
            config = config.split("\n")
        self.code = config[0]
        self.geckodriver_path = config[1]
        self.username = config[2]
        self.admins.append(self.username)
        self.password = config[3]
        self.room_name = config[4]
        self.room_password = config[5]
        self.lang = config[6]
        self.msg_man = MessageManager(directory=self.lang)
        self.driver = webdriver.Firefox(executable_path=self.geckodriver_path)
        self.state = 0
        self.tick_rate = 0.5
        self.idle_time = 40
        self.waiting_time = 180
        self.waiting_time_limit = 0
        self.ready_wait_time = 30
        self.state_timer = int(self.idle_time/self.tick_rate)
        self.log = Logger()
        self.chat_pos = 0
        self.lobby = None
        self.max_players = 8

    def set_state_time(self, new_time):
        self.state_timer = int(new_time/self.tick_rate)

    def close(self):
        self.driver.execute_script("options.logout();")
        time.sleep(1)
        self.driver.close()

    def start(self):
        self.bootstrap()
        self.run()

    def bootstrap(self):
        code = self.code
        username = self.username
        password = self.password
        room_name = self.room_name
        room_password = self.room_password
        driver = self.driver
        driver.get('https://animemusicquiz.com')
        username_input = driver.find_element_by_id("loginUsername")
        password_input = driver.find_element_by_id("loginPassword")
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button = driver.find_element_by_id("loginButton")
        login_button.click()
        time.sleep(2)
        play = driver.find_element_by_id("mpPlayButton")
        play.click()
        time.sleep(2)
        host = driver.find_element_by_id("roomBrowserHostButton")
        host.click()
        time.sleep(2)
        driver.execute_script("hostModal.selectStandard();")
        # driver.execute_script("hostModal.selectQD();")
        time.sleep(2)
        driver.execute_script("hostModal.toggleLoadContainer();")
        time.sleep(2)
        load = driver.find_element_by_id("mhLoadFromSaveCodeButton")
        load.click()
        time.sleep(2)
        load_code_entry = driver.find_element_by_class_name("swal2-input")
        load_code_entry.send_keys(code)
        load_confirm = driver.find_element_by_class_name(
            "swal2-confirm")
        load_confirm.click()
        time.sleep(2)
        if room_password != "":
            private_button = driver.find_element_by_id("mhPrivateRoom")
            box = driver.find_element_by_class_name("customCheckbox")
            actions = ActionChains(driver)
            actions.move_to_element(box)
            actions.click(private_button)
            actions.perform()
            time.sleep(2)
            room_password_input = driver.find_element_by_id("mhPasswordInput")
            room_password_input.send_keys(room_password)
        room_name_input = driver.find_element_by_id("mhRoomNameInput")
        room_name_input.send_keys(room_name)
        start_room = driver.find_element_by_id("mhHostButton")
        start_room.click()

    def run(self):
        self.chat(self.msg_man.get_message("hello_world"))
        self.lobby = WaitingLobby(self.driver, self.max_players)
        while self.state != -1:
            if self.state == 0:
                self.idle()
            elif self.state == 1:
                self.wait_for_players()
            elif self.state == 2:
                self.wait_for_ready()
            elif self.state == 3:
                self.run_game()
            elif self.state == 4:
                self.finish_game()
                # skipController.toggle()
                pass
            self.scan_chat()
            time.sleep(self.tick_rate)
        self.close()

    def idle(self):
        self.state_timer -= 1
        if self.state_timer == 0:
            self.chat(self.msg_man.get_message("idle"))
            self.set_state_time(self.idle_time)
        self.lobby.scan_lobby()
        if self.lobby.player_count() > 1:
            self.state = 1
            self.set_state_time(self.waiting_time)
            self.waiting_time_limit = 0

    def wait_for_players(self):
        self.state_timer -= 1
        if self.state_timer % (int(10/self.tick_rate)) == 0:
            self.chat(self.msg_man.get_message("starting_in", [int((self.state_timer-self.waiting_time_limit)*self.tick_rate)]))
        if self.state_timer <= self.waiting_time_limit:
            self.chat(self.msg_man.get_message("get_ready"))
            self.set_state_time(self.ready_wait_time)
            self.state = 2
        self.lobby.scan_lobby()
        self.waiting_time_limit = (self.lobby.player_count()-1)*int(self.waiting_time_limit/self.max_players)
        if self.lobby.player_count() == 1:
            self.state = 0
            self.set_state_time(self.idle_time)

    def wait_for_ready(self):
        print("wait for ready")
        self.state_timer -= 1
        self.scan_lobby()

    def run_game():
        pass

    def finish_game():
        pass

    def chat(self, message):
        chatbox = self.driver.find_element_by_id("gcInput")
        chatbox.send_keys(message)
        chatbox.send_keys(Keys.ENTER)
        self.log.chat_out(self.msg_man.get_message("log_chat_out", [message]))

    def scan_chat(self):
        """
        scans the chat for interesting events.
        Includes, but is not limited to:
        chat commands
        players joining/leaving
        kicking/banning for unwanted phrases
        """
        chat_pos = self.chat_pos
        chat_window = self.driver.find_element_by_id("gcMessageContainer")
        chat_pattern = self.chat_pattern
        chat_html = chat_window.get_attribute('innerHTML')
        chat_messages = chat_pattern.findall(chat_html)
        # print(chat_window.text)
        player_message_pattern = self.player_message_pattern
        player_joined_as_player = self.player_joined_as_player
        player_joined_as_spectator = self.player_joined_as_spectator
        player_changed_to_player = self.player_changed_to_player
        player_changed_to_spectator = self.player_changed_to_spectator
        player_left_pattern = self.player_left_pattern
        detect_amq_emoji = self.detect_amq_emoji
        detect_emoji = self.detect_emoji

        for match in chat_messages[chat_pos:]:
            print(match)
            player_message = player_message_pattern.search(match)
            join_as_player = None
            join_as_spectator = None
            spectator_to_player = None
            player_to_spectator = None
            player_left = None
            done = False
            if player_message:
                name = player_message.group(1)
                message = player_message.group(2)
                num = 1
                while num == 1:
                    message, num = detect_amq_emoji.subn(r"<\g<1>>", message, 1)
                num = 1
                while num == 1:
                    message, num = detect_emoji.subn(r"<\g<1>>", message, 1)
                self.log.chat("%s said: \"%s\"" % (name, message))
                if "bad word" in message:
                    self.kick_player(name, self.msg_man.get_message("banned_word"))
                elif message[0] == "!":
                    self.handle_command(name, message[1:])
                done = True
            if not done:
                join_as_player = player_joined_as_player.search(match)
                # the glory of not being able to assign in an if
            if not done and join_as_player:
                self.chat(self.msg_man.get_message("greeting_player",
                                                   [join_as_player.group(1)]))
                done = True
                pass
            if not done:
                join_as_spectator = player_joined_as_spectator.search(match)
            if not done and join_as_spectator:
                done = True
                pass
            if not done:
                spectator_to_player = player_changed_to_player.search(match)
            if not done and spectator_to_player:
                done = True
                pass
            if not done:
                player_to_spectator = player_changed_to_spectator.search(match)
            if not done and player_to_spectator:
                done = True
                pass
            if not done:
                player_left = player_left_pattern.search(match)
            if not done and player_left:
                done = True
                pass
        if len(chat_messages) > chat_pos:
            self.chat_pos = len(chat_messages)

    def message_player(self, username, message):
        pass

    def kick_player(self, username, reason=None):
        reason = reason or self.msg_man.get_message("something")
        if username not in self.admins:
            self.driver.execute_script('lobby.kickPlayer("%s")' % username)
            self.chat(self.msg_man.get_message("kick_chat", [username, reason]))
            self.message_player(username,
                                self.msg_man.get_message("kick_pm", [reason]))
        elif username != self.username:
            self.chat(self.msg_man.get_message("scorn_admin", [username]))

    def scan_lobby(self):
        pass

    def handle_command(self, user, command):
        print("Command detected: %s" % command)
        match = re.match("stop|addadmin|pause|help|votekick|voteban|about", command)
        if not match:
            self.chat("not implemented")
            return
        match = re.match("addadmin ([^ ]*)", command)
        if match:
            self.admins.append(match.group(1))
        elif command == "stop":
            if user in self.admins:
                print("stop detected")
                self.state = -1
            else:
                self.chat(self.msg_man.get_message("permission_denied",
                                                   [user]))
        pass


def main():
    """
    the main function, where the magic happens
    """
    # sys_log("AMQ-automator started")
    game = Game("default.config")
    try:
        game.start()
    except Exception as e:
        traceback.print_exc()
        game.close()

    return
    with open("default.config") as f:
        config = f.read()
        config = config.split("\n")
    code = config[0]
    geckodriver_path = config[1]
    username = config[2]
    admins.append(username)
    password = config[3]
    room_name = config[4]
    room_password = config[5]
    driver = webdriver.Firefox(executable_path=geckodriver_path)
    driver.get('https://animemusicquiz.com')
    username_input = driver.find_element_by_id("loginUsername")
    password_input = driver.find_element_by_id("loginPassword")
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element_by_id("loginButton")
    login_button.click()
    time.sleep(2)
    play = driver.find_element_by_id("mpPlayButton")
    play.click()
    time.sleep(2)
    host = driver.find_element_by_id("roomBrowserHostButton")
    host.click()
    time.sleep(2)
    driver.execute_script("hostModal.selectStandard();")
    # driver.execute_script("hostModal.selectQD();")
    time.sleep(2)
    driver.execute_script("hostModal.toggleLoadContainer();")
    time.sleep(2)
    load = driver.find_element_by_id("mhLoadFromSaveCodeButton")
    load.click()
    time.sleep(2)
    load_code_entry = driver.find_element_by_class_name("swal2-input")
    load_code_entry.send_keys(code)
    load_confirm = driver.find_element_by_class_name(
        "swal2-confirm")
    load_confirm.click()
    time.sleep(2)
    if room_password != "":
        private_button = driver.find_element_by_id("mhPrivateRoom")
        box = driver.find_element_by_class_name("customCheckbox")
        actions = ActionChains(driver)
        actions.move_to_element(box)
        actions.click(private_button)
        actions.perform()
        time.sleep(2)
        room_password_input = driver.find_element_by_id("mhPasswordInput")
        room_password_input.send_keys(room_password)
    room_name_input = driver.find_element_by_id("mhRoomNameInput")
    room_name_input.send_keys(room_name)
    start_room = driver.find_element_by_id("mhHostButton")
    start_room.click()
    # lobby.viewSettings();
    # lbStartButton
    # gcMessageContainer
    # lobbyAvatar3
    # <h3 class="lobbyAvatarLevel">-1</h3>
    # gcQueueList
    # gameChat.viewQueue();
    # gcQueueCount
    # lobby.kickPlayer("")
    # lobby.changeToSpectator("")
    # videoUrl = videoPreview.get_attribute("src")
    # swal2-popup
    # class="swal2-confirm
    # class="swal2-cancel
    chat(driver, "Hello World!")
    state = 0  # 0: idle
    state_timer = 40
    game = Game(driver)
    game.run()
    try:
        while not stop:
            # program loop
            if state == 0:
                scan_lobby(driver)
                if state_timer == 0:
                    chat(driver, "idle1")
                    state_timer = 40
                pass
            elif state == 1:
                pass
            elif state == 2:
                pass
            scan_chat(driver)
            time.sleep(1)
            state_timer -= 1
    except Exception as e:
        traceback.print_exc()
    else:
        sys_log("program closed normally")
    # input("Press enter to terminate")
    driver.execute_script("options.logout();")
    time.sleep(1)
    driver.close()


if __name__ == "__main__":
    main()
