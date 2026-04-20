from src.logic import HomeBot, NightBot, MainLoop


class AppBuilder:
    """将基础服务组装成可执行应用对象。"""

    def __init__(self, config, services):
        self.config = config
        self.services = services

    def build_bots(self):
        return [
            HomeBot(self.config.home_bot, self.services),
            NightBot(self.config.night_bot, self.services),
        ]

    def build_main_loop(self, runtime_script_file):
        bots = self.build_bots()
        return MainLoop(
            config=self.config,
            logger=self.services.logger,
            world_detector=self.services.world_detector,
            game_initializer=self.services.game_initializer,
            exception_handler=self.services.exception_handler,
            device_manager=self.services.device_manager,
            runtime_script_file=runtime_script_file,
            bots=bots,
        )
