from src.cocbot.advanced import center_night_meadow_to_screen


class MeadowDetector:
    def center_night_view(self, tolerance_px=45):
        return center_night_meadow_to_screen(tolerance_px=tolerance_px)
