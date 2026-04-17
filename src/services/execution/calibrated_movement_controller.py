from src.cocbot.advanced import center_night_meadow_to_screen, tracked_segmented_swipe


class CalibratedMovementController:
    def move_with_tracking(self, target_shift, max_step_px=260):
        return tracked_segmented_swipe(target_shift=target_shift, max_step_px=max_step_px)

    def center_night_world(self, tolerance_px=45):
        return center_night_meadow_to_screen(tolerance_px=tolerance_px)
