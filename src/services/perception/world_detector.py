from src.cocbot._assets import Assets
from src.cocbot.common import G, get_log_path, log_msg, pinch, sleep


class WorldDetector:
    def __init__(self, confidence_threshold=0.6):
        self.confidence_threshold = confidence_threshold

    def set_max_zoom_out(self):
        """连续捏合以扩大视野，减少识别误差。"""
        log_msg("正在捏合以扩大视野...", log_path=get_log_path())
        for _ in range(3):
            pinch(in_or_out="in", center=None, percent=0.2)
            sleep(0.5)

    def detect(self, auto_zoom=True):
        if auto_zoom:
            self.set_max_zoom_out()

        candidates = [
            ("HOME", "FIGHT_HOME", Assets.FIGHT_HOME),
            ("HOME", "FIGHT_HOME_WITH_STAR", Assets.FIGHT_HOME_WITH_STAR),
            ("HOME", "FIGHT_HOME_WITH_3_STAR", Assets.FIGHT_HOME_WITH_3_STAR),
            ("NIGHT", "NIGHT_FIGHT", Assets.NIGHT_FIGHT),
            ("NIGHT", "NIGHT_FIGHT_WITH_STAR", Assets.NIGHT_FIGHT_WITH_STAR),
        ]

        best_world = "UNKNOWN"
        best_name = None
        best_confidence = -1.0

        screen = G.DEVICE.snapshot()
        if screen is None:
            log_msg("DEBUG: detect_world snapshot is None", level=2, log_path=get_log_path())
            return "UNKNOWN"

        for world, name, template in candidates:
            results = template._cv_match(screen)
            if not results:
                log_msg(f"DEBUG: {name} 没有找到任何匹配点", level=2, log_path=get_log_path())
                continue

            confidence = float(results.get("confidence", 0.0))
            pos = results.get("result")
            log_msg(f"DEBUG: {name} confidence = {confidence:.4f} at {pos}", level=2, log_path=get_log_path())

            if confidence > best_confidence:
                best_world = world
                best_name = name
                best_confidence = confidence

        if best_confidence > self.confidence_threshold:
            log_msg(
                f"DEBUG: Final decision -> {best_world} (via {best_name} score:{best_confidence:.2f})",
                level=2,
                log_path=get_log_path(),
            )
            return best_world
        return "UNKNOWN"
