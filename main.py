# -*- encoding=utf8 -*-
__author__ = "CYM"

import argparse
import os
import random

from airtest.core.api import sleep

from cocbot.advanced import detect_world, set_max_zoom_out
from cocbot.common import (
    build_airtest_uri,
    close_popups,
    ensure_screenshot_ready,
    log_msg,
    init_log,
    setup_runtime,
    start_clash_of_clans,
    stop_clash_of_clans,
    delete_img_in_log,
)
from cocbot.config_manager import get_config_manager
from cocbot.home import run_home_world
from cocbot.night import run_night_world


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        type=str,
        default=None,
        help="全局配置 JSON 路径，复杂参数建议写入该文件",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="设备 ID，例如 emulator-5554",
    )
    parser.add_argument(
        "--cap_method",
        type=str,
        choices=["MINICAP", "JAVACAP"],
        default=None,
        help="截图方式，模拟器推荐 MINICAP",
    )
    parser.add_argument(
        "--touch_method",
        type=str,
        choices=["MINITOUCH", "ADBTOUCH"],
        default=None,
        help="触控方式",
    )
    parser.add_argument(
        "--ori_method",
        type=str,
        choices=["ADBORI", "MINICAPORI"],
        default=None,
        help="方向获取方式",
    )
    parser.add_argument(
        "--loglevel",
        type=int,
        choices=[0, 1, 2],
        default=None,
        help="日志等级: 0=仅流程完成, 1=每一步操作, 2=全部日志",
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default=None,
        help="日志文件路径",
    )
    parser.add_argument(
        "--run_times",
        type=int,
        default=None,
        help="主循环执行次数，默认 50 次",
    )
    parser.add_argument(
        "--home_attempts",
        type=int,
        default=None,
        help="每轮主世界最大进攻尝试次数",
    )
    parser.add_argument(
        "--night_attempts",
        type=int,
        default=None,
        help="每轮夜世界最大进攻尝试次数",
    )
    parser.add_argument(
        "--night_faction",
        type=str,
        choices=["witch", "archer"],
        default=None,
        help="夜世界练兵流派，默认女巫 (witch)",
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=["tencent", "global"],
        default=None,
        help="游戏版本，可选值：tencent（腾讯版）或 global（国际服），默认 tencent",
    )
    parser.add_argument(
        "--night_retrain",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_retrain",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_battle",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="是否执行主世界战斗逻辑",
    )
    parser.add_argument(
        "--night_battle",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="是否执行夜世界战斗逻辑，默认为 True，设置为 False 将跳过夜世界战斗",
    )
    parser.add_argument(
        "--home_filter",
        type=str,
        default=None,
        help="主世界战斗资源过滤配置，格式为 JSON 字符串，例如 '{\"gold\": 500000, \"water\": 500000, \"oil\": 1500}'",
    )
    parser.add_argument(
        "--home_faction",
        type=str,
        choices=["dragon", "electro_dragon"],
        default=None,
        help="主世界练兵流派，默认龙 (dragon)",
    )
    parser.add_argument(
        "--home_fight_config_path",
        type=str,
        default=None,
        help="主世界战斗参数 JSON 路径，包含 dragon_number/lightning_number/lightning_level",
    )
    parser.add_argument(
        "--lightning_data_path",
        type=str,
        default=None,
        help="闪电法术数据 CSV 路径",
    )
    parser.add_argument(
        "--anti_aircraft_data_path",
        type=str,
        default=None,
        help="防空火箭数据 CSV 路径",
    )
    return parser.parse_args()


def main_loop():
    set_max_zoom_out()
    current_loc = detect_world()

    if current_loc == "HOME":
        run_home_world()
    elif current_loc == "NIGHT":
        run_night_world()
    else:
        log_msg("无法识别当前世界...", level=0)
        raise Exception("未知世界")


if __name__ == "__main__":
    args = parse_args()
    cfg = get_config_manager().load(args)

    log_path = cfg.log_path
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    init_log(loglevel=cfg.loglevel, log_path=cfg.log_path)


    uri = build_airtest_uri(
        cfg.device,
        cfg.cap_method,
        cfg.touch_method,
        cfg.ori_method,
    )
    
    log_msg(f"连接设备: {uri}", level=0, log_path=log_path)
    delete_img_in_log(log_path)  # 开始时删除 log 目录下的图片文件，节省空间

    setup_runtime(__file__, uri, log_path, cfg.project_root)
    ensure_screenshot_ready(max_retries=5)

    log_msg("设备连接完成，进入主循环...")
    
    log_msg("启动游戏...")
    start_clash_of_clans(cfg.device, version=cfg.version)
    close_popups()
    
    for _ in range(cfg.run_times):  # 主循环，重复执行任务
        try:
            log_msg(f"第 {_ + 1} 轮主循环开始", level=0)
            main_loop()
            log_msg(f"第 {_ + 1} 轮主循环完成，等待 30 秒后继续...", level=0)

            delete_img_in_log(log_path)  # 每次循环结束后删除 log 目录下的图片文件，节省空间
            sleep_time = random.randint(25, 35)  # 随机等待 25 - 35 秒，模拟人类行为
            sleep(sleep_time)
        except Exception as e:
            log_msg(f"主循环出错: {e}", level=0)
            delete_img_in_log(log_path)  # 每次循环结束后删除 log 目录下的图片文件，节省空间
            log_msg("尝试停止游戏并重新启动...", level=0)
            stop_clash_of_clans(cfg.device, version=cfg.version)
            sleep(10)
            log_msg("启动游戏...")
            start_clash_of_clans(cfg.device, version=cfg.version)
            close_popups()

