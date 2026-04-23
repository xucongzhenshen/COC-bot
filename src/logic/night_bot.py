import os

import numpy as np
from airtest.core.api import G

from src.utils import Assets

from .base_bot import BaseBot

class NightBot(BaseBot):
    def __init__(self, config, services):
        super().__init__("NightBot", config, services)
        self.op = services.basic_operator
        self.world_detector = services.world_detector
        self.move = services.calibrated_movement_controller
        self.meadow_detector = services.meadow_detector
        self.troop_trainer = services.night_troop_trainer
        self.strategy_interpreter = services.night_strategy_interpreter
        self.attack_executor = services.night_attack_executor

    def can_handle(self, world):
        return world == "NIGHT"

    def righting_pos(self):
        self.op.set_max_zoom_out()
        self.logger.info("正在调整夜世界视角", level=1)
        tolerance_px = 45
        screen = G.DEVICE.snapshot()
        if screen is None:
            self.logger.error("夜世界回正失败: 无法截图")
            return

        h, w = screen.shape[:2]
        screen_center = np.array([w / 2.0, h / 2.0], dtype=float)
        debug_dir = os.path.join(self.logger.log_path, "meadow_detect") if self.logger.log_path else None

        center, _, _ = self.meadow_detector.detect_center(
            screen_bgr=screen,
            debug_output=bool(debug_dir),
            debug_dir=debug_dir,
            debug_prefix="before_center",
        )
        if center is None:
            self.logger.error("夜世界回正失败: 草地中心识别失败")
            return

        delta = screen_center - np.array(center, dtype=float)
        if np.linalg.norm(delta) <= tolerance_px:
            self.logger.info(f"夜世界已居中, center={center}", level=1)
            return

        total_actual, _ = self.move.move_with_tracking(target_shift=delta, max_step_px=260)

        verify_screen = G.DEVICE.snapshot()
        if verify_screen is None:
            self.logger.error("夜世界回正失败: 回正后无法截图复检")
            return

        verify_center, _, _ = self.meadow_detector.detect_center(
            screen_bgr=verify_screen,
            debug_output=bool(debug_dir),
            debug_dir=debug_dir,
            debug_prefix="after_center",
        )
        if verify_center is None:
            self.logger.error("夜世界回正失败: 复检中心识别失败")
            return

        verify_delta = screen_center - np.array(verify_center, dtype=float)
        ok = np.linalg.norm(verify_delta) <= tolerance_px
        if ok:
            self.logger.info(
                f"夜世界回正成功: center={verify_center}, offset={verify_delta.astype(int).tolist()}, actual={total_actual.astype(int).tolist()}",
                level=1,
            )
            return
        self.logger.error(
            f"夜世界回正失败: center={verify_center}, offset={verify_delta.astype(int).tolist()}, actual={total_actual.astype(int).tolist()}"
        )

    def collect_resources(self):
        total_actual, _ = self.move.move_with_tracking((0, 200), max_step_px=260)  # 移动到资源区
        for target in (Assets.NIGHT_GOLD, Assets.EREMALD):
            pos = self.op.exists(target)
            if pos:
                self.op.random_touch(pos, min_sleep_time=0.2, max_sleep_time=0.4)

        cnt = 0
        while cnt < 3:
            water = self.op.exists(Assets.NIGHT_WATER)
            if not water:
                break
            self.op.random_touch(water, min_sleep_time=0.2, max_sleep_time=0.4)
            collect_btn = self.op.exists(Assets.BTN_COLLECT)
            if collect_btn:
                self.op.random_touch(collect_btn, min_sleep_time=0.2, max_sleep_time=0.4)
            close_btn = self.op.exists(Assets.CLOSE)
            while close_btn:
                self.op.random_touch(close_btn, min_sleep_time=0.1, max_sleep_time=0.3)
                close_btn = self.op.exists(Assets.CLOSE)
            cnt += 1
        
        self.move.move_with_tracking((-total_actual[0], -total_actual[1]), max_step_px=260)  # 移回原位

    def train_logic(self):
        training_config = self.strategy_interpreter.infer_training_config()
        self.troop_trainer.train(self.op, training_config)

    def attack_logic(self):
        self.attack_executor.execute()

    def switch_world(self):
        self.op.set_max_zoom_out()
        self.op.sleep(0.5)
        self.move.move_with_tracking((-150, 350), max_step_px=260)
        self.op.sleep(0.5)
        boat = self.op.exists(Assets.SHIP_BACK_HOME)
        if not boat:
            self.logger.raise_with_screenshot("未找到返回主世界的小船")
        self.op.random_touch(boat, min_sleep_time=5.5, max_sleep_time=6.5)

    def run_bot(self):
        self.logger.info("--- 正在处理夜世界任务 ---", level=0)
        super().run_bot()
        self.logger.info("夜世界流程完成", level=0)