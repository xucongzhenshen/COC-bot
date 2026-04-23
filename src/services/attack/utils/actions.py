import random
from abc import ABC, abstractmethod
from src.utils import Assets

SPAWN_POINTS = [[169, 660], [2396, 800], [2066, 456], [2258, 577], [2281, 759]]

class Action(ABC):
    @abstractmethod
    def execute(self, interpreter):
        pass

    @staticmethod
    def _get_spawn_points():
        points = SPAWN_POINTS.copy()
        random.shuffle(points)
        return points

# 1. 单兵探路
class ProbeAction(Action):
    def __init__(self, troop):
        self.troop = troop

    def execute(self, interpreter):
        interpreter.logger.info(f"探路：{self.troop}", level=1)
        asset = interpreter.get_asset(self.troop)
        if not asset:
            interpreter.logger.warning(f"探路跳过：未配置兵种素材 {self.troop}")
            return
        icon = interpreter.op.exists(asset)
        if not icon:
            interpreter.logger.error(f"探路失败：未找到 {self.troop} 图标")
            return
        
        interpreter.op.random_touch(icon, min_sleep_time=0.0, max_sleep_time=0.0)
        points = interpreter.get_spawn_points()
        
        for p in points:
            interpreter.op.random_touch(p, min_sleep_time=0.0, max_sleep_time=0.0)
            # 通过检测是否出现“战斗结束”文字或“撤退”按钮判断是否部署成功
            if "离战斗结束" in interpreter.op.get_text():
                interpreter.valid_point = p
                interpreter.logger.debug(f"探路成功，有效点位: {p}")
                return
        interpreter.logger.warning("未能找到有效部署点位，使用默认点位")
        interpreter.valid_point = points[0]

# 2. 序列部署
class DeployAction(Action):
    def __init__(self, troop, count):
        self.troop = troop
        self.count = count

    def execute(self, interpreter):
        interpreter.logger.info(f"部署：{self.troop} x {self.count}", level=1)
        asset = interpreter.get_asset(self.troop)
        if not asset:
            interpreter.logger.warning(f"部署跳过：未配置兵种素材 {self.troop}")
            return
        point = interpreter.valid_point
        if point is None:
            point = [1200, 800]
            interpreter.valid_point = point

        icon = interpreter.op.exists(asset)
        if icon:
            interpreter.op.random_touch(icon, min_sleep_time=0.0, max_sleep_time=0.0)

        for _ in range(self.count):
            interpreter.op.random_touch(point, min_sleep_time=0.00, max_sleep_time=0.0)

# 3. 雷电法术部署
class ZapAction(Action):
    def __init__(self, count, level):
        self.count = count
        self.level = level

    def execute(self, interpreter):
        interpreter.logger.info(f"使用雷电法术：等级 {self.level} x {self.count}", level=1)
        if not interpreter.attack_optimizer or not interpreter.air_defense_detector:
            interpreter.logger.debug("缺少防空识别或优化器，跳过雷电法术")
            return

        spell_icon = interpreter.op.exists(Assets.LIGHTNING_SPELL_DEPLOY)
        if not spell_icon: return

        interpreter.op.random_touch(spell_icon, min_sleep_time=0.0, max_sleep_time=0.0)
        rockets = interpreter.air_defense_detector.detect()
        if rockets:
            damage = interpreter.attack_optimizer.load_lightning_damage(self.level)
            plan = interpreter.attack_optimizer.pick_lightning_targets(
                anti_aircraft_list=rockets,
                lightning_number=self.count,
                lightning_damage=damage,
                deploy_point=interpreter.valid_point
            )
            for target in plan["plan"]:
                for _ in range(target["strikes_needed"]):
                    interpreter.op.random_touch(target["position"], offset=1, min_sleep_time=0.0, max_sleep_time=0.0)

# 4. 英雄部署
class HeroAction(Action):
    def __init__(self, hero_name):
        self.hero_name = hero_name
        self.night_heros = ["mecha", "fighter_jet"]

    def execute(self, interpreter):
        interpreter.logger.info(f"部署英雄：{self.hero_name}", level=1)
        asset = interpreter.get_asset(self.hero_name)
        icon = interpreter.op.exists(asset)
        if icon:
            interpreter.op.random_touch(icon, min_sleep_time=0.0, max_sleep_time=0.0)
            interpreter.op.random_touch(interpreter.valid_point, min_sleep_time=0.0, max_sleep_time=0.0)
        else:
            interpreter.logger.debug(f"英雄 {self.hero_name} 不可用，跳过")
            if self.hero_name in self.night_heros:
                interpreter.logger.info(f"尝试使用另一个英雄替换", level=1)
                alternative_hero = "fighter_jet" if self.hero_name == "mecha" else "mecha"
                alt_asset = interpreter.get_asset(alternative_hero)
                alt_icon = interpreter.op.exists(alt_asset)
                if alt_icon:
                    interpreter.op.random_touch(alt_icon, min_sleep_time=0.0, max_sleep_time=0.0)
                    interpreter.op.random_touch(interpreter.valid_point, min_sleep_time=0.0, max_sleep_time=0.0)

# 5. 技能释放
class SkillAction(Action):
    def __init__(self, unit_name):
        self.unit_name = unit_name
        self.night_heros = ["mecha", "fighter_jet"]

    def execute(self, interpreter):
        interpreter.logger.info(f"释放技能：{self.unit_name}", level=1)
        # 技能图标就是对应兵种的部署图标，简化配置
        unit_asset = interpreter.get_asset(self.unit_name)
        if not unit_asset:
            interpreter.logger.debug(f"未找到兵种单元: {self.unit_name}")
            return
        icon = interpreter.op.exists(unit_asset)
        if icon:
            interpreter.op.random_touch(icon, min_sleep_time=0.0, max_sleep_time=0.0)
        else:
            interpreter.logger.debug(f"技能 {self.unit_name} 不可用，跳过")
            if self.unit_name in self.night_heros:
                interpreter.logger.info(f"尝试使用另一个英雄技能替换", level=1)
                alternative_hero = "fighter_jet" if self.unit_name == "mecha" else "mecha"
                alt_asset = interpreter.get_asset(alternative_hero)
                alt_icon = interpreter.op.exists(alt_asset)
                if alt_icon:
                    interpreter.op.random_touch(alt_icon, min_sleep_time=0.0, max_sleep_time=0.0)