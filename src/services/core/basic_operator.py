from src.cocbot.common import exists, get_text_from_roi, random_touch, touch


class BasicOperator:
    def exists(self, target):
        return exists(target)

    def touch(self, target):
        return touch(target)

    def random_touch(self, pos, offset=5, min_sleep_time=0.5, max_sleep_time=1.0):
        return random_touch(
            pos,
            offset=offset,
            min_sleep_time=min_sleep_time,
            max_sleep_time=max_sleep_time,
        )

    def get_text(self, roi=None):
        if roi is None:
            return get_text_from_roi()
        return get_text_from_roi(roi)
