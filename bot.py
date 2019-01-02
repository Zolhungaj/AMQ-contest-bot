"""
"""
import os

import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
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
