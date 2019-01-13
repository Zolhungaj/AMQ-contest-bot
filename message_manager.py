import random
import traceback
import re


class MessageManager:
    database = {"greeting_player": 3, "kick_chat": 1, "kick_pm": 1,
                "banned_word": 1, "permission_denied": 1,
                "log_chat_out": 1, "something": 1, "hello_world": 1,
                "idle": 1, "get_ready": 1, "scorn_admin": 1, "starting_in": 1,
                "pm_out": 1, "answer_reveal": 11, "abort_game": 1}
    langpack = "./langs/"

    def __init__(self, directory="en_UK"):
        self.directory = directory
        self.path = self.langpack + directory + "/"
        # self.database = MessageManager.database

    def get_message(self, name, substitutions=[], number=None):
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
            with open(self.path + filename) as file:
                base_text = file.read()[:-1]
            for n in range(len(substitutions)):
                base_text = re.sub(
                    "&%d" % (n+1), str(substitutions[n]), base_text)
            return base_text
        except Exception:
            traceback.print_exc()
            return name
