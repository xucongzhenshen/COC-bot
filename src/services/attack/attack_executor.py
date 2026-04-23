import random
from abc import ABC, abstractmethod

from src.utils import Assets


SPAWN_POINTS = [[169, 660], [2396, 800], [2066, 456], [2258, 577], [2281, 759]]
ROI_NAME = [30, 120, 80, 450]

def _sanitize_digits(text):
    return (
        text.replace("O", "0")
        .replace("o", "0")
        .replace("l", "1")
        .replace("I", "1")
        .replace("S", "5")
        .replace(",", "")
        .replace(" ", "")
    )


class AttackExecutor(ABC):
    def __init__(self, logger, op, troop_trainer, strategy_interpreter):
        self.logger = logger
        self.op = op
        self.troop_trainer = troop_trainer
        self.strategy_interpreter = strategy_interpreter
        self.attack_icons = []

    @abstractmethod
    def _search_target(self):
        pass

    def execute(self):
        self._start_attack()
        self._search_target()
        self.strategy_interpreter.run()
        self._wait_attack_finish()
        self._on_attack_finish()
        self._return_to_main()

    def _start_attack(self):
        attack_buttons = [self.op.exists(icon) for icon in self.attack_icons if self.op.exists(icon)]
        if not attack_buttons:
            self.logger.info("当前不可进攻", level=1)
            self.logger.raise_with_screenshot("未找到进攻按钮")
        self.op.random_touch(attack_buttons[0])
        return True

    def _on_attack_finish(self):
        pass

    def _wait_attack_finish(self):
        timeout = 150
        while timeout > 0 and "离战斗结束还有" in self.op.get_text():
            self.logger.debug("正在战斗中...")
            self.op.sleep(2)
            timeout -= 2

    def _return_to_main(self):
        timeout = 30
        back = self.op.exists(Assets.BTN_BACK)
        if not back:
            self.logger.raise_with_screenshot("未找到返回按钮")
        self.op.random_touch(back)
        while timeout > 0 and not self.op.exists(Assets.BTN_TRAIN):
            self.logger.debug("正在返回主界面...")
            self.op.sleep(2)
            timeout -= 2
            icon_btn_confirm = self.op.exists(Assets.BTN_CONFIRM)
            if icon_btn_confirm:
                self.op.random_touch(icon_btn_confirm)
                self.op.sleep(2)
                timeout -= 2
        if self.op.exists(Assets.BTN_TRAIN):
            self.logger.info("成功返回主界面", level=1)
        else:
            self.logger.raise_with_screenshot("未能成功返回主界面")
    
class HomeAttackExecutor(AttackExecutor):
    def __init__(self, logger, op, troop_trainer, air_defense_detector, strategy_interpreter, faction, filter_config=None):
        super().__init__(logger=logger, op=op, troop_trainer=troop_trainer, strategy_interpreter=strategy_interpreter)
        self.air_defense_detector = air_defense_detector
        self.filter_config = filter_config
        self.faction = faction
        self.attack_icons = [Assets.ATTACK_HOME_WITH_3_STAR, Assets.ATTACK_HOME_WITH_STAR, Assets.ATTACK_HOME]

    def _search_target_once(self, first_search):
        ROI_COUNTDOWN = [30, 1170, 80, 1360]

        prior_targets = None
        if not first_search:
            prior_targets = self.op.get_text(ROI_NAME)

        btn = Assets.BTN_HOME_SEARCH if first_search else Assets.BTN_NEXT
        search_btn = self.op.exists(btn)
        if not search_btn:
            self.logger.raise_with_screenshot("未找到搜索/下一个按钮")
        self.op.random_touch(search_btn, min_sleep_time=0.2, max_sleep_time=0.5)
        if first_search:
            attack_confirm = self.op.exists(Assets.BTN_ATTACK_CONFIRM)
            if not attack_confirm:
                self.logger.raise_with_screenshot("未找到开战确认按钮")
            self.op.random_touch(attack_confirm, min_sleep_time=0.2, max_sleep_time=0.5)

        waited = 0
        while waited < 50:
            self.logger.debug("正在搜索对手...")
            message = self.op.get_text(ROI_COUNTDOWN)
            if "开战" in message or "倒计时" in message:
                current_target = self.op.get_text(ROI_NAME)
                if (not first_search) and current_target == prior_targets:
                    self.logger.warning("不是首次搜索但目标未变化，可能网络异常，尝试点击继续等待")
                    self.op.random_touch(search_btn)
                    continue
                return
            self.op.sleep(2)
            waited += 2
        self.logger.raise_with_screenshot("搜索对手超时")

    def _search_target(self):
        self._search_target_once(first_search=True)
        while True:
            if not self._filter_resource():
                self.logger.info("资源不满足要求，继续搜索下一个目标", level=1)
                self._search_target_once(first_search=False)
                continue
            if self.faction == "dragon" and len(self.air_defense_detector.detect()) < 3:
                self.logger.info("可能有未检测到的防空火箭，继续搜索下一个目标", level=1)
                self._search_target_once(first_search=False)
                continue
            self.logger.info("找到合适的目标，开始部署", level=1)
            return

    def _filter_resource(self):
        cfg = self.filter_config or {"gold": 0, "water": 0, "oil": 0}
        roi_gold = [200, 120, 250, 350]
        roi_water = [275, 120, 325, 350]
        roi_oil = [350, 120, 400, 350]

        gold = _sanitize_digits(self.op.get_text(roi_gold))
        water = _sanitize_digits(self.op.get_text(roi_water))
        oil = _sanitize_digits(self.op.get_text(roi_oil))

        if gold and int(gold) < int(cfg["gold"]):
            return False
        if water and int(water) < int(cfg["water"]):
            return False
        if oil and int(oil) < int(cfg["oil"]):
            return False
        return True

class NightAttackExecutor(AttackExecutor):
    def __init__(self, logger, op, troop_trainer, strategy_interpreter, enable_second_stage=False):
        super().__init__(logger=logger, op=op, troop_trainer=troop_trainer, strategy_interpreter=strategy_interpreter)
        self.attack_icons = [Assets.NIGHT_ATTACK_WITH_STAR, Assets.NIGHT_ATTACK]
        self.enable_second_stage = enable_second_stage

    def execute(self):
        super().execute()

    def _on_attack_finish(self):
        end_btn = self.op.exists(Assets.BTN_END)
        if end_btn:
            if self.enable_second_stage:
                self.logger.info("进攻胜利, 进行下一阶段进攻", level=1)
                self.strategy_interpreter.run_second_attack()
                self._wait_attack_finish()
            else:
                self.op.random_touch(end_btn)
                confirm_btn = self.op.exists(Assets.BTN_CONFIRM)
                if not confirm_btn:
                    self.logger.raise_with_screenshot("未找到结算确认按钮")
                self.op.random_touch(confirm_btn)

    def _search_target(self):
        search = self.op.exists(Assets.BTN_SEARCH)
        if not search:
            self.logger.raise_with_screenshot("未找到搜索按钮")
        self.op.random_touch(search)

        waited = 0
        while waited < 50 and "开战倒计时" not in self.op.get_text():
            self.logger.debug("正在搜索对手...")
            self.op.sleep(3)
            waited += 3
        if waited >= 50:
            self.logger.raise_with_screenshot("搜索对手超时")
