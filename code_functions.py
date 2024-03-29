import math
import re


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


def base_36_to_int(input):
    res = 0
    for letter in input:
        res *= 36
        try:
            res += int(letter)
        except Exception as e:
            res += ord(letter)-ord("a")+10
    return res


def int_to_season(input):
    if input == 0:
        return "Winter"
    elif input == 1:
        return "Spring"
    elif input == 2:
        return "Summer"
    elif input == 3:
        return "Fall"


def season_to_int(input):
    if input.lower() == "winter":
        return 0
    elif input.lower() == "spring":
        return 1
    elif input.lower() == "summer":
        return 2
    elif input.lower() == "fall":
        return 3


def int_to_query(input):
    if input == 1:
        return "Included"
    elif input == 2:
        return "Excluded"
    elif input == 3:
        return "Optional"


def query_to_int(input):
    if input.lower() == "included":
        return 1
    elif input.lower() == "excluded":
        return 2
    elif input.lower() == "optional":
        return 3


def strbool_to_int(input):
    if input.lower() == "true":
        return 1
    elif input.lower() == "false":
        return 0


def int_to_strbool(input):
    input = int(input)
    if input == 1:
        return "True"
    elif input == 0:
        return "False"


def int_to_selection(input):
    input = int(input)
    if input == 1:
        return "Random"
    elif input == 2:
        return "Mainly Watched"
    elif input == 3:
        return "Only Watched"


def selection_to_int(input):
    if input.lower() == "random":
        return 1
    elif input.lower() == "mostly watched":
        return 2
    elif input.lower() == "only watched":
        return 3


def int_to_sample_point(input):
    input = int(input)
    if input == 1:
        return "Start"
    elif input == 2:
        return "Middle"
    elif input == 3:
        return "End"


def sample_point_to_int(input):
    if input.lower() == "start":
        return 1
    elif input.lower() == "middle":
        return 2
    elif input.lower() == "end":
        return 3


def pad3(input):
    out = int_to_base_36(input)
    if len(out) > 3:
        out = out[-3:]
    elif len(out) < 2:
        out = "00" + out
    elif len(out) < 3:
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


def create_code(
        player_count, song_count,
        skip_guess, skip_result, queueing, duplicate_shows,
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
        tags):
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
    if queueing:
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


def code_to_file(code, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code_to_text(code))


def code_to_text(code):
    lines = []
    pos = 0
    lines.append("Version: %d" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Player count: %d" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Song count: %d" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Skip guess: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Skip result: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Queuing: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Duplicate shows: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Selection advanced: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Song selection simple: %s" % int_to_selection(code[pos]))
    pos += 1
    lines.append("Watched: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Unwatched: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Random selection: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append(
        "Enable advanced type distribution: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Enable openings: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Enable endings: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Enable inserts: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Openings: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Endings: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Inserts: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Type random: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Enable random time: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Guess time: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Guess time low: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Guess time high: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Enable random sample: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Sample point: %s" % int_to_sample_point(code[pos]))
    pos += 1
    lines.append("Sample point low: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Sample point high: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Enable random speed: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Constant speed: %s" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Speed 1: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Speed 1.5: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Speed 2: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Speed 4: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Enable advanced difficulty: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Easy: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Medium: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Hard: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Difficulty low: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Difficulty high: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Enable advanced popularity: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Disliked: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Mixed: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Liked: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Popularity low: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Popularity high: %s" % base_36_to_int(code[pos:pos+2]))
    pos += 2
    lines.append("Player score advanced: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score low: %s" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Player score high: %s" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Player score 1: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 2: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 3: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 4: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 5: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 6: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 7: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 8: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 9: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Player score 10: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Enable advanced anime score: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score low: %s" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Anime score high: %s" % base_36_to_int(code[pos]))
    pos += 1
    lines.append("Anime score 2: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 3: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 4: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 5: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 6: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 7: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 8: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 9: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Anime score 10: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Year ranges{")
    while code[pos] != "-":
        year_start = base_36_to_int(code[pos:pos+3])
        pos += 3
        year_end = base_36_to_int(code[pos:pos+3])
        pos += 3
        season_start = int_to_season(base_36_to_int(code[pos]))
        pos += 1
        season_end = int_to_season(base_36_to_int(code[pos]))
        pos += 1
        lines.append("%s %d %s %d" % (season_start, year_start,
                                      season_end, year_end)
                     )
    lines.append("}")
    pos += 1
    lines.append("TV: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Movie: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("OVA: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("ONA: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Special: %s" % int_to_strbool(code[pos]))
    pos += 1
    lines.append("Genres{")
    while code[pos] != "-":
        genre_id = base_36_to_int(code[pos:pos+2])
        pos += 2
        query = int_to_query(base_36_to_int(code[pos]))
        pos += 1
        lines.append("%d %s" % (genre_id, query))
    lines.append("}")
    pos += 1
    lines.append("Tags{")
    while code[pos] != "-":
        tag_id = base_36_to_int(code[pos:pos+2])
        pos += 2
        query = int_to_query(base_36_to_int(code[pos]))
        pos += 1
        lines.append("%d %s" % (tag_id, query))
    lines.append("}")
    pos += 1
    text = "\n".join(lines)
    return text
