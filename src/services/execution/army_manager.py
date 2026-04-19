import json
import os
from abc import ABC, abstractmethod
from typing import cast

from src.utils import Assets


class ArmyManager(ABC):
    def __init__(self, logger, faction, army_setting_path, bot_name):
        self.logger = logger
        self.faction = faction
        self.army_setting_path = army_setting_path
        self.bot_name = bot_name
        self.army_setting = self.load_army_setting(self.army_setting_path)

    def load_army_setting(self, army_setting_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if not army_setting_path:
            self.logger.warning(f"{self.bot_name} 未配置 army_setting_path，采用默认设置", level=1)
            if self.bot_name == "HomeBot":
                army_setting_path = os.path.join("configs", "army_setting", "home")
            elif self.bot_name == "NightBot":
                army_setting_path = os.path.join("configs", "army_setting", "night")
            else:
                army_setting_path = os.path.join("configs", "army_setting")

        setting_path = army_setting_path
        if not os.path.isabs(setting_path):
            setting_path = os.path.join(project_root, setting_path)

        if os.path.isdir(setting_path):
            return self._load_army_setting_from_dir(setting_path)
        return self._load_json_file(setting_path)

    def _load_json_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.raise_with_screenshot(f"{self.bot_name} 配兵文件不存在: {file_path}", FileNotFoundError)
        except json.JSONDecodeError:
            self.logger.raise_with_screenshot(f"{self.bot_name} 配兵文件解析失败: {file_path}", ValueError)

    def _load_army_setting_from_dir(self, dir_path):
        army_num_path = os.path.join(dir_path, "army_num.json")
        settings = self._load_json_file(army_num_path)

        if not isinstance(settings, dict):
            self.logger.raise_with_screenshot(f"{self.bot_name} 配兵文件格式错误: {army_num_path}", ValueError)
        settings = cast(dict, settings)

        army_level_path = os.path.join(dir_path, "army_level.json")
        if os.path.exists(army_level_path):
            level_cfg = self._load_json_file(army_level_path)
            if isinstance(level_cfg, dict):
                for faction, faction_cfg in settings.items():
                    if isinstance(faction_cfg, dict):
                        merged = dict(level_cfg)
                        merged.update(faction_cfg)
                        settings[faction] = merged

        return settings

    def get_faction_setting(self, army_setting=None):
        settings = army_setting if army_setting is not None else self.army_setting
        if settings is None:
            self.logger.raise_with_screenshot(f"{self.bot_name} 尚未加载 army_setting")
        settings = cast(dict, settings)

        faction_setting = settings.get(self.faction)
        if faction_setting is None and self.faction == "witch":
            faction_setting = settings.get("witch_1")
        if faction_setting is None:
            self.logger.raise_with_screenshot(f"{self.bot_name} 中未找到流派: {self.faction}")
        return cast(dict, faction_setting)

    @staticmethod
    def normalize_army_key(key):
        return key[:-7] if key.endswith("_number") else key

    @staticmethod
    def expand_army_sequence(army_map):
        sequence = []
        for troop_name, count in army_map.items():
            troop_name = ArmyManager.normalize_army_key(troop_name)
            for _ in range(int(count)):
                sequence.append(troop_name)
        return sequence

    @abstractmethod
    def train_asset_by_troop(self, troop):
        pass

    @abstractmethod
    def train(self, op):
        pass


class HomeArmyManager(ArmyManager):
    def train_asset_by_troop(self, troop):
        if troop == "dragon":
            return Assets.DRAGON_TRAIN
        return None

    def train(self, op):
        self.logger.info("主世界训练流程", level=1)
        train_btn = op.exists(Assets.BTN_TRAIN)
        if not train_btn:
            self.logger.raise_with_screenshot("未找到练兵按钮")
        op.random_touch(train_btn)
        op.sleep(0.5)

        delete_btn = op.exists(Assets.BTN_HOME_DELETE)
        if not delete_btn:
            self.logger.raise_with_screenshot("未找到删除按钮")
        op.random_touch(delete_btn)
        op.sleep(0.5)

        faction_setting = self.get_faction_setting()
        train_list = self.expand_army_sequence({"dragon": faction_setting.get("dragon_number", 10)})

        dragon_icon = op.exists(Assets.DRAGON_TRAIN)
        if not dragon_icon:
            self.logger.error("未找到龙训练按钮")
            return

        last_troop = None
        for troop in train_list:
            train_asset = self.train_asset_by_troop(troop)
            if train_asset is None:
                continue
            if troop != last_troop:
                icon = op.exists(train_asset)
                if not icon:
                    self.logger.raise_with_screenshot(f"未找到训练按钮: {troop}")
                op.random_touch(icon, offset=1, min_sleep_time=0.05, max_sleep_time=0.12)
            else:
                op.random_touch(dragon_icon, offset=1, min_sleep_time=0.05, max_sleep_time=0.12)
            last_troop = troop

        close_pos = op.exists(Assets.CLOSE)
        op.sleep(0.5)
        if close_pos:
            op.random_touch(close_pos, min_sleep_time=0.1, max_sleep_time=0.2)
            op.sleep(0.5)


class NightArmyManager(ArmyManager):
    def train_asset_by_troop(self, troop):
        if troop == "giant":
            return Assets.GIANT_TRAIN
        if troop == "witch":
            return Assets.WITCH_TRAIN
        if troop == "archer":
            return Assets.ARCHER_TRAIN
        return None

    def train(self, op):
        train_btn = op.exists(Assets.BTN_TRAIN)
        if not train_btn:
            self.logger.raise_with_screenshot("未找到练兵按钮")
        op.random_touch(train_btn)
        op.sleep(0.5)

        delete_btn = op.exists(Assets.BTN_DELETE)
        if not delete_btn:
            self.logger.raise_with_screenshot("未找到删除按钮")
        op.random_touch(delete_btn)
        op.sleep(0.5)

        faction_setting = self.get_faction_setting()
        first_sequence = self.expand_army_sequence(faction_setting.get("first_army", {}))
        second_sequence = self.expand_army_sequence(faction_setting.get("second_army", {}))
        train_list = first_sequence + second_sequence

        last_troop = None
        for troop in train_list:
            train_asset = self.train_asset_by_troop(troop)
            if train_asset is None:
                self.logger.debug(f"跳过未知训练兵种: {troop}")
                continue
            if troop != last_troop:
                icon = op.exists(train_asset)
                if not icon:
                    self.logger.raise_with_screenshot(f"未找到训练按钮: {troop}")
                op.random_touch(icon, offset=1, min_sleep_time=0.2, max_sleep_time=0.4)
            else:
                icon = op.exists(train_asset)
                if icon:
                    op.random_touch(icon, offset=1, min_sleep_time=0.2, max_sleep_time=0.4)
            last_troop = troop

        mecha = op.exists(Assets.MECHA_TRAIN)
        if mecha:
            op.random_touch(mecha, min_sleep_time=0.2, max_sleep_time=0.4)

        close_btn = op.exists(Assets.CLOSE)
        op.sleep(0.5)
        if close_btn:
            op.random_touch(close_btn)
            op.sleep(0.5)
