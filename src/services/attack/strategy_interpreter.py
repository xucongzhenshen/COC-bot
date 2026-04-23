import os
import json
import random
from typing import Any, Dict, cast
from src.utils import Assets
from abc import ABC, abstractmethod
from src.services.attack.utils import ProbeAction, DeployAction, ZapAction, HeroAction, SkillAction

class StrategyInterpreter(ABC):
    def __init__(self, op, logger, strategy_path, attack_optimizer=None, air_defense_detector=None):
        self.op = op
        self.logger = logger
        self.attack_optimizer = attack_optimizer
        self.air_defense_detector = air_defense_detector

        if not strategy_path:
            self.logger.raise_with_screenshot("未配置 strategy_path")

        self.strategy: Dict[str, Any] = self.load_strategy(strategy_path)
        self.valid_point = [169, 660] # 默认出生点，后续可根据策略配置调整
    
    def _load_json_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.raise_with_screenshot(f"加载 JSON 文件失败: {file_path}, 错误: {str(e)}", e.__class__)
            raise

    def load_strategy(self, strategy_path):
        if not os.path.exists(strategy_path):
            self.logger.raise_with_screenshot(f"策略文件不存在: {strategy_path}", FileNotFoundError)
            raise FileNotFoundError(f"策略文件不存在: {strategy_path}")
        strategy = self._load_json_file(strategy_path)
        if not isinstance(strategy, dict):
            self.logger.raise_with_screenshot(f"策略文件格式错误: {strategy_path}", ValueError)
            raise ValueError(f"策略文件格式错误: {strategy_path}")
        return cast(Dict[str, Any], strategy)

    def _parse_actions(self, seq_config):
        actions = []
        for item in seq_config:
            a_type = item.get('type')
            if a_type == "probe":
                actions.append(ProbeAction(item['troop']))
            elif a_type == "deploy":
                actions.append(DeployAction(item['troop'], item['count']))
            elif a_type == "zap":
                actions.append(ZapAction(item['count'], item['level']))
            elif a_type == "hero":
                actions.append(HeroAction(item['troop']))
            elif a_type == "skill":
                actions.append(SkillAction(item['troop']))
            else:
                self.logger.warning(f"未知动作类型: {a_type}")
        return actions

    @staticmethod
    def get_spawn_points():
        points = [[169, 660], [2396, 800], [2066, 456], [2258, 577], [2281, 759]]
        random.shuffle(points)
        return points

    def get_asset(self, name):
        # 统一映射表，解决代码中大量的 if/else
        mapping = {
            "dragon": Assets.DRAGON_DEPLOY,
            "balloon": Assets.BALLOON_DEPLOY,
            "queen": Assets.QUEEN_DEPLOY,
            "lightning": Assets.LIGHTNING_SPELL_DEPLOY,
            "giant": Assets.GIANT_DEPLOY,
            "witch": Assets.WITCH_DEPLOY,
            "archer": Assets.ARCHER_DEPLOY,
            "the_revenant_prince": Assets.THE_REVENANT_PRINCE_DEPLOY,
            "mecha": Assets.MECHA_DEPLOY,
            "fighter_jet": Assets.FIGHTER_JET_DEPLOY,
        }
        return mapping.get(name)

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def infer_training_config(self):
        """从动作序列中推断需要训练的兵力和法术"""
        pass
    
