from ._assets import Assets
from .common import capture_debug_snapshot, exists, get_log_path, log_msg, random_touch, sleep, pinch, swipe, G
from .meadow_detector import MeadowParallelogramDetector
import os
import cv2
import numpy as np
import random


_MEADOW_DETECTOR = MeadowParallelogramDetector(sample_path=os.path.join("cocbot", "sample_imgs", "night"))

def detect_meadow_parallelogram_center(
    screen_bgr=None,
    min_area_ratio=0.07,
    debug_output=False,
    debug_dir=None,
    debug_prefix="meadow_detect",
):
    """识别草地平行四边形中心。返回 (center, box_points, mask)。"""
    if screen_bgr is None:
        screen_bgr = G.DEVICE.snapshot()
    if screen_bgr is None:
        return None, None, None

    return _MEADOW_DETECTOR.detect_with_debug(
        screen_bgr,
        min_area_ratio=min_area_ratio,
        debug_output=debug_output,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
    )


def _calc_orb_displacement(img_before, img_after):
    """使用 ORB 估算屏幕内容位移，返回 (dx, dy, matches_count)。"""
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
    for m in filtered:
        p1 = kp1[m.queryIdx].pt
        p2 = kp2[m.trainIdx].pt
        displacements.append((p2[0] - p1[0], p2[1] - p1[1]))

    if len(displacements) < 10:
        return np.array([0.0, 0.0]), len(displacements)

    dx = float(np.median([d[0] for d in displacements]))
    dy = float(np.median([d[1] for d in displacements]))
    return np.array([dx, dy]), len(displacements)


def tracked_swipe_once(p1, p2, duration=0.5, settle_time=0.8):
    """执行一次滑动并追踪实际位移。"""
    before = G.DEVICE.snapshot()
    if before is None:
        return np.array([0.0, 0.0]), 0

    swipe(tuple(map(int, p1)), tuple(map(int, p2)), duration=duration)
    sleep(settle_time)

    after = G.DEVICE.snapshot()
    if after is None:
        return np.array([0.0, 0.0]), 0

    return _calc_orb_displacement(before, after)


def tracked_segmented_swipe(
    target_shift,
    max_step_px=260,
    settle_time=0.8,
    tolerance_px=15,
    max_segments=8,
    feedback_stop_threshold=30,
    adaptive_duration_ratio=True,
    duration_ratio_growth=0.08,
    max_duration_ratio=0.8,
    min_duration=0.05,
    duration_ratio=0.4,
):
    """按小步分段滑动，追踪每段真实位移，返回总位移。"""
    target = np.array(target_shift, dtype=float)
    total_actual = np.array([0.0, 0.0])
    screen = G.DEVICE.snapshot()
    if screen is None:
        return total_actual, []

    h, w = screen.shape[:2]
    center = np.array([w / 2.0, h / 2.0], dtype=float)
    margin = 140.0
    finger_sign = 1.0
    history = []

    for idx in range(max_segments):
        remaining = target - total_actual
        rem_norm = float(np.linalg.norm(remaining))
        if rem_norm <= tolerance_px:
            break

        step_vec = remaining
        if rem_norm > max_step_px:
            step_vec = remaining * (max_step_px / rem_norm)

        finger_vec = step_vec * finger_sign
        p1 = [2560*0.8, 1440*0.8]  # 固定起点
        p2 = p1 + finger_vec
        p2[0] = min(max(p2[0], margin), w - margin)
        p2[1] = min(max(p2[1], margin), h - margin)

        step_distance = float(np.linalg.norm(step_vec))
        current_duration_ratio = duration_ratio
        if adaptive_duration_ratio:
            current_duration_ratio = duration_ratio + idx * duration_ratio_growth
        # 限制duration_ratio最大值
        current_duration_ratio = min(current_duration_ratio, max_duration_ratio)
        seg_duration = current_duration_ratio * (step_distance / 200.0) + min_duration

        actual_vec, match_count = tracked_swipe_once(p1, p2, duration=seg_duration, settle_time=settle_time)
        total_actual += actual_vec

        current_error = target - total_actual
        current_error_norm = float(np.linalg.norm(current_error))
        step_error_norm = float(np.linalg.norm(actual_vec - step_vec))

        if np.dot(actual_vec, step_vec) < 0:
            finger_sign *= -1.0

        log_msg(
            f"Segment {idx+1}: Planned={step_vec.astype(int).tolist()}, Actual={actual_vec.astype(int).tolist()}, "
            f"Remaining Error={current_error.astype(int).tolist()}, Matches={match_count}, "
            f"DurationRatio={current_duration_ratio:.3f}, Duration={seg_duration:.2f}s",
            level=2,
            log_path=get_log_path(),
        )
        history.append({
            "p1": (int(p1[0]), int(p1[1])),
            "p2": (int(p2[0]), int(p2[1])),
            "planned": step_vec.tolist(),
            "actual": actual_vec.tolist(),
            "matches": int(match_count),
            "duration_ratio": float(current_duration_ratio),
            "duration": float(seg_duration),
            "remaining_error": current_error.tolist(),
        })

        if np.linalg.norm(actual_vec) < 1.5:
            break

        # 反馈停止：实际累计位移已足够接近目标，且单段误差也足够小
        if current_error_norm <= tolerance_px and step_error_norm <= feedback_stop_threshold:
            break

    return total_actual, history


