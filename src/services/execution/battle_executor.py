import random
from abc import ABC, abstractmethod

from src.utils import Assets


SPAWN_POINTS = [[169, 660], [2396, 800], [2066, 456], [2258, 577], [2281, 759]]


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


class BattleExecutor(ABC):
    def __init__(self, logger, op, army_manager):
        self.logger = logger
        self.op = op
        self.army_manager = army_manager

    @abstractmethod
    def deploy_asset_by_troop(self, troop):
        pass

    @abstractmethod
    def execute(self):
        pass

    @staticmethod
    def _get_spawn_points():
        points = SPAWN_POINTS.copy()
        random.shuffle(points)
        return points

    def _on_battle_finish(self):
        pass

    def _wait_battle_finish(self):
        timeout = 150
        while timeout > 0 and "离战斗结束还有" in self.op.get_text():
            self.logger.debug("正在战斗中...")
            self.op.sleep(5)
            timeout -= 5
        self._on_battle_finish()

    def deploy_sequence_to_point(self, seq, point, hero_names=None, initial_troop=None):
        hero_names = set(hero_names or [])
        last_troop = initial_troop
        for troop in seq:
            deploy_asset = self.deploy_asset_by_troop(troop)
            if deploy_asset is None:
                self.logger.debug(f"跳过未知部署兵种: {troop}")
                continue

            if troop != last_troop:
                icon = self.op.exists(deploy_asset)
                if not icon:
                    if troop in hero_names:
                        self.logger.debug(f"未找到英雄部署按钮: {troop}, 可能在升级中，跳过部署")
                        last_troop = troop
                        continue
                    self.logger.raise_with_screenshot(f"未找到部署按钮: {troop}")
                self.op.random_touch(icon, min_sleep_time=0.0, max_sleep_time=0.02)

            self.op.random_touch(point, min_sleep_time=0.0, max_sleep_time=0.02)
            last_troop = troop

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
            if self.op.exists(Assets.BTN_CONFIRM):
                self.op.random_touch(self.op.exists(Assets.BTN_CONFIRM))
                self.op.sleep(2)
                timeout -= 2
        if self.op.exists(Assets.BTN_TRAIN):
            self.logger.info("成功返回主界面", level=1)
        else:
            self.logger.raise_with_screenshot("未能成功返回主界面")
    
class HomeBattleExecutor(BattleExecutor):
    def __init__(self, logger, op, army_manager, air_defense_detector, attack_optimizer, filter_config=None):
        super().__init__(logger=logger, op=op, army_manager=army_manager)
        self.air_defense_detector = air_defense_detector
        self.attack_optimizer = attack_optimizer
        self.filter_config = filter_config
        self.hero_names = ["queen", "the_revenant_prince"]

    def deploy_asset_by_troop(self, troop):
        if troop == "dragon":
            return Assets.DRAGON_DEPLOY
        if troop == "queen":
            return Assets.QUEEN_DEPLOY
        if troop == "the_revenant_prince":
            return Assets.THE_REVENANT_PRINCE_DEPLOY
        return None

    def _search_target(self, first_search):
        btn = Assets.BTN_HOME_SEARCH if first_search else Assets.BTN_NEXT
        search_btn = self.op.exists(btn)
        if not search_btn:
            self.logger.raise_with_screenshot("未找到搜索/下一个按钮")
        self.op.random_touch(search_btn, min_sleep_time=0.2, max_sleep_time=0.5)
        if first_search:
            fight_confirm = self.op.exists(Assets.BTN_FIGHT_CONFIRM)
            if not fight_confirm:
                self.logger.raise_with_screenshot("未找到开战确认按钮")
            self.op.random_touch(fight_confirm, min_sleep_time=0.2, max_sleep_time=0.5)

        waited = 0
        while waited < 50:
            self.logger.debug("正在搜索对手...")
            if "开战倒计时" in self.op.get_text():
                return
            self.op.sleep(2)
            waited += 2
        self.logger.raise_with_screenshot("搜索对手超时")

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

    def _deploy_dragons(self):
        faction_setting = self.army_manager.get_faction_setting()
        dragon_number = int(faction_setting.get("dragon_number", 10))
        lightning_number = int(faction_setting.get("lightning_number", 9))
        lightning_level = int(faction_setting.get("lightning_level", 10))

        valid_deploy_point = [2396, 800]
        dragon_icon = self.op.exists(Assets.DRAGON_DEPLOY)
        if not dragon_icon:
            self.logger.raise_with_screenshot("未找到龙部署按钮")
        self.op.random_touch(dragon_icon, min_sleep_time=0.00, max_sleep_time=0.02)

        for point in self._get_spawn_points():
            self.op.random_touch(point, min_sleep_time=0.00, max_sleep_time=0.02)
            if "离战斗结束还有" in self.op.get_text():
                valid_deploy_point = point
                break

        spell_pos = self.op.exists(Assets.LIGHTNING_SPELL_DEPLOY)
        if spell_pos:
            self.op.random_touch(spell_pos, min_sleep_time=0.00, max_sleep_time=0.02)
            rockets = self.air_defense_detector.detect()
            if rockets:
                damage = self.attack_optimizer.load_lightning_damage(lightning_level)
                plan = self.attack_optimizer.pick_lightning_targets(
                    anti_aircraft_list=rockets,
                    lightning_number=lightning_number,
                    lightning_damage=damage,
                    deploy_point=valid_deploy_point,
                )
                for target in plan["plan"]:
                    for _ in range(target["strikes_needed"]):
                        self.op.random_touch(target["position"], offset=1, min_sleep_time=0.00, max_sleep_time=0.00)

        dragon_seq = self.army_manager.expand_army_sequence({"dragon": dragon_number})
        self.deploy_sequence_to_point(dragon_seq, valid_deploy_point)

        queen_seq = self.army_manager.expand_army_sequence({"queen": 1})
        prince_seq = self.army_manager.expand_army_sequence({"the_revenant_prince": 1})
        if self.op.exists(Assets.QUEEN_DEPLOY):
            self.deploy_sequence_to_point(queen_seq, valid_deploy_point, hero_names=self.hero_names)
        if self.op.exists(Assets.THE_REVENANT_PRINCE_DEPLOY):
            self.deploy_sequence_to_point(prince_seq, valid_deploy_point, hero_names=self.hero_names)

    def execute(self):
        self.logger.info("正在执行主世界战斗", level=1)
        fight_icon = self.op.exists(Assets.FIGHT_HOME_WITH_3_STAR) or self.op.exists(Assets.FIGHT_HOME_WITH_STAR) or self.op.exists(Assets.FIGHT_HOME)
        if not fight_icon:
            self.logger.raise_with_screenshot("未找到主世界战斗入口")
        self.op.random_touch(fight_icon)

        self._search_target(first_search=True)
        while True:
            self.op.sleep(3)
            if not self._filter_resource():
                self.logger.info("资源不满足要求，继续搜索下一个目标", level=1)
                self._search_target(first_search=False)
                continue
            if self.army_manager.faction == "dragon" and len(self.air_defense_detector.detect()) < 3:
                self.logger.info("可能有未检测到的防空火箭，继续搜索下一个目标", level=1)
                self._search_target(first_search=False)
                continue
            self.logger.info("找到合适的目标，开始部署", level=1)
            break

        if self.army_manager.faction == "dragon":
            self._deploy_dragons()

        self._wait_battle_finish()
        self._return_to_main()


