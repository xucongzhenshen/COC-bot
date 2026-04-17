from src.cocbot.common import close_popups, delete_img_in_log


class GameInitializer:
    def __init__(self, config, logger, device_manager):
        self.config = config
        self.logger = logger
        self.device_manager = device_manager

    def startup(self):
        delete_img_in_log(self.config.log_path)
        self.logger.info("启动游戏...", level=0)
        self.device_manager.start_game()
        close_popups()

    def recover(self):
        self.logger.info("尝试停止游戏并重新启动...", level=0)
        self.device_manager.restart_game()
        close_popups()

    def cleanup_cycle_images(self):
        delete_img_in_log(self.config.log_path)
