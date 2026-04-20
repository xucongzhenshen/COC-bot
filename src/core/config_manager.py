import argparse
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        type=str,
        default=None,
        help="全局配置 JSON 路径，复杂参数建议写入该文件",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="设备 ID，例如 emulator-5554",
    )
    parser.add_argument(
        "--cap_method",
        type=str,
        choices=["MINICAP", "JAVACAP"],
        default=None,
        help="截图方式，模拟器推荐 MINICAP",
    )
    parser.add_argument(
        "--touch_method",
        type=str,
        choices=["MINITOUCH", "ADBTOUCH"],
        default=None,
        help="触控方式",
    )
    parser.add_argument(
        "--ori_method",
        type=str,
        choices=["ADBORI", "MINICAPORI"],
        default=None,
        help="方向获取方式",
    )
    parser.add_argument(
        "--loglevel",
        type=int,
        choices=[0, 1, 2],
        default=None,
        help="日志等级: 0=仅流程完成, 1=每一步操作, 2=全部日志",
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default=None,
        help="日志文件路径",
    )
    parser.add_argument(
        "--run_times",
        type=int,
        default=None,
        help="主循环执行次数，默认 50 次",
    )
    parser.add_argument(
        "--home_attempts",
        type=int,
        default=None,
        help="每轮主世界最大进攻尝试次数，默认 5 次",
    )
    parser.add_argument(
        "--night_attempts",
        type=int,
        default=None,
        help="每轮夜世界最大进攻尝试次数，默认 10 次",
    )
    parser.add_argument(
        "--night_faction",
        type=str,
        choices=["witch", "witch_1", "witch_2", "archer"],
        default=None,
        help="夜世界练兵流派，默认 witch_1",
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=["tencent", "global"],
        default=None,
        help="游戏版本，可选值：tencent（腾讯版）或 global（国际服），默认 tencent",
    )
    parser.add_argument(
        "--night_retrain",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_retrain",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_battle",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="是否执行主世界战斗逻辑",
    )
    parser.add_argument(
        "--night_battle",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否执行夜世界战斗逻辑，默认为 True，设置为 False 将跳过夜世界战斗",
    )
    parser.add_argument(
        "--home_switch",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="主世界流程后是否切换世界",
    )
    parser.add_argument(
        "--night_switch",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="夜世界流程后是否切换世界",
    )
    parser.add_argument(
        "--home_filter",
        type=str,
        default=None,
        help="主世界战斗资源过滤配置，格式为 JSON 字符串，例如 '{\"gold\": 500000, \"water\": 500000, \"oil\": 1500}'",
    )
    parser.add_argument(
        "--home_faction",
        type=str,
        choices=["dragon", "electro_dragon"],
        default=None,
        help="主世界练兵流派，默认龙 (dragon)",
    )
    parser.add_argument(
        "--home_fight_config_path",
        type=str,
        default=None,
        help="主世界战斗参数 JSON 路径，包含 dragon_number/lightning_number/lightning_level",
    )
    parser.add_argument(
        "--lightning_data_path",
        type=str,
        default=None,
        help="闪电法术数据 CSV 路径",
    )
    parser.add_argument(
        "--anti_aircraft_data_path",
        type=str,
        default=None,
        help="防空火箭数据 CSV 路径",
    )
    parser.add_argument(
        "--home_army_setting_path",
        type=str,
        default=None,
        help="主世界配兵配置路径，支持目录或 JSON 文件，默认 configs/army_setting/home",
    )
    parser.add_argument(
        "--night_army_setting_path",
        type=str,
        default=None,
        help="夜世界配兵配置路径，支持目录或 JSON 文件，默认 configs/army_setting/night",
    )
    parser.add_argument(
        "--exception_retry_times",
        type=int,
        default=None,
        help="异常恢复最大重试次数，默认 3",
    )
    parser.add_argument(
        "--exception_recovery_wait_seconds",
        type=int,
        default=None,
        help="异常恢复时每轮等待秒数，默认 5",
    )
    parser.add_argument(
        "--exception_wait_for_start_timeout",
        type=int,
        default=None,
        help="异常恢复时等待游戏启动超时（秒），默认 50",
    )
    return parser.parse_args()


