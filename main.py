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
from cocbot.home import run_home_world
from cocbot.night import run_night_world


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device",
        type=str,
        default="emulator-5554",
        help="设备 ID，例如 emulator-5554",
    )
    parser.add_argument(
        "--cap_method",
        type=str,
        choices=["MINICAP", "JAVACAP"],
        default="MINICAP",
        help="截图方式，模拟器推荐 MINICAP",
    )
    parser.add_argument(
        "--touch_method",
        type=str,
        choices=["MINITOUCH", "ADBTOUCH"],
        default="MINITOUCH",
        help="触控方式",
    )
    parser.add_argument(
        "--ori_method",
        type=str,
        choices=["ADBORI", "MINICAPORI"],
        default="ADBORI",
        help="方向获取方式",
    )
    parser.add_argument(
        "--loglevel",
        type=int,
        choices=[0, 1, 2],
        default=1,
        help="日志等级: 0=仅流程完成, 1=每一步操作, 2=全部日志",
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default="log",
        help="日志文件路径",
    )
    parser.add_argument(
        "--run_times",
        type=int,
        default=50,
        help="主循环执行次数，默认 50 次",
    )
    parser.add_argument(
        "--night_faction",
        type=str,
        choices=["witch", "archer"],
        default="witch",
        help="夜世界练兵流派，默认女巫 (witch)",
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=["tencent", "global"],
        default="tencent",
        help="游戏版本，可选值：tencent（腾讯版）或 global（国际服），默认 tencent",
    )
    parser.add_argument(
        "--night_retrain",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_retrain",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="是否重新训练模型，默认为 False，设置为 True 将删除现有配兵并重新训练",
    )
    parser.add_argument(
        "--home_battle",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否执行主世界战斗逻辑",
    )
    parser.add_argument(
        "--night_battle",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="是否执行夜世界战斗逻辑，默认为 True，设置为 False 将跳过夜世界战斗",
    )
    parser.add_argument(
        "--home_filter",
        type=str,
        default='{"gold": 400000, "water": 400000, "oil": 1500}',
        help="主世界战斗资源过滤配置，格式为 JSON 字符串，例如 '{\"gold\": 500000, \"water\": 500000, \"oil\": 1500}'",
    )
    parser.add_argument(
        "--home_faction",
        type=str,
        choices=["dragon", "electro_dragon"],
        default="dragon",
        help="主世界练兵流派，默认龙 (dragon)",
    )
    return parser.parse_args()


def main_loop():
    set_max_zoom_out()
    current_loc = detect_world()

    if current_loc == "HOME":
        run_home_world(
            retrain=args.home_retrain, 
            filter_config=eval(args.home_filter), 
            battle=args.home_battle, 
            faction=args.home_faction
        )
    elif current_loc == "NIGHT":
        run_night_world(
            faction=args.night_faction, 
            retrain=args.night_retrain, 
            battle=args.night_battle
        )
    else:
        log_msg("无法识别当前世界...", level=0)
        raise Exception("未知世界")


if __name__ == "__main__":
    args = parse_args()

    curr_path = os.path.dirname(__file__)
    log_path = os.path.join(curr_path, args.log_path)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    init_log(loglevel=args.loglevel, log_path=args.log_path)


    uri = build_airtest_uri(
        args.device,
        args.cap_method,
        args.touch_method,
        args.ori_method,
    )
    
    log_msg(f"连接设备: {uri}", level=0, log_path=log_path)
    delete_img_in_log(log_path)  # 开始时删除 log 目录下的图片文件，节省空间

    setup_runtime(__file__, uri, log_path, "D:/Programming/COC-bot")
    ensure_screenshot_ready(max_retries=5)

    log_msg("设备连接完成，进入主循环...")
    
    log_msg("启动游戏...")
    start_clash_of_clans(args.device, version=args.version)
    close_popups()
    
    for _ in range(args.run_times):  # 主循环，重复执行任务
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
            stop_clash_of_clans(args.device, version=args.version)
            sleep(10)
            log_msg("启动游戏...")
            start_clash_of_clans(args.device, version=args.version)
            close_popups()

