import subprocess
import time
import os

from airtest.core.api import auto_setup, connect_device, snapshot, sleep


class DeviceManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.uri = None

    def ensure_device_running(self):
        """确保设备正在运行"""
        if self._is_device_connected():
            self.logger.info(f"设备 {self.config.device} 已连接")
            return True
        
        self.logger.info(f"设备 {self.config.device} 未连接，尝试启动...")

        retry_times = int(getattr(self.config, "device_retry_times", 3))
        for attempt in range(retry_times):
            if self._start_device_from_shortcut():
                return True
            self.logger.warning(f"启动设备失败，重试 {attempt + 1}/{retry_times}")
        return False
    
    def _is_device_connected(self):
        """检查设备是否已通过ADB连接"""
        try:
            cmd = ["adb", "devices"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # 解析设备列表
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳过第一行标题
                if line.strip() and self.config.device in line:
                    return True
            return False
        except Exception as e:
            self.logger.error(f"检查设备连接失败: {e}")
            return False
    
    def _start_device_from_shortcut(self):
        """通过快捷方式启动设备"""
        shortcut_name = f"{self.config.device}.lnk"
        shortcut_path = os.path.join(self.config.device_shortcut_dir, shortcut_name)
        
        if not os.path.exists(shortcut_path):
            self.logger.error(f"设备快捷方式不存在: {shortcut_path}")
            return False
        
        try:
            if os.name == 'nt':  # Windows系统
                # 方法1: 使用start命令（推荐）
                subprocess.Popen(["start", "", shortcut_path], shell=True)
                # 或方法2: 直接运行快捷方式
                # os.startfile(shortcut_path)
                
                self.logger.info(f"正在启动设备: {shortcut_path}")
                
                # 等待设备启动
                return self._wait_for_device_ready(timeout=120)
            else:
                # Linux/macOS 不支持 .lnk
                self.logger.error("非Windows系统不支持.lnk快捷方式")
                return False
                
        except Exception as e:
            self.logger.error(f"启动设备失败: {e}")
            return False
    
    def _wait_for_device_ready(self, timeout=120):
        """等待设备启动就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_device_connected():
                # 额外等待设备完全初始化
                time.sleep(10)
                self.logger.info("设备启动完成")
                return True
            
            self.logger.debug("等待设备启动...")
            time.sleep(5)
        
        self.logger.error(f"设备启动超时 ({timeout}秒)")
        return False
    
    def connect_runtime(self, script_file):
        if not self.ensure_device_running():
            self.logger.raise_with_screenshot("设备启动失败，无法继续运行")

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

