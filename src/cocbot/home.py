from ._assets import Assets
from .advanced import find_boat_and_switch, set_max_zoom_out, tracked_segmented_swipe, _get_deploy_point_list
from .common import get_log_path, log_msg, random_touch, sleep, find_all, swipe, exists, capture_debug_snapshot, get_text_from_roi
from .config_manager import get_config_manager
import csv
import math


def _load_lightning_damage(lightning_level, csv_path=None):
    """读取指定等级闪电法术单次伤害。"""
    cfg = get_config_manager()
    if csv_path is None:
        csv_path = cfg.lightning_data_path
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["Level"]) == int(lightning_level):
                return int(row["TotalDamage"])
    raise ValueError(f"未找到闪电法术等级数据: level={lightning_level}, path={csv_path}")


def _load_anti_aircraft_stats(csv_path=None):
    """读取防空火箭等级属性（DPSecond、Hitpoints）。"""
    cfg = get_config_manager()
    if csv_path is None:
        csv_path = cfg.anti_aircraft_data_path
    stats = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            level = int(row["Level"])
            stats[level] = {
                "dp_second": int(row["DPSecond"]),
                "hitpoints": int(row["Hitpoints"]),
            }
    return stats


def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _pick_lightning_targets(anti_aircraft_list, lightning_number, lightning_damage, deploy_point):
    """选择闪电法术最优劈法。

    目标：让剩余防空火箭总 DPSecond 最小。
    约束：只有被完全击毁的火箭，DPSecond 才归零。
    次级目标：同等收益下优先击毁离部署点更远的火箭。

    返回结构：
    - plan: 按实际施法顺序排列的动作列表
    - total_removed_dp_second: 预计被清除的 DPSecond 总和
    - remaining_dp_second: 执行计划后预计剩余的 DPSecond
    - total_strikes_used: 计划总共使用的闪电次数
    """
    candidates = []
    for idx, rocket in enumerate(anti_aircraft_list):
        needed = int(math.ceil(rocket["hitpoints"] / lightning_damage))
        dist = _distance(rocket["position"], deploy_point)
        candidates.append({
            "idx": idx,
            "level": rocket["level"],
            "position": rocket["position"],
            "dp_second": rocket["dp_second"],
            "hitpoints": rocket["hitpoints"],
            "strikes_needed": needed,
            "distance": dist,
        })

    # 0/1 背包：容量是可用闪电次数，价值是可消除的 DPSecond。
    killable_candidates = [item for item in candidates if item["strikes_needed"] <= lightning_number]
    best = [(0, 0.0, []) for _ in range(lightning_number + 1)]
    for candidate in killable_candidates:
        cost = candidate["strikes_needed"]
        value = candidate["dp_second"]
        dist = candidate["distance"]
        for cap in range(lightning_number, cost - 1, -1):
            prev_value, prev_dist, prev_pick = best[cap - cost]
            new_state = (prev_value + value, prev_dist + dist, prev_pick + [candidate])
            if new_state[0] > best[cap][0] or (new_state[0] == best[cap][0] and new_state[1] > best[cap][1]):
                best[cap] = new_state

    best_state = max(best, key=lambda s: (s[0], s[1]))
    kill_plan = list(best_state[2])
    used_strikes = sum(item["strikes_needed"] for item in kill_plan)
    total_removed_dp_second = sum(item["dp_second"] for item in kill_plan)

    remaining_lightning = lightning_number - used_strikes
    remaining_targets = [item for item in candidates if item["idx"] not in {picked["idx"] for picked in kill_plan}]
    remaining_targets.sort(key=lambda item: (item["dp_second"], item["distance"]), reverse=True)

    if remaining_lightning > 0 and remaining_targets:
        strike_state = {item["idx"]: 0 for item in remaining_targets}
        remaining_hp = {item["idx"]: item["hitpoints"] for item in remaining_targets}
        remaining_dp_map = {item["idx"]: item["dp_second"] for item in remaining_targets}
        filler_targets = list(remaining_targets)
        filler_plan = []

        while remaining_lightning > 0 and filler_targets:
            target = filler_targets[0]
            strike_state[target["idx"]] += 1
            remaining_lightning -= 1
            will_destroy = strike_state[target["idx"]] * lightning_damage >= remaining_hp[target["idx"]]
            filler_plan.append({
                "idx": target["idx"],
                "level": target["level"],
                "position": target["position"],
                "dp_second": target["dp_second"],
                "hitpoints": target["hitpoints"],
                "strikes_needed": 1,
                "distance": target["distance"],
                "mode": "kill" if will_destroy else "filler",
            })

            if will_destroy:
                total_removed_dp_second += remaining_dp_map[target["idx"]]
                filler_targets = [item for item in filler_targets if item["idx"] != target["idx"]]

        plan = [
            {
                **item,
                "mode": "kill",
            }
            for item in sorted(kill_plan, key=lambda x: x["distance"], reverse=True)
        ] + filler_plan
    else:
        plan = [
            {
                **item,
                "mode": "kill",
            }
            for item in sorted(kill_plan, key=lambda x: x["distance"], reverse=True)
        ]

    total_strikes_used = sum(item["strikes_needed"] for item in plan)
    remaining_dp_second = sum(item["dp_second"] for item in candidates) - total_removed_dp_second
    return {
        "plan": plan,
        "total_removed_dp_second": total_removed_dp_second,
        "remaining_dp_second": remaining_dp_second,
        "total_strikes_used": total_strikes_used,
    }


