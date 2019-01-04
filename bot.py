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
    # videoUrl = videoPreview.get_attribute("src")
    chat(driver, "Hello World!")
    state = 0  # 0: lobby
    while True:
        # program loop
        break
        time.sleep(0.1)
    log("program closed normally")
    input("Press enter to terminate")
    driver.execute_script("options.logout();")
    driver.close()


if __name__ == "__main__":
    main()
