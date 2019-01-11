import datetime


class Logger:

    def __init__(self, sys_log="AMQ-bot.log", chat_log="AMQ-bot-chat.log",
                 chat_out_log="AMQ-bot-chat_out.log",
                 event_log="AMQ-bot-events.log"
                 ):
        self.sys_log = sys_log
        self.chat_log = chat_log
        self.chat_out_log = chat_out_log
        self.event_log = event_log

    def log(self, message, logfile):
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

    def sys(self, message):
        self.log(message, self.sys_log)

    def chat(self, message):
        self.log(message, self.chat_log)

    def chat_out(self, message):
        self.log(message, self.chat_out_log)

    def event(self, message):
        self.log(message, self.event_log)