class NightBattleExecutor(BattleExecutor):
    def __init__(self, logger, op, army_manager):
        super().__init__(logger=logger, op=op, army_manager=army_manager)
        self.hero_names = ["mecha", "fighter_jet"]

    def deploy_asset_by_troop(self, troop):
        if troop == "giant":
            return Assets.GIANT_DEPLOY
        if troop == "witch":
            return Assets.WITCH_DEPLOY
        if troop == "archer":
            return Assets.ARCHER_DEPLOY
        if troop == "mecha":
            return Assets.MECHA_DEPLOY
        if troop == "fighter_jet":
            return Assets.FIGHTER_JET_DEPLOY
        return None

    def _on_battle_finish(self):
        end_btn = self.op.exists(Assets.BTN_END)
        if end_btn:
            self.op.random_touch(end_btn)
            confirm = self.op.exists(Assets.BTN_CONFIRM)
            if confirm:
                self.op.random_touch(confirm)

    def _deploy_night_army_once(self):
        faction_setting = self.army_manager.get_faction_setting()
        first_army = faction_setting.get("first_army", {})
        first_seq = self.army_manager.expand_army_sequence(first_army)
        if not first_seq:
            return

        last_giant_index = -1
        for index, troop in enumerate(first_seq):
            if troop == "giant":
                last_giant_index = index

        if last_giant_index != -1 and len(first_seq) > last_giant_index + 1:
            for hero in self.hero_names:
                if hero not in first_seq:
                    first_seq.insert(last_giant_index + 1, hero)

        probe_asset = self.deploy_asset_by_troop(first_seq[0])
        if probe_asset is None:
            self.logger.raise_with_screenshot(f"未知兵种，无法探路部署: {first_seq[0]}")

        probe_icon = self.op.exists(probe_asset)
        if not probe_icon:
            self.logger.raise_with_screenshot(f"未找到部署按钮: {first_seq[0]}")
        self.op.random_touch(probe_icon, min_sleep_time=0.02, max_sleep_time=0.04)

        valid = [2396, 800]
        for point in self._get_spawn_points():
            self.op.random_touch(point, min_sleep_time=0.02, max_sleep_time=0.04)
            if self.op.exists(Assets.BTN_GIVE_UP):
                valid = point
                break

        self.deploy_sequence_to_point(
            first_seq[1:],
            valid,
            hero_names=self.hero_names,
            initial_troop=first_seq[0],
        )

    def execute(self):
        fight = self.op.exists(Assets.NIGHT_FIGHT_WITH_STAR) or self.op.exists(Assets.NIGHT_FIGHT)
        if not fight:
            self.logger.info("夜世界当前不可战斗", level=1)
            return
        self.op.random_touch(fight)

        search = self.op.exists(Assets.BTN_SEARCH)
        if not search:
            self.logger.raise_with_screenshot("未找到搜索按钮")
        self.op.random_touch(search)

        waited = 0
        while waited < 50 and "开战倒计时" not in self.op.get_text():
            self.logger.debug("正在搜索对手...")
            self.op.sleep(3)
            waited += 3

        self._deploy_night_army_once()
        self._wait_battle_finish()
        self._return_to_main()
