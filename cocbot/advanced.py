from ._assets import Assets
from .common import capture_debug_snapshot, exists, get_log_path, log_msg, random_touch, sleep, pinch, swipe, G


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
        swipe((1280, 700), (1280, 300), duration=0.5)
        sleep(0.5)
        boat = Assets.SHIP_TO_NIGHT
    else:
        log_msg("寻找回主世界的小船...", log_path=get_log_path())
        swipe((1280, 300), (1280, 700), duration=0.5)
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
