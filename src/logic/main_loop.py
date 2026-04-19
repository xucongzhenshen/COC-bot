import random

from airtest.core.api import sleep


class MainLoop:
    def __init__(self, config, logger, world_detector, game_initializer, bots):
        self.config = config
        self.logger = logger
        self.world_detector = world_detector
        self.game_initializer = game_initializer
        self.bots = bots

    def _pick_bot(self, world):
        for bot in self.bots:
            if bot.can_handle(world):
                return bot
        return None

    def run_once(self, index):
        self.logger.info(f"第 {index + 1} 轮主循环开始", level=0)
        world = self.world_detector.detect(auto_zoom=True)
        bot = self._pick_bot(world)
        if bot is None:
            self.logger.raise_with_screenshot(f"无法识别当前世界: {world}")
        bot.run_bot()
        self.logger.info(f"第 {index + 1} 轮主循环完成", level=0)

    def run(self):
        for index in range(self.config.run_times):
            try:
                self.run_once(index)
                self.game_initializer.cleanup_cycle_images()
                sleep_time = random.randint(25, 35)
                self.logger.debug(f"等待 {sleep_time} 秒后进入下一轮")
                sleep(sleep_time)
            except Exception as exc:
                self.logger.error(f"主循环出错: {exc}")
                self.game_initializer.cleanup_cycle_images()
                self.game_initializer.recover()
