from ._assets import Assets
from .advanced import center_night_meadow_to_screen, find_boat_and_switch, set_max_zoom_out, tracked_segmented_swipe, _get_deploy_point_list
from .common import capture_debug_snapshot, exists, get_log_path, log_msg, random_touch, sleep, touch, wait, swipe, get_text_from_roi
from .config_manager import get_config_manager
import random

WITCH_TRAIN_LIST = ["giant", "witch", "witch", "witch", "witch", "witch", "giant", "witch"]
ARCHER_TRAIN_LIST_1 = ["giant", "giant", "giant", "archer"]

# 夜世界原点相对于屏幕中心的位置向量 [dx, dy]
NIGHT_ORIGIN = [0.0, 0.0]


def _night_tracked_move(target_shift, max_step_px=260, duration_ratio=0.35, min_duration=0.2, settle_time=0.8):
    """夜世界位移封装：自动分段滑动并按真实位移更新 NIGHT_ORIGIN。"""
    global NIGHT_ORIGIN
    total_actual, history = tracked_segmented_swipe(
        target_shift=target_shift,
        max_step_px=max_step_px,
        duration_ratio=duration_ratio,
        min_duration=min_duration,
        settle_time=settle_time,
        tolerance_px=12,
        max_segments=10,
    )
    if history:
        for idx, step in enumerate(history, start=1):
            NIGHT_ORIGIN[0] += float(step["actual"][0])
            NIGHT_ORIGIN[1] += float(step["actual"][1])
            log_msg(
                f"[NightMove] step {idx}/{len(history)} actual={list(map(int, step['actual']))}, NIGHT_ORIGIN={list(map(int, NIGHT_ORIGIN))}",
                level=2,
                log_path=get_log_path(),
            )
    else:
        NIGHT_ORIGIN[0] += float(total_actual[0])
        NIGHT_ORIGIN[1] += float(total_actual[1])

    log_msg(
        f"[NightMove] 目标位移={list(map(int, target_shift))}, 实际位移={total_actual.astype(int).tolist()}, NIGHT_ORIGIN={list(map(int, NIGHT_ORIGIN))}",
        level=1,
        log_path=get_log_path(),
    )
    return total_actual, history


def collect_night_resources():
    """夜世界资源收集：水、金、绿宝石"""
    if exists(Assets.NIGHT_GOLD):
        random_touch(exists(Assets.NIGHT_GOLD))
    if exists(Assets.EREMALD):
        random_touch(exists(Assets.EREMALD))

    cnt = 0
    while exists(Assets.NIGHT_WATER) and cnt < 3:
        random_touch(exists(Assets.NIGHT_WATER))
        sleep(0.3)
        if exists(Assets.BTN_COLLECT):
            random_touch(exists(Assets.BTN_COLLECT))
        while exists(Assets.CLOSE):
            random_touch(exists(Assets.CLOSE))
            sleep(0.3)
        cnt += 1


def night_train_logic(faction=None):
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.night_faction

    if faction == "witch":
        log_msg("夜世界练兵流派: 女巫", level=1, log_path=get_log_path())
        train_list = WITCH_TRAIN_LIST
    elif faction == "archer":
        log_msg("夜世界练兵流派: 弓箭手", level=1, log_path=get_log_path())
        train_list = ARCHER_TRAIN_LIST_1
    else:
        log_msg(f"未知的训练流派类型: {faction}", level=0, log_path=get_log_path())
        capture_debug_snapshot(f"unknown_faction_{faction}", log_path=get_log_path())
        raise Exception(f"未知的训练流派类型: {faction}")
    
    """夜世界练兵逻辑：删除现有并按配置训练"""
    log_msg("正在进入夜世界练兵界面...", log_path=get_log_path())
    try:
        random_touch(exists(Assets.BTN_TRAIN))
    except Exception as e:
        log_msg("未找到练兵按钮，跳过练兵流程", level=0, log_path=get_log_path())
        capture_debug_snapshot("night_train_button_not_found", log_path=get_log_path())
        raise Exception(f"练兵流程失败: {str(e)}")
    sleep(0.5)

    try:
        random_touch(exists(Assets.BTN_DELETE))
    except Exception as e:
        log_msg("未找到删除按钮，跳过删除流程", level=0, log_path=get_log_path())
        capture_debug_snapshot("night_delete_button_not_found", log_path=get_log_path())
        raise Exception(f"删除流程失败: {str(e)}")
    sleep(0.5)

    for troop_name in train_list:
        if troop_name == "giant":
            try:
                random_touch(exists(Assets.GIANT_TRAIN))
                sleep(0.5)
            except Exception as e:
                log_msg("未找到巨人训练按钮，跳过巨人训练", level=0, log_path=get_log_path())
                capture_debug_snapshot("night_giant_train_not_found", log_path=get_log_path())
                raise Exception(f"巨人训练流程失败: {str(e)}")
        elif troop_name == "witch":
            try:
                random_touch(exists(Assets.WITCH_TRAIN))
                sleep(0.5)
            except Exception as e:
                log_msg("未找到女巫训练按钮，跳过女巫训练", level=0, log_path=get_log_path())
                capture_debug_snapshot("night_witch_train_not_found", log_path=get_log_path())
                raise Exception(f"女巫训练流程失败: {str(e)}")
        elif troop_name == "archer":
            try:
                random_touch(exists(Assets.ARCHER_TRAIN), offset=1)
                sleep(0.5)
            except Exception as e:
                log_msg("未找到弓箭手训练按钮，跳过弓箭手训练", level=0, log_path=get_log_path())
                capture_debug_snapshot("night_archer_train_not_found", log_path=get_log_path())
                raise Exception(f"弓箭手训练流程失败: {str(e)}")
    if exists(Assets.MECHA_TRAIN):
        random_touch(exists(Assets.MECHA_TRAIN))
        sleep(0.5)
    
    random_touch(exists(Assets.CLOSE))
    # 结束检验
    if exists(Assets.BTN_DELETE):
        log_msg("关闭训练界面后，删除按钮仍然存在，可能训练未成功", level=0, log_path=get_log_path())
        capture_debug_snapshot("train_end_delete_button_still_exists", log_path=get_log_path())
        raise Exception("训练流程结束检验失败: 删除按钮仍然存在")
    log_msg("练兵流程完成", level=0, log_path=get_log_path())


