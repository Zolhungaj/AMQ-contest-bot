from lobby import Lobby, GameLobby, WaitingLobby
from logger import Logger
from message_manager import MessageManager
from player import Player
from song import Song
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
        self.banned_word_path = config[7]
        self.chattiness = int(config[8]) / 100
        self.banned_players_list = []

        self.banned_players_file = config[9]
        self.admins_file = config[10]
        with open(self.admins_file) as f:
            for line in f.readlines():
                self.admins.append(line[:-1])
        print(self.admins)
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
        self.idle_time = 40
        self.waiting_time = 90
        self.waiting_time_limit = 0
        self.ready_wait_time = 15
        self.state_timer = int(self.idle_time/self.tick_rate)
        self.log = Logger()
        self.chat_pos = 0
        self.lobby = None
        self.max_players = 8
        self.last_round = -1
        self.skipped_playback = False
        self.kick_list = []
        self.silent_counter = int(5/self.tick_rate)
        self.detect_command = re.compile(r"(?i)(?:(?:/)|(?:@"+self.username+r"\s))(.*)")
        self.message_backlog = []
        self.player_records = {}
        self.recently_used_list = []
        self.last_round_list = None

    def set_chattiness(self, newpercentage):
        self.chattiness = newpercentage / 100

    def tick(self):
        time.sleep(self.tick_rate)

    def set_state_time(self, new_time):
        self.state_timer = int(new_time/self.tick_rate)

    def set_state_idle(self):
        self.state = 0
        self.set_state_time(self.idle_time)
        self.chat(self.msg_man.get_message("idle"))

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
                self.record_game()
            elif self.state == 5:
                self.finish_game()
            #    # skipController.toggle()
            self.scan_chat()
            self.send_backlog()
            self.state_timer -= 1
            self.silent_counter -= 1
            if self.silent_counter < 0:
                for u in self.kick_list:
                    self.silent_kick(u)
                self.silent_counter = int(5/self.tick_rate)
            self.tick()
        self.close()

    def idle(self):
        if self.state_timer == 0:
            self.chat(self.msg_man.get_message("idle"))
            self.set_state_time(self.idle_time)
        self.lobby.scan_lobby()
        if self.lobby.player_count > 1:
            self.state = 1
            self.set_state_time(self.waiting_time)
            self.waiting_time_limit = 0

    def wait_for_players(self):
        time_left = self.state_timer - self.waiting_time_limit
        if time_left % (int(10/self.tick_rate)) == 0 or time_left <= 0:
            if time_left < 0:
                time_left = 0
            self.chat(self.msg_man.get_message("starting_in", [int((time_left)*self.tick_rate)]))
        if self.state_timer <= self.waiting_time_limit:
            self.chat(self.msg_man.get_message("get_ready"))
            for p in self.lobby.get_unready():
                self.chat("@%s" % p.username)
            self.set_state_time(self.ready_wait_time)
            self.state = 2
            return
        self.lobby.scan_lobby()
        self.waiting_time_limit = int(((self.lobby.player_count-1)*(self.waiting_time/(self.max_players-1)) - 10)/self.tick_rate)
        if self.lobby.player_count == 1:
            self.set_state_idle()

    def wait_for_ready(self):
        print("wait for ready")
        self.lobby.scan_lobby()
        time_remaining = self.state_timer*self.tick_rate
        if self.lobby.player_count == 1:
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
        self.driver.execute_script("lobby.fireMainButtonEvent();")
        time.sleep(2)
        try:
            pop_up = self.driver.find_element_by_class_name("swal2-container")
            accept = pop_up.find_element_by_class_name("swal2-confirm")
            accept.click()
            time.sleep(2)
        except Exception:
            pass
        try:
            new_lobby = self.lobby.generateGameLobby()
            self.state = 3
            self.last_round = -1
            new_lobby.scan_lobby()
            new_lobby.verify_players()
            self.mute_sound()
            self.select_quality("Sound")
            self.lobby = new_lobby
        except Exception:
            self.set_state_idle()
            self.chat(self.msg_man.get_message("no_songs"))
            self.exchange_players()

    def run_game(self):
        self.lobby.scan_lobby()
        if self.lobby.round > self.last_round:
            self.last_round = self.lobby.round
            self.driver.execute_script('skipController.toggle()')
            self.skipped_playback = False
        if self.lobby.playback and not self.skipped_playback:
            self.skipped_playback = True
            self.driver.execute_script('skipController.toggle()')
            if random.random() < self.chattiness:
                self.chat(self.msg_man.get_message("answer_reveal", [self.lobby.last_song.anime]))
            for p in self.lobby.players:
                print("%s: %d" % (p.username, p.score))
            if self.lobby.round == self.lobby.total_rounds:
                self.state = 4
                return
        if self.lobby.player_count < 2:
            self.abort_game()

    def abort_game(self):
        self.chat(self.msg_man.get_message("abort_game"))
        self.driver.execute_script('quiz.startReturnLobbyVote();')
        time.sleep(1)
        self.driver.execute_script('skipController.toggle()')
        time.sleep(1)
        self.state = 4

    def record_game(self):
        try:
            for p in self.lobby.players:
                self.player_records[p.username] = [p, False]
            self.last_round_list = self.lobby.song_list
            self.recently_used_list = []
            self.chat("Great work everyone! If you want to train on your missed songs do /missed, and I'll send you a list :)")
        except Exception:
            log_exceptions()
        self.state = 5

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
        queue_size += (len(players)-len(active_players))  # original size
        if queue_size < self.max_players-len(active_players):
            return
        self.chat(self.msg_man.get_message("exchange_players"))
        names = [p.username for p in players if p.username != self.username]
        chosen = []
        if queue_size >= self.max_players-1:
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
        self.driver.execute_script('lobby.changeToSpectator("%s")' % username)

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
            chatbox = self.driver.find_element_by_id("gcInput")
            chatbox.send_keys(message)
            chatbox.send_keys(Keys.ENTER)
            self.log.chat_out(self.msg_man.get_message("log_chat_out", [message]))
        except Exception:
            log_exceptions()

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

            for match in chat_messages[chat_pos:]:
                print(match)
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
                    self.log.chat("%s said: \"%s\"" % (name, message))
                    match = self.detect_command.match(message)
                    if self.detect_banned_words(message):
                        self.kick_player(name, self.msg_man.get_message("banned_word"))
                    elif match:
                        self.handle_command(name, match.group(1))
                    done = True
                if not done:
                    join_as_player = self.player_joined_as_player.search(match)
                    # the glory of not being able to assign in an if
                if join_as_player:
                    username = join_as_player.group(1)
                    if self.detect_banned_words(username):
                        self.kick_player(username, self.msg_man.get_message("banned_word"))
                    else:
                        self.chat(self.msg_man.get_message("greeting_player",
                                                           [join_as_player.group(1)]))
                    done = True
                    pass
                if not done:
                    join_as_spectator = self.player_joined_as_spectator.search(match)
                if join_as_spectator:
                    username = join_as_spectator.group(1)
                    if self.detect_banned_words(username):
                        self.kick_player(username, self.msg_man.get_message("banned_word"))
                    else:
                        self.chat(self.msg_man.get_message("greeting_player",
                                                           [join_as_spectator.group(1)]))
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
                print(match.group(0))
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
            self.log.chat_out(self.msg_man.get_message("pm_out", [username, message]))
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
            reason = reason or self.msg_man.get_message("something")
            issuer = issuer or self.msg_man.get_message("system")
            with open(self.banned_players_file, "a", encoding="utf-8") as f:
                f.write(self.msg_man.get_message("ban_comment", [username, issuer, reason])+"\n")
            reason = self.msg_man.get_message("banned_for", [reason])
            self.kick_player(username, reason, issuer)

        except Exception:
            log_exceptions()

    def kick_player(self, username, reason=None, issuer=None):
        try:
            reason = reason or self.msg_man.get_message("something")
            issuer = issuer or self.msg_man.get_message("system")
            if username not in self.admins:
                if self.state < 3:
                    self.lobby.remove_player(username, reason)
                    self.driver.execute_script('lobby.kickPlayer("%s")' % username)
                    self.chat(self.msg_man.get_message("kick_chat", [username, reason]))
                    self.message_player(username,
                                        self.msg_man.get_message("kick_pm", [reason]))
                elif username not in [p.username for p in self.lobby.players]:
                    self.driver.execute_script('gameChat.kickSpectator("%s")' % username)
                    self.chat(self.msg_man.get_message("kick_chat", [username, reason]))
                    self.message_player(username,
                                        self.msg_man.get_message("kick_pm", [reason]))
                self.kick_list.append(username)
            elif username != self.username:
                self.chat(self.msg_man.get_message("scorn_admin", [username]))
        except Exception:
            log_exceptions()

    def silent_kick(self, username):
        if self.state < 3:
            self.driver.execute_script('lobby.kickPlayer("%s")' % username)
        else:
            self.driver.execute_script('gameChat.kickSpectator("%s")' % username)

    def handle_command(self, user, command):
        try:
            print("Command detected: %s" % command)
            match = re.match(r"(?i)stop|addadmin|help|kick|ban|about|forceevent|missed|setchattiness|list", command)
            if not match:
                self.chat(self.msg_man.get_message("unknown_command"))
                return
            if command == "help":
                self.chat(self.msg_man.get_message("help"))
                if user in self.admins:
                    self.chat(self.msg_man.get_message("help_admin"))
                return
            match = re.match(r"(?i)help\s([^ ]*)", command)
            if match:
                command = match.group(1).lower()
                match = re.match(r"(?i)stop|addadmin|help|kick|ban|about|forceevent|missed|setchattiness|list|answer|vote", command)
                if not match:
                    self.chat(self.msg_man.get_message("unknown_command"))
                    return
                if command == "help":
                    self.chat(self.msg_man.get_message("help_help"))
                elif command == "about":
                    self.chat(self.msg_man.get_message("help_about"))
                elif command == "list":
                    self.chat("Sends you a list of the previous game the bot ran, can only be used once per game PLACEHOLDER")
                elif command == "missed":
                    self.chat("Send you a list of songs you missed in the last game you played with the bot, can only be used once per game PLACEHOLDER")
                elif user not in self.admins:
                    self.chat(self.msg_man.get_message("permission_denied",
                                                       [user]))
                elif command == "stop":
                    self.chat("Usage: stop| PLACEHOLDER: shuts the bot down")
                elif command == "setchattiness":
                    self.chat("Usage: setchattiness [0-100]| PLACEHOLDER: sets the likelyhood in percent of [the bot] speaking in certain situations")
                elif command == "addadmin":
                    self.chat("Usage: addadmin [username]| PLACEHOLDER: adds a new admin to the bot")
                elif command == "kick":
                    self.chat("Usage: kick [username] <reason>| PLACEHOLDER: kicks the user and bans them until the bot is restarted")
                elif command == "ban":
                    self.chat("Usage: ban [username] <reason>| PLACEHOLDER: kicks the user and bans them until the bot is restarted, they are then kicked upon rejoining")
                elif command == "forceevent":
                    self.chat("Usage: forceevent| PLACEHOLDER: sets the timer to 1, resulting an immediate activation of time activated events")
                return
            if command.lower() == "about":
                self.chat(self.msg_man.get_message("about"))
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
                            messages.append([user, self.msg_man.get_message("you_answered", [answer])])
                        self.message_backlog += messages
                    else:
                        self.chat(self.msg_man.get_message("already_done", [user]))
                    record[1] = True
                else:
                    self.chat(self.msg_man.get_message("no_game_recorded", [user]))
                return
            if command.lower() == "list":
                if self.last_round_list is None:
                    self.chat("No games registered yet, @[PLACEHOLDER].")
                elif user in self.recently_used_list:
                    self.chat("You've already done that, @[PLACEHOLDER].")
                else:
                    song_list = self.last_round_list
                    messages = []
                    for s in song_list:
                        messages.append([user, str(s)])
                    self.message_backlog += messages
                    self.chat("The list is being sent to you over PM, @[PLACEHOLDER].")
                    self.recently_used_list.append(user)
                return
            match = re.match(r"(?i)answer\s(.*)\s", command)
            if match:
                self.chat("not implemented")
                return
            match = re.match(r"(?i)vote\s\d+\s", command)
            if match:
                self.chat("not implemented")
                return
            # admin only commands below
            if user not in self.admins:
                self.chat(self.msg_man.get_message("permission_denied",
                                                   [user]))
                return
            if command.lower() == "forceevent":
                self.state_timer = 1
                return
            if command.lower() == "stop":
                self.chat(self.msg_man.get_message("stop"))
                self.state = -1
                return
            match = re.match(r"(?i)addadmin\s@?([^ ]*)", command)
            if match:
                self.admins.append(match.group(1))
                with open(self.admins_file, "a", encoding="utf-8") as f:
                    f.write(match.group(1) + "\n")
                return
            match = re.match(r"(?i)kick\s@?([^ ]*)(?:\s(.*))", command)
            if match:
                username = match.group(1)
                reason = match.group(2)
                if reason == "":
                    reason = None
                self.kick_player(username, reason, user)
                return
            match = re.match(r"(?i)ban\s@?([^ ]*)(?:\s(.*))?", command)
            if match:
                username = match.group(1)
                reason = match.group(2)
                if reason == "":
                    reason = None
                self.ban_player(username, reason, user)
                return
            match = re.match(r"(?i)setchattiness\s(-?\d+)", command)
            if match:
                self.set_chattiness(int(match.group(1)))
            pass
        except Exception:
            log_exceptions()