class HomeStrategyInterpreter(StrategyInterpreter):
    def __init__(self, op, logger, strategy_path, attack_optimizer=None, air_defense_detector=None):
        super().__init__(
            op,
            logger,
            strategy_path,
            attack_optimizer=attack_optimizer,
            air_defense_detector=air_defense_detector,
        )
    
    def infer_training_config(self):
        """从动作序列中推断需要训练的兵力"""
        troops = {}
        spells = {}
        heroes = ["queen", "the_revenant_prince"] # 主世界英雄加入单独训练列表
        heroes_in_strategy = set()

        for action in self._parse_actions(self.strategy.get('sequence', [])):
            if isinstance(action, DeployAction):
                troops[action.troop] = troops.get(action.troop, 0) + action.count
            elif isinstance(action, ProbeAction):
                troops[action.troop] = troops.get(action.troop, 0) + 1
            elif isinstance(action, ZapAction):
                spells["lightning"] = action.count
            elif isinstance(action, HeroAction):
                heroes_in_strategy.add(action.hero_name)
        
        return {"troops": troops, "spells": spells, "heroes": list(heroes_in_strategy)}
    
    def run(self):
        actions = self._parse_actions(self.strategy.get('sequence', []))
        for action in actions:
            action.execute(self)
    
class NightStrategyInterpreter(StrategyInterpreter):
    def __init__(self, op, logger, strategy_path, attack_optimizer=None, air_defense_detector=None):
        super().__init__(
            op,
            logger,
            strategy_path,
            attack_optimizer=attack_optimizer,
            air_defense_detector=air_defense_detector,
        )
        self.night_heros = ["mecha", "fight_jet"] # 夜世界英雄加入单独训练列表

    def _merge_two_sequences(self):
        """夜世界有两轮进攻，第一个序列是第一轮的动作，第一轮进攻后的剩余兵力可以在第二轮继续使用，这里直接将第一轮中与第二轮重复的部分合并，保证第二轮部署时第一轮剩余兵力也能被部署"""
        first_troops = self.infer_training_config().get("first_troops", {})
        second_seq = self.strategy.get('second_sequence', [])
        merged_seq = []
        for item in second_seq:
            if item.get('type') == 'deploy':
                troop = item.get('troop')
                count = item.get('count', 0)
                # 查找第一轮中是否有相同兵种的部署
                merged_count = count + first_troops.pop(troop, 0)  # 第二轮需要部署的数量 + 第一轮剩余的数量
                merged_seq.append({'type': 'deploy', 'troop': troop, 'count': merged_count})
            else:
                if item.get('type') in ['probe', 'hero']:
                    merged_seq.append(item)
        if first_troops:
            for troop, count in first_troops.items():
                if troop in self.night_heros:
                    merged_seq.append({'type': 'hero', 'troop': troop})
                else:
                    merged_seq.append({'type': 'deploy', 'troop': troop, 'count': count})
        return merged_seq

    def infer_training_config(self):
        """夜世界目前没有英雄，直接推断兵力和法术"""
        first_troops = {}
        second_troops = {}

        # 解析序列一, 夜世界没有法术
        for action in self._parse_actions(self.strategy.get('first_sequence', [])):
            if isinstance(action, DeployAction):
                first_troops[action.troop] = first_troops.get(action.troop, 0) + action.count
            elif isinstance(action, ProbeAction):
                first_troops[action.troop] = first_troops.get(action.troop, 0) + 1
            elif isinstance(action, HeroAction):
                first_troops[action.hero_name] = first_troops.get(action.hero_name, 0) + 1

        for action in self._parse_actions(self.strategy.get('second_sequence', [])):
            if isinstance(action, DeployAction):
                second_troops[action.troop] = second_troops.get(action.troop, 0) + action.count
            elif isinstance(action, ProbeAction):
                second_troops[action.troop] = second_troops.get(action.troop, 0) + 1
            elif isinstance(action, HeroAction):
                second_troops[action.hero_name] = second_troops.get(action.hero_name, 0) + 1

        return {"first_troops": first_troops, "second_troops": second_troops}
    
    def run(self):
        first_actions = self._parse_actions(self.strategy.get('first_sequence', []))
        self.logger.info("执行第一轮部署", level=1)
        for action in first_actions:
            action.execute(self)
        
    def run_second_attack(self):
        second_actions = self._parse_actions(self._merge_two_sequences())
        self.logger.info("执行第二轮部署", level=1)
        for action in second_actions:
            action.execute(self)

    
    