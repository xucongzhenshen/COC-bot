from src.cocbot.home import run_home_world

from .base_bot import BaseBot


class HomeBot(BaseBot):
    def __init__(self, logger):
        super().__init__("HomeBot", logger)

    def can_handle(self, world):
        return world == "HOME"

    def run_bot(self):
        run_home_world()
