import argparse

from src.cocbot.config_manager import get_config_manager


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
        help="每轮主世界最大进攻尝试次数",
    )
    parser.add_argument(
        "--night_attempts",
        type=int,
        default=None,
        help="每轮夜世界最大进攻尝试次数",
    )
    parser.add_argument(
        "--night_faction",
        type=str,
        choices=["witch", "archer"],
        default=None,
        help="夜世界练兵流派，默认女巫 (witch)",
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
    return parser.parse_args()


class ConfigManager:
    """配置入口层：包装旧版配置器，提供统一装配入口。"""

    def __init__(self):
        self._legacy = get_config_manager()

    def load(self, args_namespace=None):
        return self._legacy.load(args_namespace)

    @property
    def config(self):
        return self._legacy
