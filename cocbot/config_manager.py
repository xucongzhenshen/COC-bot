import json
import os
from typing import Any, Optional


class ConfigManager:
    """统一管理项目参数：默认值 + JSON 配置 + 命令行覆盖。"""

    def __init__(self):
        self.device: str = ""
        self.cap_method: str = ""
        self.touch_method: str = ""
        self.ori_method: str = ""
        self.loglevel: int = 0
        self.log_path: str = ""
        self.run_times: int = 0
        self.night_faction: str = ""
        self.version: str = ""
        self.night_retrain: bool = False
        self.home_retrain: bool = False
        self.home_battle: bool = True
        self.night_battle: bool = True
        self.home_filter: dict[str, int] = {"gold": 0, "water": 0, "oil": 0}
        self.home_faction: str = ""
        self.home_fight_config_path: str = ""
        self.lightning_data_path: str = ""
        self.anti_aircraft_data_path: str = ""
        self.home_attempts: int = 0
        self.night_attempts: int = 0
        self.config_path: Optional[str] = None
        self.home_fight: dict[str, int] = {"dragon_number": 0, "lightning_number": 0, "lightning_level": 0}

        self._loaded = False
        self._project_root = os.path.dirname(os.path.dirname(__file__))
        self._defaults = {
            "device": "emulator-5554",
            "cap_method": "MINICAP",
            "touch_method": "MINITOUCH",
            "ori_method": "ADBORI",
            "loglevel": 1,
            "log_path": "log",
            "run_times": 50,
            "night_faction": "witch",
            "version": "tencent",
            "night_retrain": False,
            "home_retrain": False,
            "home_battle": True,
            "night_battle": True,
            "home_filter": {
                "gold": 400000,
                "water": 400000,
                "oil": 1500,
            },
            "home_faction": "dragon",
            "home_fight_config_path": os.path.join("config", "home_fight.json"),
            "lightning_data_path": os.path.join("GameData", "home", "lightning_spell.csv"),
            "anti_aircraft_data_path": os.path.join("GameData", "home", "anti_aircraft_rocket.csv"),
            "home_attempts": 5,
            "night_attempts": 10,
            "config_path": None,
        }
        self._home_fight_defaults = {
            "dragon_number": 10,
            "lightning_number": 9,
            "lightning_level": 10,
        }

    @property
    def project_root(self):
        return self._project_root

    @property
    def loaded(self):
        return self._loaded

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"ConfigManager has no attribute: {name}")

    def _merge_dict(self, base, incoming):
        merged = dict(base)
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_dict(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _abs_path(self, path_value):
        if not path_value:
            return None
        if os.path.isabs(path_value):
            return path_value
        return os.path.abspath(os.path.join(self._project_root, path_value))

    def _load_json_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _parse_home_filter(self, value):
        if isinstance(value, dict):
            parsed = value
        elif isinstance(value, str):
            parsed = json.loads(value)
        else:
            raise ValueError(f"home_filter 类型错误: {type(value)}")

        return {
            "gold": int(parsed["gold"]),
            "water": int(parsed["water"]),
            "oil": int(parsed["oil"]),
        }

    def load(self, args_namespace=None):
        data = dict(self._defaults)

        args_map = vars(args_namespace) if args_namespace is not None else {}
        config_path = args_map.get("config_path")
        if config_path:
            config_abs_path = self._abs_path(config_path)
            loaded_config = self._load_json_file(config_abs_path)
            data = self._merge_dict(data, loaded_config)
            data["config_path"] = config_abs_path

        for key, value in args_map.items():
            if value is None:
                continue
            data[key] = value

        data["home_filter"] = self._parse_home_filter(data["home_filter"])
        data["loglevel"] = int(data["loglevel"])
        data["run_times"] = int(data["run_times"])
        data["home_attempts"] = int(data["home_attempts"])
        data["night_attempts"] = int(data["night_attempts"])

        data["log_path"] = self._abs_path(data["log_path"])
        data["home_fight_config_path"] = self._abs_path(data["home_fight_config_path"])
        data["lightning_data_path"] = self._abs_path(data["lightning_data_path"])
        data["anti_aircraft_data_path"] = self._abs_path(data["anti_aircraft_data_path"])

        home_fight = dict(self._home_fight_defaults)
        home_fight_path = data["home_fight_config_path"]
        try:
            if home_fight_path and os.path.exists(home_fight_path):
                loaded_home_fight = self._load_json_file(home_fight_path)
                home_fight = self._merge_dict(home_fight, loaded_home_fight)
        except Exception:
            # home_fight 文件读取失败时退回默认值，避免阻塞主流程。
            pass

        data["home_fight"] = {
            "dragon_number": int(home_fight["dragon_number"]),
            "lightning_number": int(home_fight["lightning_number"]),
            "lightning_level": int(home_fight["lightning_level"]),
        }

        for key, value in data.items():
            setattr(self, key, value)

        self._loaded = True
        return self


CONFIG = ConfigManager()


def get_config_manager():
    return CONFIG
