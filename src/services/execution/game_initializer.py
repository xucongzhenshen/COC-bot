import os
import subprocess
import time

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
        self._start_game()

    def recover(self):
        self.logger.info("尝试停止游戏并重新启动...", level=0)
        self._restart_game()

    def _start_game(self):
        ok = self._start_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            self.logger.raise_with_screenshot("游戏启动失败")
        self._close_popups()

    def _stop_game(self):
        ok = self._stop_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            self.logger.error("停止游戏失败，继续后续流程")

    def _restart_game(self):
        self._stop_game()
        self._start_game()

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

    def _start_clash_of_clans(self, device_serial="emulator-5554", version="tencent", adb_path="adb"):
        if version == "global":
            package_name = "com.supercell.clashofclans"
            component = f"{package_name}/com.supercell.titan.GameApp"
        else:
            package_name = "com.tencent.tmgp.supercell.clashofclans"
            component = f"{package_name}/com.supercell.titan.tencent.GameAppTencent"

        subprocess.run([adb_path, "-s", device_serial, "shell", "am", "force-stop", package_name], capture_output=True)
        sleep(1)
        cmd = [adb_path, "-s", device_serial, "shell", "am", "start", "-n", component]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if "Error" in result.stdout or "error" in result.stderr:
            self.logger.error(f"启动命令失败: {result.stderr or result.stdout}")
            return False

        self.logger.info("启动命令已发送，等待游戏启动...")
        return self.wait_for_game_start(timeout=90)

    def _stop_clash_of_clans(self, device_serial="emulator-5554", version="tencent", adb_path="adb"):
        package_name = "com.supercell.clashofclans" if version == "global" else "com.tencent.tmgp.supercell.clashofclans"
        cmd = [adb_path, "-s", device_serial, "shell", "am", "force-stop", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0
    
    def _is_game_started(self):
        if exists(Assets.BTN_TRAIN):
            return True
        return False
    
    def wait_for_game_start(self, timeout=90):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_game_started():
                self.logger.info("游戏启动成功")
                return True
            sleep(2)
        self.logger.error("等待游戏启动超时")
        return False
