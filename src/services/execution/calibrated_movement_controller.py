import os

import cv2
import numpy as np

from src.cocbot.common import G, get_log_path, log_msg, sleep, swipe


class CalibratedMovementController:
    def __init__(self, meadow_detector=None):
        self.meadow_detector = meadow_detector

    @staticmethod
    def _calc_orb_displacement(img_before, img_after):
        gray1 = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img_after, cv2.COLOR_BGR2GRAY)

        h, w = gray1.shape
        mask = np.zeros_like(gray1)
        y1, y2 = int(h * 0.2), int(h * 0.8)
        x1, x2 = int(w * 0.2), int(w * 0.8)
        mask[y1:y2, x1:x2] = 255

        orb_create = getattr(cv2, "ORB_create", None)
        orb = orb_create(nfeatures=500) if orb_create is not None else cv2.ORB.create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(gray1, mask=mask)
        kp2, des2 = orb.detectAndCompute(gray2, mask=mask)
        if des1 is None or des2 is None:
            return np.array([0.0, 0.0]), 0

        matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(des1, des2)
        if not matches:
            return np.array([0.0, 0.0]), 0

        matches = sorted(matches, key=lambda m: m.distance)
        keep_n = max(30, int(len(matches) * 0.5))
        filtered = matches[:keep_n]

        displacements = []
        for match in filtered:
            p1 = kp1[match.queryIdx].pt
            p2 = kp2[match.trainIdx].pt
            displacements.append((p2[0] - p1[0], p2[1] - p1[1]))

        if len(displacements) < 10:
            return np.array([0.0, 0.0]), len(displacements)

        dx = float(np.median([d[0] for d in displacements]))
        dy = float(np.median([d[1] for d in displacements]))
        return np.array([dx, dy]), len(displacements)

    def _tracked_swipe_once(self, p1, p2, duration=0.5, settle_time=0.8):
        before = G.DEVICE.snapshot()
        if before is None:
            return np.array([0.0, 0.0]), 0

        swipe(tuple(map(int, p1)), tuple(map(int, p2)), duration=duration)
        sleep(settle_time)

        after = G.DEVICE.snapshot()
        if after is None:
            return np.array([0.0, 0.0]), 0

        return self._calc_orb_displacement(before, after)

    def move_with_tracking(self, target_shift, max_step_px=260):
        target = np.array(target_shift, dtype=float)
        total_actual = np.array([0.0, 0.0])
        screen = G.DEVICE.snapshot()
        if screen is None:
            return total_actual, []

        h, w = screen.shape[:2]
        margin = 140.0
        finger_sign = 1.0
        history = []

        settle_time = 0.8
        tolerance_px = 15
        max_segments = 8
        feedback_stop_threshold = 30
        adaptive_duration_ratio = True
        duration_ratio_growth = 0.08
        max_duration_ratio = 0.8
        min_duration = 0.05
        duration_ratio = 0.4

        for idx in range(max_segments):
            remaining = target - total_actual
            rem_norm = float(np.linalg.norm(remaining))
            if rem_norm <= tolerance_px:
                break

            step_vec = remaining
            if rem_norm > max_step_px:
                step_vec = remaining * (max_step_px / rem_norm)

            finger_vec = step_vec * finger_sign
            p1 = np.array([2560 * 0.8, 1440 * 0.8], dtype=float)
            p2 = p1 + finger_vec
            p2[0] = min(max(p2[0], margin), w - margin)
            p2[1] = min(max(p2[1], margin), h - margin)

            step_distance = float(np.linalg.norm(step_vec))
            current_duration_ratio = duration_ratio
            if adaptive_duration_ratio:
                current_duration_ratio = duration_ratio + idx * duration_ratio_growth
            current_duration_ratio = min(current_duration_ratio, max_duration_ratio)
            seg_duration = current_duration_ratio * (step_distance / 200.0) + min_duration

            actual_vec, match_count = self._tracked_swipe_once(p1, p2, duration=seg_duration, settle_time=settle_time)
            total_actual += actual_vec

            current_error = target - total_actual
            current_error_norm = float(np.linalg.norm(current_error))
            step_error_norm = float(np.linalg.norm(actual_vec - step_vec))

            if np.dot(actual_vec, step_vec) < 0:
                finger_sign *= -1.0

            log_msg(
                f"Segment {idx + 1}: Planned={step_vec.astype(int).tolist()}, Actual={actual_vec.astype(int).tolist()}, "
                f"Remaining Error={current_error.astype(int).tolist()}, Matches={match_count}, "
                f"DurationRatio={current_duration_ratio:.3f}, Duration={seg_duration:.2f}s",
                level=2,
                log_path=get_log_path(),
            )
            history.append(
                {
                    "p1": (int(p1[0]), int(p1[1])),
                    "p2": (int(p2[0]), int(p2[1])),
                    "planned": step_vec.tolist(),
                    "actual": actual_vec.tolist(),
                    "matches": int(match_count),
                    "duration_ratio": float(current_duration_ratio),
                    "duration": float(seg_duration),
                    "remaining_error": current_error.tolist(),
                }
            )

            if np.linalg.norm(actual_vec) < 1.5:
                break
            if current_error_norm <= tolerance_px and step_error_norm <= feedback_stop_threshold:
                break

        return total_actual, history

    def center_night_world(self, tolerance_px=45):
        if self.meadow_detector is None:
            raise RuntimeError("CalibratedMovementController 缺少 MeadowDetector 依赖")

        screen = G.DEVICE.snapshot()
        if screen is None:
            log_msg("[NightCenter] 无法截图，跳过草地中心回正", level=0, log_path=get_log_path())
            return False, None, np.array([0.0, 0.0]), []

        h, w = screen.shape[:2]
        screen_center = np.array([w / 2.0, h / 2.0], dtype=float)
        debug_dir = os.path.join(get_log_path(), "meadow_detect")

        meadow_center, _, _ = self.meadow_detector.detect_center(
            screen_bgr=screen,
            debug_output=True,
            debug_dir=debug_dir,
            debug_prefix="before_center",
        )
        if meadow_center is None:
            log_msg("[NightCenter] 草地中心识别失败", level=0, log_path=get_log_path())
            return False, None, np.array([0.0, 0.0]), []

        delta = screen_center - np.array(meadow_center, dtype=float)
        if np.linalg.norm(delta) <= tolerance_px:
            return True, meadow_center, np.array([0.0, 0.0]), []

        total_actual, history = self.move_with_tracking(target_shift=delta, max_step_px=260)

        verify_screen = G.DEVICE.snapshot()
        if verify_screen is None:
            return False, meadow_center, total_actual, history

        verify_center, _, _ = self.meadow_detector.detect_center(
            screen_bgr=verify_screen,
            debug_output=True,
            debug_dir=debug_dir,
            debug_prefix="after_center",
        )
        if verify_center is None:
            return False, meadow_center, total_actual, history

        verify_delta = screen_center - np.array(verify_center, dtype=float)
        ok = np.linalg.norm(verify_delta) <= tolerance_px
        log_msg(
            f"[NightCenter] 回正后复检中心={verify_center}, 与屏幕中心偏差={verify_delta.astype(int).tolist()}, ok={ok}",
            level=1,
            log_path=get_log_path(),
        )
        return ok, verify_center, total_actual, history