def run_home_world(faction=None, filter_config=None, retrain=None, battle=None):
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.home_faction
    if filter_config is None:
        filter_config = cfg.home_filter
    if retrain is None:
        retrain = cfg.home_retrain
    if battle is None:
        battle = cfg.home_battle

    log_msg("--- 正在处理主世界任务 ---", level=0, log_path=get_log_path())

    home_righting_pos()
    collect_resources_home([Assets.OIL, Assets.WATER, Assets.GOLD])

    if retrain:
        log_msg("重新训练主世界模型，删除现有配兵", level=0, log_path=get_log_path())
        home_train_logic(faction=faction)
    if battle:
        for index in range(cfg.home_attempts):
            log_msg(f"主战尝试 {index + 1}/{cfg.home_attempts}", level=0, log_path=get_log_path())
            home_battle_logic(faction=faction, filter_config=filter_config)

    if find_boat_and_switch("NIGHT"):
        pass
    log_msg("主世界流程完成", level=0, log_path=get_log_path())


def collect_resources_home(res_list, offset=5):
    """循环收集资源"""
    for res in res_list:
        icons = find_all(res)
        if icons:
            for icon in icons:
                random_touch(icon["result"], offset=offset)
                sleep(0.3)


def home_righting_pos():
    """回正视角，先向右下角移动到最大，再向上回正"""
    log_msg("正在调整主世界视角...", log_path=get_log_path())
    swipe((800, 600), (400, 200), duration=0.5)
    sleep(0.5)
    tracked_segmented_swipe((200, 250))
    sleep(0.5)


def home_train_logic(faction=None):
    """主世界训练逻辑"""
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.home_faction

    log_msg("正在执行主世界训练...", log_path=get_log_path())

    if faction == "dragon":
        try:
            random_touch(exists(Assets.DRAGON_TRAIN))
        except Exception as e:
            log_msg(f"未找到龙训练图标: {e}", level=1, log_path=get_log_path())
    for _ in range(11):
        random_touch(exists(Assets.DRAGON_TRAIN))

    try:
        random_touch(exists(Assets.CLOSE))
    except Exception as e:
        log_msg(f"未找到关闭按钮: {e}", level=1, log_path=get_log_path())


