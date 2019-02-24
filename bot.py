"""
"""

import traceback

from game import Game


def main():
    """
    the main function, where the magic happens
    """
    # sys_log("AMQ-automator started")
    configfile = input("select config name [default = \"default\"]")
    if configfile == "":
        configfile = "default"
    game = Game(configfile + ".config")
    try:
        game.start()
    except Exception as e:
        error = traceback.format_exc()
        print(error)
        with open("fatalcrash.log", "a", encoding="utf-8") as f:
            f.write(error)
        game.close()


if __name__ == "__main__":
    main()
