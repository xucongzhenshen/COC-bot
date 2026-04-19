import subprocess
import time

from airtest.core.api import auto_setup, connect_device, exists, snapshot, sleep

from src.utils import Assets


class DeviceManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.uri = None

    def connect_runtime(self, script_file):
        self.uri = (
            f"android://127.0.0.1:5037/{self.config.device}"
            f"?cap_method={self.config.cap_method}"
            f"&touch_method={self.config.touch_method}"
            f"&ori_method={self.config.ori_method}"
        )
        self.logger.info(f"连接设备: {self.uri}", level=0)
        connect_device(self.uri)
        auto_setup(
            script_file,
            logdir=self.config.log_path,
            devices=[self.uri],
            project_root=self.config.project_root,
        )
        ready = self._ensure_screenshot_ready(max_retries=5)
        if not ready:
            self.logger.raise_with_screenshot("截图功能不可用，无法继续运行")

    def start_game(self):
        ok = self._start_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            self.logger.raise_with_screenshot("游戏启动失败")
        self._close_popups()

    def stop_game(self):
        ok = self._stop_clash_of_clans(self.config.device, version=self.config.version)
        if not ok:
            self.logger.error("停止游戏失败，继续后续流程")

    def restart_game(self):
        self.stop_game()
        self.start_game()

    def _close_popups(self):
        for target in (Assets.CLOSE, Assets.CLOSE_ACTIVITY, Assets.BTN_CONFIRM):
            pos = exists(target)
            while pos:
                from airtest.core.api import touch

                touch(pos)
                sleep(0.5)
                pos = exists(target)

    def _ensure_screenshot_ready(self, max_retries=5):
        for idx in range(max_retries):
            try:
                img = snapshot()
                if img is not None:
                    self.logger.debug("截图功能正常")
                    return True
            except Exception as exc:
                self.logger.debug(f"截图异常: {exc}")
            self.logger.info(f"截图不可用，重试 {idx + 1}/{max_retries}", level=1)
            sleep(1)
        return False

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

        start_time = time.time()
        while time.time() - start_time < 90:
            if exists(Assets.BTN_TRAIN):
                return True
            sleep(2)
        return False

    def _stop_clash_of_clans(self, device_serial="emulator-5554", version="tencent", adb_path="adb"):
        package_name = "com.supercell.clashofclans" if version == "global" else "com.tencent.tmgp.supercell.clashofclans"
        cmd = [adb_path, "-s", device_serial, "shell", "am", "force-stop", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0