def _home_dragon_fight_logic(dragon_number=None, lightning_number=None, lightning_level=None):
    """主世界龙战斗逻辑"""
    cfg = get_config_manager()
    if dragon_number is None:
        dragon_number = cfg.home_fight["dragon_number"]
    if lightning_number is None:
        lightning_number = cfg.home_fight["lightning_number"]
    if lightning_level is None:
        lightning_level = cfg.home_fight["lightning_level"]

    valid_deploy_point = [2396, 800]
    try:
        random_touch(exists(Assets.DRAGON_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到龙部署按钮，进攻失败", level=0, log_path=get_log_path())
        capture_debug_snapshot("archer_dragon_deploy_not_found", log_path=get_log_path())
        raise Exception(f"龙部署流程失败: {str(e)}")
    
    for point in _get_deploy_point_list():
        random_touch(point, min_sleep_time=0, max_sleep_time=0.02)
        countdown_prompt = get_text_from_roi()
        if "离战斗结束还有" in countdown_prompt:
            valid_deploy_point = point
            log_msg(f"找到有效的部署点: {point}", level=1, log_path=get_log_path())
            break
    
    # 先放法术：优先最小化剩余总 DPSecond，收益相同则优先远离部署点；
    # 若还有剩余法术，则按防空火箭价值从高到低补打，没击毁也允许。
    try:
        random_touch(exists(Assets.LIGHTNING_SPELL_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg(f"未找到法术图标: {e}", level=0, log_path=get_log_path())
        capture_debug_snapshot("spell_icon_not_found", log_path=get_log_path())
        raise Exception("法术部署失败")

    anti_aircraft_targets = _detect_anti_aircraft_rocket()
    if not anti_aircraft_targets:
        log_msg("未检测到防空火箭，继续部署龙", level=1, log_path=get_log_path())
    else:
        lightning_damage = _load_lightning_damage(lightning_level)
        lightning_plan = _pick_lightning_targets(
            anti_aircraft_list=anti_aircraft_targets,
            lightning_number=lightning_number,
            lightning_damage=lightning_damage,
            deploy_point=valid_deploy_point,
        )

        if not lightning_plan["plan"]:
            log_msg("法术部署计划为空, 出错", level=2, log_path=get_log_path())
        else:
            kill_count = sum(1 for item in lightning_plan["plan"] if item["mode"] == "kill")
            filler_count = sum(1 for item in lightning_plan["plan"] if item["mode"] == "filler")
            log_msg(
                f"闪电法术等级={lightning_level} 单次伤害={lightning_damage}，计划使用 {lightning_plan['total_strikes_used']} 发，完整击毁 {kill_count} 个，补打 {filler_count} 发，预计剩余总DPSecond={lightning_plan['remaining_dp_second']}",
                level=1,
                log_path=get_log_path(),
            )
            for index, target in enumerate(lightning_plan["plan"], start=1):
                log_msg(
                    f"第{index}发 -> level={target['level']} pos={target['position']} mode={target['mode']} strikes={target['strikes_needed']} dp_second={target['dp_second']} dist={target['distance']:.1f}",
                    level=1,
                    log_path=get_log_path(),
                )
                for _ in range(target["strikes_needed"]):
                    random_touch(target["position"], offset=1, min_sleep_time=0, max_sleep_time=0.02)

    # 继续部署剩余的龙
    try:
        random_touch(exists(Assets.DRAGON_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    except Exception as e:
        log_msg("未找到龙部署按钮，进攻失败", level=0, log_path=get_log_path())
        capture_debug_snapshot("archer_dragon_deploy_not_found", log_path=get_log_path())
        raise Exception(f"龙部署流程失败: {str(e)}")
    for _ in range(dragon_number):
        random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
    
    # 部署英雄
    if exists(Assets.QUEEN_DEPLOY):
        random_touch(exists(Assets.QUEEN_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)
        sleep(1)
        # 手动放技能
        random_touch(exists(Assets.QUEEN_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
    if exists(Assets.THE_REVENANT_PRINCE_DEPLOY):
        random_touch(exists(Assets.THE_REVENANT_PRINCE_DEPLOY), min_sleep_time=0, max_sleep_time=0.02)
        random_touch(valid_deploy_point, min_sleep_time=0, max_sleep_time=0.02)


def _wait_the_battle_finish():
    countdown_prompt = get_text_from_roi()
    timeout = 200
    while "离战斗结束还有" in countdown_prompt and timeout > 0:
        log_msg(f"战斗进行中，继续等待...", log_path=get_log_path())
        sleep(5)
        countdown_prompt = get_text_from_roi()
        timeout -= 5
        if timeout <= 0:
            log_msg("战斗超时...", level=0, log_path=get_log_path())
            capture_debug_snapshot("battle_timeout", log_path=get_log_path())
            raise Exception("战斗超时")


def home_battle_logic(faction=None, filter_config=None):
    """主世界战斗逻辑"""
    cfg = get_config_manager()
    if faction is None:
        faction = cfg.home_faction
    if filter_config is None:
        filter_config = cfg.home_filter

    log_msg("正在执行主世界战斗...", log_path=get_log_path())
    try:
        if exists(Assets.FIGHT_HOME_WITH_3_STAR):
            random_touch(exists(Assets.FIGHT_HOME_WITH_3_STAR))
        elif exists(Assets.FIGHT_HOME_WITH_STAR):
            random_touch(exists(Assets.FIGHT_HOME_WITH_STAR))
        elif exists(Assets.FIGHT_HOME):
            random_touch(exists(Assets.FIGHT_HOME))
        else:
            log_msg("未找到任何战斗图标", level=0, log_path=get_log_path())
            raise Exception("未找到任何战斗图标")
    except Exception as e:
        log_msg(f"执行主世界战斗时发生错误: {e}", level=0, log_path=get_log_path())

    log_msg("正在搜寻对手...", log_path=get_log_path())
    _search_and_wait(first_search=True)
    while(1):
        if not _filter_with_resource(filter_config):
            log_msg("资源不满足条件，继续搜索下一个对手...", log_path=get_log_path())
            _search_and_wait(first_search=False)
            continue
        if faction == "dragon":
            anti_aircraft_positions = _detect_anti_aircraft_rocket()
            if len(anti_aircraft_positions) < 3:
                log_msg(f"有未识别的防空火箭，跳过该目标，继续搜索下一个对手...", log_path=get_log_path())
                _search_and_wait(first_search=False)
                continue
        break
            
    if faction == "dragon":
        _home_dragon_fight_logic(
            dragon_number=cfg.home_fight["dragon_number"],
            lightning_number=cfg.home_fight["lightning_number"],
            lightning_level=cfg.home_fight["lightning_level"],
        )
    
    _wait_the_battle_finish()

    try:
        random_touch(exists(Assets.BTN_BACK))
    except Exception as e:
        log_msg(f"未找到返回按钮: {e}", level=1, log_path=get_log_path())


def _filter_with_resource(filter_config=None):
    """根据资源多少过滤出高价值进攻目标"""
    cfg = get_config_manager()
    if filter_config is None:
        filter_config = cfg.home_filter

    ROI_GOLD = [200, 120, 250, 350]
    ROI_WATER = [275, 120, 325, 350]
    ROI_OIL = [350, 120, 400, 350]

    gold_amount = get_text_from_roi(ROI_GOLD).replace("O", "0").replace("o", "0").replace(",", "").replace(" ", "").replace("l", "1").replace("I", "1").replace("S", "5")
    water_amount = get_text_from_roi(ROI_WATER).replace("O", "0").replace("o", "0").replace(",", "").replace(" ", "").replace("l", "1").replace("I", "1").replace("S", "5")
    oil_amount = get_text_from_roi(ROI_OIL).replace("O", "0").replace("o", "0").replace(",", "").replace(" ", "").replace("l", "1").replace("I", "1").replace("S", "5")

    log_msg(f"识别到的资源数量 - 金币: {gold_amount}, 圣水: {water_amount}, 黑油: {oil_amount}", level=2, log_path=get_log_path())
    if gold_amount and int(gold_amount) < filter_config["gold"]:
        return False
    if water_amount and int(water_amount) < filter_config["water"]:
        return False
    if oil_amount and int(oil_amount) < filter_config["oil"]:
        return False
    
    log_msg(f"目标资源满足条件，金币: {gold_amount}, 圣水: {water_amount}, 黑油: {oil_amount}", level=1, log_path=get_log_path())
    return True


def _detect_anti_aircraft_rocket():
    """识别防空火箭等级与位置（当前仅识别 1-7 级模板）。"""
    level_template_map = {
        1: Assets.ANTI_AIRCRAFT_ROCKET1,
        2: Assets.ANTI_AIRCRAFT_ROCKET2,
        3: Assets.ANTI_AIRCRAFT_ROCKET3,
        4: Assets.ANTI_AIRCRAFT_ROCKET4,
        5: Assets.ANTI_AIRCRAFT_ROCKET5,
        6: Assets.ANTI_AIRCRAFT_ROCKET6,
        7: Assets.ANTI_AIRCRAFT_ROCKET7,
    }
    anti_aircraft_stats = _load_anti_aircraft_stats()

    raw_detects = []
    for level, template in level_template_map.items():
        matches = find_all(template)
        if not matches:
            continue
        for match in matches:
            raw_detects.append({
                "level": level,
                "position": match["result"],
                "confidence": float(match.get("confidence", 0.0)),
                "dp_second": anti_aircraft_stats[level]["dp_second"],
                "hitpoints": anti_aircraft_stats[level]["hitpoints"],
            })

    # 去重：同一位置可能被不同等级模板重复命中，保留置信度更高的一条。
    deduped = []
    merge_radius = 25
    for item in sorted(raw_detects, key=lambda x: x["confidence"], reverse=True):
        if any(_distance(item["position"], kept["position"]) <= merge_radius for kept in deduped):
            continue
        deduped.append(item)

    detail = ", ".join([f"L{item['level']}@{item['position']}" for item in deduped])
    log_msg(f"检测到 {len(deduped)} 个防空火箭: {detail}", level=1, log_path=get_log_path())
    return deduped


def _search_and_wait(first_search=True):
    if first_search:
        try:
            random_touch(exists(Assets.BTN_HOME_SEARCH))
        except Exception as e:
            log_msg(f"未找到搜索按钮: {e}", level=0, log_path=get_log_path())
    else:
        try:
            random_touch(exists(Assets.BTN_NEXT))
        except Exception as e:
            log_msg(f"未找到搜索下一个按钮: {e}", level=0, log_path=get_log_path())
    
    if exists(Assets.BTN_FIGHT_CONFIRM):
        random_touch(exists(Assets.BTN_FIGHT_CONFIRM))
        
    MAX_SEARCH_TIME = 50
    search_time = 0
    countdown_prompt = get_text_from_roi()
    while "开战倒计时" not in countdown_prompt and search_time < MAX_SEARCH_TIME:
        log_msg(f"匹配结果: {countdown_prompt}", level=2, log_path=get_log_path())
        log_msg(f"正在搜索对手，继续等待...", log_path=get_log_path())
        sleep(3)
        countdown_prompt = get_text_from_roi()
        search_time += 3