import logging
import os
import re
from datetime import datetime


def _sanitize_filename(value):
    text = re.sub(r'[\\/:*?"<>|]+', "_", str(value))
    text = text.strip(" ._")
    return text or "exception"


class LoggerService:
    def __init__(self, config):
        self.config = config
        self.log_path = None
        self.log_level = 1
        self.log_file = None

    def initialize(self):
        airtest_logger = logging.getLogger("airtest")
        airtest_logger.setLevel(logging.ERROR)
        self.log_path = self.config.log_path
        os.makedirs(self.log_path, exist_ok=True)
        self.log_level = int(self.config.loglevel)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_path, f"cocbot_{timestamp}.log")
        with open(self.log_file, "w", encoding="utf-8") as _:
            pass

    def _screenshot_dir(self):
        if not self.log_path:
            return None
        path = os.path.join(self.log_path, "screenshots")
        os.makedirs(path, exist_ok=True)
        return path

    def capture_screenshot(self, summary):
        screenshot_dir = self._screenshot_dir()
        if not screenshot_dir:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{_sanitize_filename(summary)}_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)

        try:
            from airtest.core.api import G

            if not getattr(G, "DEVICE", None):
                return None
            G.DEVICE.snapshot(filepath)
            return filepath
        except Exception as exc:
            self._write(f"截图保存失败: {exc}", 0)
            return None

    def _write(self, message, level):
        if self.log_level < int(level):
            return
        text = str(message)
        print(text)
        if not self.log_file:
            return
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{level}] {text}\n")

    def info(self, message, level=1):
        self._write(message, level)

    def error(self, message):
        self._write(message, 0)

    def debug(self, message):
        self._write(message, 2)

    def raise_with_screenshot(self, message, exc_type=RuntimeError):
        screenshot_path = self.capture_screenshot(message)
        if screenshot_path:
            self.error(f"{message} | 截图: {screenshot_path}")
        else:
            self.error(message)
        raise exc_type(message)
