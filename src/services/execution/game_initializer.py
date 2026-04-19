import os

from airtest.core.api import exists, sleep, touch

from src.utils import Assets


class GameInitializer:
    def __init__(self, config, logger, device_manager):
        self.config = config
        self.logger = logger
        self.device_manager = device_manager

    def startup(self):
        self.cleanup_cycle_images()
        self.logger.info("启动游戏...", level=0)
        self.device_manager.start_game()
        self._close_popups()

    def recover(self):
        self.logger.info("尝试停止游戏并重新启动...", level=0)
        self.device_manager.restart_game()
        self._close_popups()

    def cleanup_cycle_images(self):
        removed = 0
        log_dir = self.config.log_path
        if not os.path.exists(log_dir):
            return 0
        for root, _, files in os.walk(log_dir):
            for name in files:
                if "debug" in name.lower():
                    continue
                if not name.lower().endswith((".png", ".jpg", ".jpeg")):
                    continue
                file_path = os.path.join(root, name)
                try:
                    os.remove(file_path)
                    removed += 1
                except Exception as exc:
                    self.logger.debug(f"清理图片失败 {file_path}: {exc}")
        return removed

    def _close_popups(self):
        for target in (Assets.CLOSE, Assets.CLOSE_ACTIVITY, Assets.BTN_CONFIRM):
            pos = exists(target)
            while pos:
                touch(pos)
                sleep(0.5)
                pos = exists(target)
