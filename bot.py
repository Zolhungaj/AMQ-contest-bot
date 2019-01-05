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


global logfile
logfile = "AMQ-automator.log"


def chat(driver, message):
    chatbox = driver.find_element_by_id("gcInput")
    chatbox.send_keys(message)
    chatbox.send_keys(Keys.ENTER)


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
    player_joined_as_player_pattern = re.compile(r'')
    player_joined_as_spectator_pattern = re.compile(r'')
    player_left_pattern = re.compile(r'')

    for match in chat_messages[chat_pos:]:
        print(match)
        player_message = player_message_pattern.search(match)
        if player_message:
            name = player_message.group(1)
            message = player_message.group(2)
            print("%s said: \"%s\"" % (name, message))
            if name not in admins and "bad word" in message:
                kick_player(driver, name, "Pls do not use such language")
            elif message[0] == "!":
                handle_command(driver, name, message[1:])

    if len(chat_messages) > chat_pos:
        chat_pos = len(chat_messages)
    pass


def kick_player(driver, username, reason="something"):
    driver.execute_script('lobby.kickPlayer("%s")' % username)
    chat(driver, "Kicked player %s for %s." % (username, reason))


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
    chat(driver, "Hello World!")
    state = 0  # 0: lobby
    try:
        while not stop:
            # program loop
            scan_chat(driver)
            time.sleep(1)
    except Exception as e:
        log(str(e))
    else:
        log("program closed normally")
    # input("Press enter to terminate")
    driver.execute_script("options.logout();")
    time.sleep(1)
    driver.close()


if __name__ == "__main__":
    main()
