from abc import ABC, abstractmethod


class BaseBot(ABC):
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger
        self.trained = False
        self.fight = True
        self.faction = None
        self.switch = True

    @abstractmethod
    def can_handle(self, world):
        pass

    @abstractmethod
    def run_bot(self):
        pass

    def on_interrupt(self, exc):
        self.logger.error(f"{self.name} 异常中断: {exc}")