def center_night_meadow_to_screen(tolerance_px=45, max_step_px=260, max_segments=8, debug_detect=False):
    """识别草地中心并移到屏幕中心，返回 (ok, meadow_center, total_actual, history)。"""
    screen = G.DEVICE.snapshot()
    if screen is None:
        log_msg("[NightCenter] 无法截图，跳过草地中心回正", level=0, log_path=get_log_path())
        return False, None, np.array([0.0, 0.0]), []

    h, w = screen.shape[:2]
    screen_center = np.array([w / 2.0, h / 2.0], dtype=float)
    debug_dir = os.path.join(get_log_path(), "meadow_detect") if debug_detect else None
    meadow_center, _, _ = detect_meadow_parallelogram_center(
        screen_bgr=screen,
        debug_output=debug_detect,
        debug_dir=debug_dir,
        debug_prefix="before_center",
    )
    if meadow_center is None:
        log_msg("[NightCenter] 草地中心识别失败", level=0, log_path=get_log_path())
        return False, None, np.array([0.0, 0.0]), []

    delta = screen_center - np.array(meadow_center, dtype=float)
    if np.linalg.norm(delta) <= tolerance_px:
        return True, meadow_center, np.array([0.0, 0.0]), []

    total_actual, history = tracked_segmented_swipe(
        target_shift=delta,
        max_step_px=max_step_px,
        settle_time=0.8,
        tolerance_px=int(max(8, tolerance_px * 0.35)),
        max_segments=max_segments,
        adaptive_duration_ratio=True,
    )

    # 末次复核是否已基本居中
    verify_screen = G.DEVICE.snapshot()
    if verify_screen is None:
        return False, meadow_center, total_actual, history

    verify_center, _, _ = detect_meadow_parallelogram_center(
        screen_bgr=verify_screen,
        debug_output=debug_detect,
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


def detect_world():
    """
    通过指定模板的最高置信度识别当前世界
    """
    candidates = [
        ("HOME", "FIGHT_HOME", Assets.FIGHT_HOME),
        ("HOME", "FIGHT_HOME_WITH_STAR", Assets.FIGHT_HOME_WITH_STAR),
        ("HOME", "FIGHT_HOME_WITH_3_STAR", Assets.FIGHT_HOME_WITH_3_STAR),
        ("NIGHT", "NIGHT_FIGHT", Assets.NIGHT_FIGHT),
        ("NIGHT", "NIGHT_FIGHT_WITH_STAR", Assets.NIGHT_FIGHT_WITH_STAR),
    ]

    best_world = "UNKNOWN"
    best_name = None
    best_confidence = -1.0

    # 获取当前屏幕截图
    screen = G.DEVICE.snapshot()

    for world, name, target in candidates:
        # --- 核心修改：使用 _cv_match ---
        # 它返回一个字典，例如: {'result': (167, 1266), 'rectangle': ((43, 1144.28), (43, 1389.28), (291, 1389.28), (291, 1144.28)), 'confidence': 0.9998106956481934, 'time': 0.011312723159790039}
        results = target._cv_match(screen)
        
        if not results:
            log_msg(f"DEBUG: {name} 没有找到任何匹配点", level=2, log_path=get_log_path())
            continue

        confidence = results['confidence']
        pos = results['result']

        log_msg(f"DEBUG: {name} confidence = {confidence:.4f} at {pos}", level=2, log_path=get_log_path())

        # 比较最高置信度
        if confidence > best_confidence:
            best_world = world
            best_name = name
            best_confidence = confidence

    # 判定逻辑
    if best_confidence > 0.6:
        log_msg(f"DEBUG: Final decision -> {best_world} (via {best_name} score:{best_confidence:.2f})", level=2, log_path=get_log_path())
        return best_world

    return "UNKNOWN"


def set_max_zoom_out():
    """连续捏合，获得最大视野"""
    log_msg("正在捏合以扩大视野...", log_path=get_log_path())
    for _ in range(3):
        pinch(in_or_out="in", center=None, percent=0.2)
        sleep(0.5)


def find_boat_and_switch(target_world="NIGHT"):
    """
    寻找小船并转换世界
    :param target_world: "NIGHT" (去夜世界) 或 "HOME" (回主世界)
    """
    set_max_zoom_out()
    sleep(0.5)

    if target_world == "NIGHT":
        log_msg("寻找去夜世界的小船...", log_path=get_log_path())
        tracked_segmented_swipe(
            target_shift=(150, -350),  # 这个值可能需要根据实际情况调整
            max_step_px=260,
            settle_time=0.8,
            tolerance_px=15,
            max_segments=6,
            adaptive_duration_ratio=True,
        )
        sleep(0.5)
        boat = Assets.SHIP_TO_NIGHT
    else:
        log_msg("寻找回主世界的小船...", log_path=get_log_path())
        tracked_segmented_swipe(
            target_shift=(-150, 350),  # 这个值可能需要根据实际情况调整
            max_step_px=260,
            settle_time=0.8,
            tolerance_px=15,
            max_segments=6,
            adaptive_duration_ratio=True,
        )
        sleep(0.5)
        boat = Assets.SHIP_BACK_HOME

    pos = exists(boat)
    if pos:
        random_touch(pos)
        log_msg(f"点击小船，正在前往 {target_world}...", level=0, log_path=get_log_path())
        sleep(6)
        return True

    log_msg("未找到小船，截图以供分析", level=0, log_path=get_log_path())
    capture_debug_snapshot("boat_not_found", log_path=get_log_path())
    return False

SPAWN_POINTS = [[169, 660], [2396, 800], [2066, 456], [2258, 577], [2281, 759]]
def _get_deploy_point_list():
    """随机shuffle一下部署点，增加多样性"""
    points = SPAWN_POINTS.copy()
    random.shuffle(points)
    return points