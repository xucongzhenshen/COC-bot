from airtest.core.api import G

from src.utils import Assets


class WorldDetector:
    def __init__(self, confidence_threshold=0.6, logger=None, basic_operator=None):
        self.confidence_threshold = confidence_threshold
        self.logger = logger
        self.basic_operator = basic_operator

    def _log(self, msg, level=1):
        if self.logger is None:
            return
        if level == 0:
            self.logger.error(msg)
        elif level == 2:
            self.logger.debug(msg)
        else:
            self.logger.info(msg, level=1)

    def detect(self, auto_zoom=True):
        if auto_zoom and self.basic_operator is not None:
            self.basic_operator.set_max_zoom_out()

        candidates = [
            ("HOME", "ATTACK_HOME", Assets.ATTACK_HOME),
            ("HOME", "ATTACK_HOME_WITH_STAR", Assets.ATTACK_HOME_WITH_STAR),
            ("HOME", "ATTACK_HOME_WITH_3_STAR", Assets.ATTACK_HOME_WITH_3_STAR),
            ("NIGHT", "NIGHT_ATTACK", Assets.NIGHT_ATTACK),
            ("NIGHT", "NIGHT_ATTACK_WITH_STAR", Assets.NIGHT_ATTACK_WITH_STAR),
        ]

        best_world = "UNKNOWN"
        best_name = None
        best_confidence = -1.0

        screen = G.DEVICE.snapshot()
        if screen is None:
            self._log("DEBUG: detect_world snapshot is None", level=2)
            return "UNKNOWN"

        for world, name, template in candidates:
            results = template._cv_match(screen)
            if not results:
                self._log(f"DEBUG: {name} 没有找到任何匹配点", level=2)
                continue

            confidence = float(results.get("confidence", 0.0))
            pos = results.get("result")
            self._log(f"DEBUG: {name} confidence = {confidence:.4f} at {pos}", level=2)

            if confidence > best_confidence:
                best_world = world
                best_name = name
                best_confidence = confidence

        if best_confidence > self.confidence_threshold:
            self._log(
                f"DEBUG: Final decision -> {best_world} (via {best_name} score:{best_confidence:.2f})",
                level=2,
            )
            return best_world
        return "UNKNOWN"
