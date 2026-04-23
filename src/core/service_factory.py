from dataclasses import dataclass

from src.services.core.basic_operator import BasicOperator
from src.services.core.logger import LoggerService
from src.services.attack.troop_trainer import HomeTroopTrainer, NightTroopTrainer
from src.services.attack.strategy_interpreter import HomeStrategyInterpreter, NightStrategyInterpreter
from src.services.attack.attack_executor import HomeAttackExecutor, NightAttackExecutor
from src.services.attack.utils.attack_optimizer import AttackOptimizer
from src.services.attack.utils.air_defense_detector import AirDefenseDetector
from src.services.exception.exception_handler import ExceptionHandler
from src.services.initializer.device_manager import DeviceManager
from src.services.initializer.game_initializer import GameInitializer
from src.services.movement.calibrated_movement_controller import CalibratedMovementController
from src.services.positioning.meadow_detector import MeadowDetector
from src.services.positioning.world_detector import WorldDetector


@dataclass
class ServiceContainer:
    logger: LoggerService
    device_manager: DeviceManager
    basic_operator: BasicOperator
    world_detector: WorldDetector
    meadow_detector: MeadowDetector
    air_defense_detector: AirDefenseDetector
    attack_optimizer: AttackOptimizer
    home_troop_trainer: HomeTroopTrainer
    night_troop_trainer: NightTroopTrainer
    home_strategy_interpreter: HomeStrategyInterpreter
    night_strategy_interpreter: NightStrategyInterpreter
    home_attack_executor: HomeAttackExecutor
    night_attack_executor: NightAttackExecutor
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
        home_troop_trainer = HomeTroopTrainer(
            logger=logger,
            bot_name="HomeBot",
        )
        night_troop_trainer = NightTroopTrainer(
            logger=logger,
            bot_name="NightBot",
        )
        home_strategy_interpreter = HomeStrategyInterpreter(
            op=basic_operator,
            logger=logger,
            strategy_path=self.config.home_strategy_path,
            attack_optimizer=attack_optimizer,
            air_defense_detector=air_defense_detector,
        )
        night_strategy_interpreter = NightStrategyInterpreter(
            op=basic_operator,
            logger=logger,
            strategy_path=self.config.night_strategy_path,
        )
        home_attack_executor = HomeAttackExecutor(
            logger=logger,
            op=basic_operator,
            troop_trainer=home_troop_trainer,
            air_defense_detector=air_defense_detector,
            strategy_interpreter=home_strategy_interpreter,
            faction=self.config.home_bot.faction,
            filter_config=self.config.home_bot.filter_config,
        )
        night_attack_executor = NightAttackExecutor(
            logger=logger,
            op=basic_operator,
            troop_trainer=night_troop_trainer,
            strategy_interpreter=night_strategy_interpreter,
            enable_second_stage=self.config.enable_second_stage,
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
            home_troop_trainer=home_troop_trainer,
            night_troop_trainer=night_troop_trainer,
            home_strategy_interpreter=home_strategy_interpreter,
            night_strategy_interpreter=night_strategy_interpreter,
            home_attack_executor=home_attack_executor,
            night_attack_executor=night_attack_executor,
            game_initializer=game_initializer,
            exception_handler=exception_handler,
            calibrated_movement_controller=calibrated_movement_controller,
        )
