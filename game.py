from lobby import Lobby, GameLobby, WaitingLobby
from logger import Logger
from message_manager import MessageManager
from player import Player
from song import Song
from database import Database
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from collections import defaultdict
import time
import traceback
import random


def log_exceptions():
    error = traceback.format_exc()
    print(error)
    with open("exeptions.log", "a", encoding="utf-8") as f:
        f.write(error)


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
        self.banned_players_list = []
        self.enable_leaderboard = False
        with open(config_file) as f:
            config = f.read()
            config = config.split("\n")
        self.code = config[0]
        self.geckodriver_path = config[1]
        self.username = config[2]
        self.password = config[3]
        self.room_name = config[4]
        self.room_password = config[5]
        self.lang = config[6]
        self.banned_word_path = config[7]
        self.chattiness = int(config[8]) / 100
        self.banned_players_file = config[9]
        self.admins_file = config[10]
        self.db_file = config[11]
        self.read_config_file(config_file)
        self.admins.append(self.username)
        self.database = Database(self.db_file)
        with open(self.admins_file) as f:
            for line in f.readlines():
                self.admins.append(line[:-1])
        print(self.admins)
        for a in self.admins:
            self.database.add_administrator(a)
        with open(self.banned_players_file) as f:
            for line in f.readlines():
                self.banned_players_list.append(line[:-1])
        print(self.banned_players_list)
        with open(self.banned_word_path) as f:
            list = f.read().split("\n")[:-1]
            self.banned_word_pattern = re.compile(r"\b(" + "|".join(list) + ")")
        self.msg_man = MessageManager(directory=self.lang)
        self.driver = webdriver.Firefox(executable_path=self.geckodriver_path)
        self.state = 0
        self.tick_rate = 0.5
        self.idle_time = 3600
        self.waiting_time = 45
        self.waiting_time_limit = 0
        self.ready_wait_time = 15
        self.state_timer = int(self.idle_time/self.tick_rate)
        self.log = Logger()
        self.chat_pos = 0
        self.lobby = None
        self.max_players = 40
        self.last_round = -1
        self.skipped_playback = False
        self.kick_list = []
        self.silent_counter = int(5/self.tick_rate)
        self.detect_command = re.compile(r"(?i)(?:(?:/)|(?:@"+self.username+r"\s))(.*)")
        self.message_backlog = []
        self.player_records = {}
        self.recently_used_list = []
        self.last_round_list = None
        self.delay = 3
        self.player_anime_answer = {}  # str to str, for spectators
        self.player_anime_score = defaultdict(lambda: 0)  # str to int
        self.player_song_answer = {}  # str to str
        self.player_song_score = defaultdict(lambda: 0)  # str to int
        self.player_artist_answer = {}
        self.player_artist_score = defaultdict(lambda: 0)
        self.answer_limit_upper = 3
        self.answer_limit_lower = 0
        self.last_generated = -1
        self.tiers = {}
        self.max_chat_message_length = 150

    def read_config_file(self, config_file):
        with open(config_file) as f:
            config = f.read()
        match = re.search(r"(?im)^enable_leaderboard\s?=\s?(true|false)", config)
        if match:
            if match.group(1).lower() == "true":
                print("ENABLE_LEADERBOARD=TRUE")
                self.enable_leaderboard = True
            else:
                print("ENABLE_LEADERBOARD=FALSE")
                self.enable_leaderboard = False
        else:
            print("ENABLE_LEADERBOARD=DEFAULT(FALSE)")
            self.enable_leaderboard = False

    def set_chattiness(self, newpercentage):
        self.chattiness = newpercentage / 100

    def tick(self):
        time.sleep(self.tick_rate)

    def set_state_time(self, new_time):
        self.state_timer = int(new_time/self.tick_rate)

    def set_state_idle(self):
        self.state = 0
        self.set_state_time(self.idle_time)
        self.auto_chat("idle")

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
        time.sleep(self.delay)
        driver.execute_script(""" document.getElementById("mpNewsContainer").innerHTML = '<button id="myfunnyvalentine" onclick="expandLibrary.lobby = lobby">Click me!</button>' """)
        ActionChains(driver).move_to_element(driver.find_element_by_id("myfunnyvalentine")).click().perform()
        driver.execute_script(""" document.getElementById("mpNewsContainer").innerHTML = '' """)
        play = driver.find_element_by_id("mpPlayButton")
        play.click()
        time.sleep(self.delay)
        host = driver.find_element_by_id("roomBrowserHostButton")
        host.click()
        time.sleep(self.delay)
        driver.execute_script("hostModal.selectStandard();")
        # driver.execute_script("hostModal.selectQD();")
        time.sleep(self.delay)
        driver.execute_script("hostModal.toggleLoadContainer();")
        time.sleep(self.delay)
        load = driver.find_element_by_id("mhLoadFromSaveCodeButton")
        load.click()
        time.sleep(self.delay)
        load_code_entry = driver.find_element_by_class_name("swal2-input")
        load_code_entry.send_keys(code)
        load_confirm = driver.find_element_by_class_name(
            "swal2-confirm")
        load_confirm.click()
        time.sleep(self.delay)
        driver.find_element_by_id("mhRoomSizeAdvancedText").send_keys(Keys.BACKSPACE)
        driver.find_element_by_id("mhRoomSizeAdvancedText").send_keys(Keys.BACKSPACE)
        driver.find_element_by_id("mhRoomSizeAdvancedText").send_keys("40")
        if room_password != "":
            private_button = driver.find_element_by_id("mhPrivateRoom")
            box = driver.find_element_by_class_name("customCheckbox")
            actions = ActionChains(driver)
            actions.move_to_element(box)
            actions.click(private_button)
            actions.perform()
            time.sleep(self.delay)
            room_password_input = driver.find_element_by_id("mhPasswordInput")
            room_password_input.send_keys(room_password)
        room_name_input = driver.find_element_by_id("mhRoomNameInput")
        room_name_input.send_keys(room_name)
        start_room = driver.find_element_by_id("mhHostButton")
        start_room.click()
        time.sleep(self.delay)
        driver.execute_script("expandLibrary.lobby.changeToSpectator(selfName);")
        self.max_chat_message_length = driver.execute_script("return gameChat.MAX_MESSAGE_LENGTH")

    def run(self):
        self.auto_chat("hello_world")
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
                self.record_game()
            elif self.state == 5:
                self.finish_game()
            #    # skipController.toggle()
            self.scan_chat()
            self.send_backlog()
            self.state_timer -= 1
            self.silent_counter -= 1
            if self.silent_counter < 0:
                self.driver.execute_script("document.getElementsByTagName('body')[0].click();")
                for u in self.kick_list:
                    self.silent_kick(u)
                self.silent_counter = int(5/self.tick_rate)
            self.tick()
        self.close()

    def idle(self):
        if self.state_timer == 0:
            self.auto_chat("idle")

            self.set_state_time(self.idle_time)
        self.lobby.scan_lobby()
        if self.lobby.player_count > 0:
            self.state = 1
            self.set_state_time(self.waiting_time)
            self.waiting_time_limit = 0
        self.check_if_active_game()

    def check_if_active_game(self):
        try:
            new_lobby = self.lobby.generateGameLobby()
            new_lobby.scan_lobby()
            new_lobby.verify_players()
            self.mute_sound()
            self.select_quality("Sound")
            self.state = 3
            self.last_round = -1
            self.lobby = new_lobby
        except Exception:
            pass

    def wait_for_players(self):
        time_left = self.state_timer - self.waiting_time_limit
        if time_left % (int(10/self.tick_rate)) == 0 or time_left <= 0:
            if time_left < 0:
                time_left = 0
            self.auto_chat("starting_in", [int((time_left)*self.tick_rate)])
        if self.state_timer <= self.waiting_time_limit:
            self.auto_chat("get_ready")
            for p in self.lobby.get_unready():
                self.chat("@%s" % p.username)
            self.set_state_time(self.ready_wait_time)
            self.state = 2
            return
        self.lobby.scan_lobby()
        self.waiting_time_limit = int(((self.lobby.player_count)*(self.waiting_time/(self.max_players)) - 10)/self.tick_rate)
        if self.lobby.player_count == 0:
            self.set_state_idle()

    def wait_for_ready(self):
        # print("wait for ready")
        self.lobby.scan_lobby()
        time_remaining = self.state_timer*self.tick_rate
        if self.lobby.player_count == 0:
            self.set_state_idle()
            return
        if self.lobby.all_ready():
            self.start_game()
        elif self.state_timer < int(-10/self.tick_rate):
            self.start_game()
        elif self.state_timer == 0:
            for p in self.lobby.get_unready():
                self.move_to_spectator(p.username)
        elif (time_remaining) % 1 == 0:
            if (time_remaining) < 0:
                self.chat(str(int(time_remaining+10))+"!")
            else:
                self.chat(str(int(time_remaining)))

    def start_game(self):
        self.driver.execute_script("expandLibrary.lobby.fireMainButtonEvent(true);")
        time.sleep(self.delay)
        try:
            pop_up = self.driver.find_element_by_class_name("swal2-container")
            accept = pop_up.find_element_by_class_name("swal2-confirm")
            accept.click()
            time.sleep(self.delay)
        except Exception:
            pass
        try:
            time.sleep(self.delay)
            new_lobby = self.lobby.generateGameLobby()
            new_lobby.scan_lobby()
            new_lobby.verify_players()
            self.mute_sound()
            self.select_quality("Sound")
            self.state = 3
            self.last_round = -1
            self.lobby = new_lobby
        except Exception:
            self.set_state_idle()
            self.auto_chat("no_songs")
            self.exchange_players()

    def run_game(self):
        try:
            self.lobby.scan_lobby()
        except Exception:
            # this happens if everyone leaves during the reveal phase
            log_exceptions()
            self.chat("Oh Fiddlesticks! aborting")
            self.abort_game()
            return
        if self.lobby.round > self.last_round:
            self.last_round = self.lobby.round
            #self.driver.execute_script('skipController.toggle()')
            self.skipped_playback = False
        if self.lobby.playback and not self.skipped_playback:
            self.skipped_playback = True
            #self.driver.execute_script('skipController.toggle()')
            if random.random() < self.chattiness:
                self.auto_chat("answer_reveal", [self.lobby.last_song.anime])
            # for p in self.lobby.players:
            #    print("%s: %d" % (p.username, p.score))
            # print(self.player_anime_answer)
            # print(self.player_song_answer)
            # print(self.player_artist_answer)
            correct_players = []
            was_wrong = False
            for p, a in self.player_anime_answer.items():
                if a == "":
                    continue
                if a.lower() == self.lobby.last_song.anime.lower():
                    self.player_anime_score[p] += 1
                    correct_players.append(p)
                else:
                    was_wrong = True
                    self.player_anime_score[p] += 0
            self.player_anime_answer = {}
            if len(correct_players) > 0:
                self.chat("anime++ " + " ".join(correct_players))
            elif was_wrong:
                self.chat(self.lobby.last_song.anime)
            correct_players = []
            for p, a in self.player_song_answer.items():
                if a == "":
                    continue
                if a.lower() == self.lobby.last_song.name.lower():
                    self.player_song_score[p] += 1
                    correct_players.append(p)
                else:
                    # print("'%s' != '%s'", a, self.lobby.last_song.name)
                    self.player_song_score[p] += 0
            self.player_song_answer = {}
            if len(correct_players) > 0:
                self.chat("song++ " + " ".join(correct_players))
            correct_players = []
            for p, a in self.player_artist_answer.items():
                if a == "":
                    continue
                if a.lower() == self.lobby.last_song.artist.lower():
                    self.player_artist_score[p] += 1
                    correct_players.append(p)
                else:
                    # print("'%s' != '%s'", a, self.lobby.last_song.artist)
                    self.player_artist_score[p] += 0
            self.player_artist_answer = {}
            if len(correct_players) > 0:
                self.chat("artist++ " + " ".join(correct_players))
            if self.lobby.round == self.lobby.total_rounds:
                self.state = 4
                return
        if self.lobby.player_count < 1:
            self.abort_game()

    def abort_game(self):
        self.auto_chat("abort_game")
        self.driver.execute_script('quiz.startReturnLobbyVote();')
        time.sleep(1)
        #self.driver.execute_script('skipController.toggle()')
        time.sleep(1)
        self.state = 4

    def record_game(self):
        try:
            for p in self.lobby.players:
                self.player_records[p.username] = [p, False]
            self.last_round_list = self.lobby.song_list
            self.recently_used_list = []
            self.database.record_game(self.lobby.song_list, self.lobby.players)
            self.auto_chat("game_complete")
            i = len(self.player_anime_score)
            i += len(self.player_song_score)
            i += len(self.player_artist_score)
            if i > 0:
                self.chat("bonus game scores:")
                if len(self.player_anime_score) > 0:
                    self.chat("anime guess")
                    self.print_scores(self.player_anime_score)
                if len(self.player_song_score) > 0:
                    self.chat("song guess")
                    self.print_scores(self.player_song_score)
                if len(self.player_artist_score) > 0:
                    self.chat("artist guess")
                    self.print_scores(self.player_artist_score)
            self.player_anime_score = defaultdict(lambda: 0)
            self.player_song_score = defaultdict(lambda: 0)
            self.player_artist_score = defaultdict(lambda: 0)
        except Exception:
            log_exceptions()
        self.state = 5

    def print_scores(self, player_score_pair):
        scores = []
        names = []
        for k, v in player_score_pair.items():
            names.append(k)
            scores.append(v)
        sortedscores = []
        sortednames = []
        while len(scores) > 0:
            maxscore = -1
            maxpos = -1
            for i in range(len(scores)):
                if scores[i] > maxscore:
                    maxpos = i
                    maxscore = scores[i]
            sortedscores.append(scores[maxpos])
            sortednames.append(names[maxpos])
            scores.pop(maxpos)
            names.pop(maxpos)
        pos = 1
        prevscore = -1
        toadd = 0
        for i in range(len(sortedscores)):
            if sortedscores[i] != prevscore:
                pos += toadd
                toadd = 0
            prevscore = sortedscores[i]
            toadd += 1
            self.chat("%d. %s %d" % (pos, sortednames[i], sortedscores[i]))

    def finish_game(self):
        """Waits for the lobby to change"""
        try:
            self.lobby.scan_lobby()
            return
        except Exception:
            pass
        self.exchange_players()
        self.lobby = WaitingLobby(self.driver, self.max_players)
        self.state = 0
        self.set_state_time(self.idle_time)

    def exchange_players(self):
        players = self.lobby.all_players()
        active_players = self.lobby.active_players()
        queue_size = int(self.driver.find_element_by_id("gcQueueCount").text)
        if queue_size == 0:
            return
        queue_size += (len(players)-len(active_players))  # original size
        if queue_size < self.max_players-len(active_players):
            return
        self.auto_chat("exchange_players")
        names = [p.username for p in players if p.username != self.username]
        chosen = []
        if queue_size >= self.max_players:
            chosen = names
        else:
            for m in range(queue_size):
                choice = random.choice(names)
                names = [n for n in names if n != choice]
                chosen.append(choice)
        for n in range(2):
            for name in chosen:
                self.move_to_spectator(name)
            self.tick()

    def move_to_spectator(self, username):
        self.driver.execute_script('expandLibrary.lobby.changeToSpectator("%s")' % username)

    def mute_sound(self):
        try:
            icon = self.driver.find_element_by_id("qpVolumeIcon")
            if "off" not in icon.get_attribute("class"):
                icon.click()
        except Exception:
            log_exceptions()

    def select_quality(self, quality):
        try:
            quality_list = self.driver.find_element_by_id("qpQualityList")
            cog = self.driver.find_element_by_id("qpQuality")
            actions = ActionChains(self.driver)
            actions.move_to_element(cog)
            actions.perform()
            for p in quality_list.find_elements_by_tag_name("li"):
                if p.text == quality:
                    button = p
            time.sleep(1)
            actions = ActionChains(self.driver)
            actions.move_to_element(button)
            actions.click(button)
            actions.perform()
        except Exception:
            log_exceptions()

    def chat(self, message):
        """Sends a message through the chat
        """
        try:
            # chatbox = self.driver.find_element_by_id("gcInput")
            # chatbox.send_keys(message)
            # chatbox.send_keys(Keys.ENTER)
            msg = message[:150]
            self.driver.execute_script("""
            socket.sendCommand(
                {
                    type: "lobby",
                    command: "game chat message",
                    data:
                    {
                        msg: arguments[0]
                    }
                }
            );""", msg)
            self.log.chat_out(self.msg_man.get_text("log_chat_out", [message]))
        except Exception:
            log_exceptions()

    def auto_chat(self, message_name, arguments=[]):
        self.chat(self.msg_man.get_text(message_name, arguments))

    def true_log_chat(self, message):
        try:
            with open(self.username + "-true.log", "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception:
            pass

    def scan_chat(self):
        """
        scans the chat for interesting events.
        Includes, but is not limited to:
        chat commands
        players joining/leaving
        kicking/banning for unwanted phrases
        """
        try:
            chat_pos = self.chat_pos
            chat_window = self.driver.find_element_by_id("gcMessageContainer")
            # chat_pattern = self.chat_pattern
            # chat_html = chat_window.get_attribute('innerHTML')
            # chat_messages = chat_pattern.findall(chat_html)
            chat_messages_raw = chat_window.find_elements_by_tag_name("li")
            chat_messages = [c.get_attribute("innerHTML") for c in chat_messages_raw]
            if len(chat_messages) > chat_pos:
                self.chat_pos = len(chat_messages)
            if self.chat_pos > 50:
                self.clear_chat()
            # print(chat_window.text)
            gcMessageFix = re.compile('<span class="gcMessage">(.*)</span>')
            for match in chat_messages[chat_pos:]:
                self.true_log_chat(match)
                player_message = self.player_message_pattern.search(match)

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
                        message, num = self.detect_amq_emoji.subn(r"<\g<1>>", message, 1)
                    num = 1
                    while num == 1:
                        message, num = self.detect_emoji.subn(r"<\g<1>>", message, 1)
                    message = gcMessageFix.search(message).group(1)
                    self.log.chat("%s said: \"%s\"" % (name, message))
                    self.database.save_message(name, message)
                    match = self.detect_command.match(message)
                    if self.detect_banned_words(message):
                        self.kick_player(name, self.msg_man.get_text("banned_word"))
                    elif match:
                        self.handle_command(name, match.group(1))
                    done = True
                if not done:
                    join_as_player = self.player_joined_as_player.search(match)
                    # the glory of not being able to assign in an if
                if join_as_player:
                    username = join_as_player.group(1)
                    self.database.create_player(username)
                    if self.detect_banned_words(username):
                        self.kick_player(username, self.msg_man.get_text("banned_word"))
                    else:
                        self.auto_chat("greeting_player",
                                       [join_as_player.group(1)])
                    done = True
                    pass
                if not done:
                    join_as_spectator = self.player_joined_as_spectator.search(match)
                if join_as_spectator:
                    username = join_as_spectator.group(1)
                    self.database.create_player(username)
                    if self.detect_banned_words(username):
                        self.kick_player(username, self.msg_man.get_text("banned_word"))
                    else:
                        self.auto_chat("greeting_spectator", [username])
                    done = True
                    pass
                if not done:
                    spectator_to_player = self.player_changed_to_player.search(match)
                if spectator_to_player:
                    done = True
                    pass
                if not done:
                    player_to_spectator = self.player_changed_to_spectator.search(match)
                if player_to_spectator:
                    done = True
                    pass
                if not done:
                    player_left = self.player_left_pattern.search(match)
                if player_left:
                    done = True
                    pass
        except Exception:
            log_exceptions()

    def clear_chat(self):
        self.chat_pos = 0
        self.driver.execute_script('document.getElementById("gcMessageContainer").innerHTML = ""')

    def detect_banned_words(self, message):
        try:
            match = self.banned_word_pattern.search(message.lower())
            if match:
                # print(match.group(0))
                return True
            else:
                return False
        except Exception:
            log_exceptions()
            return False

    def message_player(self, username, message):
        # socialTab.startChat("username")
        try:
            self.driver.execute_script('socialTab.startChat("%s")' % username)
            box = self.driver.find_element_by_id("chatBox-%s" % username)
            chatbox = box.find_element_by_tag_name("textarea")
            chatbox.send_keys(message)
            chatbox.send_keys(Keys.ENTER)
            self.log.chat_out(self.msg_man.get_text("pm_out",
                                                    [username, message]))
        except Exception as e:
            log_exceptions()

    def send_backlog(self):
        try:
            amount = min(3, len(self.message_backlog))
            if amount == 0:
                return
            for msg in self.message_backlog[:amount]:
                self.message_player(msg[0], msg[1])
            self.message_backlog = self.message_backlog[amount:]
        except Exception:
            log_exceptions()
            self.message_backlog = []

    def ban_player(self, username, reason=None, issuer=None):
        try:
            reason = reason or self.msg_man.get_text("something")
            issuer = issuer or self.msg_man.get_text("system")
            with open(self.banned_players_file, "a", encoding="utf-8") as f:
                f.write(self.msg_man.get_text("ban_comment", [username, issuer, reason])+"\n")
            reason = self.msg_man.get_text("banned_for", [reason])
            self.kick_player(username, reason, issuer)
            self.database.ban_player(username, reason, issuer)

        except Exception:
            log_exceptions()

    def check_for_disconnect(self):
        body = self.driver.find_element_by_tag_name("body")
        return "swal2-shown" in body.get_attribute("class")

    def handle_popup(self, accept=True):
        try:
            self.tick()
            pop_up = self.driver.find_element_by_class_name("swal2-container")
            if accept:
                button = pop_up.find_element_by_class_name("swal2-confirm")
            else:
                button = pop_up.find_element_by_class_name("swal2-cancel")
            button.click()
        except Exception:
            log_exceptions()

    def kick_player(self, username, reason=None, issuer=None):
        try:
            reason = reason or self.msg_man.get_text("something")
            issuer = issuer or self.msg_man.get_text("system")
            if not self.database.is_moderator(username):
                if self.state < 3:
                    self.lobby.remove_player(username, reason)
                    self.driver.execute_script(
                        'expandLibrary.lobby.kickPlayer("%s")' % username)
                    self.handle_popup()
                    self.auto_chat("kick_chat", [username, reason])
                    self.message_player(username,
                                        self.msg_man.get_text("kick_pm",
                                                              [reason]))
                elif username not in [p.username for p in self.lobby.players]:
                    self.driver.execute_script(
                        'gameChat.kickSpectator("%s")' % username)
                    self.handle_popup()
                    self.auto_chat("kick_chat", [username, reason])
                    self.message_player(username,
                                        self.msg_man.get_text("kick_pm",
                                                              [reason]))
                self.kick_list.append(username)
            elif username != self.username:
                self.auto_chat("scorn_admin", [username])
        except Exception:
            log_exceptions()

    def silent_kick(self, username):
        spectator_list = [s.lower() for s in self.get_spectators()]
        print(spectator_list)
        if self.state < 3:
            player_list = [player.username.lower() for player in self.lobby.all_players()]
            if username.lower() in spectator_list or username.lower() in player_list:
                self.driver.execute_script('expandLibrary.lobby.kickPlayer("%s")' % username)
                self.handle_popup()
        elif username.lower() in spectator_list:
            self.driver.execute_script(
                'gameChat.kickSpectator("%s")' % username)
            self.handle_popup()

    def get_spectators(self):
        try:
            self.driver.execute_script("gameChat.viewSpectators()")
            spectator_list = self.driver.find_element_by_id("gcSpectatorList")
            name_list = spectator_list.find_elements_by_tag_name("h3")
            ret = [name.text for name in name_list]
            self.driver.execute_script("gameChat.viewChat()")
            return ret
        except Exception:
            return []

    def get_queue(self):
        self.driver.execute_script("gameChat.viewQueue()")
        spectator_list = self.driver.find_element_by_id("gcQueueList")
        name_list = spectator_list.find_elements_by_tag_name("h3")
        ret = [name.text for name in name_list]
        self.driver.execute_script("gameChat.viewChat()")
        return ret

    def generate_tiers(self):
        """generates the tiers
        by level:
        Champion: the best player(s) on the bot
        Grandmaster: top 0.5%
        Master: top 2%
        Diamond: top 5%
        Platinum: top 20%
        Gold: top 40%
        Silver: top 80%
        Bronze: top 99.9%
        the bot: literally the worst players"""
        if(self.last_generated < self.database.get_total_games()):
            self.tiers["champion"] = -1
            self.tiers["grandmaster"] = -1
            self.tiers["master"] = -1
            self.tiers["diamond"] = -1
            self.tiers["platinum"] = -1
            self.tiers["gold"] = -1
            self.tiers["silver"] = -1
            self.tiers["bronze"] = -1
            self.tiers[self.username+"bot"] = -1
            player_ratings = self.database.get_all_ratings()
            total = len(player_ratings)
            count = 0
            for player_id, rating in player_ratings:
                if(self.tiers["champion"] == -1 and count == 0):
                    self.tiers["champion"] = rating
                elif(self.tiers["grandmaster"] == -1 and count >= total*0.005):
                    self.tiers["grandmaster"] = rating
                elif(self.tiers["master"] == -1 and count >= total*0.02):
                    self.tiers["master"] = rating
                elif(self.tiers["diamond"] == -1 and count >= total*0.05):
                    self.tiers["diamond"] = rating
                elif(self.tiers["platinum"] == -1 and count >= total*0.20):
                    self.tiers["platinum"] = rating
                elif(self.tiers["gold"] == -1 and count >= total-total*0.40):
                    self.tiers["gold"] = rating
                elif(self.tiers["silver"] == -1 and count >= total*0.80):
                    self.tiers["silver"] = rating
                elif(self.tiers["bronze"] == -1 and count == total-2):
                    self.tiers["bronze"] = rating
                elif(count == total-1):
                    self.tiers[self.username+"bot"] = rating
                count += 1

    def elo_to_tier(self, elo):
        """returns the tier equivalent"""
        self.generate_tiers()
        if(elo >= self.tiers["champion"]):
            return "Champion"
        elif(elo >= self.tiers["grandmaster"]):
            return "Grandmaster"
        elif(elo >= self.tiers["master"]):
            return "Master"
        elif(elo >= self.tiers["diamond"]):
            return "Diamond"
        elif(elo >= self.tiers["platinum"]):
            return "Platinum"
        elif(elo >= self.tiers["gold"]):
            return "Gold"
        elif(elo >= self.tiers["silver"]):
            return "Silver"
        elif(elo >= self.tiers["bronze"]):
            return "Bronze"
        elif(elo >= self.tiers[self.username+"bot"]):
            return self.username
        else:
            return "Undefined"

    def profile(self, username):
        id = self.database.get_player_id(username)
        if id is None:
            self.auto_chat("profile_unknown")
            return
        truename = self.database.get_player_truename(id)
        self.auto_chat("profile_username", [truename])
        elo = self.database.get_or_create_elo(id)
        self.auto_chat("profile_elo", [elo, self.elo_to_tier(elo)])
        play_count = self.database.get_player_game_count(id)
        self.auto_chat("profile_play_count", [play_count])
        wins = self.database.get_player_win_count(id)
        self.auto_chat("profile_wins", [wins])
        song_count = self.database.get_player_song_count(id)
        self.auto_chat("profile_song_count", [song_count])
        hit_count = self.database.get_player_hit_count(id)
        self.auto_chat("profile_hit_count", [hit_count])
        hit_rate = self.database.get_player_hit_rate(id)
        self.auto_chat("profile_hit_rate", [hit_rate])

    def is_answer_time(self):
        box = self.driver.find_element_by_id("qpVideoHider")
        if "hide" not in box.get_attribute("class"):
            text = self.driver.find_element_by_id("qpHiderText")
            return ("Answers" == text.text
                    or "0" == text.text
                    or "1" == text.text)
        else:
            return False

    def leaderboard(self, top=10):
        self.auto_chat("leaderboard", [top])
        position = 1
        pos_to_add = 0
        last_score = 1000000
        for name, result in self.database.get_result_leaderboard_truename(top):
            if (result < last_score):
                position += pos_to_add
                pos_to_add = 0
                last_score = result
            self.chat("%2d: %20s | %3d" % (position, name, result))
            pos_to_add += 1

    def handle_command(self, user, command):
        try:
            # print("Command detected: %s" % command)
            match = re.match(r"(?i)stop|addadmin|addmoderator|help|kick|ban|about|forceevent|missed|setchattiness|list|answer\s|answeranime|answersong|answerartist|vote|elo|profile|leaderboard|ping", command)
            if not match:
                self.auto_chat("unknown_command")
                return
            if command == "ping":
                self.chat("Pong!")
            if command == "help":
                self.auto_chat("help")
                if self.database.is_moderator(user):
                    self.auto_chat("help_moderator")
                if self.database.is_administrator(user):
                    self.auto_chat("help_admin")
                return
            match = re.match(r"(?i)help\s([^ ]*)", command)
            if match:
                command = match.group(1).lower()
                match = re.match(r"(?i)leaderboard|stop|addadmin|addmoderator|help|kick|ban|about|forceevent|missed|setchattiness|list|answer|answeranime|answersong|answerartist|vote|elo|profile", command)
                if not match:
                    self.auto_chat("unknown_command")
                    return
                if command == "help":
                    self.auto_chat("help_help")
                elif command == "about":
                    self.auto_chat("help_about")
                elif command == "list":
                    self.auto_chat("help_list")
                elif command == "missed":
                    self.auto_chat("help_missed")
                elif not self.database.is_moderator(user):
                    self.auto_chat("permission_denied", [user])
                elif command == "setchattiness":
                    self.auto_chat("help_setchattiness", [self.username])
                elif command == "kick":
                    self.auto_chat("help_kick")
                elif command == "forceevent":
                    self.auto_chat("help_forceevent")
                elif not self.database.is_administrator(user):
                    self.auto_chat("permission_denied", [user])
                elif command == "stop":
                    self.auto_chat("help_stop")
                elif command == "addadmin":
                    self.auto_chat("help_addadmin")
                elif command == "addmoderator":
                    self.auto_chat("help_addmoderator")
                elif command == "ban":
                    self.auto_chat("help_ban")
                return
            if command.lower() == "about":
                self.auto_chat("about")
                if random.random()*100 > 90:
                    self.chat(self.msg_man.get_text("about_joke_intro") + " " +
                              self.msg_man.get_text("about_joke"))
                return
            if command.lower() == "profile":
                self.profile(user)
                return
            if command.lower() == "leaderboard":
                if self.enable_leaderboard:
                    self.leaderboard()
                else:
                    self.auto_chat("leaderboard_disabled")
                return
            if command.lower() == "elo":
                id = self.database.get_player_id(user)
                elo = self.database.get_or_create_elo(id)
                self.auto_chat("elo", [user, elo, self.elo_to_tier(elo)])
                return
            if command.lower() == "missed":
                if user in self.player_records:
                    record = self.player_records[user]
                    if not record[1]:
                        player = record[0]
                        miss = player.wrong_songs
                        messages = []
                        for s in miss:
                            song = s[0]
                            answer = s[1]

                            messages.append([user, str(song)])
                            messages.append([user, self.msg_man.get_text("you_answered", [answer])])
                        self.message_backlog += messages
                    else:
                        self.auto_chat("already_done", [user])
                    record[1] = True
                else:
                    self.auto_chat("no_game_recorded", [user])
                return
            if command.lower() == "list":
                if self.last_round_list is None:
                    self.auto_chat("list_fail_no_games", [user])
                elif user in self.recently_used_list:
                    self.auto_chat("list_fail_already_done", [user])
                else:
                    song_list = self.last_round_list
                    messages = []
                    for s in song_list:
                        messages.append([user, str(s)])
                    self.message_backlog += messages
                    self.auto_chat("list_success", [user])
                    self.recently_used_list.append(user)
                return
            a = self.is_answer_time()
            match = re.match(r"(?i)answer\s(.*)\s?[|]\s?(.*)\s?[|]\s?(.*)\s?", command)
            if match:
                if a:
                    self.player_anime_answer[user] = match.group(1)
                    self.player_song_answer[user] = match.group(2)
                    self.player_artist_answer[user] = match.group(3)
                else:
                    self.chat("please submit your answer at \"Answers\"")
                return
            match = re.match(r"(?i)answeranime\s(.*)\s?", command)
            if match:
                if a:
                    self.player_anime_answer[user] = match.group(1)
                else:
                    self.chat("please submit your answer at \"Answers\"")
                return
            match = re.match(r"(?i)answersong\s(.*)\s?", command)
            if match:
                if a:
                    self.player_song_answer[user] = match.group(1)
                else:
                    self.chat("please submit your answer at \"Answers\"")
                return
            match = re.match(r"(?i)answerartist\s(.*)\s?", command)
            if match:
                if a:
                    self.player_artist_answer[user] = match.group(1)
                else:
                    self.chat("please submit your answer at \"Answers\"")
                return
            match = re.match(r"(?i)answer\s", command)
            if match:
                self.chat("Usage: /answer anime|song|artist")
                return
            match = re.match(r"(?i)vote\s\d+\s", command)
            if match:
                self.chat("not implemented")
                return
            # admin only commands below
            if not self.database.is_moderator(user):
                self.auto_chat("permission_denied", [user])
                return
            match = re.match(r"(?i)leaderboard\s(\d+)\s?", command)
            if match:
                self.leaderboard(int(match.group(1)))
            match = re.match(r"(?i)setchattiness\s(-?\d+)", command)
            if match:
                self.set_chattiness(int(match.group(1)))
            match = re.match(r"(?i)kick\s@?([^ ]*)(?:\s?(.*))", command)
            if match:
                username = match.group(1)
                reason = match.group(2)
                if reason == "":
                    reason = None
                    self.kick_player(username, reason, user)
                    return
            if command.lower() == "forceevent":
                self.state_timer = 1
                return
            match = re.match(r"(?i)elo\s@?([^ ]*)\s?", command)
            if match:
                username = match.group(1)
                id = self.database.get_player_id(username)
                elo = self.database.get_or_create_elo(id)
                self.auto_chat("elo", [username, elo, self.elo_to_tier(elo)])
                return
            if not self.database.is_administrator(user):
                self.auto_chat("permission_denied", [user])
                return
            if command.lower() == "stop":
                self.auto_chat("stop")
                self.state = -1
                return
            match = re.match(r"(?i)addadmin\s@?([^ ]*)", command)
            if match:
                self.database.add_administrator(match.group(1), user)
                self.admins.append(match.group(1))
                with open(self.admins_file, "a", encoding="utf-8") as f:
                    f.write(match.group(1) + "\n")
                return
            match = re.match(r"(?i)addmoderator\s@?([^ ]*)", command)
            if match:
                self.database.add_moderator(match.group(1), user)
                return
            match = re.match(r"(?i)ban\s@?([^ ]*)(?:\s?(.*))", command)
            if match:
                username = match.group(1)
                reason = match.group(2)
                if reason == "":
                    reason = None
                self.ban_player(username, reason, user)
                return
            pass
        except Exception:
            log_exceptions()
