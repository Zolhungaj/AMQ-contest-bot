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
        with open(self.banned_word_path) as f:
            list = f.read().split("\n")[:-1]
            self.banned_word_pattern = re.compile(r"\b(" + "|".join(list) + ")")
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
        self.last_round = -1
        self.skipped_playback = False
        self.kick_list = []
        self.silent_counter = int(5/self.tick_rate)

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
            # elif self.state == 4:
            #    # self.finish_game()
            #    # skipController.toggle()
            self.scan_chat()
            self.silent_counter -= 1
            if self.silent_counter < 0:
                for u in self.kick_list:
                    self.silent_kick(u)
                self.silent_counter = int(5/self.tick_rate)
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
        self.waiting_time_limit = (self.lobby.player_count()-1)*int(self.waiting_time/(self.max_players-1))
        if self.lobby.player_count() == 1:
            self.state = 0
            self.set_state_time(self.idle_time)

    def wait_for_ready(self):
        print("wait for ready")
        self.state_timer -= 1
        self.lobby.scan_lobby()
        if self.lobby.player_count() == 1:
            self.state = 0
            self.set_state_time(self.idle_time)
            return
        if self.lobby.all_ready():
            self.start_game()
        elif self.state_timer < int(-10/self.tick_rate):
            self.start_game()
        elif self.state_timer == 0:
            for p in self.lobby.get_unready():
                self.move_to_spectator(p.username)

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
        self.lobby = self.lobby.generateGameLobby()
        self.state = 3
        self.last_round = -1
        self.mute_sound()
        self.select_quality("Sound")
        self.lobby.verify_players()

    def run_game(self):
        self.lobby.scan_lobby()
        if self.lobby.round > self.last_round:
            self.last_round = self.lobby.round
            self.driver.execute_script('skipController.toggle()')
            self.skipped_playback = False
        if self.lobby.playback and not self.skipped_playback:
            self.skipped_playback = True
            self.driver.execute_script('skipController.toggle()')
            self.chat(self.msg_man.get_message("answer_reveal", [self.lobby.last_song.anime]))
            for p in self.lobby.players:
                print("%s: %d" % (p.username, p.score))
            if self.lobby.round == self.lobby.total_rounds:
                self.finish_game()
                return
        if self.lobby.player_count < 2:
            self.abort_game()

    def abort_game(self):
        self.chat(self.msg_man.get_message("abort_game"))
        self.driver.execute_script('quiz.startReturnLobbyVote();')
        time.sleep(1)
        self.driver.execute_script('skipController.toggle()')
        time.sleep(1)
        self.finish_game()

    def finish_game(self):
        # TODO record game
        while True:
            try:
                self.lobby.scan_lobby()
            except Exception:
                break
            time.sleep(self.tick_rate)
        self.lobby = WaitingLobby(self.driver, self.max_players)
        self.state = 0
        self.set_state_time(self.idle_time)

    def move_to_spectator(self, username):
        self.driver.execute_script('lobby.changeToSpectator("%s")' % username)

    def mute_sound(self):
        icon = self.driver.find_element_by_id("qpVolumeIcon")
        if "off" not in icon.get_attribute("class"):
            icon.click()

    def select_quality(self, quality):
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
                if self.detect_banned_words(message):
                    self.kick_player(name, self.msg_man.get_message("banned_word"))
                elif message[0] == "!":
                    self.handle_command(name, message[1:])
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
        if len(chat_messages) > chat_pos:
            self.chat_pos = len(chat_messages)

    def detect_banned_words(self, message):
        match = self.banned_word_pattern.search(message.lower())
        if match:
            print(match.group(0))
            return True
        else:
            return False

    def message_player(self, username, message):
        # socialTab.startChat("username")
        self.driver.execute_script('socialTab.startChat("%s")' % username)
        box = self.driver.find_element_by_id("chatBox-%s" % username)
        chatbox = box.find_element_by_tag_name("textarea")
        chatbox.send_keys(message)
        chatbox.send_keys(Keys.ENTER)
        self.log.chat_out(self.msg_man.get_message("pm_out", [username, message]))

    def kick_player(self, username, reason=None):
        reason = reason or self.msg_man.get_message("something")
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

    def silent_kick(self, username):
        if self.state < 3:
            self.driver.execute_script('lobby.kickPlayer("%s")' % username)
        else:
            self.driver.execute_script('gameChat.kickSpectator("%s")' % username)

    def handle_command(self, user, command):
        print("Command detected: %s" % command)
        match = re.match("stop|addadmin|pause|help|votekick|voteban|about|forceevent", command)
        if not match:
            self.chat("Unrecognized command")
            return
        # admin only commands below
        if user not in self.admins:
            self.chat(self.msg_man.get_message("permission_denied",
                                               [user]))
            return
        if command == "forceevent":
            self.state_timer = 1
            return
        if command == "stop":
            print("stop detected")
            self.state = -1
            return
        match = re.match("addadmin ([^ ]*)", command)
        if match:
            self.admins.append(match.group(1))
            return
        pass
