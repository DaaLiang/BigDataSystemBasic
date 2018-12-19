from Config import Config


class Logger:
    def __init__(self, name, debug=Config.DEBUG):
        self.name = name
        self.debug = debug

    def log(self, event):
        if self.debug:
            print("[%15s]: %s" % (self.name, event))
