import os

from src.cocbot.common import G
from src.cocbot.meadow_detector import MeadowParallelogramDetector


class MeadowDetector:
    def __init__(self, sample_path=None):
        if sample_path is None:
            sample_path = os.path.join("cocbot", "sample_imgs", "night")
        self._detector = MeadowParallelogramDetector(sample_path=sample_path)

    def detect_center(self, screen_bgr=None, debug_output=False, debug_dir=None, debug_prefix="meadow_detect"):
        """识别夜世界草地中心，返回 (center, box_points, mask)。"""
        if screen_bgr is None:
            screen_bgr = G.DEVICE.snapshot()
        if screen_bgr is None:
            return None, None, None

        return self._detector.detect_with_debug(
            screen_bgr,
            min_area_ratio=0.07,
            debug_output=debug_output,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
        )

    def center_night_view(self, tolerance_px=45):
        """兼容旧接口：仅返回当前是否已居中和中心点，不执行移动。"""
        screen = G.DEVICE.snapshot()
        if screen is None:
            return False, None, None, []

        h, w = screen.shape[:2]
        screen_center = (w / 2.0, h / 2.0)
        center, _, _ = self.detect_center(screen_bgr=screen)
        if center is None:
            return False, None, None, []

        dx = screen_center[0] - center[0]
        dy = screen_center[1] - center[1]
        ok = (dx * dx + dy * dy) ** 0.5 <= tolerance_px
        return ok, center, (0.0, 0.0), []
