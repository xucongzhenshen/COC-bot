import os

from src.cocbot.common import init_log, log_msg


class LoggerService:
    def __init__(self, config):
        self.config = config
        self.log_path = None

    def initialize(self):
        self.log_path = self.config.log_path
        os.makedirs(self.log_path, exist_ok=True)
        init_log(loglevel=self.config.loglevel, log_path=self.log_path)

    def info(self, message, level=1):
        log_msg(message, level=level, log_path=self.log_path)

    def error(self, message):
        log_msg(message, level=0, log_path=self.log_path)

    def debug(self, message):
        log_msg(message, level=2, log_path=self.log_path)
