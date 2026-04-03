from ._assets import Assets
from .advanced import find_boat_and_switch
from .common import get_log_path, log_msg, random_touch, sleep, find_all, swipe


def run_home_world():
    log_msg("--- 正在处理主世界任务 ---", level=0, log_path=get_log_path())

    home_righting_pos()
    collect_resources_home([Assets.OIL, Assets.WATER, Assets.GOLD])
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
    swipe((1280, 300), (1280, 550), duration=0.5)
    sleep(0.5)