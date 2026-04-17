from src.cocbot.advanced import detect_world, set_max_zoom_out


class WorldDetector:
    def detect(self, auto_zoom=True):
        if auto_zoom:
            set_max_zoom_out()
        return detect_world()