def _wait_and_finish_battle_once():
    countdown_prompt = get_text_from_roi()
    timeout = 150
    while "离战斗结束还有" in countdown_prompt and timeout > 0:
        log_msg(f"战斗进行中，继续等待...", log_path=get_log_path())
        sleep(5)
        countdown_prompt = get_text_from_roi()
        timeout -= 5
        if timeout <= 0:
            log_msg("战斗超时，尝试结束战斗...", level=0, log_path=get_log_path())
            capture_debug_snapshot("battle_timeout", log_path=get_log_path())
            raise Exception("战斗超时")
        
    if exists(Assets.BTN_END):
        random_touch(exists(Assets.BTN_END))
        sleep(1)
        try:
            random_touch(exists(Assets.BTN_CONFIRM))
        except Exception as e:
            log_msg("未找到结束战斗确认按钮，无法正常结束战斗", level=0, log_path=get_log_path())
            capture_debug_snapshot("battle_end_confirm_not_found", log_path=get_log_path())
            raise Exception(f"结束战斗流程失败: {str(e)}")


def _night_battle_witch_once():
    """夜世界战斗中女巫流派的部署逻辑, 仅打一阶段"""
    valid_deploy_point = [2396, 800]
    try:
        random_touch(exists(Assets.GIANT_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到巨人部署按钮，进攻失败", level=0, log_path=get_log_path())
        capture_debug_snapshot("witch_giant_deploy_not_found", log_path=get_log_path())
        raise Exception(f"巨人部署流程失败: {str(e)}")
    
    for point in _get_deploy_point_list():
        random_touch(point, min_sleep_time=0, max_sleep_time=0.02)
        if exists(Assets.BTN_GIVE_UP):
            valid_deploy_point = point
            break

    if exists(Assets.MECHA_DEPLOY):
        random_touch(exists(Assets.MECHA_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(2):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    if exists(Assets.FIGHTER_JET_DEPLOY):
        random_touch(exists(Assets.FIGHTER_JET_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(2):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)

    try:
        random_touch(exists(Assets.WITCH_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(7):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到女巫部署按钮，跳过女巫部署", level=0, log_path=get_log_path())
        capture_debug_snapshot("witch_deploy_not_found", log_path=get_log_path())
        raise Exception(f"女巫部署流程失败: {str(e)}")
    
    log_msg("部署完成，等待战斗结束...", log_path=get_log_path())
    _wait_and_finish_battle_once()


def _night_battle_archer_once():
    """夜世界战斗中巨人弓箭手流派的部署逻辑, 打一阶段"""
    f"""夜世界战斗中女巫流派的部署逻辑, 仅打一阶段"""
    valid_deploy_point = [2396, 800]
    try:
        random_touch(exists(Assets.GIANT_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到巨人部署按钮，进攻失败", level=0, log_path=get_log_path())
        capture_debug_snapshot("archer_giant_deploy_not_found", log_path=get_log_path())
        raise Exception(f"巨人部署流程失败: {str(e)}")

    for point in _get_deploy_point_list():
        random_touch(point, min_sleep_time=0, max_sleep_time=0.02)
        if exists(Assets.BTN_GIVE_UP):
            valid_deploy_point = point
            break
    # 继续部署剩余的巨人
    for _ in range(3):
        random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    
    if exists(Assets.MECHA_DEPLOY):
        random_touch(exists(Assets.MECHA_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(2):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    if exists(Assets.FIGHTER_JET_DEPLOY):
        random_touch(exists(Assets.FIGHTER_JET_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(2):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
            
    try:
        random_touch(exists(Assets.ARCHER_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        for _ in range(5):
            random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到弓箭手部署按钮，弓箭手部署失败", level=0, log_path=get_log_path())
        capture_debug_snapshot("archer_deploy_not_found", log_path=get_log_path())
        raise Exception(f"弓箭手部署流程失败: {str(e)}")
    
    log_msg("部署完成，等待战斗结束...", log_path=get_log_path())
    _wait_and_finish_battle_once()


ROI_START = [30, 1170, 80, 1360] # 搜索对手界面倒计时文本的 ROI，根据你的设备分辨率调整
def night_battle_logic(faction=None):
    """夜世界搜索并自动下兵"""
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.night_faction

    if not exists(Assets.NIGHT_FIGHT_WITH_STAR) and not exists(Assets.NIGHT_FIGHT):
        return

    if exists(Assets.NIGHT_FIGHT_WITH_STAR):
        random_touch(exists(Assets.NIGHT_FIGHT_WITH_STAR))
    else:
        random_touch(exists(Assets.NIGHT_FIGHT))

    try:
        random_touch(exists(Assets.BTN_SEARCH))
    except Exception as e:
        log_msg("未找到搜索按钮，跳过战斗流程", level=0, log_path=get_log_path())
        capture_debug_snapshot("battle_search_button_not_found", log_path=get_log_path())
        raise Exception(f"战斗流程失败: {str(e)}")

    log_msg("正在搜寻对手...", log_path=get_log_path())
    MAX_SEARCH_TIME = 50
    search_time = 0
    countdown_prompt = get_text_from_roi()
    while "开战倒计时" not in countdown_prompt and search_time < MAX_SEARCH_TIME:
        log_msg(f"正在搜索对手，继续等待...", log_path=get_log_path())
        sleep(3)
        countdown_prompt = get_text_from_roi()
        search_time += 3

    # 战斗逻辑
    log_msg("搜索完成，准备下兵...", log_path=get_log_path())
    if faction == "witch":
        _night_battle_witch_once()
    elif faction == "archer":
        _night_battle_archer_once()
    log_msg("战斗结束, 正在返回...", log_path=get_log_path())

    sleep(2)
    try:
        random_touch(exists(Assets.BTN_BACK))
    except Exception as e:
        log_msg("未找到回营按钮，无法正常返回", level=0, log_path=get_log_path())
        capture_debug_snapshot("battle_back_button_not_found", log_path=get_log_path())
        raise Exception(f"返回流程失败: {str(e)}")
    sleep(1)
    if exists(Assets.BTN_CONFIRM):
        random_touch(exists(Assets.BTN_CONFIRM))
        sleep(1)


def night_righting_pos():
    """基于草地平行四边形中心回正视角，并在成功后将 NIGHT_ORIGIN 置零。"""
    global NIGHT_ORIGIN
    log_msg("正在调整夜世界视角...", log_path=get_log_path())

    ok, detected_center, total_actual, history = center_night_meadow_to_screen(
        tolerance_px=45,
        max_step_px=260,
        max_segments=10,
        debug_detect=True,
    )
    NIGHT_ORIGIN[0] = detected_center[0]
    NIGHT_ORIGIN[1] = detected_center[1]
    if ok:
        log_msg(f"视角调整完成，检测到的草地中心={detected_center}, 实际位移={total_actual.astype(int).tolist()}", level=1, log_path=get_log_path())
    else:
        log_msg("视角调整失败", level=0, log_path=get_log_path())


def run_night_world(faction=None, retrain=None, battle=None):
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.night_faction
    if retrain is None:
        retrain = cfg.night_retrain
    if battle is None:
        battle = cfg.night_battle

    log_msg("--- 正在处理夜世界任务 ---", level=0, log_path=get_log_path())
    
    night_righting_pos()
    log_msg("稍微上移动视野，确保所有资源在屏幕内...", log_path=get_log_path())
    _night_tracked_move(target_shift=(0, 260), max_step_px=220)
    collect_night_resources()

    if retrain:
        night_train_logic(faction=faction)

    if battle: 
        for index in range(cfg.night_attempts):
            log_msg(f"夜战尝试 {index + 1}/{cfg.night_attempts}", level=0, log_path=get_log_path())
            night_battle_logic(faction=faction)

    # 最后再调整一下视角，准备切回主世界
    set_max_zoom_out()
    night_righting_pos()

    log_msg("再次收集资源", level=0, log_path=get_log_path())
    _night_tracked_move(target_shift=(0, 260), max_step_px=220)
    collect_night_resources()
    _night_tracked_move(target_shift=(0, -260), max_step_px=220)

    if find_boat_and_switch("HOME"):
        pass
    log_msg("夜世界流程完成", level=0, log_path=get_log_path())
