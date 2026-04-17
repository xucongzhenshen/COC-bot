from dataclasses import dataclass

from src.services.core.basic_operator import BasicOperator
from src.services.core.device_manager import DeviceManager
from src.services.core.logger import LoggerService
from src.services.decision.attack_optimizer import AttackOptimizer
from src.services.execution.calibrated_movement_controller import CalibratedMovementController
from src.services.execution.game_initializer import GameInitializer
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
    game_initializer: GameInitializer
    calibrated_movement_controller: CalibratedMovementController


class ServiceFactory:
    """集中管理服务构建，隔离业务层对构造细节的感知。"""

    def __init__(self, config):
        self.config = config

    def build(self):
        logger = LoggerService(self.config)
        logger.initialize()

        basic_operator = BasicOperator()
        device_manager = DeviceManager(self.config, logger)

        world_detector = WorldDetector()
        meadow_detector = MeadowDetector()
        air_defense_detector = AirDefenseDetector(self.config)
        attack_optimizer = AttackOptimizer()
        calibrated_movement_controller = CalibratedMovementController(meadow_detector=meadow_detector)
        game_initializer = GameInitializer(self.config, logger, device_manager)

        return ServiceContainer(
            logger=logger,
            device_manager=device_manager,
            basic_operator=basic_operator,
            world_detector=world_detector,
            meadow_detector=meadow_detector,
            air_defense_detector=air_defense_detector,
            attack_optimizer=attack_optimizer,
            game_initializer=game_initializer,
            calibrated_movement_controller=calibrated_movement_controller,
        )
