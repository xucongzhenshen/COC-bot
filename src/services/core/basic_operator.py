import random

import cv2
import ddddocr
from airtest.core.api import G, exists, find_all, pinch, sleep, swipe, touch, wait


_OCR_INSTANCE = ddddocr.DdddOcr(show_ad=False, beta=True)
ROI_COUNTDOWN = [10, 1080, 60, 1450]


class BasicOperator:
    def __init__(self, logger=None):
        self.logger = logger

    def exists(self, target):
        return exists(target)

    def find_all(self, target):
        return find_all(target)

    def touch(self, target):
        return touch(target)

    def wait(self, target, timeout=10, interval=0.5):
        return wait(target, timeout=timeout, interval=interval)

    def swipe(self, p1, p2, duration=0.5):
        return swipe(p1, p2, duration=duration)

    def sleep(self, seconds):
        return sleep(seconds)

    def set_max_zoom_out(self):
        """连续捏合以扩大视野，减少识别误差。"""
        if self.logger is not None:
            self.logger.info("正在捏合以扩大视野...", level=1)
        for _ in range(3):
            pinch(in_or_out="in", center=None, percent=0.2)
            sleep(0.5)

    def random_touch(self, pos, offset=5, min_sleep_time=0.5, max_sleep_time=1.0):
        if not pos:
            self.logger.raise_with_screenshot("random_touch: 无效位置", ValueError)
        x, y = pos
        target_x = int(x) + random.randint(-offset, offset)
        target_y = int(y) + random.randint(-offset, offset)
        touch([target_x, target_y])
        sleep(random.uniform(min_sleep_time, max_sleep_time))

    def get_text(self, roi=ROI_COUNTDOWN):
        roi_to_use = roi if isinstance(roi, (list, tuple)) else ROI_COUNTDOWN
        screen = G.DEVICE.snapshot() if G.DEVICE else None
        if screen is None:
            return ""

        h, w = screen.shape[:2]
        y_min, x_min, y_max, x_max = [int(v) for v in roi_to_use]
        y_min, y_max = max(0, y_min), min(h, y_max)
        x_min, x_max = max(0, x_min), min(w, x_max)
        cropped = screen[y_min:y_max, x_min:x_max]
        if cropped.size == 0:
            return ""

        ok, encoded_image = cv2.imencode(".png", cropped)
        if not ok:
            return ""
        text = _OCR_INSTANCE.classification(encoded_image.tobytes())
        return text.strip() if text else ""
