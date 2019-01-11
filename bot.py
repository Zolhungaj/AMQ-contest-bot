"""
"""

import traceback

from game import Game


def main():
    """
    the main function, where the magic happens
    """
    # sys_log("AMQ-automator started")
    game = Game("default.config")
    try:
        game.start()
    except Exception as e:
        traceback.print_exc()
        game.close()


if __name__ == "__main__":
    main()
