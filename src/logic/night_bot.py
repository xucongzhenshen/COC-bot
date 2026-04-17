from src.cocbot.night import run_night_world

from .base_bot import BaseBot


class NightBot(BaseBot):
    def __init__(self, logger):
        super().__init__("NightBot", logger)

    def can_handle(self, world):
        return world == "NIGHT"

    def run_bot(self):
        run_night_world()
