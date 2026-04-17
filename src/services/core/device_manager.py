from src.cocbot.common import (
    build_airtest_uri,
    close_popups,
    ensure_screenshot_ready,
    setup_runtime,
    start_clash_of_clans,
    stop_clash_of_clans,
)


class DeviceManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.uri = None

    def connect_runtime(self, script_file):
        self.uri = build_airtest_uri(
            self.config.device,
            self.config.cap_method,
            self.config.touch_method,
            self.config.ori_method,
        )
        self.logger.info(f"连接设备: {self.uri}", level=0)
        setup_runtime(script_file, self.uri, self.config.log_path, self.config.project_root)
        ready = ensure_screenshot_ready(max_retries=5)
        if not ready:
            raise RuntimeError("截图功能不可用，无法继续运行")

    def start_game(self):
        ok = start_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            raise RuntimeError("游戏启动失败")
        close_popups()

    def stop_game(self):
        ok = stop_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            self.logger.error("停止游戏失败，继续后续流程")

    def restart_game(self):
        self.stop_game()
        self.start_game()