class ConfigManager:
    """配置入口层：统一管理默认值 + JSON + CLI 覆盖。"""

    def __init__(self):
        self._loaded = False
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        self._defaults = {
            "device": "emulator-5554",
            "cap_method": "MINICAP",
            "touch_method": "MINITOUCH",
            "ori_method": "ADBORI",
            "loglevel": 2,
            "log_path": f"logs/global",
            "run_times": 50,
            "version": "global",
            "home_retrain": False,
            "night_retrain": False,
            "home_battle": True,
            "night_battle": True,
            "home_attempts": 5,
            "night_attempts": 10,
            "home_faction": "dragon",
            "night_faction": "witch_1",
            "home_switch": True,
            "night_switch": True,
            "home_filter": {
                "gold": 400000,
                "water": 400000,
                "oil": 1500,
            },
            "home_fight_config_path": os.path.join("configs", "home_fight.json"),
            "lightning_data_path": os.path.join("data", "game_data", "home", "lightning_spell.csv"),
            "anti_aircraft_data_path": os.path.join("data", "game_data", "home", "anti_aircraft_rocket.csv"),
            "home_army_setting_path": os.path.join("configs", "army_setting", "home"),
            "night_army_setting_path": os.path.join("configs", "army_setting", "night"),
            "exception_retry_times": 3,
            "exception_recovery_wait_seconds": 5,
            "exception_wait_for_start_timeout": 50,
            "sample_path": os.path.join("data", "sample_imgs", "night"),
            "device_shortcut_dir": "devices",
        }
        self._home_fight_defaults = {
            "dragon_number": 10,
            "lightning_number": 9,
            "lightning_level": 10,
        }

        self.home_retrain = False
        self.night_retrain = False
        self.home_battle = True
        self.night_battle = True
        self.home_attempts = 5
        self.night_attempts = 10
        self.home_faction = "dragon"
        self.night_faction = "witch_1"
        self.home_switch = True
        self.night_switch = True
        self.home_filter = {"gold": 400000, "water": 400000, "oil": 1500}
        self.home_army_setting_path = "configs/army_setting/home"
        self.night_army_setting_path = "configs/army_setting/night"
        self.device_shortcut_dir = "devices"

        self.home_bot: Optional[BotConfig] = None
        self.night_bot: Optional[BotConfig] = None

    def _abs_path(self, value):
        if not value:
            return None
        if os.path.isabs(value):
            return value
        return os.path.abspath(os.path.join(self.project_root, value))

    def _merge_dict(self, base: dict[str, Any], incoming: dict[str, Any]):
        merged = dict(base)
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_dict(merged[key], value)
            else:
                merged[key] = value
        return merged

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

    def _load_json_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load(self, args_namespace=None):
        args_map = vars(args_namespace) if args_namespace is not None else {}
        data = dict(self._defaults)

        config_path = args_map.get("config_path")
        if config_path:
            config_abs_path = self._abs_path(config_path)
            loaded_config = self._load_json_file(config_abs_path)
            data = self._merge_dict(data, loaded_config)

        for key, value in args_map.items():
            if value is None:
                continue
            data[key] = value

        data["run_times"] = int(data["run_times"])
        data["home_attempts"] = int(data["home_attempts"])
        data["night_attempts"] = int(data["night_attempts"])
        data["loglevel"] = int(data["loglevel"])
        data["exception_retry_times"] = int(data["exception_retry_times"])
        data["exception_recovery_wait_seconds"] = int(data["exception_recovery_wait_seconds"])
        data["exception_wait_for_start_timeout"] = int(data["exception_wait_for_start_timeout"])

        data["log_path"] = self._abs_path(data["log_path"])
        data["lightning_data_path"] = self._abs_path(data["lightning_data_path"])
        data["anti_aircraft_data_path"] = self._abs_path(data["anti_aircraft_data_path"])
        data["home_fight_config_path"] = self._abs_path(data["home_fight_config_path"])
        data["home_army_setting_path"] = self._abs_path(data["home_army_setting_path"])
        data["night_army_setting_path"] = self._abs_path(data["night_army_setting_path"])
        data["device_shortcut_dir"] = self._abs_path(data["device_shortcut_dir"])
        data["home_filter"] = self._parse_home_filter(data["home_filter"])

        home_fight = dict(self._home_fight_defaults)
        home_fight_path = data["home_fight_config_path"]
        if home_fight_path and os.path.exists(home_fight_path):
            loaded_home_fight = self._load_json_file(home_fight_path)
            home_fight = self._merge_dict(home_fight, loaded_home_fight)
        data["home_fight"] = {
            "dragon_number": int(home_fight["dragon_number"]),
            "lightning_number": int(home_fight["lightning_number"]),
            "lightning_level": int(home_fight["lightning_level"]),
        }

        for key, value in data.items():
            setattr(self, key, value)

        self.home_bot = BotConfig(
            retrain=self.home_retrain,
            battle=self.home_battle,
            attempts=self.home_attempts,
            faction=self.home_faction,
            switch=self.home_switch,
            filter_config=self.home_filter,
            army_setting_path=self.home_army_setting_path,
        )
        self.night_bot = BotConfig(
            retrain=self.night_retrain,
            battle=self.night_battle,
            attempts=self.night_attempts,
            faction=self.night_faction,
            switch=self.night_switch,
            army_setting_path=self.night_army_setting_path,
        )

        self._loaded = True
        return self

    @property
    def config(self):
        return self


@dataclass
class BotConfig:
    retrain: bool
    battle: bool
    attempts: int
    faction: str
    switch: bool
    filter_config: Optional[Dict[str, int]] = None
    army_setting_path: Optional[str] = None

