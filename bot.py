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

class Player(object):
    """represents a player"""
    def __init__(self, username, note=""):
        self.score = 0
        self.username = username
        self.note = note

    def __repr__(self):
        return "Player('%s', '%s')" % (self.username, self.note)


class GameLobby(object):
    """represents the lobby"""
    def __init__(self, round=0, players=[]):
        self.round = round
        self.players = players
        self.player_count = 0
        for p in self.player:
            if p.note == "":
                player_count += 1

    def remove_player(self, username, reason):
        for p in self.players:
            if p.username == username and p.note == "":
                p.note = "[%s in round %d]" % (reason, self.round)
                player_count -= 1

    def add_player(self, username):
        self.players.append(Player(username))
        player_count += 1

    def __repr__(self):
        out = "GameLobby(%d, [" % (self.round)
        for p in self.players:
            out += repr(p) + ", "
        out += "])"
        return out


class WaitingLobby:
    def __init__(self, players=[]):
        self.players = players
    pass


class MessageManager:
    database = {"greeting": 3, "kick_chat": 1, "kick_pm": 1, "banned_word": 1,
                "log_chat": 1, "something": 1}
    langpack = "./langs/"

    def __init__(self, directory="en_UK"):
        self.directory = directory

    def get_message(self, name, substitutions=[], number=None):
        filename = name
        if number is None:
            filename += str(random.choice(range(self.database[name])))
        else:
            if number < self.database[name]:
                filename += name + str(number)
            else:
                filename += name + str(self.database[name]-1)
        filename += ".txt"
        with open(langpack + directory + filename) as file:
            base_text = file.read()
        for n in range(len(substitutions)):
            base_text = re.sub("$%d" % n+1, substitutions[n], base_text)
        return base_text


def log(message):
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


logfile = "AMQ-bot.log"


def chat(driver, message):
    chatbox = driver.find_element_by_id("gcInput")
    chatbox.send_keys(message)
    chatbox.send_keys(Keys.ENTER)
    log("Sent message: %s" % message)


chat_pos = 0


def scan_chat(driver):
    """
    scans the chat for interesting events.
    Includes, but is not limited to:
    chat commands
    players joining/leaving
    kicking/banning for unwanted phrases
    """
    global chat_pos
    chat_window = driver.find_element_by_id("gcMessageContainer")
    chat_pattern = re.compile(r"(?s)<li>(.*?)</li>")
    chat_html = chat_window.get_attribute('innerHTML')
    chat_messages = chat_pattern.findall(chat_html)
    # print(chat_window.text)
    player_message_pattern = re.compile(r'(?s)<img class="backerBadge.*?>.*<span class="gcUserName(?: clickAble" data-original-title="" title=")?">(.*?)</span>(.*)\n')
    player_joined_as_player = re.compile(r'<span>(.*?) joined the room.</span><br>')
    player_joined_as_spectator = re.compile(r'<span>(.*?) has started spectating.</span><br>')
    player_changed_to_player = re.compile(r'<span>(.*?) changed to player</span><br>')
    player_changed_to_spectator = re.compile(r'<span>(.*?) changed to spectator</span><br>')
    player_left = re.compile(r'<span>(.*?) has left the game.</span><br>')
    detect_amq_emoji = re.compile(r'\n\s<img class="amqEmoji" alt="(.*?)" draggable="false" src=".*?">\n')
    detect_emoji = re.compile(r'<img class="emoji" draggable="false" alt=".*?" src="(.*?)">')

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
            print("%s said: \"%s\"" % (name, message))
            if name not in admins and "bad word" in message:
                kick_player(driver, name, "Pls do not use such language")
            elif message[0] == "!":
                handle_command(driver, name, message[1:])
            done = True
        if not done:
            join_as_player = player_joined_as_player.search(match)
            # the glory of not being able to assign in an if
        if not done and join_as_player:
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
            player_left = player_left.search(match)
        if not done and player_left:
            done = True
            pass
    if len(chat_messages) > chat_pos:
        chat_pos = len(chat_messages)
    pass


def message_player(driver, username, message):
    pass


def kick_player(driver, username, reason=None):
    reason = reason or "something"
    driver.execute_script('lobby.kickPlayer("%s")' % username)
    chat(driver, "Kicked player %s for %s." % (username, reason))
    message_player(driver, username, "You were kicked for: %s" % reason)


def scan_lobby(driver):
    pass


admins = []
stop = False


def handle_command(driver, user, command):
    print("Command detected: %s" % command)
    if command.lower() == "stop":
        if user in admins:
            print("stop detected")
            global stop
            stop = True
        else:
            chat(driver, "You do not have permission to do that, %s" % user)
    pass


def main():
    """
    the main function, where the magic happens
    """
    log("AMQ-automator started")
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
        log("program closed normally")
    # input("Press enter to terminate")
    driver.execute_script("options.logout();")
    time.sleep(1)
    driver.close()


if __name__ == "__main__":
    main()
