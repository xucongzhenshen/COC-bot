from abc import ABC, abstractmethod


class BaseBot(ABC):
    def __init__(self, name, config, services):
        self.name = name
        self.config = config
        self.services = services
        self.logger = services.logger
        self.trained = not config.retrain
        self.battle = config.battle
        self.attempts = config.attempts
        self.switch = config.switch

    @abstractmethod
    def can_handle(self, world):
        pass

    @abstractmethod
    def righting_pos(self):
        pass

    @abstractmethod
    def collect_resources(self):
        pass

    @abstractmethod
    def train_logic(self):
        pass

    @abstractmethod
    def battle_logic(self):
        pass

    @abstractmethod
    def switch_world(self):
        pass

    def run_bot(self):
        self.righting_pos()
        self.collect_resources()
        if not self.trained and self.battle:
            self.logger.info("重新训练模型，删除现有配兵", level=0)
            self.train_logic()
            self.trained = True
        if self.battle:
            for index in range(self.config.attempts):
                self.logger.info(f"战斗尝试 {index + 1}/{self.config.attempts}", level=0)
                self.battle_logic()
        self.righting_pos()
        self.collect_resources()
        if self.switch:
            self.logger.info("切换世界", level=0)
            self.switch_world()
            
    def on_interrupt(self, exc):
        self.logger.error(f"{self.name} 异常中断: {exc}")
