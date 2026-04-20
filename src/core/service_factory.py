from dataclasses import dataclass

from src.services.core.basic_operator import BasicOperator
from src.services.core.device_manager import DeviceManager
from src.services.core.logger import LoggerService
from src.services.decision.attack_optimizer import AttackOptimizer
from src.services.execution.calibrated_movement_controller import CalibratedMovementController
from src.services.execution.army_manager import HomeArmyManager, NightArmyManager
from src.services.execution.battle_executor import HomeBattleExecutor, NightBattleExecutor
from src.services.execution.game_initializer import GameInitializer
from src.services.exception.exception_handler import ExceptionHandler
from src.services.perception.air_defense_detector import AirDefenseDetector
from src.services.perception.meadow_detector import MeadowDetector
from src.services.perception.world_detector import WorldDetector


@dataclass
class ServiceContainer:
    logger: LoggerService
    device_manager: DeviceManager
    basic_operator: BasicOperator
    world_detector: WorldDetector
    meadow_detector: MeadowDetector
    air_defense_detector: AirDefenseDetector
    attack_optimizer: AttackOptimizer
    home_army_manager: HomeArmyManager
    night_army_manager: NightArmyManager
    home_battle_executor: HomeBattleExecutor
    night_battle_executor: NightBattleExecutor
    game_initializer: GameInitializer
    exception_handler: ExceptionHandler
    calibrated_movement_controller: CalibratedMovementController


class ServiceFactory:
    """集中管理服务构建，隔离业务层对构造细节的感知。"""

    def __init__(self, config):
        self.config = config

    def build(self):
        logger = LoggerService(self.config)
        logger.initialize()

        basic_operator = BasicOperator(logger=logger)
        device_manager = DeviceManager(self.config, logger)
        world_detector = WorldDetector(logger=logger, basic_operator=basic_operator)
        meadow_detector = MeadowDetector({"sample_path": getattr(self.config, "sample_path", None)})
        air_defense_detector = AirDefenseDetector(self.config, basic_operator=basic_operator, logger=logger)
        attack_optimizer = AttackOptimizer(self.config, logger=logger)
        home_army_manager = HomeArmyManager(
            logger=logger,
            faction=self.config.home_bot.faction,
            army_setting_path=self.config.home_bot.army_setting_path,
            bot_name="HomeBot",
        )
        night_army_manager = NightArmyManager(
            logger=logger,
            faction=self.config.night_bot.faction,
            army_setting_path=self.config.night_bot.army_setting_path,
            bot_name="NightBot",
        )
        home_battle_executor = HomeBattleExecutor(
            logger=logger,
            op=basic_operator,
            army_manager=home_army_manager,
            air_defense_detector=air_defense_detector,
            attack_optimizer=attack_optimizer,
            filter_config=self.config.home_bot.filter_config,
        )
        night_battle_executor = NightBattleExecutor(
            logger=logger,
            op=basic_operator,
            army_manager=night_army_manager,
        )
        calibrated_movement_controller = CalibratedMovementController(logger=logger)
        game_initializer = GameInitializer(self.config, logger, device_manager)
        exception_handler = ExceptionHandler(
            config=self.config,
            op=basic_operator,
            logger=logger,
            game_initializer=game_initializer,
        )

        return ServiceContainer(
            logger=logger,
            device_manager=device_manager,
            basic_operator=basic_operator,
            world_detector=world_detector,
            meadow_detector=meadow_detector,
            air_defense_detector=air_defense_detector,
            attack_optimizer=attack_optimizer,
            home_army_manager=home_army_manager,
            night_army_manager=night_army_manager,
            home_battle_executor=home_battle_executor,
            night_battle_executor=night_battle_executor,
            game_initializer=game_initializer,
            exception_handler=exception_handler,
            calibrated_movement_controller=calibrated_movement_controller,
        )
