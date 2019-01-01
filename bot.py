"""
"""
import os

import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import _thread
import subprocess

import math

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


def int_to_base_36(input):
    order = int(math.floor(math.log(input, 36)))
    out = ""
    while order >= 0:
        res = math.floor(input / 36**order)
        print(res)
        if res < 10:
            out += str(res)
        else:
            out += chr(ord("a")+(res-10))
        input = input % (36**order)
        order -= 1
    print(out)


def create_code(player_count, song_count):
    code = "1"
    code += min(max(2, player_count), 8)
    code += int_to_base_36(song_count)
    if skip_guess:
        code += "1"
    else:
        code += "0"
    if skip_result:
        code += "1"
    else:
        code += "0"
    if queuing:
        code += "1"
    else:
        code += "0"
    if duplicate_shows:
        code += "1"
    else:
        code += "0"


def main():
    """
    the main function, where the magic happens
    """
    log("AMQ-automator started")
    driver = webdriver.Firefox(executable_path='geckodriver/geckodriver.exe')
    driver.get('https://animemusicquiz.com')
    username_input = driver.find_element_by_id("loginUsername")
    password_input = driver.find_element_by_id("loginPassword")
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button = driver.find_element_by_id("loginButton")
    login_button.click()
    play = driver.find_element_by_id("mpPlayButton")
    play.click()
    host = driver.find_element_by_id("roomBrowserHostButton")
    host.click()
    driver.execute_script("hostModal.selectStandard();")
    driver.execute_script("hostModal.selectQD();")
    driver.execute_script("hostModal.toggleLoadContainer();")
    load = driver.find_element_by_id("mhLoadFromSaveCodeButton")
    load.click()
    videoUrl = videoPreview.get_attribute("src")
    while True:

        submit.click()
    log("program closed normally")
    logfile.close()
    input("Press enter to terminate")
    driver.close()


if __name__ == "__main__":
    main()
