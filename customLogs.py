import logging, os

#Logging config
class CustomLog:
    def __init__(self, conf, logname):
        logPath = conf.logsPath+logname+'.log'
        if os.path.exists(logPath):
            try:
                os.remove(logPath)
            except:
                pass
        self.logger = logging.getLogger(logname)
        loglevel = getattr(logging, conf.loglevel.upper())
        formatterLog = logging.Formatter('\n%(asctime)s - %(levelname)s: %(message)s', datefmt="%d-%m-%Y %H:%M:%S")
        formatterConsole = logging.Formatter('\n%(asctime)s: %(message)s', datefmt="%d-%m-%Y %H:%M:%S")
        log_handler = logging.FileHandler(logPath, encoding='utf-8-sig')
        log_handler.setFormatter(formatterLog)
        log_handler.setLevel(loglevel)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatterConsole)
        self.logger.addHandler(log_handler)
        self.logger.addHandler(console)
        self.logger.setLevel(loglevel)

    def strListFromArgs(self, args):
        compiledStr = str(args[0])
        sizeArgs = len(args)
        if sizeArgs > 1:
            for x in range(1, sizeArgs):
                compiledStr += " " + str(args[x])
        return compiledStr

    def debug(self, *args):
        message = self.strListFromArgs(args)
        self.logger.debug(message)

    def info(self, *args):
        message = self.strListFromArgs(args)
        self.logger.info(message)

    def warning(self, *args):
        message = self.strListFromArgs(args)
        self.logger.warning(message)

    def error(self, *args):
        message = self.strListFromArgs(args)
        self.logger.error(message)