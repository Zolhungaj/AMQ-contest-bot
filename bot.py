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
    return out


def pad3(input):
    out = int_to_base_36(input)
    if len(out) > 3:
        out = out[-3:]
    elif len(out) < 2:
        out = "0" + out
    return out


def pad2(input):
    out = int_to_base_36(input)
    if len(out) > 2:
        out = out[-2:]
    elif len(out) < 2:
        out = "0" + out
    return out


def pad1(input):
    out = int_to_base_36(input)
    if len(out) > 1:
        out = out[-1]
    return out


def create_code(player_count, song_count,
                skip_guess, skip_result, queuing, duplicate_shows,
                selection_advanced, song_selection_simple,
                selection_watched, selection_unwatched, selection_random,
                type_advanced, type_opening, type_ending, type_insert,
                openings, endings, inserts, type_random,
                random_time,
                guess_time, guess_time_low, guess_time_high,
                random_sample,
                sample_point, sample_point_low, sample_point_high,
                random_speed, const_speed,
                random_speed1, random_speed1_5, random_speed2, random_speed4,
                song_difficulty_advanced, easy, medium, hard,
                difficulty_low, difficulty_high,
                popularity_advanced, disliked, mixed, liked,
                popularity_low, popularity_high,
                player_score_advanced, player_score_low, player_score_high,
                player_score_1, player_score_2, player_score_3,
                player_score_4, player_score_5, player_score_6,
                player_score_7, player_score_8, player_score_9,
                player_score_10,
                anime_score_advanced, anime_score_low, anime_score_high,
                anime_score_2, anime_score_3, anime_score_4, anime_score_5,
                anime_score_6, anime_score_7, anime_score_8, anime_score_9,
                anime_score_10,
                year_ranges,
                tv, movie, ova, ona, special,
                genres,
                tags
                ):
    code = "1"  # version number?
    code += pad1(player_count)
    code += pad2(song_count)
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
    if selection_advanced:
        code += "1"
    else:
        code += "0"
    code += str(song_selection_simple)
    # 1:random 2:mainly watched 3: only watched
    code += pad2(selection_watched)
    code += pad2(selection_unwatched)
    code += pad2(selection_random)
    if type_advanced:
        code += "1"
    else:
        code += "0"
    if type_opening:
        code += "1"
    else:
        code += "0"
    if type_ending:
        code += "1"
    else:
        code += "0"
    if type_insert:
        code += "1"
    else:
        code += "0"
    code += pad2(openings)
    code += pad2(endings)
    code += pad2(inserts)
    code += pad2(type_random)
    if random_time:
        code += "1"
    else:
        code += "0"
    code += pad2(guess_time)
    code += pad2(guess_time_low)
    code += pad2(guess_time_high)
    if random_sample:
        code += "1"
    else:
        code += "0"
    code += str(sample_point)  # 1: start 2: middle 3: end
    code += pad2(sample_point_low)
    code += pad2(sample_point_high)
    if random_speed:
        code += "1"
    else:
        code += "0"
    code += str(const_speed)  # 1, 2, 3, 4
    if random_speed1:
        code += "1"
    else:
        code += "0"
    if random_speed1_5:
        code += "1"
    else:
        code += "0"
    if random_speed2:
        code += "1"
    else:
        code += "0"
    if random_speed4:
        code += "1"
    else:
        code += "0"
    if song_difficulty_advanced:
        code += "1"
    else:
        code += "0"
    if easy:
        code += "1"
    else:
        code += "0"
    if medium:
        code += "1"
    else:
        code += "0"
    if hard:
        code += "1"
    else:
        code += "0"
    code += pad2(difficulty_low)
    code += pad2(difficulty_high)
    if popularity_advanced:
        code += "1"
    else:
        code += "0"
    if disliked:
        code += "1"
    else:
        code += "0"
    if mixed:
        code += "1"
    else:
        code += "0"
    if liked:
        code += "1"
    else:
        code += "0"
    code += pad2(popularity_low)
    code += pad2(popularity_high)
    if player_score_advanced:
        code += "1"
    else:
        code += "0"
    code += pad1(player_score_low)
    code += pad1(player_score_high)
    if player_score_1:
        code += "1"
    else:
        code += "0"
    if player_score_2:
        code += "1"
    else:
        code += "0"
    if player_score_3:
        code += "1"
    else:
        code += "0"
    if player_score_4:
        code += "1"
    else:
        code += "0"
    if player_score_5:
        code += "1"
    else:
        code += "0"
    if player_score_6:
        code += "1"
    else:
        code += "0"
    if player_score_7:
        code += "1"
    else:
        code += "0"
    if player_score_8:
        code += "1"
    else:
        code += "0"
    if player_score_9:
        code += "1"
    else:
        code += "0"
    if player_score_10:
        code += "1"
    else:
        code += "0"
    if anime_score_advanced:
        code += "1"
    else:
        code += "0"
    code += pad1(anime_score_low)
    code += pad1(anime_score_high)
    if anime_score_2:
        code += "1"
    else:
        code += "0"
    if anime_score_3:
        code += "1"
    else:
        code += "0"
    if anime_score_4:
        code += "1"
    else:
        code += "0"
    if anime_score_5:
        code += "1"
    else:
        code += "0"
    if anime_score_6:
        code += "1"
    else:
        code += "0"
    if anime_score_7:
        code += "1"
    else:
        code += "0"
    if anime_score_8:
        code += "1"
    else:
        code += "0"
    if anime_score_9:
        code += "1"
    else:
        code += "0"
    if anime_score_10:
        code += "1"
    else:
        code += "0"
    for year_low, year_high, season_low, season_high in year_ranges:
        code += pad3(year_low)
        code += pad3(year_high)
        code += str(season_low)  # 0: winter, 1: spring, 3:summer 4:fall
        code += str(season_high)  #
    # year ranges are defined as tuples containing 4 elements
    code += "-"
    if tv:
        code += "1"
    else:
        code += "0"
    if movie:
        code += "1"
    else:
        code += "0"
    if ova:
        code += "1"
    else:
        code += "0"
    if ona:
        code += "1"
    else:
        code += "0"
    if special:
        code += "1"
    else:
        code += "0"
    for genre_id, genre_status in genres:
        code += pad2(genre_id)
        code += str(genre_status)  # 1: include, 2: exclude, 3: optional
    code += "-"
    for tag_id, tag_status in tags:
        code += pad2(tag_id)
        code += str(tag_status)  # 1: include, 2: exclude, 3: optional
    code += "-"
    return code


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
