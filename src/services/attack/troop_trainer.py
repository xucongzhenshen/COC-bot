from abc import ABC, abstractmethod

from src.utils import Assets


class TroopTrainer(ABC):
    def __init__(self, logger, bot_name):
        self.logger = logger
        self.bot_name = bot_name
        
    @abstractmethod
    def train(self, op, training_config):
        pass

    def mapping_troop_to_train_asset(self, troop):
        """根据兵种名称返回对应的训练素材"""
        mapping = {
            "giant": Assets.GIANT_TRAIN,
            "witch": Assets.WITCH_TRAIN,
            "archer": Assets.ARCHER_TRAIN,
            "mecha": Assets.MECHA_TRAIN,
            "dragon": Assets.DRAGON_TRAIN,
            "balloon": Assets.BALLOON_TRAIN,
        }
        return mapping.get(troop)


class HomeTroopTrainer(TroopTrainer):
    def train(self, op, training_config):
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

        troops = training_config.get("troops", {}) if training_config else {}
        for troop, count in troops.items():
            asset = self.mapping_troop_to_train_asset(troop)
            if not asset:
                self.logger.debug(f"未知的训练兵种: {troop}, 跳过训练")
                continue
            for _ in range(count):
                btn = op.exists(asset)
                if not btn:
                    self.logger.raise_with_screenshot(f"未找到训练按钮: {troop}")
                op.random_touch(btn, min_sleep_time=0.1, max_sleep_time=0.3)
                op.sleep(0.5)
        
        close_pos = op.exists(Assets.CLOSE)
        op.sleep(0.5)
        if close_pos:
            op.random_touch(close_pos, min_sleep_time=0.1, max_sleep_time=0.2)
            op.sleep(0.5)


class NightTroopTrainer(TroopTrainer):
    def train(self, op, training_config):
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

        training_json = training_config or {}
        first_troops = training_json.get("first_troops", {})
        second_troops = training_json.get("second_troops", {})
        # 先训练第一轮兵力
        for troop, count in first_troops.items():
            asset = self.mapping_troop_to_train_asset(troop)
            if not asset:
                self.logger.debug(f"未知的训练兵种: {troop}, 跳过训练")
                continue
            for _ in range(count):
                btn = op.exists(asset)
                if not btn:
                    self.logger.raise_with_screenshot(f"未找到训练按钮: {troop}")
                op.random_touch(btn, min_sleep_time=0.1, max_sleep_time=0.3)
                op.sleep(0.5)

        # 再训练第二轮兵力
        for troop, count in second_troops.items():
            asset = self.mapping_troop_to_train_asset(troop)
            if not asset:
                self.logger.debug(f"未知的训练兵种: {troop}, 跳过训练")
                continue
            for _ in range(count):
                btn = op.exists(asset)
                if not btn:
                    self.logger.raise_with_screenshot(f"未找到训练按钮: {troop}")
                op.random_touch(btn, min_sleep_time=0.1, max_sleep_time=0.3)
                op.sleep(0.5)

        close_btn = op.exists(Assets.CLOSE)
        op.sleep(0.5)
        if close_btn:
            op.random_touch(close_btn)
            op.sleep(0.5)
