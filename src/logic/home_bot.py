from src.utils import Assets

from .base_bot import BaseBot


class HomeBot(BaseBot):
    def __init__(self, config, services):
        super().__init__("HomeBot", config, services)
        self.op = services.basic_operator
        self.world_detector = services.world_detector
        self.move = services.calibrated_movement_controller
        self.army_manager = services.home_army_manager
        self.battle_executor = services.home_battle_executor

    def can_handle(self, world):
        return world == "HOME"

    def righting_pos(self):
        self.op.set_max_zoom_out()
        self.logger.info("正在调整主世界视角", level=1)
        self.op.swipe((800, 600), (400, 200), duration=0.5)
        self.op.sleep(0.5)
        self.move.move_with_tracking((200, 250), max_step_px=240)
        self.op.sleep(0.5)

    def collect_resources(self):
        for target in (Assets.OIL, Assets.WATER, Assets.GOLD):
            icons = self.op.find_all(target) or []
            for icon in icons:
                self.op.random_touch(icon["result"], offset=5, min_sleep_time=0.2, max_sleep_time=0.4)

    def train_logic(self):
        self.army_manager.train(self.op)

    def battle_logic(self):
        self.battle_executor.execute()

    def switch_world(self):
        self.op.set_max_zoom_out()
        self.op.sleep(0.5)
        self.move.move_with_tracking((150, -350), max_step_px=260)
        self.op.sleep(0.5)
        boat = self.op.exists(Assets.SHIP_TO_NIGHT)
        if not boat:
            self.logger.raise_with_screenshot("未找到前往夜世界的小船")
        self.op.random_touch(boat, min_sleep_time=5.5, max_sleep_time=6.5)

    def run_bot(self):
        self.logger.info("--- 正在处理主世界任务 ---", level=0)
        super().run_bot()
        self.logger.info("主世界流程完成", level=0)
