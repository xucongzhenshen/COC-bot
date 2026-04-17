import csv
import math

from src.cocbot._assets import Assets
from src.cocbot.common import find_all, get_log_path, log_msg


class AirDefenseDetector:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def _distance(p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _load_anti_aircraft_stats(self):
        stats = {}
        with open(self.config.anti_aircraft_data_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                level = int(row["Level"])
                stats[level] = {
                    "dp_second": int(row["DPSecond"]),
                    "hitpoints": int(row["Hitpoints"]),
                }
        return stats

    def detect(self):
        level_template_map = {
            1: Assets.ANTI_AIRCRAFT_ROCKET1,
            2: Assets.ANTI_AIRCRAFT_ROCKET2,
            3: Assets.ANTI_AIRCRAFT_ROCKET3,
            4: Assets.ANTI_AIRCRAFT_ROCKET4,
            5: Assets.ANTI_AIRCRAFT_ROCKET5,
            6: Assets.ANTI_AIRCRAFT_ROCKET6,
            7: Assets.ANTI_AIRCRAFT_ROCKET7,
        }
        anti_aircraft_stats = self._load_anti_aircraft_stats()

        raw_detects = []
        for level, template in level_template_map.items():
            matches = find_all(template)
            if not matches:
                continue
            for match in matches:
                raw_detects.append(
                    {
                        "level": level,
                        "position": match["result"],
                        "confidence": float(match.get("confidence", 0.0)),
                        "dp_second": anti_aircraft_stats[level]["dp_second"],
                        "hitpoints": anti_aircraft_stats[level]["hitpoints"],
                    }
                )

        deduped = []
        merge_radius = 25
        for item in sorted(raw_detects, key=lambda x: x["confidence"], reverse=True):
            if any(self._distance(item["position"], kept["position"]) <= merge_radius for kept in deduped):
                continue
            deduped.append(item)

        detail = ", ".join([f"L{item['level']}@{item['position']}" for item in deduped])
        log_msg(f"检测到 {len(deduped)} 个防空火箭: {detail}", level=1, log_path=get_log_path())
        return deduped
