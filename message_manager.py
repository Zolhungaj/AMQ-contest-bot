import random
import traceback
import re


class MessageManager:
    database = {"greeting_player": 3, "kick_chat": 1, "kick_pm": 1,
                "banned_word": 1, "permission_denied": 1,
                "log_chat_out": 1, "something": 1, "hello_world": 1,
                "idle": 1, "get_ready": 1, "scorn_admin": 1, "starting_in": 1,
                "pm_out": 1, "answer_reveal": 35, "abort_game": 1,
                "help": 1, "help_admin": 1, "help_help": 1, "stop": 1,
                "unknown_command": 1, "no_songs": 1, "about": 1,
                "exchange_players": 1, "help_about": 1, "you_answered": 1,
                "already_done": 1, "no_game_recorded": 1, "ban_comment": 1,
                "banned_for": 1, "system": 1, "about_joke_intro": 1,
                "about_joke": 3, "greeting_spectator": 1, "help_addadmin": 1,
                "help_list": 1, "help_missing": 1, "help_stop": 1,
                "help_setchattiness": 1, "help_ban": 1, "help_kick": 1,
                "help_forceevent": 1, "list_success": 1, "game_complete": 1,
                "list_fail_no_games": 1, "list_fail_already_done": 1,
                "help_moderator": 1, "help_addmoderator": 1, "elo": 1,
                "profile_username": 1, "profile_unknown": 1,
                "profile_elo": 1, "profile_play_count": 1, "profile_wins": 1,
                "profile_song_count": 1, "profile_hit_count": 1,
                "profile_hit_rate": 1, "leaderboard": 1}
    langpack = "./langs/"

    def __init__(self, directory="en_UK"):
        self.directory = directory
        self.path = self.langpack + directory + "/"
        # self.database = MessageManager.database

    def get_text(self, name, substitutions=[], number=None):
        filename = name
        try:
            if number is None:
                filename += str(random.choice(range(self.database[name])))
            else:
                if number < self.database[name]:
                    filename += name + str(number)
                else:
                    filename += name + str(self.database[name]-1)
            filename += ".txt"
            with open(self.path + filename, encoding="utf-8") as file:
                base_text = file.read()[:-1]
            for n in range(len(substitutions)):
                base_text = re.sub(
                    "&%d" % (n+1), str(substitutions[n]), base_text)
            return base_text
        except Exception:
            error = traceback.format_exc()
            print(error)
            with open("message_manager_fail.log", "a", encoding="utf-8") as f:
                f.write(error)
            return name
